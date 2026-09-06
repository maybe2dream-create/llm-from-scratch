# LLM from Scratch — Session 04

**날짜:** 2026년 9월 6일
**주제:** 2.6 슬라이딩 윈도우 데이터 샘플링 · 2.7 토큰 임베딩
**직전 세션:** [LLM_project_session_03.md](LLM_project_session_03.md) (2026.9.5, 커밋 `e133cff`)
**커밋:** 없음 — §6 참고

---

## 0. 이 세션의 성격

전날 세션 03이 끝난 지점(2.4절, `SimpleTokenizerV1`까지)에서 이어서, 2.5절 BPE(`tiktoken`)를 거쳐 2.6절 슬라이딩 윈도우, 2.7절 토큰 임베딩까지 진행했다. 코드는 계속 `bpe.ipynb`(루트, 미커밋)에 직접 타이핑하는 방식을 유지했다.

세션 03에서 세운 원칙 — "코드는 직접 입력한다, Claude는 검토·디버깅 역할" — 이 그대로 이어졌다. 오늘 새로 나온 버그 넷 중 셋이 다시 "이름이 어긋나는" 유형이었고, 본인이 직접 "name 관리도 쉽지 않군요"라고 짚었다. 세 세션 연속 같은 패턴이 나오는 중이다.

---

## 1. 2.5~2.6절 — BPE와 슬라이딩 윈도우

`tiktoken.get_encoding("gpt2")`로 BPE 인코딩을 확인했다. 어휘 밖 단어 `someunknownPlace`, 없는 단어 `Akwirw ier`도 `<|unk|>` 없이 조각으로 쪼개져 왕복(encode→decode)이 그대로 성립하는 것을 확인 — 세션 03에서 남긴 예고("어떻게 조각나는지 직접 본다")가 여기서 풀렸다.

`enc_sample`에서 `context_size=4`로 x/y 쌍을 만드는 절차를 먼저 손으로 확인한 뒤, `GPTdatasetV1`(PyTorch `Dataset`)과 `create_dataloader_v1` 함수로 옮겼다.

### `GPTdatasetV1`에서 나온 버그 넷 — 하나의 셀에서 한 번에

```python
class GPTdatasetV1(Dataset):
    def __init__(self, text, tokenizer, max_length, stride):
        ...
        token_ids = tokenizer.encode(txt)                      # ① text로 받고 txt를 씀
        for i in range(0, len(token_ids) - max_length, stride):
            input_chunk = token_ids[i:i + max_length]
            target_chunk = token_ids[i + i: i + max_length + 1]  # ② i+1이어야 할 자리에 i+i
            ...
    def __getitem__(self, idx):
        return self.input_idss[idx], self.target_ids[ids]        # ③ input_idss 오타  ④ ids는 idx여야 함
```

| # | 무엇 | 유형 | 왜 |
|---|---|---|---|
| ① | `tokenizer.encode(txt)` | B (에러 남) | 매개변수는 `text`인데 몸통은 `txt`. `NameError`가 즉시 나서 나머지 셋을 가려버림 |
| ② | `token_ids[i + i : ...]` | **A (에러 없음)** | `i+1`이어야 할 자리에 `i+i`. `i=0`일 때는 우연히 값이 같아 안 보이다가 `i`가 커지면 target이 계속 더 크게 밀림 |
| ③ | `self.input_idss[idx]` | B (에러 남) | `__init__`에서 만든 적 없는 이름. `AttributeError` |
| ④ | `self.target_ids[ids]` | B (에러 남) | 매개변수는 `idx`인데 `ids`. `NameError` |

①을 고쳐야 ③·④가 보이는 구조였다 (인스턴스 생성 시점에 ①이 바로 터지므로). ②는 에러가 안 나서 따로, `x`/`y` 데모 결과와 대조해서 잡았다.

**최종 확인:** `batch_size=1, max_length=4, stride=1`로 `[tensor([[40, 367, 2885, 1464]]), tensor([[367, 2885, 1464, 1807]])]` — 한 칸씩 밀린 입력/타깃 쌍을 확인. 이후 `batch_size=8`까지 확장해서 `create_dataloader_v1`로 정리.

---

## 2. 2.7절 — 토큰 임베딩

### 장난감 예제 → 실전 규모

```python
# 장난감 (vocab_size=6, output_dim=3)
torch.manual_seed(123)
embedding_layer = torch.nn.Embedding(num_embeddings=6, embedding_dim=3)

# 실전 규모 (gpt2 어휘 그대로)
vocab_size = 50257
output_dim = 256
token_embedding = torch.nn.Embedding(num_embeddings=vocab_size, embedding_dim=output_dim)
```

여기서 **`output_dim`과 `torch.manual_seed(123)`이 각각 무엇이고 왜 쓰는지** 질문이 나와서, 별도 PDF로 답했다 — `docs/LLM_Embedding_OutputDim_and_Seed_Explained.pdf` (gitignore 대상이라 로컬에만 있음). 요지:

- **output_dim**: 토큰 하나를 몇 개의 실수로 표현할지 정하는 하이퍼파라미터. `vocab_size`(토크나이저가 고정)와 성격이 다르다. 세션 03의 "어휘 ID에는 의미가 없다"는 관찰이 이 절의 동기 그 자체 — 정수 하나로는 못 담는 유사성을, output_dim개의 실수 벡터로는 학습을 통해 담을 수 있다.
- **torch.manual_seed(123)**: nn.Embedding의 weight는 무작위(의사난수)로 초기화되는데, 시드를 고정해야 책의 숫자와 대조할 기준이 생긴다. 함정: 시드는 "그 시점 이후 다음 무작위 연산"에만 적용되므로, 호출 시점과 순서가 어긋나면 같은 123을 줘도 다른 값이 나올 수 있다.

