# LLM from Scratch — Session 01

**날짜:** 2026년 8월 29일
**주제:** 개발환경 구축 완료 + 프로젝트 방향 설정
**장비:** MacBook Pro / Apple M3 / 16GB / macOS 26.6.2

---

## 0. 프로젝트 개요

### 배경

- 65세, 경제학·경영학 전공, 평생 경제학자로 활동
- Python 중급, 통계학·선형대수·미적분 학습 이력
- 2026.8.6 ~ 12.28 K-Digital Training "AI Native 사이버보안 엔지니어" 과정 수강 중
- 참고 도서 3권
  - Sebastian Raschka, *Build a Large Language Model (From Scratch)*, 2025
  - Dilyan Grigorov, *Building Large Language Models from Scratch*, 2026
  - Harriet Farlow, *Practical AI Security*, 2026

### 목표 (본인 정리)

1. LLM의 전체적인 메커니즘과 흐름 파악
2. 사이버보안 관점에서 LLM을 깊게 이해
3. (장기·조건부) 네트워크 보안 특화 LLM 구축

> ML 분야 취업 목적 아님. 목표 3은 현재 실행 계획이 아니라 여건이 되면 시도할 장기 과제.

---

## 1. 환경 구축 (Step 0 ~ 11)

### 최종 결과

| 항목 | 값 | 검증 방법 |
|---|---|---|
| Python | 3.12.14, `arm64` 네이티브 | Rosetta 에뮬레이션 아님 확인 |
| macOS | 26.6.2 | Metal 최소 요구(13) 충족 |
| PyTorch | 2.13.0 | `mps.is_available()` → `True` |
| GPU 정확도 | 차이 `0.00e+00` | CPU 결과와 완전 일치 |
| GPU 처리량 | **2,939 GFLOP/s** | M3 이론 최대치의 약 70% |
| 패키지 | 15개 | 전체 import 성공 |
| Jupyter 커널 | "LLM from Scratch (3.12)" | 노트북 내 MPS `True` |
| VS Code | Python / Jupyter / Ruff | 인터프리터 `.venv` 지정 |
| Git | commit `a1fc822` | working tree clean |
| MPS fallback | `PYTORCH_ENABLE_MPS_FALLBACK=1` | `echo` → `1` |

### 수행한 단계

**Step 0 — 머신 확인**
```bash
sw_vers
system_profiler SPHardwareDataType | grep -E "Chip|Memory"
```

**Step 1 — Xcode Command Line Tools**
```bash
xcode-select --install
```

**Step 2 — Homebrew**
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
# 설치 후 출력되는 PATH 설정(eval) 라인 반드시 실행
```

**Step 3 — uv, git**
```bash
brew install uv git
```

**Step 4 — 프로젝트 폴더 + 가상환경**
```bash
mkdir -p ~/projects/llm-from-scratch
cd ~/projects/llm-from-scratch
uv venv --python 3.12
source .venv/bin/activate
```

**Step 5 — PyTorch**
```bash
uv pip install torch torchvision torchaudio
```
결과: `2.13.0 True`

**Step 6 — 나머지 패키지**
```bash
uv pip install tiktoken numpy pandas matplotlib jupyterlab ipykernel ipywidgets \
  tqdm tensorboard transformers datasets huggingface_hub safetensors sentencepiece \
  pytest ruff python-dotenv
```
결과: `all imports ok`

**Step 7 — GPU 검증 (`check_env.py`)**
```
Python   : 3.12.14  (arm64)
macOS    : 26.6.2
PyTorch  : 2.13.0
MPS built     : True
MPS available : True
CPU vs GPU max difference: 0.00e+00
GPU  :   0.94 s   (2,939 GFLOP/s)
CPU  :   2.20 s   (estimated)
Speedup: 2.4x
Environment is ready.
```

**Step 8 — Jupyter 커널 등록**
```bash
python -m ipykernel install --user --name llm-scratch \
  --display-name "LLM from Scratch (3.12)"
