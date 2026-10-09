# embed_exec.py — Annabel Lee로 따라가는 Chapter 2 파이프라인

`docs/Chapter2_Pipeline_Flowchart.pdf`의 흐름(원본 텍스트 → BPE → 슬라이딩 윈도우 → 토큰 임베딩 → 위치 임베딩 → 입력 임베딩)을
책의 `the-verdict.txt`가 아닌 Edgar Allan Poe의 *Annabel Lee*로 다시 실행한 스크립트.

- 작성일: 2026-09-14
- 입력 파일: `experiments/ch02/embedding_exec/annabel_lee.txt` (제목·저자 줄 포함, 들여쓰기는 일반 공백)
- 실행: 저장소 루트에서 실행한다 (파일 경로가 루트 기준 상대경로).

```bash
python experiments/ch02/embedding_exec/embed_exec.py
```

## 소스 코드

```python
import tiktoken
import torch
from torch.utils.data import Dataset, DataLoader
tokenizer = tiktoken.get_encoding("gpt2")
with open("experiments/ch02/embedding_exec/annabel_lee.txt", "r", encoding="utf-8") as f:
    raw_text = f.read()

class GPTDatasetV1(Dataset):
    def __init__(self, txt, tokenizer, max_length, stride):
        self.input_ids = []
        self.target_ids = []

        token_ids = tokenizer.encode(txt)

        for i in range(0, len(token_ids) - max_length, stride):
            input_chunk = token_ids[i:i + max_length]
            target_chunk = token_ids[i + 1:i + max_length + 1]
            self.input_ids.append(torch.tensor(input_chunk))
            self.target_ids.append(torch.tensor(target_chunk)) 

    def __len__(self):
        return len(self.input_ids)

    def __getitem__(self, idx):
        return self.input_ids[idx], self.target_ids[idx]
def create_dataloader_v1(txt, batch_size=4, max_length=128, stride=64,
                         shuffle=True, drop_last=True, num_workers=0):  
    tokenizer = tiktoken.get_encoding("gpt2")
    dataset = GPTDatasetV1(txt, tokenizer, max_length, stride)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=shuffle, drop_last=drop_last, num_workers=num_workers)
    return dataloader
max_length = 4
batch_size = 8
dataloader = create_dataloader_v1(raw_text, batch_size=batch_size, max_length=max_length, stride=max_length, shuffle=False)
data_iter = iter(dataloader)
inputs, targets = next(data_iter)
vocab_size = 50257
output_dim = 128
torch.manual_seed(123)
token_embedding_layer = torch.nn.Embedding(vocab_size, output_dim)
token_embeddings = token_embedding_layer(inputs)
context_length = max_length
pos_embedding_layer = torch.nn.Embedding(context_length, output_dim)
pos_embeddings = pos_embedding_layer(torch.arange(context_length))
input_embeddings = token_embeddings + pos_embeddings
print(input_embeddings.shape)
```

## 실행 결과

```
torch.Size([8, 4, 128])
```

## 단계별로 확인한 값

스크립트가 출력하는 것은 마지막 shape 하나지만, 작성 과정에서 각 단계를 출력해 확인했다.

| 흐름도 단계 | 확인한 값 |
|---|---|
| 2.5 BPE 토큰화 | 467 토큰 |
| 2.6 윈도우 (`max_length=4, stride=4`) | `range(0, 463, 4)` → 윈도우 116개 |
| 2.6 배치 (`batch_size=8, drop_last=True`) | `len(dataloader)` = 14, 윈도우 4개 버려짐 |
| 2.6 첫 배치 | `inputs` `[8, 4]`, `targets` `[8, 4]` |
| 2.7 토큰 임베딩 | `[8, 4, 128]` |
| 2.8 위치 임베딩 | `[4, 128]` |
| 합산 (브로드캐스팅) | `[8, 4, 128]` |

첫 배치:

```
Inputs:
tensor([[18858,  9608,  5741,   198],
        [ 3886, 29166, 31908, 34815],
        [  198,   198,  1026,   373],
        [  867,   290,   867,   257],
        [  614,  2084,    11,   198],
        [  220,   220,   554,   257],
        [13239,   416,   262,  5417],
        [   11,   198,  2504,   257]])

Targets:
tensor([[ 9608,  5741,   198,  3886],
        [29166, 31908, 34815,   198],
        [  198,  1026,   373,   867],
        [  290,   867,   257,   614],
        [ 2084,    11,   198,   220],
        [  220,   554,   257, 13239],
        [  416,   262,  5417,    11],
        [  198,  2504,   257, 34827]])
```

## 위치 임베딩 효과 확인

첫 배치 안의 반복 토큰으로 확인했다 (현재 스크립트에서는 이 비교 코드를 지운 상태).

| 비교 | 토큰 임베딩 같은가 | 입력 임베딩 같은가 |
|---|---|---|
| `inputs[2, 0]` vs `inputs[2, 1]` — 둘 다 `198`, **다른 자리** | `True` | `False` |
| `inputs[3, 3]` vs `inputs[5, 3]` — 둘 다 `257`, **같은 자리** | `True` | `True` |

같은 토큰이라도 자리가 다르면 입력 임베딩이 갈라지고, 자리가 같으면 그대로 같다.

## 작성 중 발견한 것

- **파일에 따라 토큰 수가 다르다.** 저장소의 `data/Annabel_Lee.txt`는 463 토큰, 이 파일은 467 토큰.
  제목·저자 줄의 유무와, 들여쓰기 공백이 `\xa0`(줄바꿈 없는 공백)인지 일반 공백인지의 차이.
  같은 공백으로 보이지만 BPE 토큰 ID가 다르다(`4603, 1849` vs `220, 220`).
- **`drop_last=True`가 시의 마지막 두 줄을 버린다.** 버려진 윈도우 4개와 윈도우를 만들기에 부족한 끝 토큰을 합쳐
  토큰 448~466(19개)이 입력으로 한 번도 쓰이지 않는다:
  `chre there by the sea— / In her tomb by the sounding sea.` 에러나 경고는 없다.
- **`shuffle`을 매개변수로 받아놓고 `DataLoader`에 `True`를 그대로 적었던 버그.** 호출할 때 `shuffle=False`를 넘겨도
  무시되어 "첫 배치"가 실행할 때마다 달라졌다. 매개변수를 넘기도록 고친 뒤 해결.
- **`vocab_size`에 463(윈도우 수)을 넣었다가 `IndexError`.** `vocab_size`는 텍스트가 아니라 토크나이저가 정한다(gpt2 = 50,257).
  이 시에서 가장 큰 토큰 ID는 47897.

## 남은 개선점

- 4번 줄의 바깥 `tokenizer`는 이제 쓰이지 않는다. `GPTDatasetV1`은 매개변수로 받은 값을, `create_dataloader_v1`은
  함수 안에서 새로 만든 값을 쓴다.
- 위치 임베딩 비교 코드를 다시 넣는다면, 비교 대상이 정말 같은 토큰인지 `assert`로 전제를 확인해 둘 것.
  설정이나 텍스트가 바뀌면 인덱스가 다른 토큰을 가리키게 된다.
- `GPTDatasetV1`, `create_dataloader_v1`이 `bpe.ipynb`에도 있어 중복이다. 2장 정리 때 `src/`로 모은다.
