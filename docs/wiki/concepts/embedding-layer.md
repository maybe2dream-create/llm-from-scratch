# Embedding Layer

[tokenization](tokenization.md)에서 확인했듯, 토큰 ID는 그 자체로 의미가 없는 숫자다 — `sorted()`가 정한 우연한 순서일 뿐인데 신경망은 그걸 크기가 있는 수로 받아들인다. 임베딩 레이어는 이 문제를 푸는 자리다: **정수 ID 하나를, 학습을 통해 의미를 담을 수 있는 실수 벡터로 바꾼다.**

## `nn.Embedding`은 룩업 테이블이다

```python
embedding_layer = torch.nn.Embedding(num_embeddings=vocab_size, embedding_dim=output_dim)
```

내부적으로 `(vocab_size × output_dim)` 크기의 행렬(`embedding_layer.weight`) 하나를 만든다. 행 하나가 토큰 하나에 대응한다. `embedding_layer(token_id)`는 그 행을 그대로 꺼내오는 것 — 계산이 아니라 조회(lookup)다.

**shape 규칙:** 임베딩을 거치면 맨 뒤에 `output_dim` 차원이 하나 붙는다. `[4]` → `[4, 3]`, `[8, 4]` → `[8, 4, 256]`.

## 조회 = 원-핫 × 행렬 곱

```
one-hot for ID 3   = [0, 0, 0, 1, 0, 0]
one-hot  @  weight = [-0.4015, 0.9666, -1.1481]
weight[3]          = [-0.4015, 0.9666, -1.1481]      torch.allclose -> True
```

원-핫 벡터는 한 자리만 1이라 행렬과 곱하면 그 행만 남는다. 조회는 이 곱셈의 지름길이다. **행렬 곱이라는 건 이 표가 평범한 신경망 층이라는 뜻이고, 따라서 역전파로 학습된다.** 출력의 `requires_grad=True`, `grad_fn=<EmbeddingBackward0>`가 그 표시다.

## `vocab_size` vs `output_dim` — 성격이 다른 두 숫자

| | 누가 정하는가 | 의미 |
|---|---|---|
| `vocab_size` | 토크나이저 (고정값, 못 바꿈) | 서로 다른 토큰이 몇 개인가 (gpt2 BPE는 50,257) |
| `output_dim` | 모델 설계자 (하이퍼파라미터) | 토큰 하나를 몇 개의 실수로 표현할 것인가 |

숫자 하나가 아니라 `output_dim`개가 필요한 이유: 의미는 한 개의 축이 아니다. 품사, 감정, 격식 등 여러 축을 동시에 표현하려면 축의 개수만큼 숫자가 필요하다. 책의 장난감 예제는 `output_dim=3`, 실전 규모는 `256`을 썼다 (GPT-2 small은 768, GPT-3는 12,288).

## `torch.manual_seed(123)` — 재현성

```python
torch.manual_seed(123)
embedding_layer = torch.nn.Embedding(vocab_size, output_dim)
```

`nn.Embedding`의 초기 weight는 무작위(표준정규분포)로 채워진다. 이 "무작위"는 사실 의사난수 — 시드라는 시작점에서 정해진 규칙으로 다음 숫자들을 만들어낸다. 시드를 고정하지 않으면 실행할 때마다 다른 값이 나와서, [tokenization](tokenization.md)에서 이미 확인한 검증 습관("책이 적어둔 숫자와 대조하는 것 말고는 발견할 방법이 없다")이 애초에 성립하지 않는다.

**함정:** `manual_seed`는 "그 시점 이후 다음 무작위 연산"에만 적용된다. `nn.Embedding` 생성 직전에 호출해야 하며, 그 사이에 다른 무작위 연산이 끼어들면(다른 레이어 생성, `shuffle=True` DataLoader 등) 난수 생성기의 내부 상태가 그만큼 진행되어 같은 시드를 줘도 다른 값이 나온다.

## 실제 사용 — [sliding-window-sampling](sliding-window-sampling.md)과의 연결

```python
inputs, targets = next(iter(dataloader))     # shape: (batch_size, max_length)
token_embeddings = token_embedding(inputs)   # shape: (batch_size, max_length, output_dim)
```

DataLoader가 뽑아낸 정수 ID 배치를 그대로 임베딩 레이어에 넣으면, 각 ID가 `output_dim` 길이의 벡터로 치환되어 텐서에 차원 하나가 추가된다.

## 아직 남은 한계

이 임베딩은 **같은 토큰이면 문장 어디에 있든 항상 같은 벡터**를 준다. 어순 정보가 없다 — 다음 개념 [positional-embedding.md](positional-embedding.md)가 이 한계를 다룬다.

## 검증된 사실

- 장난감 예제 (`seed=123, vocab_size=6, output_dim=3`): `embedding_layer(torch.tensor([3]))` → `[-0.4015, 0.9666, -1.1481]`
- 실전 규모 (`vocab_size=50257, output_dim=256`), `batch_size=8, max_length=4`: `token_embeddings.shape == torch.Size([8, 4, 256])`
- 실수 사례: `embedding_layer`(장난감, vocab_size=6)로 실제 GPT-2 토큰 ID(예: 2885)를 조회하면 `IndexError: index out of range in self` — 이름은 존재하지만 가리키는 대상(그리고 그 vocab_size)이 맞지 않았던 경우.

## 참고

- 개념 질의응답 상세: `docs/LLM_Embedding_OutputDim_and_Seed_Explained.pdf` (마크다운 원본 없음 — 정책 이전 자료, [wiki README](../README.md) 참고)
- 구현·디버깅: [session 04](../../LLM_project_session_04.md) §2
- 2.7·2.8 통합 해설: `docs/Token_and_Positional_Embeddings_Explained.pdf` (이 문서와 positional-embedding.md에서 생성)
- 이전 개념: [sliding-window-sampling.md](sliding-window-sampling.md)
- 다음 개념: [positional-embedding.md](positional-embedding.md)