jupyter lab
```

**Step 9 — Git 저장소**
```bash
git init
git config user.name "..."
git config user.email "..."
curl -o .gitignore https://raw.githubusercontent.com/github/gitignore/main/Python.gitignore
printf "\n.venv/\ndata/\ncheckpoints/\nruns/\n*.pt\n*.bin\n*.safetensors\n.DS_Store\n" >> .gitignore
uv pip freeze > requirements.txt
mkdir -p notebooks src tests configs data checkpoints
touch src/__init__.py tests/__init__.py
git add . && git commit -m "Set up development environment for LLM from scratch"
```

**Step 10 — VS Code**
- 이미 설치되어 있어 `brew install --cask visual-studio-code` 생략
- 확장: Python, Jupyter, Ruff (모두 Microsoft/Astral 공식, 파란 체크 확인)
- `Cmd+Shift+P` → Python: Select Interpreter → `.venv` 경로 선택

**Step 11 — 16GB 설정**
```bash
echo 'export PYTORCH_ENABLE_MPS_FALLBACK=1' >> ~/.zshrc
source ~/.zshrc
```

### 미완료 항목

- [ ] `git branch -m main` — 브랜치명이 아직 `master`
- [ ] Step 8 이후 작업분 커밋

---

## 2. 과정에서 나온 주요 Q&A

### 가상환경은 무엇을 격리하는가

**Q.** VS Code를 가상환경 안에 다시 설치해야 하는가?

**A.** 아니다. 가상환경은 **Python 패키지만** 격리한다. VS Code, Terminal, Chrome 같은 응용프로그램은 macOS 전역에 설치되며 가상환경과 무관하다. 가상환경은 컨테이너나 샌드박스가 아니라 그냥 Python 라이브러리가 들어있는 폴더다.

단, 기존 VS Code가 새 가상환경을 인식하도록 인터프리터를 `.venv`로 지정하는 작업은 필요하다.

### 속도 향상 2.4배 — 예측 실패

가이드에서 5~15배를 예상했으나 실측 2.4배. **예측이 틀린 것이지 설치가 잘못된 것이 아님.**

- GPU 2,939 GFLOP/s = M3 이론 최대치의 약 70% → 정상
- Apple CPU에는 행렬연산 전용 코프로세서가 있어 큰 정사각 행렬곱에서 유독 빠름 → 비율이 작게 나옴
- 실제 트랜스포머 학습은 matmul 외 연산이 많아 격차가 더 벌어짐
- **절대값(2,939 GFLOP/s)을 기준선으로 기록할 것.** 이 수치가 급락하면 메모리 압박 신호

### VS Code 확장 설치 여부 판별

- **Install** 버튼 하나 → 미설치
- **Disable / Uninstall** 쌍 → 이미 설치됨
- "Switch to Pre-Release Version"은 무시 (미완성 빌드용)
- 파란 체크 = 공식 배포자. 취소선 + 경고 삼각형 = deprecated

### Notebook vs Console

- **Notebook** — 셀 저장·재실행·편집 가능, `.ipynb`로 영구 보존. 두 책 모두 이 형식
- **Console** — 임시 프롬프트, 닫으면 소멸
- 항상 Notebook + "LLM from Scratch (3.12)" 커널 선택

---

## 3. 데이터와 아키텍처에 관한 논의

### 비유: 뱀과 소

> 뱀이 물을 마시면 독을 만들고, 소가 물을 마시면 젖을 만든다.

같은 아키텍처라도 학습 데이터에 따라 결과가 달라진다는 통찰. 방향은 맞다. 동일한 트랜스포머를 한국어 법률 문서, Python 소스코드, 단백질 서열로 학습시키면 각각 다른 모델이 된다.

### 보완할 점

비유가 시사하는 것만큼 그릇이 중립적이지는 않다. 뱀과 소가 다른 것은 **몸이 다르기 때문**이고, 아키텍처도 몸이다.

- 컨텍스트 256 토큰 모델은 1,000 토큰 의존성을 물리적으로 학습할 수 없다 — 데이터가 아니라 구조의 한계
- 토크나이저가 모델의 지각 범위를 결정한다. 영어용 토크나이저는 한국어를 의미가 파괴되는 단위로 쪼갠다
- 어텐션 자체가 "의미는 위치 간 관계에서 나온다"는 가정을 내장하고 있다

**정리: 데이터는 모델이 무엇을 아는지를 결정하고, 아키텍처는 무엇을 알 수 있는지를 결정한다.**

### 세 번째 요소: 목적함수

손실함수가 "좋음"의 정의를 결정한다. 다음 토큰 예측은 진실성이나 유용성과 같지 않다. 측정 가능한 목표와 실제로 원하는 행동 사이의 간극 — 경제학자에게는 익숙한 문제다. 잘못된 지표를 최적화하면 요구한 것을 정확히 얻되 원한 것은 얻지 못한다.

### 보안 연결점

데이터 포이즈닝은 이 비유가 묘사하는 공격 그 자체다. 공격자가 물에 무언가를 섞는 것. 전체 파이프라인을 통제하므로 정량 측정이 가능하다.

---

## 4. 비용-편익 분석

### 비용

| 항목 | 규모 |
|---|---|
| 시간 | 150~250시간 (주 10~15시간 × 4개월) |
| 금전 | $50 미만 |
| 기회비용 | 클라우드 보안 심화, 자격증, 응용 프로젝트 3~4개, 네트워킹 |
| 중도포기 위험 | 3~4장(멀티헤드 어텐션)에서 30~40% 확률로 정체 |
| 역량 착각 | 읽고 이해한 것과 빈 파일에서 구현하는 것은 다름 |

### 편익 (지속성 순)

- **메커니즘적 이해** — 임베딩의 실체, 어텐션이 시퀀스 길이에 제곱으로 비례하는 이유, KV 캐시, 컨텍스트 한계. 세대가 바뀌어도 유효
- **보안 전문성** — 프롬프트 인젝션이 왜 작동하는지 어텐션 수준에서 설명 가능. 현재 AI 보안 실무는 대부분 시행착오 수준이라 희소함
- **논문 독해력** — 수년간 복리로 작용
- **포트폴리오** — 실재하나 과대평가되기 쉬움. 차별화는 책 내용이 아니라 테스트·노트·커밋 이력·보안 실험에서 나옴

### 얻지 못하는 것

- 만든 모델은 형편없다. 교육적 가치 100%, 실용적 가치 0%
- 프로덕션 ML(데이터 파이프라인, 분산학습, 서빙, MLOps)은 전혀 다루지 않음
- ML 엔지니어 취업 경쟁력 없음 (본인도 목적 아님을 명시)

### 비교우위 관점

ML 엔지니어링 실력으로는 이길 수 없다. 그러나 비교우위는 절대우위가 아니라 상대적 비용의 문제다.

**교차점:** 40년 경제학 추론 + 불확실성 하 모델링 훈련 + 사이버보안 자격 + LLM 내부 이해

이 넷을 모두 가진 사람은 드물다. 25세 ML 엔지니어는 구현에서 이기지만 앞의 둘에서는 상대가 되지 않는다. AI가 노동시장에 미치는 영향, 금융 리스크 관리 관행과 모델 리스크의 접점, AI 보안 실패의 경제적 손실 환산 — 이 지점에서의 가치는 학습루프를 빨리 짜는 데 있지 않다.

---

## 5. 목표 3(네트워크 보안 특화 LLM)에 대한 비판적 검토

### 핵심 지적: from-scratch는 목표 3으로 가는 길이 아니다

Raschka 책이 가르치는 것은 **아키텍처 내부**(어텐션 shape, 포지셔널 임베딩, 학습 루프). 도메인 특화 모델에 필요한 것은 **데이터 큐레이션, 파인튜닝 인프라, 평가 설계, 배포**. 겹치는 부분 20% 미만.

실제 경로는 사전학습된 오픈 모델(Qwen/Llama/Mistral 소형) + LoRA/QLoRA 파인튜닝, 또는 파인튜닝 없이 RAG. 이 경로에서 트랜스포머를 직접 구현할 일은 없다.

**목표 1·2를 위해 책을 하는 것은 옳지만, "목표 3의 준비단계"로 생각하면 안 된다. 별개의 두 프로젝트다.**

### 진짜 병목: 데이터와 평가

**데이터** — 네트워크 보안 도메인의 공개 라벨링 데이터셋은 빈약하다. KDD'99, CIC-IDS2017 계열은 중복 레코드, 비현실적 트래픽 분포, 현재 위협환경과의 괴리 등 결함이 오래 지적되어 왔다. 현실적 데이터는 대부분 기업 내부 로그이고 민감정보라 공개되지 않는다. 노력이 아니라 접근권의 문제.

**평가** — 벤치마크가 없으면 "그럴듯한 답"과 "정확한 답"을 구별할 수 없다. 보안 도메인에서 존재하지 않는 CVE 번호를 자신 있게 제시하는 모델은 없는 것보다 나쁘다.

목표 3 진행 시 **시간의 60% 이상이 데이터와 평가에 투입된다.** 학습 자체는 몇 시간이면 끝난다.

### 선결 질문: 특화 모델이 정말 필요한가

프론티어 모델이 이미 보안 추론을 상당히 잘 한다. 작은 특화 모델이 이기는 지점은 넷뿐이다.

1. **프라이버시** — 로그를 외부 API로 보낼 수 없는 환경(폐쇄망, 금융, 공공). 한국 시장에서 특히 유효
2. **비용** — 하루 수백만 건 알람 분류 시 프론티어 API는 경제적으로 불가능
3. **지연시간** — 실시간 인라인 탐지
4. **협소·구조화된 작업** — "이 로그를 6개 범주 중 하나로 분류" 같은 좁은 작업. 3B 모델이 파인튜닝만 되면 대등하거나 우위

**넷 중 어디에도 해당하지 않으면 특화 모델은 순수한 낭비다.**

### 스코프 재정의 제안

"네트워크 보안 특화 LLM"은 포트폴리오 주제로 너무 넓다. 넓으면 평가 불가능하고, 평가 불가능하면 방어할 수 없다.

좁힌 예시:
- 방화벽 로그를 정해진 범주로 분류하는 3B 모델
- CVE 설명문에서 영향 자산 유형·심각도를 구조화 출력으로 추출
- 한국어 보안관제 보고서 요약 (한국어 자체가 프론티어 대비 데이터 우위 가능 영역)
- 피싱 메일 판별기

심사자는 숫자를 본다. "F1 0.87, 베이스라인 대비 +12%p"가 "보안 특화 LLM 개발"을 이긴다.

### 하드웨어

16GB에서 QLoRA로 7B 파인튜닝은 가능하나 빡빡하다. 1~3B가 현실적. 최종 학습은 클라우드 GPU 몇 시간 대여 권장(수만 원 수준).

### 안전성 주의

공격 기법 데이터로 파인튜닝하면 원 모델의 안전 정렬이 상당 부분 훼손된다는 것이 반복 확인된 연구 결과다. 방어 목적 모델이 의도치 않게 공격 도구가 되는 경로. **방어 태스크(탐지·분류·요약) 중심으로 스코프를 잡으면 대체로 회피 가능하고 실용적 가치도 그쪽이 크다.**

---

## 6. 학습 방법론

### 가장 큰 함정

코드를 읽고, 끄덕이고, 셀을 실행하고, 예상된 출력을 보고, 넘어간다. 학습처럼 느껴지지만 거의 아무것도 남지 않는다. **재인(recognition)은 지식이 아니다.**

### 네 가지 습관

1. **손으로 타이핑한다.** 저장소에서 복사·붙여넣기 금지. 느린 것이 핵심이다. 오타를 내고 그 오타를 디버깅하면서 코드가 어떻게 맞물리는지 배운다
2. **실행 전에 예측한다.** 셀을 돌리기 전에 출력 텐서의 shape을 소리 내어 말한다. 틀렸을 때 멈추고 이유를 찾는다. 예측과 결과의 간극이 학습이 일어나는 지점이다
3. **shape을 계속 출력한다.** 모든 변환 뒤에 `print(x.shape)`. 이 분야 혼란의 대부분은 어느 차원이 무엇을 의미하는지에 대한 혼란이다
4. **의도적으로 망가뜨린다.** 컨텍스트 길이를 3으로 놓아본다. stride를 바꿔 겹침을 관찰한다. 한국어 문장과 영어 번역문의 토큰 수를 비교한다

### 챕터별 루프

1. 컴퓨터 없이 한 번 읽는다 — 논지의 형태를 파악
2. `notebooks/`에서 직접 타이핑하며 따라간다, shape 출력
3. 남길 만한 부분을 `src/`로 옮겨 깨끗한 함수로 재작성
4. `tests/`에 테스트 하나 작성 (예: encode-decode 왕복이 원문을 반환하는지)
5. 배운 것을 서술하는 메시지로 커밋

**3단계가 다른 수백 개 저장소와 갈리는 지점이다.** 노트북에서 모듈로 재작성하려면 무엇이 본질인지 판단해야 하고, 이건 흉내낼 수 없다.

**4단계** — 테스트가 있는 포트폴리오는 거의 없다. README의 어떤 주장보다 강한 신호다.

### NOTES.md

세션마다 무엇이 헷갈렸고 어떻게 풀렸는지 몇 문장씩 기록. 두 달 뒤 어텐션에 파묻혔을 때 토크나이제이션에서 무엇이 헷갈렸는지 다시 읽게 된다. 12월 최종 정리의 원재료이기도 하다. 5개월치 정직한 기록이 마지막에 기억으로 재구성한 어떤 것보다 낫다.

---

## 7. 일정 계획

4개월(~12/28) 안에 목표 1·2와 3을 모두 제대로 하는 것은 불가능하다. 둘 다 시도하면 둘 다 어중간해진다.

| 기간 | 내용 |
|---|---|
| **9~11월** | Raschka 2~5장. 완료 시 GPT를 직접 만들고 학습시키고 실제 가중치를 얹은 상태. 목표 1·2 사실상 달성 |
| **12월** | 목표 2 심화. 자체 제작 모델 대상 데이터 포이즈닝 실험 — 학습 코퍼스의 0.1%/1%/5% 오염 후 행동변화 측정. 파이프라인 전체를 통제하므로 ground truth를 아는 상태에서 측정 가능. API 모델로는 원리적으로 불가능한 실험 |
| **2027 상반기** | 목표 3. 파인튜닝은 밑바닥 구현보다 훨씬 빠르게 배울 수 있음 |

### 우선순위 규칙

- **주 10시간 상한.** 부트캠프가 본업이며 수료증이 걸린 쪽이다. LLM 프로젝트가 그것을 잠식하면 LLM 쪽을 줄인다
- **2~5장 우선, 6~7장은 선택.** 2~5장이 이해의 80%를 준다. 6~7장(분류 파인튜닝, 인스트럭션 튜닝)은 수익체감이 뚜렷하다. 11월 중순에 5장이 끝났으면 거기서 멈추고 12월은 보안 실험에 쓴다
- **중단 조건을 지금 정해둔다.** 10월 말까지 4장을 못 끝냈으면 중단한다. 실패가 아니라 새 정보에 따른 올바른 결정이다. 2~3장만으로도 투입 시간은 정당화된다. 미리 정해두는 것이 나중에 설득력 있게 느껴질 매몰비용 논리로부터 보호해준다

---

## 8. 운영 규칙

| 규칙 | 이유 |
|---|---|
| `rm` 함부로 쓰지 않기 | 휴지통을 거치지 않는다. 즉시·복구불가. Finder나 `mv` 사용 |
| 가중치·데이터셋 커밋 금지 | GitHub 100MB 제한, 저장소가 지저분해짐. `.gitignore`에 이미 반영 |
| 시스템 Python에 설치 금지 | `/usr/bin/python3`은 macOS 소유. 손상 시 깨끗한 복구 불가 |
| 부트캠프 파일 분리 | 두 프로젝트가 한 저장소에 있으면 도구도 사람도 혼란 |
| 세션마다 커밋 | 5개월간의 작고 서술적인 커밋 자체가 지속적 작업의 증거 |
| 변경 후 `check_env.py` 재실행 | 10초 투자로, 문제가 아니었던 학습 스크립트를 한 시간 디버깅하는 일을 방지 |

### 세션 시작
```bash
cd ~/projects/llm-from-scratch
source .venv/bin/activate    # 프롬프트에 (llm-from-scratch) 확인
jupyter lab                  # 또는 code .
```

### 세션 종료
```bash
# 1. 노트북 저장 (Cmd+S)
# 2. Jupyter 서버 종료 (터미널에서 Ctrl+C 2회)
# 3. 커밋
git add .
git commit -m "오늘 한 일 서술"
```

### 가장 흔한 오류
`ModuleNotFoundError: No module named 'torch'` → torch가 없는 게 아니라 가상환경이 활성화되지 않은 것. 프롬프트에 `(llm-from-scratch)`가 있는지 확인. 터미널 창마다 각각 활성화 필요.

Jupyter에서 import 실패 시 → 노트북 우상단 커널이 "LLM from Scratch (3.12)"인지 확인.

---

## 9. 다음 단계

**Raschka 2장 — Working with text data**

신경망이 없는 유일한 장. 텍스트를 숫자로 바꾸는 것이 전부다: 토큰 분할, 어휘 구축, BPE, 토큰 임베딩, 포지셔널 임베딩, 슬라이딩 윈도우 샘플러.

배관처럼 보이지만 이 분야에서 가장 깊은 아이디어 셋이 여기 숨어 있다.

- 모델이 단어 안의 글자를 볼 수 없는 이유
- 같은 문장이 한국어에서 영어보다 2~3배 많은 토큰을 소비하는 이유 — 상업적 결과를 낳는 실제 비용 비대칭
- 위치 정보를 왜 인위적으로 더해야 하는가 — 어텐션이 구조적으로 순서를 보지 못한다는 사실과 처음 만나는 지점

작업 방식: `notebooks/02_text_data.ipynb`에서 따라가고, 남길 부분을 `src/tokenizer.py`로 옮긴다.

---

## 10. 대화 방식 합의

- 칭찬이 아니라 냉철하고 정확한 비판·지적·충고·제안을 요청함
- 단, 근거 없는 습관적 비판은 무조건적 칭찬만큼 무가치하므로 지양
- Claude의 판단도 틀릴 수 있음 — 이날 GPU 속도 향상 예측(5~15배 vs 실측 2.4배)이 이미 한 번 틀렸음. 단정적 진술에도 근거가 있으면 반박할 것

---

## 부록: 생성된 파일

| 파일 | 내용 |
|---|---|
| `LLM_Environment_Setup_Guide.pdf` | Step 0~11 전체 설치 가이드 (10p) |
| `LLM_Quick_Reference.pdf` | 환경 기록, 일일 워크플로, 명령어 시트 (4p) |
| `LLM_project_session_01.md` | 본 문서 |

### 권장 배치
```
~/projects/llm-from-scratch/
├── NOTES.md          <- 앞으로 세션 기록
└── docs/
    ├── LLM_Environment_Setup_Guide.pdf
    ├── LLM_Quick_Reference.pdf
    └── LLM_project_session_01.md
```
