# /// script
# dependencies = ["markdown"]
# ///
"""Fine-tuning overview in Korean -> docs/Ch6_Fine_Tuning_Overview_KO.pdf

Run from anywhere:  uv run tools/pdf/finetuning_overview_ko.py

Why fine-tune, what it is, and how classification fine-tuning (chapter 6) differs from
instruction fine-tuning (chapter 7). Dataset numbers come from the files in notebooks/
(SMSSpamCollection.tsv, train/validation/test.csv) and notebooks/06_classification.ipynb;
parameter counts were computed with src/gpt_model.py. Korean text is kept out of
monospace blocks, where it breaks alignment.
"""
import subprocess
import tempfile
from pathlib import Path

import markdown
from gpt_model_walkthrough import CHROME

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "docs" / "Ch6_Fine_Tuning_Overview_KO.pdf"
TITLE = "파인튜닝 한눈에 보기"

CSS = """
@page {
  size: A4; margin: 17mm 18mm 19mm 18mm;
  @bottom-left { content: "파인튜닝 한눈에 보기"; font: 7.5pt 'Apple SD Gothic Neo'; color: #777; }
  @bottom-right { content: counter(page); font: 7.5pt 'Apple SD Gothic Neo'; color: #777; }
}
body { font: 9.9pt/1.7 'Apple SD Gothic Neo', 'Helvetica Neue', sans-serif; color: #1a1a1a; }
h1 { font-size: 20pt; margin: 0 0 3pt; }
.sub { color: #5a5a5a; margin: 0 0 12pt; }
h2 { font-size: 14pt; color: #2f4f76; border-top: 1pt solid #2f4f76; padding-top: 8pt;
     margin: 18pt 0 6pt; break-after: avoid; }
h3 { font-size: 11.2pt; margin: 13pt 0 3pt; break-after: avoid; }
p { margin: 0 0 6pt; }
ul, ol { margin: 0 0 7pt; padding-left: 18pt; }
li { margin-bottom: 2pt; }
blockquote { margin: 6pt 0 9pt; padding: 6pt 10pt; background: #eef2f8; color: #243b5c;
             border-left: 3pt solid #2f4f76; break-inside: avoid; }
blockquote p { margin: 0 0 3pt; }
pre { background: #f4f5f7; border: 0.5pt solid #cfcfcf; padding: 6pt 8pt; margin: 4pt 0 8pt;
      font: 8.3pt/1.42 Menlo, monospace; white-space: pre-wrap; break-inside: avoid; }
code { font: 8.6pt Menlo, monospace; color: #2f4f76; }
pre code { color: #1a1a1a; font-size: inherit; }
table { border-collapse: collapse; width: 100%; margin: 4pt 0 9pt; break-inside: avoid; }
th, td { border: 0.5pt solid #d4d4d4; padding: 3.5pt 7pt; vertical-align: top; text-align: left; }
th { background: #ececec; }
.flow { display: flex; align-items: stretch; gap: 0; margin: 8pt 0 10pt; break-inside: avoid; }
.flow .box { flex: 1; border: 0.8pt solid #9fb6d3; background: #f6f9fd; padding: 6pt 8pt; font-size: 9pt; }
.flow .box b { display: block; color: #2f4f76; margin-bottom: 2pt; }
.flow .arrow { align-self: center; padding: 0 5pt; color: #2f4f76; font-size: 13pt; }
.warn { border-left: 3pt solid #b5651d; background: #fbf3ea; padding: 5pt 9pt; margin: 6pt 0 8pt;
        break-inside: avoid; }
.end { color: #777; font-size: 7.8pt; text-align: center; margin-top: 16pt; }
"""

