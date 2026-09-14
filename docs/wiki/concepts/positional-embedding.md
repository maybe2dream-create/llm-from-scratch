# Positional Embedding

[embedding-layer](embedding-layer.md)의 토큰 임베딩은 행 번호만 보고 벡터를 꺼낸다. 같은 토큰이면 문장 몇 번째 자리에 있든 똑같은 벡터가 나온다. 위치 임베딩은 이 공백을 메운다 (책 2.8절).

## 문제 — 실제 데이터에서

첫 배치(`batch_size=8, max_length=4, stride=4`) 안에 토큰 257(`" a"`)이 두 번 나온다.

```
inputs[2] = [10899, 2138, [257], 7026]    position 2
inputs[3] = [15632,  438, 2016, [257]]    position 3

torch.equal(token_embeddings[2, 2], token_embeddings[3, 3])  ->  True
```

자리가 다른데 벡터가 소수점 끝까지 같다. 어텐션은 이 벡터만 받으므로 둘을 구별할 수 없다 ([query-key-value.md](query-key-value.md)에서 `The`/`the`가 같은 점수 0.11을 받은 것과 같은 현상).

## 해법 — 자리 번호도 표에서 찾는다

```python
context_length = max_length                                         # 4
pos_embedding_layer = torch.nn.Embedding(context_length, output_dim)  # 4 x 256
pos_embeddings = pos_embedding_layer(torch.arange(max_length))        # [4, 256]
input_embeddings = token_embeddings + pos_embeddings                  # [8, 4, 256]
```

**클래스도 원리도 토큰 임베딩과 같다. 첫 번째 인자가 무엇을 세느냐만 다르다.**

| | token_embedding_layer (2.7) | pos_embedding_layer (2.8) |
|---|---|---|
| 표 크기 | 50,257 × 256 | 4 × 256 |
| 행 하나의 뜻 | 어휘 속 토큰 하나 | 문장 속 자리 하나 |
| 조회에 쓰는 번호 | 토큰 ID (`inputs`) | 자리 번호 (`torch.arange(4)` = `[0, 1, 2, 3]`) |
| 결과 shape | `[8, 4, 256]` | `[4, 256]` |
| 답하는 질문 | 무슨 토큰인가? | 몇 번째 자리인가? |

위치 쪽에 배치 차원(8)이 없는 이유: 자리 번호는 문장과 무관하다. 8개 문장 모두 0~3번 자리로 똑같으니 한 벌만 만든다.

## 더하기와 브로드캐스팅

`[8, 4, 256] + [4, 256]`이 에러 없이 `[8, 4, 256]`이 되는 건, PyTorch가 `[4, 256]` 한 벌을 8개 문장 각각에 복사해 더하기 때문이다. 뒤쪽 차원부터 맞추고, 앞쪽에 없는 차원은 늘려 채운다.

| 문장 | 자리 | 토큰 | 토큰 벡터 | + 위치 벡터 | = 결과 |
|---|---|---|---|---|---|
| 1 | 0 | **a** | [1, 0] | [0.5, -0.5] | **[1.5, -0.5]** |
| 1 | 1 | cat | [0, 2] | [-0.5, 0.5] | [-0.5, 2.5] |
| 1 | 2 | sat | [2, 2] | [0, 1] | [2, 3] |
| 2 | 0 | dog | [0, 3] | [0.5, -0.5] | [0.5, 2.5] |
| 2 | 1 | **a** | [1, 0] | [-0.5, 0.5] | **[0.5, 0.5]** |
| 2 | 2 | sat | [2, 2] | [0, 1] | [2, 3] |

**같은 토큰 + 다른 자리 = 다른 벡터. 같은 토큰 + 같은 자리 = 같은 벡터.** (위치 벡터 값에 증가 규칙은 없다 — 무작위로 시작해 학습된다.)

실제 데이터로 확인:

```
torch.equal(token_embeddings[2, 2], token_embeddings[3, 3])   ->  True   (before)
torch.equal(input_embeddings[2, 2], input_embeddings[3, 3])   ->  False  (after)
```

## 왜 이어 붙이지 않고 더하는가

이어 붙이면 512차원이 되고 이후 모든 층이 커진다. 더하면 256 그대로다. 두 표 모두 학습되므로 모델이 서로 방해하지 않게 값을 조정한다. GPT-2가 쓰는 방식이고, 경험적으로 잘 작동한다.

## 절대 위치 임베딩의 한계

위치 표의 행은 `context_length`개뿐이다. 더 긴 입력은 꺼낼 행이 없다.

```
pos_embedding_layer(torch.arange(5))   ->  IndexError: index out of range in self
```

세션 04에서 장난감 표(행 6개)에 GPT-2 ID 2885를 넣었을 때와 **같은 에러, 같은 원인** — 표에 없는 행 번호를 요구했다. GPT-2는 `context_length=1024`라 1,025번째 토큰부터 처리할 수 없다. 상대 위치 방식(Llama의 RoPE 등)은 이 제약을 완화하려는 설계지만, 책은 GPT-2를 따라 절대 방식을 쓴다.

## 검증 기준 — 값이 아니라 shape

2.8절 코드의 두 레이어에는 `manual_seed`가 없어서 실행할 때마다 값이 다르다. 대조할 것은 shape이다: `[8, 4]` → `[8, 4, 256]`, `arange` → `[0, 1, 2, 3]`, `[4, 256]`, 최종 `[8, 4, 256]`.

## 참고

- 2.7·2.8 통합 해설: `docs/Token_and_Positional_Embeddings_Explained.pdf`
- 이전 개념: [embedding-layer.md](embedding-layer.md)
- 다음 개념: [query-key-value.md](query-key-value.md)