### 실전 임베딩 조회에서 나온 버그 — 두 단계짜리

```python
token_embeddings = embedding_layer(inputs)          # (1차 시도)
# IndexError: index out of range in self

token_embeddings = token_embedding_layer(inputs)     # (2차 시도, 고치다가)
# NameError 예정 — 이 이름은 어디에도 정의된 적 없음
```

| 시도 | 참조한 이름 | 문제 |
|---|---|---|
| 1차 | `embedding_layer` | **존재는 하는 이름**이지만 장난감 예제(`vocab_size=6`)를 가리킴. `inputs`는 실제 GPT-2 토큰 ID(`2885` 등)라 테이블 크기를 넘어서 `IndexError` |
| 2차 | `token_embedding_layer` | **존재하지 않는 이름**. 앞 셀에서 실제로 만든 건 `token_embedding` |

같은 셀에서 "맞는 이름인데 틀린 대상을 가리킴"과 "아예 없는 이름"을 연달아 만난 셈이다. 정답은 `token_embedding`. 고친 뒤 `torch.Size([8, 4, 256])`로 성공 — `batch_size=8, max_length=4, output_dim=256`이 그대로 shape에 찍혔다.

> **패턴 확인, 세 번째.** 세션 03의 유형 A/B 구분이 오늘도 그대로 반복됐다: 넷 중 셋이 "이름은 문법적으로 멀쩡한데 가리키는 대상이 어긋난" 오타였다. 본인 표현으로 "코딩할 때 문법의 오류보다 오타에 의한 오류가 많다" — 두 세션 연속 관찰이라 우연이 아니라 특징으로 봐도 될 것 같다.

---

## 3. 검증된 숫자 (이번 세션)

| 항목 | 값 |
|---|---|
| gpt2 BPE, 테스트 문장 토큰 수 | 20 |
| the-verdict.txt, gpt2 BPE 토큰 수 | 5,145 |
| GPTDatasetV1 첫 배치 (batch=1, max_length=4) | 입력 `[40, 367, 2885, 1464]` / 타깃 `[367, 2885, 1464, 1807]` |
| 토큰 임베딩 최종 shape (batch=8, max_length=4, output_dim=256) | `torch.Size([8, 4, 256])` |
| 장난감 임베딩 (seed=123, vocab=6, dim=3) 확인용 | `embedding_layer(torch.tensor([3]))` → `[-0.4015, 0.9666, -1.1481]` |

---

## 4. 저장소 상태 — 정리 안 됨, 커밋 없음

```
D  Untitled.ipynb   (삭제됐지만 아직 git rm 안 함 — 세션 03부터 판단 대기)
?? bpe.ipynb        (오늘 작업 전체가 여기 들어있음, 미추적)
```

세션 03 §7의 정리안(파일 구조 정돈)은 **오늘도 손대지 않았다** — 원래 계획대로 "2장을 끝낸 뒤"로 미룬 것이라 의도된 것이다. 다만 오늘 작업분이 **아직 한 번도 커밋되지 않았다.** 세션 02가 지적하고 세션 03이 고쳤던 "당일 커밋" 습관이 이번엔 다시 끊겼다 — 다음 세션 시작 전에 최소한 `bpe.ipynb`만이라도 커밋해두는 게 안전하다 (2.8절 작업 중 실수로 되돌리면 오늘 것 전부 날아간다).

---

## 5. 다음 세션 — 2.8 Encoding word positions

이번 절이 2.7의 한계에서 곧바로 이어진다: 지금 만든 `token_embedding`은 **같은 토큰이면 문장 어디에 있든 항상 같은 벡터**를 준다. "그 강아지가 문다"와 "문 강아지가 그렇다" 같은 어순 차이를 구별할 방법이 없다는 뜻이다. 2.8절이 여기에 위치 정보를 더하는 절이다.

### 시작 전 확인할 것

- `bpe.ipynb` 커밋부터 (§4)
- 이어서 타이핑할 위치: 지금까지와 같은 `bpe.ipynb`. 임베딩과 같은 2.7~2.8절 흐름이라 새 노트북으로 쪼갤 이유가 없다 (세션 03 §7의 "노트북 → src, 실험 중엔 한 파일" 원칙 그대로)

---

## 6. 총평

**잘된 것.** 2.6~2.7절을 하루에 끝냈고, 버그를 만날 때마다 세션 03의 유형 A/B 구분을 그대로 적용해서 원인을 빠르게 좁혔다. `output_dim`/`seed`처럼 코드로 안 잡히는 개념 질문은 코드를 직접 건드리지 않고 별도로 질의해서 타이핑 흐름을 안 끊었다.

**부족한 것.** 커밋이 다시 빠졌다 (§4). 세션 02→03에서 고쳤던 문제가 재발했다는 것은, "당일 커밋"이 아직 습관으로 굳지 않았다는 뜻이다.

**기록해 둘 것.** 오늘 버그 넷 중 셋, 그리고 임베딩 조회 버그의 1차 시도까지 포함하면 사실상 다섯 번 전부가 "이름은 문법적으로 유효하지만 가리키는 대상이 어긋남" 유형이었다. 세션 03이 이걸 유형 A/B로 나눴을 때는 하루짜리 관찰이었지만, 오늘로 두 번째다. 본인도 "name 관리도 쉽지 않다"고 직접 짚었다 — 다음에 비슷한 에러가 나면 "오타인가?"를 제일 먼저 의심해볼 만하다.
