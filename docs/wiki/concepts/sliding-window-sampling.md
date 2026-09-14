# Sliding Window Sampling

토크나이저가 텍스트 전체를 정수 ID 하나의 긴 나열로 바꿔놓으면, 그다음 문제는 "이걸 어떻게 학습 예제로 자르는가"다. 다음 토큰 예측 모델의 학습 목표는 단순하다 — **연속된 토큰 몇 개(input)를 보고 그다음 토큰(target)을 맞힌다.**

## 기본 아이디어

```python
context_size = 4
x = enc_sample[:context_size]        # 입력
y = enc_sample[1:context_size+1]     # 타깃 — x보다 정확히 한 칸 밀림
```

`x`와 `y`는 같은 시퀀스에서 시작점이 하나 다를 뿐이다. 이걸 `context_size`번 반복하면, 하나의 윈도우 안에서 "토큰 1개 보고 다음 맞히기"부터 "토큰 `context_size`개 보고 다음 맞히기"까지 전부 학습 예제가 된다:

```
[290] ----> 4920
[290, 4920] ----> 2241
[290, 4920, 2241] ----> 287
[290, 4920, 2241, 287] ----> 257
```

## PyTorch `Dataset`/`DataLoader`로 일반화

```python
class GPTDatasetV1(Dataset):
    def __init__(self, text, tokenizer, max_length, stride):
        self.input_ids, self.target_ids = [], []
        token_ids = tokenizer.encode(text)
        for i in range(0, len(token_ids) - max_length, stride):
            input_chunk = token_ids[i : i + max_length]
            target_chunk = token_ids[i + 1 : i + max_length + 1]   # target은 input보다 한 칸 밀림
            self.input_ids.append(torch.tensor(input_chunk))
            self.target_ids.append(torch.tensor(target_chunk))

    def __len__(self):
        return len(self.input_ids)

    def __getitem__(self, idx):
        return self.input_ids[idx], self.target_ids[idx]
```

`max_length`는 한 윈도우의 길이(=위 예시의 `context_size`), `stride`는 다음 윈도우를 얼마나 밀고 시작할지다.

## `stride`가 하는 일 — 왜 그냥 `max_length`만큼 밀지 않는가

- `stride == max_length`: 윈도우끼리 겹치지 않는다. 텍스트를 낭비 없이 딱 나눠 쓰지만, 학습 예제 수가 적다.
- `stride < max_length`: 윈도우가 겹친다. 같은 텍스트로 더 많은 학습 예제를 뽑을 수 있지만, 겹치는 부분이 많을수록 예제 간 상관관계가 커져 과적합 위험도 커진다.

`stride`는 "텍스트 하나에서 몇 개의 학습 신호를 뽑아낼 것인가"와 "그 신호들이 서로 얼마나 독립적인가" 사이의 트레이드오프를 조절하는 손잡이다.

## 검증된 사실

- `batch_size=1, max_length=4, stride=1`: 첫 배치 입력 `[40, 367, 2885, 1464]`, 타깃 `[367, 2885, 1464, 1807]` — 정확히 한 칸 밀림.
- `batch_size=8, max_length=4, stride=4` (겹치지 않음): 8개 윈도우가 한 배치로 묶여 나옴.

## 참고

- 구현·디버깅 (이름 관련 버그 넷): [session 04](../../LLM_project_session_04.md) §1
- 다음 개념: [embedding-layer.md](embedding-layer.md) — 여기서 나온 정수 ID 배치가 임베딩 레이어의 입력이 된다.
