# Tokenization

LLM은 글자나 단어를 직접 읽지 않는다. 정수 하나하나로 바뀐 것만 받는다. 토큰화는 그 변환의 첫 단계 — 텍스트를 작은 단위(토큰)로 쪼갠 뒤, 각 토큰에 정수 ID를 부여하는 과정이다.

## 두 가지 접근

### 1. 정규식 기반 (직접 구현, `SimpleTokenizerV1`)

```python
SPLIT_PATTERN = r'([,.:;?_!"()\']|--|\s)'

def preprocess(text):
    preprocessed = re.split(SPLIT_PATTERN, text)
    return [item.strip() for item in preprocessed if item.strip()]

def build_vocab(text):
    all_words = sorted(set(preprocess(text)))
    return {token: integer for integer, token in enumerate(all_words)}
```

단어와 구두점 단위로 쪼갠 뒤, 훈련 코퍼스에 등장한 단어만으로 어휘를 만든다. 근본적 한계: **어휘 밖 단어를 표현할 방법이 없다.** 훈련 코퍼스에 없던 단어를 만나면 `KeyError`로 죽는다 (`SimpleTokenizerV1`). 이 한계를 메우려고 특수 토큰 `<|unk|>`(모르는 단어), `<|endoftext|>`(문서 경계)를 도입하면 `SimpleTokenizerV2`가 된다 — 죽는 대신 `<|unk|>`로 치환하지만, **그 순간 원래 단어 정보는 되돌릴 수 없이 사라진다** (`Hello`와 `palace`가 둘 다 `<|unk|>`가 되면 서로 구별이 안 됨).

### 2. BPE — Byte Pair Encoding (`tiktoken`)

```python
tokenizer = tiktoken.get_encoding("gpt2")
ids = tokenizer.encode(text, allowed_special={"<|endoftext|>"})
```

어휘 밖 단어를 통째로 버리는 대신, **아는 조각들로 쪼갠다.** 예: 어휘에 없는 `someunknownPlace`도 `<|unk|>` 없이 인코딩되고, `decode(encode(x)) == x`가 항상 성립한다 (완전한 왕복). GPT-2 어휘는 50,257개 토큰이다.

## 왜 정규식 기반 V1/V2로 먼저 만들어보는가

BPE가 왜 필요한지는 정규식 기반 토크나이저의 실패(어휘 밖 단어에서 죽거나, `<|unk|>`로 정보를 잃는 것)를 직접 겪어봐야 체감된다. BPE의 "조각으로 쪼갠다"는 해법은, "통째로 버린다"는 문제를 먼저 겪지 않으면 왜 좋은 아이디어인지 와닿지 않는다.

## 토큰 ID에는 의미가 없다

```python
vocab = {token: integer for integer, token in enumerate(sorted(set(...)))}
```

`sorted()`는 유니코드 코드포인트 순으로 정렬할 뿐이다. 구두점(33~63) < 대문자(65~90) < 소문자(97~122) 순서가 그대로 ID 순서가 된다. `'a'`가 115번인 데는 아무 의미가 없고, 114번·116번과 의미상 관계가 없다. **그런데 신경망 입장에서 115는 114보다 큰 수다.** 이 "의미 없는 순서에 수치적 크기가 부여되는 문제"가 다음 개념인 [embedding-layer](embedding-layer.md)의 동기가 된다.

## 검증된 사실

- 검증에는 눈으로 보는 "그럴듯함"이 아니라 **기준값과의 대조**가 필요하다. 정규식 문자 하나(홑따옴표 vs 쌍따옴표), 공백 하나 차이로 토큰 수가 조용히 달라지는데, 실행은 에러 없이 성공한다.
- `the-verdict.txt` 기준값: 20,479자 → 4,690토큰 (정규식 기반), 5,145토큰 (`tiktoken` gpt2 BPE). 두 토크나이저가 같은 텍스트를 다른 크기로 쪼갠다는 것 자체가 "토큰"이 고정된 단위가 아니라 **토크나이저가 정의하는 것**이라는 증거다.

## 참고

- 처음 구현: [session 02](../../LLM_project_session_02.md)
- 재구현·버그 다섯 개: [session 03](../../LLM_project_session_03.md) §1~2
- BPE 도입: [session 04](../../LLM_project_session_04.md) §1
- 구현: [src/tokenizer.py](../../../src/tokenizer.py)
