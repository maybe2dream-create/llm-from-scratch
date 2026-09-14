# LLM Wiki — 개인 지식 저장소

`~/projects/llm-from-scratch`에서 Raschka, *Build a Large Language Model (From Scratch)*를 따라가며 정리한 개념 위키다.

## 이 위키와 다른 문서의 관계

| 문서 | 성격 | 위치 |
|---|---|---|
| `docs/LLM_project_session_NN.md` | 일지 — 그날 무엇을 하다 어떤 버그를 만나 어떻게 고쳤는지 (시간순, 계속 새로 씀) | `docs/` |
| `docs/wiki/concepts/*.md` | 참고서 — 개념 하나를 "무엇 / 왜 / 어떻게"로 정리 (주제순, 확정된 뒤 계속 갱신) | `docs/wiki/concepts/` |
| `docs/blog/*.md` | 외부 공개용 글 — 블로그 연재 원고 (독자가 제3자다) | `docs/blog/` |
| PDF | 산출물 — 필요할 때만 마크다운에서 뽑아내는 읽기·보관용 사본. 생성 스크립트는 `tools/pdf/` | `docs/*.pdf` (git에 안 잡힘) |

**원본은 항상 마크다운이다.** PDF가 필요할 때 그 시점에 마크다운으로부터 만든다 — 반대 순서는 없다.

2026-09-09 이전에 PDF로만 존재하게 된 자료(`Lesson_04_Attention_Mechanism.pdf`, `LLM_Companion_Textbook_Syllabus.pdf`, `LLM_Embedding_OutputDim_and_Seed_Explained.pdf` 등)는 이 정책 이전 것이라 소급 정리하지 않기로 했다. 이 정책은 **이 시점 이후 새로 다루는 개념부터** 적용된다.

## 개념 문서

- [tokenization.md](concepts/tokenization.md) — 텍스트를 토큰으로, 토큰을 ID로 (2.1~2.5절)
- [sliding-window-sampling.md](concepts/sliding-window-sampling.md) — 긴 텍스트를 (입력, 다음 토큰) 학습 쌍으로 자르기 (2.6절)
- [embedding-layer.md](concepts/embedding-layer.md) — 토큰 ID를 의미를 담을 수 있는 벡터로 (2.7절)
- [positional-embedding.md](concepts/positional-embedding.md) — 자리 번호도 표에서 찾아 더한다, 브로드캐스팅 (2.8절)
- [query-key-value.md](concepts/query-key-value.md) — self-attention의 세 역할, 가중치 행렬 이전 단계 (3.3절)

각 문서 끝에 그 개념을 처음 다룬 세션 로그로 역참조를 걸어둔다 — 버그·시행착오·질문이 오간 실제 맥락은 일지 쪽에 있고, 여기는 그 결과 확정된 것만 남긴다.

## 새 개념을 추가할 때 순서

1. 세션 로그에 그날 있었던 일을 그대로 기록한다 (지금처럼).
2. 그 세션에서 확정된 개념을 `concepts/`에 별도 문서로 뽑는다 — 일지체가 아니라 참고서체로, 나중에 다시 찾아볼 사람 기준으로 쓴다.
3. 두 문서는 서로 링크한다.
4. PDF는 필요할 때만 만든다.