TEXT = r'''
# 파인튜닝 한눈에 보기

<p class="sub">왜 하는지, 무엇을 하는지, 그리고 두 가지 방법 — 분류 파인튜닝(Raschka 6장)과 지시 파인튜닝(7장)이
어떻게 다른지. 5장까지 직접 해 본 것 위에서 설명한다.</p>

> **한 줄 요약.** 사전학습은 "언어 전반"을 배우는 **비싼** 단계이고, 파인튜닝은 이미 배운 모델을 "특정한 일"에
> 맞게 조금 더 가르치는 **싼** 단계다. 분류 파인튜닝은 모델이 *정해진 보기 중 하나를 고르게* 만들고, 지시
> 파인튜닝은 모델이 *지시를 읽고 답을 써내게* 만든다.

<div class="flow">
<div class="box"><b>1. 사전학습 (5장)</b>엄청난 양의 글로 "다음 토큰 맞히기"를 반복한다. 문법, 단어 뜻, 세상 지식이 가중치에 쌓인다.</div>
<div class="arrow">→</div>
<div class="box"><b>2. 파인튜닝 (6·7장)</b>그 가중치에서 출발해, 목적에 맞는 작은 데이터로 조금 더 학습한다.</div>
<div class="arrow">→</div>
<div class="box"><b>3. 사용</b>스팸 필터(분류), 또는 질문에 답하는 어시스턴트(지시).</div>
</div>

## 1. 5장까지 만든 모델은 무엇을 할 수 있나

5장 끝에서 OpenAI의 GPT-2 가중치를 불러와 이런 문장을 얻었다.

```text
Every effort moves you toward finding an ideal new way to practice something!
```

이 모델은 **다음 토큰 예측기**다. 출력은 `[batch, tokens, 50257]`, 즉 위치마다 "다음에 올 토큰" 50,257개의
점수다. 그래서 **글을 이어 쓰는 것**은 잘한다.

하지만 **시킨 일을 하지는 못한다.** 책 6.4절에서는 사전학습만 된 GPT-2에게 "다음 문자가 스팸인가? yes 또는 no로
답하라"라고 묻는다. 모델은 yes나 no로 답하지 않고, 질문 문장을 그대로 따라 쓴다. 이상한 일이 아니다. 이 모델은
인터넷 글을 이어 쓰는 연습만 했지, "질문을 받으면 답한다"는 형식이나 "스팸이란 무엇인가"를 따로 배운 적이 없다.

> **비유.** 사전학습된 모델은 도서관의 책을 엄청나게 많이 읽은 사람이다. 말은 유창하지만, 회사에 처음 온 날이라
> "이 메일이 스팸인지 분류해 주세요"라는 업무는 아직 모른다. 파인튜닝은 **업무 교육**이다. 읽기를 처음부터 다시
> 가르치는 게 아니라, 이미 있는 실력 위에 일하는 법만 짧게 가르친다.

## 2. 왜 파인튜닝이 필요한가

### 이유 1. 사전학습은 너무 비싸다

GPT-2는 약 40GB의 웹 텍스트로 학습했다. 5장에서 우리는 단편 소설 한 편(5,145 토큰)으로 10 epoch를 학습했는데,
결과는 학습 손실 0.391, 검증 손실 6.452. 모델은 영어를 배운 게 아니라 **소설을 외웠다.** 쓸 만한 언어 모델을
처음부터 만들려면 이보다 수십만 배 많은 데이터와 GPU가 필요하다.

### 이유 2. 이미 배운 것을 다시 쓸 수 있다

스팸을 가려내려면 "free prize", "call now", "you have won" 같은 표현이 어떤 느낌인지 알아야 한다. 사전학습된
모델은 이런 언어 지식을 이미 가중치 안에 갖고 있다. 파인튜닝은 이 지식을 버리지 않고 **그 위에** 새 일을 얹는다.

### 이유 3. 적은 데이터로 충분하다

6장의 학습 데이터는 문자 메시지 **1,045개**뿐이다. 이것만으로 영어를 처음부터 배우는 건 불가능하지만, 이미 영어를
아는 모델에게 "스팸이냐 아니냐"를 가르치기에는 충분하다.

| | 처음부터 학습 | 파인튜닝 |
|---|---|---|
| 시작 가중치 | 무작위 | 사전학습된 가중치 |
| 필요한 데이터 | 수십억 토큰 | 수천 개의 예시 |
| 필요한 계산 | GPU 여러 대로 며칠~몇 주 | 노트북으로 몇 분 (책 6장 기준 약 6분) |
| 결과 | 언어 전반을 배운 모델 | 그 모델 + 특정한 일을 하는 능력 |

## 3. 파인튜닝이란 정확히 무엇인가

**정의:** 사전학습된 가중치에서 출발해, 목적에 맞는 (대개 정답이 붙은) 작은 데이터로 학습을 더 하는 것.

가장 중요한 사실은 **학습하는 방법이 5장과 똑같다**는 것이다. 손실을 계산하고, `loss.backward()`로 기울기를 구하고,
`optimizer.step()`으로 가중치를 조금 움직인다. 바뀌는 것은 세 가지뿐이다.

| | 사전학습 (5장) | 파인튜닝 (6·7장) |
|---|---|---|
| **무엇에서 시작하나** | 무작위 가중치 | 사전학습된 가중치 |
| **무엇을 보여주나** | 아무 글 (정답 = 다음 토큰, 공짜) | 목적에 맞게 사람이 준비한 예시 |
| **무엇을 맞히게 하나** | 모든 위치의 다음 토큰 | 분류: 클래스 하나 / 지시: 응답의 다음 토큰 |

## 4. 두 가지 방법 — 먼저 큰 그림

| | 분류 파인튜닝 (6장) | 지시 파인튜닝 (7장) |
|---|---|---|
| 하는 일 | 글을 읽고 **정해진 보기 중 하나**를 고른다 | **지시를 읽고 답을 써낸다** |
| 비유 | 객관식 채점자 | 주관식 답안 작성자 |
| 예 | 스팸/정상, 긍정/부정 | "이 문장을 요약해 줘", "수동태로 바꿔 줘" |
| 출력 | 클래스 점수 2개 | 다음 토큰 점수 50,257개 (그대로) |

## 5. 분류 파인튜닝 (6장) 자세히

### 5-1. 무엇을 하나

입력 글 하나 → **미리 정한 클래스 중 하나.** 6장의 과제는 SMS 스팸 분류다: 클래스는 0(정상, "ham")과 1(스팸).
같은 방법으로 감성 분석(긍정/부정), 뉴스 주제 분류, 언어 판별 등을 할 수 있다.

### 5-2. 데이터: 글 + 정답 라벨 (노트북 셀 3–9)

| 단계 | 내 노트북의 숫자 |
|---|---|
| 원본 SMS Spam Collection | 5,572개 (정상 4,825, 스팸 747) |
| 균형 맞추기: 정상을 스팸 수만큼만 뽑기 | 747 + 747 = 1,494개 |
| 70 / 10 / 20 으로 나누기 | 학습 1,045 · 검증 149 · 테스트 300 |

**왜 균형을 맞추나?** 원본은 87%가 정상이다. 그대로 학습하면 모델은 "무조건 정상"이라고만 답해도 87%를 맞힌다.
이 꼼수를 배우지 못하게 두 클래스를 같은 수로 맞춘다.

### 5-3. 패딩: 길이를 맞춰 배치로 묶기 (셀 10–17)

문자 길이가 제각각이라, 가장 긴 학습 문자(**120 토큰**)에 맞춰 짧은 문자 뒤를 토큰 50256(`<|endoftext|>`)으로
채운다. 그래서 배치는 입력 `[8, 120]`, 라벨 `[8]`이 된다. 문자 8개에 정답 8개 — **문자 하나에 정답 하나**다.
배치 수는 학습 130, 검증 19, 테스트 38.

### 5-4. 모델 수술: 출력층 바꾸기 (6.5절)

```python
model.out_head = torch.nn.Linear(768, 2)    # was Linear(768, 50257)
```

토큰 50,257개 중에 고르던 출력층을, 클래스 2개 중에 고르는 출력층으로 **교체**한다. 새 층은 768 × 2 + 2 = 1,538개의
가중치를 무작위로 갖고 시작한다. 나머지(임베딩, 트랜스포머 블록 12개, 마지막 LayerNorm)는 사전학습된 그대로다.

### 5-5. 얼리기(freeze): 대부분은 학습하지 않는다

모든 가중치를 `requires_grad = False`로 얼린 뒤, **마지막 트랜스포머 블록, 마지막 LayerNorm, 새 출력층**만 다시
학습 가능하게 푼다.

| | 가중치 수 |
|---|---|
| 모델 전체 (새 출력층 포함) | 124,441,346 |
| 학습하는 부분 | 7,090,946 (약 5.7%) |

이유는 두 가지다. 학습이 훨씬 빠르고, 적은 데이터로 학습하다가 사전학습에서 얻은 언어 지식을 망가뜨릴 위험이
줄어든다. 아래쪽 층은 어떤 일에나 쓰이는 일반적인 언어 특징을, 위쪽 층은 과제에 가까운 특징을 담는 경향이 있어서,
위쪽만 고쳐도 충분하다.

### 5-6. 마지막 토큰의 출력만 쓴다

트랜스포머는 여전히 토큰마다 출력을 낸다. "Do you have time"(4토큰)을 넣으면 출력은 `[1, 4, 2]`다. 문자 하나에
필요한 답은 하나이므로 **마지막 토큰의 행만** 쓴다.

```python
logits = model(input_ids)[:, -1, :]    # [1, 4, 2] -> [1, 2]
```

왜 마지막인가? 3장의 causal mask 때문에 각 토큰은 자기와 **앞의** 토큰만 볼 수 있다. 문장 전체를 본 것은 마지막
토큰뿐이다. (자세한 설명: `docs/Ch6_One_Message_One_Class_Decision.pdf`)

### 5-7. 손실과 정확도 (6.6절)

- **손실:** 5장과 같은 cross-entropy. 다만 점수 2개와 정답 1개를 비교한다.
  `cross_entropy(logits[:, -1, :], labels)`
- **정확도:** 점수 2개 중 큰 쪽(`argmax`)이 정답과 같은 문자의 비율.
- 학습 전에는 약 50% — 동전 던지기 수준이다. 책에서는 5 epoch 학습 후 테스트 정확도가 약 96%가 된다.

정답이 하나로 정해져 있으니 **평가가 쉽다.** "맞았나, 틀렸나"만 세면 된다.

### 5-8. 사용 (6.8절)

새 문자를 토큰으로 바꾸고, 모델에 넣고, 마지막 토큰의 점수 2개 중 큰 쪽을 고른다. 결과는 "spam" 또는 "not spam".

<div class="warn"><b>장점:</b> 작은 모델과 적은 데이터로 빠르게, 높은 정확도. 출력이 항상 정해진 보기 중 하나라서
쓰기도 평가하기도 쉽다.<br><b>단점:</b> 그 일만 한다. 스팸 분류기는 요약도, 번역도, 다른 분류도 못 한다. 클래스를
바꾸려면 새 라벨 데이터로 다시 학습해야 한다.</div>

## 6. 지시 파인튜닝 (7장) 자세히

### 6-1. 무엇을 하나

사람이 쓴 **지시(instruction)**를 읽고 그에 맞는 **응답**을 써낸다. ChatGPT 같은 어시스턴트의 기본이 되는 방법이다.
한 가지 일이 아니라 "요약해 줘", "고쳐 줘", "설명해 줘" 같은 **여러 종류의 일**을 하나의 모델이 하게 된다.

### 6-2. 데이터: 지시–응답 쌍

책 7장은 약 1,100개의 지시–응답 쌍을 쓴다. 각 예시는 정해진 틀(프롬프트 형식)에 맞춰 하나의 글로 이어 붙인다.
아래는 책이 쓰는 Alpaca 형식의 예시다.

```text
Below is an instruction that describes a task. Write a response that
appropriately completes the request.

### Instruction:
Convert the active sentence to passive: 'The chef cooks the meal every day.'

### Response:
The meal is cooked every day by the chef.
```

### 6-3. 모델은 거의 그대로다

분류와 가장 크게 다른 점이다. **출력층을 바꾸지 않는다.** 출력은 여전히 토큰 50,257개의 점수이고, 학습 목표도 여전히
**다음 토큰 예측**이다. 바뀌는 것은 **데이터의 모양**뿐이다. 모델은 "`### Response:` 다음에는 지시에 맞는 답이
온다"는 패턴을 배운다. 즉 5장의 학습을, 지시–응답 형식의 글로 한 번 더 하는 것이다.

### 6-4. 세부 사항 몇 가지

- **패딩은 손실에서 뺀다.** 길이를 맞추려고 채운 토큰까지 맞히라고 하면 의미 없는 학습이 된다. 책은 정답의 패딩
  토큰을 `-100`으로 바꾸는데, PyTorch의 `cross_entropy`는 `-100`인 위치를 계산에서 제외한다.
- **더 큰 모델을 쓴다.** 124M 모델로는 지시 따르기 품질이 낮아서, 책은 355M(gpt2-medium)을 쓴다.
- **평가가 어렵다.** "요약해 줘"의 정답은 하나가 아니다. 그래서 정확도를 셀 수 없다. 책은 더 큰 모델(Ollama로
  실행한 Llama 3)에게 응답을 0–100점으로 채점하게 한다.

<div class="warn"><b>장점:</b> 하나의 모델이 여러 종류의 일을 한다. 학습 때 보지 못한 지시에도 어느 정도 대응한다.<br>
<b>단점:</b> 더 많은 데이터와 더 큰 모델이 필요하고, 학습이 더 오래 걸리며, 결과가 좋은지 판단하기 어렵다.</div>

## 7. 나란히 비교

| | 분류 파인튜닝 (6장) | 지시 파인튜닝 (7장) |
|---|---|---|
| 목표 | 정해진 클래스 중 하나 고르기 | 지시에 맞는 응답 쓰기 |
| 데이터 | 글 + 클래스 번호 (1,494개) | 지시 + 응답 (약 1,100개) |
| 정답의 모양 | 문자당 숫자 하나 `[batch]` | 응답의 토큰들 `[batch, tokens]` |
| 출력층 | **교체**: `Linear(768, 2)` | **그대로**: `Linear(768, 50257)` |
| 쓰는 출력 위치 | 마지막 토큰 하나 | 모든 위치 (5장과 같음) |
| 손실 | 점수 2개 vs 정답 1개 | 다음 토큰 cross-entropy, 패딩 제외 |
| 학습하는 부분 (책) | 마지막 블록 + LayerNorm + 출력층 | 모델 전체 |
| 모델 크기 (책) | 124M | 355M |
| 평가 | 정확도 (맞았나/틀렸나) | 다른 LLM이 채점 |
| 비유 | 객관식 채점자 | 주관식 답안 작성자 |

## 8. 어떤 방법을 골라야 하나

- **답이 몇 가지 중 하나로 정해져 있다** → 분류 파인튜닝. 스팸 필터, 리뷰 감성, 고객 문의 분류처럼. 더 작고, 빠르고,
  평가가 쉽고, 엉뚱한 답을 낼 수가 없다.
- **답이 자유로운 글이다, 또는 여러 종류의 일을 시키고 싶다** → 지시 파인튜닝.

실제 대형 어시스턴트는 지시 파인튜닝 뒤에, 사람이 더 좋다고 고른 답을 따르도록 하는 단계를 더 거친다. 이 책의
범위 밖이다.

## 9. 6장 지도 — 지금 어디까지 왔나

| 절 | 내용 | 내 노트북 |
|---|---|---|
| 6.1 | 파인튜닝의 종류 (이 문서의 4장) | — |
| 6.2 | 데이터 준비: 다운로드, 균형, 라벨, 나누기 | 셀 3–9 완료 |
| 6.3 | 데이터 로더: 패딩, 배치 | 셀 10–17 완료 |
| 6.4 | 사전학습 가중치로 모델 만들기 | 셀 18–19 진행 중 |
| 6.5 | 출력층 교체, 얼리기 | |
| 6.6 | 분류 손실과 정확도 | |
| 6.7 | 파인튜닝 (학습 루프) | |
| 6.8 | 스팸 분류기로 사용하기 | |

6.4의 나머지에서는 불러온 모델이 여전히 글을 잘 이어 쓰는지 확인하고, 위 1장에서 말한 스팸 질문을 던져 본다.
모델이 제대로 답하지 **못하는 것**을 직접 보는 것이 이 절의 목적이다 — 그것이 6.5부터의 파인튜닝이 필요한 이유다.

## 10. 스스로 확인

1. 사전학습만 된 GPT-2에게 "이 문자가 스팸인가?"라고 물으면 왜 제대로 답하지 못하나?
2. 파인튜닝에서 5장과 **같은** 것은 무엇이고, **바뀌는** 것 세 가지는 무엇인가?
3. 분류 데이터의 균형을 맞추지 않으면 어떤 꼼수가 생기나?
4. 분류 파인튜닝은 출력층을 바꾸는데, 지시 파인튜닝은 왜 바꾸지 않나?
5. 분류에서 마지막 토큰의 출력만 쓰는 이유는?
6. 분류 모델은 정확도로 평가하는데, 지시 모델은 왜 그렇게 할 수 없나?

**답.** (1) 다음 토큰 이어 쓰기만 배웠고, 질문에 답하는 형식도 스팸의 기준도 배운 적이 없어서. (2) 같은 것: 손실 →
`backward()` → `step()`의 학습 방법. 바뀌는 것: 시작 가중치(사전학습된 것), 데이터(목적에 맞는 예시), 맞힐
대상(클래스 또는 응답). (3) 원본의 87%가 정상이라 "무조건 정상"만 답해도 87%를 맞힌다. (4) 지시 모델이 낼 답은
여전히 글, 즉 다음 토큰들이기 때문이다. (5) causal mask 때문에 문장 전체를 본 것은 마지막 토큰뿐이라서.
(6) 좋은 답이 여러 개일 수 있어 "맞았다/틀렸다"로 나눌 수 없기 때문이다.
'''


def build():
    body = markdown.markdown(TEXT, extensions=["fenced_code", "tables"])
    page = (f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{TITLE}</title>'
            f"<style>{CSS}</style></head><body>{body}"
            '<p class="end">생성 스크립트: tools/pdf/finetuning_overview_ko.py · 데이터 수치는 '
            'notebooks/의 SMS 데이터와 06_classification.ipynb에서 확인</p></body></html>')
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(page)
        tmp = Path(f.name)
    try:
        subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={OUT}", tmp.as_uri()], check=True, capture_output=True)
    finally:
        tmp.unlink()
    print("wrote", OUT)


if __name__ == "__main__":
    build()
