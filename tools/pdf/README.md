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

## 주의

- 스크립트에 들어 있는 숫자(토큰 수, 가중치 값, shape)는 `data/the-verdict.txt`와 프로젝트 가상환경에서 실제로 실행해 확인한 값을 옮겨 적은 것이다. 데이터나 설정이 바뀌면 다시 확인해야 한다.
- 코드 블록(Courier 폰트)에는 한글을 넣지 않는다. Courier에는 한글 글리프가 없어 검은 네모로 깨진다.
