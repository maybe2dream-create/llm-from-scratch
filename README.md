# llm-from-scratch

Sebastian Raschka, *Build a Large Language Model (From Scratch)*를 따라 GPT 계열 LLM을
처음부터 구현하는 학습 저장소. 목표는 쓸 만한 모델이 아니라 **동작 원리를 이해하기 위한
축소 모형**이다. 따라서 성능 수치보다 "이 줄이 왜 필요한가"를 기록하는 데 비중을 둔다.

## 진행 상황

| 장 | 내용 | 상태 |
|---|---|---|
| 2 | 토크나이저, BPE, 슬라이딩 윈도우, 토큰·위치 임베딩 | 완료 |
| 3 | Self / Causal / Multi-head Attention | 완료 (`MultiHeadAttention`은 `src/attention.py`) |
| 4 | LayerNorm, GELU, FFN, Shortcut, Transformer Block, GPTModel, 텍스트 생성 | 완료 (`src/gpt_model.py`) |
| 5 | 사전학습, 디코딩 전략(temperature·top-k), OpenAI GPT-2 가중치 로드 | 완료 (`src/dataset.py`) |
| 6 | 분류 파인튜닝 (SMS 스팸 분류) | 시작 |
| 7 | 지시 파인튜닝 | 미착수 |

**노트북은 장별 학습 기록이고, 다음 장에서 다시 쓰는 것만 `src/`로 옮겨 import한다.**
3장 Attention 구현 5종(`SelfAttention_v1`, `SelfAttention_v2`, `CausalAttention`,
`MultiHeadAttentionWrapper`, `MultiHeadAttention`)은 `notebooks/03_attention.ipynb`에 있고,
4장이 쓰는 `MultiHeadAttention`만 `src/attention.py`에 있다. 같은 이유로 5장이 학습시킬
4장 산출물(`GELU`, `LayerNorm`, `FeedForward`, `TransformerBlock`, `GPTModel`,
`generate_text_simple`)은 `src/gpt_model.py`에 있다.

학습 전 `GPTModel`(GPT-2 124M 구성, 파라미터 163,009,536개)은 "Hello, I am"을
"Hello, I am Featureiman Byeswickattribute argue"로 이어 쓴다(책과 일치). 5장에서 이 모델을
학습시키므로 이 출발점을 `tests/test_gpt_model.py`가 고정해 둔다.

## 구조

```
src/            재사용하는 모듈 (import 대상)
  tokenizer.py    preprocess, build_vocab, SimpleTokenizerV1
  attention.py    MultiHeadAttention (3장 → 4장에서 import)
  gpt_model.py    GELU, LayerNorm, FeedForward, TransformerBlock, GPTModel,
                  generate_text_simple (4장 → 5장에서 import)
  dataset.py      GPTDatasetV1, create_dataloader_v1 (2장 → 5장에서 import)
tests/          src/에 대한 pytest
  test_tokenizer.py   정규식 분리, 어휘, encode/decode 왕복
  test_gpt_model.py   PyTorch 내장 구현과 대조 + 4장 기준값(파라미터 수·생성 결과) 고정
notebooks/      장별 실습 노트북
  02_text_data.ipynb   2장 전체 파이프라인
  03_attention.ipynb   3장 Attention 5종
  04_gpt_model.ipynb   4장 LayerNorm · GELU · FFN · Shortcut · TransformerBlock · GPTModel · 텍스트 생성
  05_pretraining.ipynb 5장 사전학습 · 디코딩 전략 · GPT-2 가중치 로드
  06_classification.ipynb 6장 분류 파인튜닝 (진행 중)
  gpt_download.py      GPT-2 가중치 다운로더 — Raschka 코드(Apache 2.0, 내 작업물 아님)
  LICENSE-gpt_download.txt  위 파일에만 적용되는 라이선스 사본
  bpe.ipynb            BPE 토크나이저 실험
experiments/    노트북에 넣기 전 단계의 습작. src/가 정식판이다.
  ch02/
    SimpleTokenizerV2.py  <UNK>·<|endoftext|> 처리를 붙인 초기 버전
    raw_text.py           정규식 토크나이저 + 어휘 구축
    embedding_exec/       Annabel Lee로 2장 파이프라인 재실행 (02_text_data.ipynb도 여기
                          annabel_lee.txt를 읽는다)
scripts/        유틸리티
  check_env.py    설치된 패키지·디바이스 확인
tools/pdf/      학습 자료 PDF 생성기 (reportlab). docs/의 PDF를 만든다.
docs/           학습 자료 PDF와 세션 기록 (.md). PDF는 .gitignore 처리.
  LLMs-from-scratch-main/  Raschka 공식 저장소 사본 (참조용, 내 작업물 아님)
data/           코퍼스. .gitignore 처리 — 출처와 복구 방법은 NOTES.md 참고.
checkpoints/    학습 체크포인트 (5장부터 사용)
configs/        하이퍼파라미터 (5장부터 사용)
```

빌드 산출물 `tmp/`(중간 PNG), `output/`(완성 PDF)는 커밋하지 않는다.

## 실행

모든 스크립트는 **저장소 루트에서** 실행한다. 경로가 루트 기준 상대경로이기 때문이다.

```bash
source .venv/bin/activate
python scripts/check_env.py                              # 환경 확인
python experiments/ch02/embedding_exec/embed_exec.py      # 2장 파이프라인 → torch.Size([8, 4, 128])
pytest                                                   # src/ 테스트
```

`data/`가 비어 있으면 `experiments/ch02/raw_text.py`가 `the-verdict.txt`를 자동으로 받는다.

`tools/pdf/*.py`는 `uv run tools/pdf/<파일>.py`로 돌린다. 각 스크립트 맨 위 `# /// script`
블록에 의존성이 선언돼 있어 `uv`가 격리된 환경을 만들고, 프로젝트 `.venv`에는 아무것도
설치하지 않는다. macOS 시스템 한글 폰트 경로를 참조하며, 일부는 PDF 변환에
`/Applications/Google Chrome.app`을 쓴다. 자세한 내용은 `tools/pdf/README.md`.

## 기록

- `NOTES.md` — 세션마다 무엇이 헷갈렸고 어떻게 풀렸는지, 코퍼스 출처와 검증 수치
- `docs/LLM_project_session_*.md` — 세션별 정식 정리

검증 기준값: `data/the-verdict.txt`는 문자 20,479 / 정규식 토큰 4,690 / 어휘 1,130.

## 분리된 자료

학습 중 만들었지만 LLM 구현과 주제가 다른 자료는 저장소 밖으로 옮겼다.

- `../ollama/` — Ollama 기반 LLM 보안 실습 (프롬프트 인젝션, 탈옥, RAG 권한, canary token 등 d_01~d_09)
- `../study-archive/` — 네트워크 보안(ARTEX)·Docker 학습 자료
