# PDF 생성 스크립트

`docs/`의 PDF를 다시 만드는 스크립트다. PDF 파일 자체는 `.gitignore` 대상이라 저장소에 올라가지 않으므로, 이 스크립트가 PDF의 재현 수단이다.

## 실행

```bash
uv run tools/pdf/chapter2_flowchart.py
uv run tools/pdf/token_positional_embeddings.py
```

- 각 파일 맨 위의 `# /// script` 블록에 의존성(`reportlab`)이 선언되어 있어서, `uv run`이 격리된 환경을 알아서 만든다. 프로젝트 `.venv`에는 아무것도 설치하지 않는다.
- 출력 경로는 저장소 루트 기준이라 어느 폴더에서 실행해도 `docs/`에 생성된다.
- 한글 표시를 위해 macOS 시스템 폰트 `AppleGothic.ttf`를 쓴다. 다른 OS에서는 각 스크립트의 `KOREAN_FONT` 경로를 바꿔야 한다.

## 스크립트와 결과물

| 스크립트 | 결과물 | 내용 원본 |
|---|---|---|
| `chapter2_flowchart.py` | `docs/Chapter2_Pipeline_Flowchart.pdf` | 스크립트 안의 단계 정의 |
| `token_positional_embeddings.py` | `docs/Token_and_Positional_Embeddings_Explained.pdf` | `docs/wiki/concepts/embedding-layer.md`, `positional-embedding.md` |
| `embed_exec_walkthrough.py` | `docs/Embed_Exec_Line_by_Line.pdf` | `embedding_exec/embed_exec.py` (코드는 파일에서 직접 읽음), `embed_exec.md` |
| `self_attention_guide.py` | `docs/Self_Attention_Conceptual_Guide.pdf` | 붙여넣은 self-attention 개념 설명 (스크립트 안 `RAW_TEXT`) |
| `attention_worked_example.py` | `docs/Self_Attention_Worked_Example.pdf` | 붙여넣은 "I love cats" 손계산 예제 + 검토 노트 (스크립트 안 `RAW_MD`, `NOTES`) |

## 주의

- 스크립트에 들어 있는 숫자(토큰 수, 가중치 값, shape)는 `data/the-verdict.txt`와 프로젝트 가상환경에서 실제로 실행해 확인한 값을 옮겨 적은 것이다. 데이터나 설정이 바뀌면 다시 확인해야 한다.
- 코드 블록(Courier 폰트)에는 한글을 넣지 않는다. Courier에는 한글 글리프가 없어 검은 네모로 깨진다.
- AppleGothic에는 `é`와 수학 빼기 기호 `−`(U+2212)가 없다. `embed_exec_walkthrough.py`는 각각 Helvetica 글자와 ASCII `-`로 바꿔 넣는다.
- `KeepTogether` 안에 또 `KeepTogether`를 넣으면 높이가 과하게 잡혀 매 절이 새 페이지로 넘어간다. 안쪽은 풀어서 넣는다.
- `embed_exec_walkthrough.py`는 코드 줄을 `embed_exec.py`에서 직접 읽는다. 그 파일의 줄 번호가 바뀌면 설명의 줄 번호도 다시 맞춰야 한다.
- `attention_worked_example.py`는 수식이 많아 ReportLab 대신 markdown → HTML(MathML) → 헤드리스 Google Chrome으로 PDF를 만든다. `/Applications/Google Chrome.app`이 있어야 하고, 네트워크는 쓰지 않는다.
