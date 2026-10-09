# /// script
# dependencies = ["reportlab"]
# ///
"""Flashcards + quiz generator -> docs/Ch<N>_Flashcards_KR.pdf, docs/Ch<N>_Quiz_KR.pdf

Run from anywhere:  uv run tools/pdf/study_material.py

Add a new topic by adding an entry to TOPICS: cards are (question, answer) pairs,
quiz items are (question, [4 options], correct index, why). Numbers in the chapter 2
set were verified by running the project's own code; chapter 3 facts were checked
against the book notebook docs/LLMs-from-scratch-main/ch03.
"""
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Table,
    TableStyle,
)

KOREAN_FONT = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
FONT = "KR"
pdfmetrics.registerFont(TTFont(FONT, KOREAN_FONT))

REPO = Path(__file__).resolve().parents[2]
DOCS = REPO / "docs"

INK = colors.HexColor("#1a1a1a")
GREY = colors.HexColor("#5a5a5a")
LINE = colors.HexColor("#cfcfcf")
ACCENT = "#2f4f76"
ROW_ALT = colors.HexColor("#f7f8fa")
HEAD = colors.HexColor("#ececec")
KEY_BG = colors.HexColor("#ebf5ec")

CONTENT_W = 172 * mm

title_s = ParagraphStyle("T", fontName=FONT, fontSize=18, leading=24, textColor=INK)
sub_s = ParagraphStyle("S", fontName=FONT, fontSize=9.6, leading=14, textColor=GREY, spaceAfter=8)
note_s = ParagraphStyle("N", fontName=FONT, fontSize=9, leading=13.5, textColor=GREY, spaceAfter=10)
sec_s = ParagraphStyle("SEC", fontName=FONT, fontSize=11, leading=15, spaceBefore=10, spaceAfter=5,
                       textColor=colors.HexColor(ACCENT), keepWithNext=1)
q_s = ParagraphStyle("Q", fontName=FONT, fontSize=9.6, leading=13.6)
a_s = ParagraphStyle("A", fontName=FONT, fontSize=9.4, leading=13.4, textColor=colors.HexColor("#333333"))
num_s = ParagraphStyle("NUM", fontName=FONT, fontSize=9.4, leading=13.4, alignment=TA_CENTER,
                       textColor=colors.HexColor(ACCENT))
quiz_q = ParagraphStyle("QQ", fontName=FONT, fontSize=10, leading=15, spaceBefore=8, spaceAfter=3)
quiz_o = ParagraphStyle("QO", fontName=FONT, fontSize=9.6, leading=14, leftIndent=14, spaceAfter=1)
key_s = ParagraphStyle("K", fontName=FONT, fontSize=9.3, leading=13.4)
cap_s = ParagraphStyle("C", fontName=FONT, fontSize=8.4, leading=12, alignment=TA_CENTER,
                       textColor=GREY, spaceBefore=6)


def accent(t):
    return t.replace("<b>", f'<font color="{ACCENT}">').replace("</b>", "</font>")


def P(t, s):
    return Paragraph(accent(t), s)


def C(t):
    """Inline code inside Korean text - Courier has no Hangul, so ASCII only."""
    return f'<font face="Courier" size="8.8">{escape(t)}</font>'


def footer_maker(label):
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont(FONT, 8)
        canvas.setFillColor(GREY)
        canvas.drawString(19 * mm, 10 * mm, label)
        canvas.drawRightString(A4[0] - 19 * mm, 10 * mm, str(doc.page))
        canvas.restoreState()
    return footer


def build_flashcards(topic):
    story = [
        P(f"{topic['title']} · 플래시카드", title_s),
        P(f"{len(topic['cards'])}장 · 왼쪽은 질문, 오른쪽은 답", sub_s),
        HRFlowable(width="100%", thickness=0.7, color=LINE, spaceAfter=8),
        P("<b>쓰는 법:</b> 오른쪽 열을 손이나 종이로 가리고, 질문을 보고 답을 먼저 말한 뒤 확인한다. "
          "막힌 카드는 번호를 적어두고 다음 회차에 그것부터 본다.", note_s),
    ]
    rows = [[P("#", q_s), P("질문", q_s), P("답", q_s)]]
    styles = [
        ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("BACKGROUND", (0, 0), (-1, 0), HEAD),
        ("LINEAFTER", (1, 0), (1, -1), 1.2, colors.HexColor(ACCENT)),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for i, (q, a) in enumerate(topic["cards"], start=1):
        rows.append([P(str(i), num_s), P(q, q_s), P(a, a_s)])
        if i % 2 == 0:
            styles.append(("BACKGROUND", (0, i), (-1, i), ROW_ALT))
    t = Table(rows, colWidths=[10 * mm, 74 * mm, 88 * mm], repeatRows=1)
    t.setStyle(TableStyle(styles))
    story.append(t)
    story.append(P(f"생성 스크립트: tools/pdf/study_material.py · {topic['verified']}", cap_s))
    doc = SimpleDocTemplate(str(DOCS / topic["cards_file"]), pagesize=A4,
                            leftMargin=19 * mm, rightMargin=19 * mm,
                            topMargin=17 * mm, bottomMargin=17 * mm,
                            title=f"{topic['title']} 플래시카드")
    f = footer_maker(f"{topic['title']} · 플래시카드")
    doc.build(story, onFirstPage=f, onLaterPages=f)
    return topic["cards_file"]


def build_quiz(topic):
    marks = ["①", "②", "③", "④"]
    story = [
        P(f"{topic['title']} · 퀴즈", title_s),
        P(f"{len(topic['quiz'])}문항 객관식 · 정답과 해설은 마지막 쪽", sub_s),
        HRFlowable(width="100%", thickness=0.7, color=LINE, spaceAfter=6),
        P("점수: ______ / " + str(len(topic["quiz"])), note_s),
    ]
    for i, (q, opts, _, _) in enumerate(topic["quiz"], start=1):
        block = [P(f"<b>{i}.</b> {q}", quiz_q)]
        block += [P(f"{marks[j]} {o}", quiz_o) for j, o in enumerate(opts)]
        story.append(KeepTogether(block))
    story.append(PageBreak())
    story.append(P(f"{topic['title']} · 정답과 해설", title_s))
    story.append(HRFlowable(width="100%", thickness=0.7, color=LINE, spaceAfter=8))
    rows = [[P("문항", key_s), P("정답", key_s), P("왜", key_s)]]
    for i, (_, opts, correct, why) in enumerate(topic["quiz"], start=1):
        rows.append([P(str(i), num_s), P(f"{marks[correct]} {opts[correct]}", key_s), P(why, key_s)])
    t = Table(rows, colWidths=[12 * mm, 52 * mm, 108 * mm], repeatRows=1)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("BACKGROUND", (0, 0), (-1, 0), HEAD),
        ("BACKGROUND", (1, 1), (1, -1), KEY_BG),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t)
    story.append(P(f"생성 스크립트: tools/pdf/study_material.py · {topic['verified']}", cap_s))
    doc = SimpleDocTemplate(str(DOCS / topic["quiz_file"]), pagesize=A4,
                            leftMargin=19 * mm, rightMargin=19 * mm,
                            topMargin=17 * mm, bottomMargin=17 * mm,
                            title=f"{topic['title']} 퀴즈")
    f = footer_maker(f"{topic['title']} · 퀴즈")
    doc.build(story, onFirstPage=f, onLaterPages=f)
    return topic["quiz_file"]


CH2 = {
    "title": "Chapter 2 — 텍스트 데이터 다루기",
    "cards_file": "Ch2_Flashcards_KR.pdf",
    "quiz_file": "Ch2_Quiz_KR.pdf",
    "verified": "숫자는 the-verdict.txt와 annabel_lee.txt로 직접 실행해 확인",
    "cards": [
        ("토큰화(tokenization)란 무엇인가?",
         "텍스트를 토큰 단위로 쪼개고, 각 토큰에 정수 ID를 붙이는 과정. 신경망은 글자가 아니라 숫자만 받는다."),
        ("정규식 토크나이저로 the-verdict.txt를 쪼개면 토큰 수와 어휘 크기는?",
         "토큰 4,690개, 어휘 1,130개. 특수 토큰 두 개를 더하면 1,132개."),
        ("특수 토큰 &lt;|unk|&gt;와 &lt;|endoftext|&gt;는 각각 왜 필요한가?",
         "&lt;|unk|&gt;는 어휘에 없는 단어를 표시하고, &lt;|endoftext|&gt;는 서로 다른 문서의 경계를 표시한다."),
        ("SimpleTokenizerV1이 어휘 밖 단어를 만나면?",
         f"{C('KeyError')}로 죽는다. V2는 대신 &lt;|unk|&gt;로 바꾸지만, 그 순간 원래 단어 정보는 사라진다."),
        ("BPE는 왜 &lt;|unk|&gt;가 필요 없는가?",
         "모르는 단어를 통째로 버리지 않고 <b>아는 조각으로 쪼개기</b> 때문이다."),
        ("같은 the-verdict.txt가 BPE로는 몇 토큰인가? 정규식과 비교하면?",
         "5,145개. 정규식(4,690)보다 많다. '토큰'은 고정 단위가 아니라 토크나이저가 정의한다."),
        ("BPE는 'HAD'를 어떻게 쪼개는가?",
         "' H' + 'AD' 두 조각. 정규식 토크나이저는 'HAD' 한 토큰으로 본다."),
        ("gpt2 토크나이저의 어휘 크기는?", "50,257개."),
        ("눈에 보이지 않는 문자가 결과를 바꾼 사례는?",
         f"들여쓰기가 일반 공백이면 {C('[220, 220]')}, {C('nbsp')}면 {C('[4603, 1849]')}. 같은 시가 463 vs 467 토큰."),
        ("슬라이딩 윈도우에서 target은 input과 어떤 관계인가?",
         "input을 <b>한 칸 민 것</b>. 각 자리마다 '바로 다음 토큰'이 정답이 되어 다음 토큰 맞히기 문제가 된다."),
        ("윈도우 개수는 어떻게 세는가?",
         f"{C('range(0, len(token_ids) - max_length, stride)')}의 개수. 끝값은 포함되지 않는다."),
        ("467토큰을 max_length 4, stride 4로 자르면 윈도우는 몇 개?",
         "116개. 463 ÷ 4 = 115 나머지 3 → 나머지가 있으니 +1."),
        ("stride가 max_length보다 작으면 무엇이 달라지는가?",
         "윈도우가 겹친다. 학습 예제는 많아지지만 예제끼리 상관관계가 커져 과적합 위험이 늘어난다."),
        (f"{C('drop_last=True')}는 무슨 일을 하는가?",
         "배치 크기를 못 채운 마지막 윈도우들을 <b>에러 없이 버린다</b>. Annabel Lee에서는 윈도우 4개, 시의 마지막 두 줄이 사라졌다."),
        ("DataLoader가 Dataset에게 요구하는 두 메서드는?",
         f"{C('__len__')}(개수)과 {C('__getitem__')}(idx번째 항목)."),
        ("토큰 ID를 그대로 신경망에 넣으면 왜 안 되는가?",
         "ID는 정렬 순서가 만든 이름표일 뿐인데, 신경망은 115를 114보다 큰 수로 취급한다."),
        (f"{C('nn.Embedding(a, b)')}에서 a와 b는 각각 무엇인가?",
         "a = 표의 행 개수(어휘 크기 또는 자리 개수), b = 열 개수(output_dim)."),
        ("임베딩 조회는 수학적으로 무엇과 같은가?",
         "원-핫 벡터 × 가중치 행렬. 그래서 평범한 신경망 층이고 역전파로 학습된다."),
        ("임베딩 표가 학습된다는 것을 출력에서 어떻게 확인하나?",
         f"{C('requires_grad=True')}와 조회 결과의 {C('grad_fn=<EmbeddingBackward0>')}."),
        (f"{C('[8, 4]')}를 임베딩에 넣으면 shape는?",
         f"{C('[8, 4, 256]')}. 규칙: 맨 뒤에 output_dim 차원이 하나 붙는다."),
        (f"{C('vocab_size')}는 무엇이 정하는가?",
         "텍스트가 아니라 <b>토크나이저</b>가 정한다. gpt2를 쓰면 언제나 50,257."),
        (f"{C('torch.manual_seed(123)')}를 쓰는 이유와 함정은?",
         "재현성 — 책의 숫자와 대조하려고. 함정: 그 시점 이후 첫 난수에만 적용되므로 사이에 다른 난수 연산이 끼면 값이 어긋난다."),
        ("위치 임베딩 표의 크기와 조회 번호는?",
         f"{C('nn.Embedding(context_length, output_dim)')}, 조회는 {C('torch.arange(context_length)')} = [0, 1, 2, 3]."),
        (f"{C('[8,4,256] + [4,256]')}이 에러 없이 되는 이유는?",
         "브로드캐스팅. [4,256] 한 벌을 8개 문장 각각에 복사해서 더한다."),
        ("같은 토큰이 다른 자리에 있을 때, 토큰 임베딩과 입력 임베딩은?",
         "토큰 임베딩은 같다(True). 위치 임베딩을 더한 입력 임베딩은 달라진다(False). 같은 자리라면 둘 다 같다."),
        (f"{C('IndexError: index out of range in self')}는 무엇을 뜻하나?",
         "표의 행 개수를 넘는 번호를 조회했다. 어느 표에 어떤 번호를 넣었는지부터 확인한다."),
    ],
    "quiz": [
        ("BPE 토크나이저가 어휘에 없는 단어를 만나면 어떻게 하는가?",
         ["&lt;|unk|&gt; 토큰으로 바꾼다", "에러를 낸다", "아는 조각들로 쪼갠다", "그 단어를 건너뛴다"],
         2, "BPE는 조각(subword) 단위라 모르는 단어도 아는 조각의 조합으로 표현한다. 그래서 &lt;|unk|&gt;가 필요 없다."),
        ("the-verdict.txt의 토큰 수가 정규식 4,690에서 BPE 5,145로 늘어난 이유로 가장 적절한 것은?",
         ["BPE가 공백을 토큰으로 세기 때문만이다", "BPE가 단어를 조각으로 더 잘게 나누기 때문이다",
          "텍스트가 손상되었기 때문이다", "어휘 크기가 50,257이기 때문이다"],
         1, "BPE는 'HAD'를 ' H'+'AD'처럼 조각으로 나눈다. 단어 하나가 여러 토큰이 되므로 총 개수가 늘어난다."),
        ("467토큰을 max_length=4, stride=4로 자르면 윈도우는 몇 개인가?",
         ["115개", "116개", "117개", "463개"],
         1, "range(0, 463, 4)의 개수 = 463 ÷ 4 = 115 나머지 3 → 116. 끝값은 포함되지 않는다."),
        ("윈도우 116개를 batch_size=8, drop_last=True로 묶으면?",
         ["배치 14개, 윈도우 4개 버림", "배치 15개, 버림 없음", "배치 14개, 버림 없음", "배치 15개, 윈도우 4개 버림"],
         0, "116 ÷ 8 = 14 나머지 4. 남은 4개는 배치를 채우지 못해 버려진다 — 에러도 경고도 없다."),
        ("target_chunk를 input_chunk보다 한 칸 뒤에서 자르는 이유는?",
         ["배치 크기를 맞추려고", "각 자리의 정답이 '바로 다음 토큰'이 되게 하려고",
          "패딩을 피하려고", "어휘 크기를 줄이려고"],
         1, "다음 토큰 맞히기 문제를 만들기 위해서다. input의 i번째 자리에 대한 정답이 target의 i번째가 된다."),
        (f"{C('nn.Embedding(50257, 256)')}에서 50257은 무엇인가?",
         ["텍스트의 토큰 개수", "서로 다른 토큰 종류(토크나이저 어휘 크기)", "배치 크기", "벡터의 길이"],
         1, "표의 행 개수다. 토큰 ID가 가질 수 있는 모든 값마다 행이 하나씩 있어야 하므로 토크나이저가 정한다."),
        (f"{C('inputs')}가 {C('[8, 4]')}일 때 토큰 임베딩(output_dim=256)의 결과 shape는?",
         ["[8, 4]", "[8, 256]", "[8, 4, 256]", "[4, 256]"],
         2, "임베딩을 거치면 맨 뒤에 output_dim 차원이 하나 붙는다."),
        ("위치 임베딩의 결과에 배치 차원(8)이 없는 이유는?",
         ["메모리를 아끼려고", "자리 번호는 문장과 무관해 모든 문장이 같기 때문", "버그다", "batch_size가 1이기 때문"],
         1, "8개 문장 모두 0·1·2·3번 자리로 똑같다. 한 벌만 만들고 브로드캐스팅으로 각 문장에 더한다."),
        ("같은 토큰이 서로 다른 자리에 있을 때, 위치 임베딩을 더한 뒤의 두 벡터는?",
         ["항상 같다", "달라진다", "무작위라 알 수 없다", "shape가 달라진다"],
         1, "자리마다 다른 위치 벡터가 더해지기 때문이다. 반대로 자리까지 같으면 결과도 같다."),
        (f"{C('IndexError: index out of range in self')}가 났다. 가장 먼저 확인할 것은?",
         ["배치 크기", "텍스트 인코딩", "조회한 번호가 표의 행 개수를 넘었는지", "학습률"],
         2, "임베딩 표에 없는 행을 요구했다는 뜻이다. vocab_size를 463으로 두고 ID 2885를 조회한 경우가 그 예다."),
    ],
}

CH3 = {
    "title": "Chapter 3 — 어텐션 메커니즘",
    "cards_file": "Ch3_Flashcards_KR.pdf",
    "quiz_file": "Ch3_Quiz_KR.pdf",
    "verified": "책 3장 노트북(ch03.ipynb)의 코드와 대조",
    "cards": [
        ("어텐션 이전 RNN 계열의 두 가지 한계는?",
         "① 고정 크기 기억에 눌러 담아 앞 내용이 희미해진다 ② 순차 처리라 병렬 계산이 안 된다."),
        ("self-attention의 핵심 발상은?",
         "문장을 펼쳐놓고 <b>모든 토큰이 모든 토큰을 동시에</b> 본다. 첫 단어와 백 번째 단어의 거리가 옆 단어와 다르지 않다."),
        ("어텐션 점수(attention score)는 어떻게 구하는가?",
         "Query와 Key의 <b>내적</b>. 두 벡터의 방향이 비슷할수록 큰 값이 나온다."),
        ("점수를 softmax에 통과시키는 이유는?",
         "합이 1인 비율로 바꾸기 위해서. 하나를 고르는(argmax) 연산이 아니라 <b>부드러운 비율</b>이라 미분이 되고 학습할 수 있다."),
        ("context vector란?",
         "attention weight를 가중치로 삼아 Value들을 모두 더한 값. 그 토큰의 문맥이 반영된 새 표현이다."),
        ("3.3절(가중치 없는 버전)에서 Query·Key·Value는 무엇인가?",
         "입력 임베딩 <b>자체</b>가 세 역할을 겸한다. 숫자는 같고 역할만 다르다."),
        ("Key와 Value를 왜 굳이 나누는가?",
         "'무엇으로 검색되는가'와 '무엇을 건네주는가'는 다르기 때문이다(도서관의 제목 vs 본문)."),
        ("전체 토큰 쌍의 점수를 한 줄로 구하면? (가중치 없는 버전)",
         f"{C('attn_scores = inputs @ inputs.T')}"),
        ("attention weights 한 행의 합은?", "정확히 1. softmax의 결과이기 때문이다."),
        ("3.4절에서 새로 도입되는 것은?",
         f"학습 가능한 가중치 행렬 {C('W_query')}, {C('W_key')}, {C('W_value')}. 책에서는 {C('nn.Linear')}로 만든다."),
        ("가중치 행렬이 들어오면 무엇이 바뀌는가? (세 가지)",
         "① Q·K·V가 서로 다른 벡터가 된다 ② 무엇이 서로 관련있는지를 학습으로 알아낸다 ③ 점수를 스케일링한다."),
        ("가중치 있는 버전에서 점수 계산식은?",
         f"{C('attn_scores = queries @ keys.T')}"),
        ("점수를 √d_k로 나누는 이유는?",
         "차원이 커지면 내적 값도 커져 softmax가 한쪽으로 극단적으로 치우치고, 그러면 기울기가 작아져 학습이 잘 안 된다."),
        (f"{C('d_k')}는 무엇인가?", f"key 벡터의 차원. 코드에서는 {C('keys.shape[1]')}."),
        ("인과적(causal) 어텐션이란?",
         "각 토큰이 <b>자기보다 뒤에 있는</b> 토큰의 가중치를 0으로 만드는 것. 다음 단어 맞히기에서 답을 미리 보지 못하게 한다."),
        ("마스크는 어떻게 만드는가?",
         f"{C('torch.triu(torch.ones(n, n), diagonal=1)')}로 위쪽 삼각형을 만들고, {C('masked_fill(mask.bool(), -torch.inf)')}로 덮는다."),
        ("0이 아니라 -inf를 채우는 이유는?",
         f"softmax <b>이전</b>에 덮기 때문이다. {C('exp(-inf) = 0')}이라 정규화 뒤 정확히 0이 되고, 남은 값들의 합은 1이 된다."),
        ("dropout은 어디에 적용하는가?",
         "softmax를 지난 attention weights에 적용한다. 학습할 때만 동작하고 평가할 때는 꺼진다."),
        (f"{C('register_buffer')}를 쓰는 이유는?",
         "mask처럼 <b>학습 대상은 아니지만</b> 모델과 함께 저장·이동되어야 하는 값을 등록하기 위해서다."),
        ("멀티헤드 어텐션이 필요한 이유는?",
         "문장에는 여러 종류의 관계가 동시에 있는데, 가중치를 한 벌만 계산하면 그중 하나만 잡히기 때문이다."),
        ("MultiHeadAttentionWrapper는 어떻게 구현되는가?",
         f"CausalAttention을 num_heads개 만들어 각각 돌린 뒤 결과를 {C('torch.cat')}으로 이어 붙인다."),
        ("효율적인 MultiHeadAttention은 무엇이 다른가?",
         "큰 행렬 하나를 만들고 <b>헤드 수만큼 쪼개서</b> 쓴다(weight splits). 여러 층을 따로 돌리지 않는다."),
        ("d_out과 num_heads의 관계는?",
         f"{C('d_out % num_heads == 0')}이어야 하고, 각 헤드의 차원은 {C('head_dim = d_out // num_heads')}."),
        ("self-attention과 cross-attention의 차이는?",
         "self는 같은 시퀀스 안에서, cross는 서로 다른 두 시퀀스 사이에서 관계를 계산한다."),
    ],
    "quiz": [
        ("어텐션에서 두 토큰의 관련도를 재는 기본 연산은?",
         ["코사인 유사도", "유클리드 거리", "내적(dot product)", "교차 엔트로피"],
         2, "Query와 Key의 내적으로 점수를 만든다. 방향이 비슷할수록 값이 커진다."),
        ("softmax를 쓰는 이유로 가장 적절한 것은?",
         ["가장 큰 점수 하나를 고르려고", "점수를 합이 1인 비율로 바꿔 미분 가능하게 하려고",
          "계산을 빠르게 하려고", "음수를 없애려고"],
         1, "하나를 고르는 연산은 미분이 안 되어 학습할 수 없다. softmax는 골라내기를 부드러운 섞기로 바꾼다."),
        ("가중치 행렬이 없는 3.3절 단계에서 Query, Key, Value의 관계는?",
         ["서로 다른 세 벡터다", "Query만 있고 나머지는 없다", "셋 다 입력 임베딩과 같은 벡터다", "무작위로 초기화된다"],
         2, "행렬이 없으면 세 벡터를 따로 만들 수 없다. 같은 임베딩이 세 역할을 겸하고, 역할만 다르다."),
        ("점수를 √d_k로 나누지 않으면 어떤 문제가 생기는가?",
         ["점수의 합이 1이 되지 않는다", "softmax가 한쪽으로 치우쳐 기울기가 작아진다",
          "행렬 곱이 불가능해진다", "마스크가 동작하지 않는다"],
         1, "차원이 커질수록 내적 값이 커진다. 그대로 softmax에 넣으면 분포가 극단적이 되어 학습이 느려진다."),
        ("인과적(causal) 어텐션에서 가리는 대상은?",
         ["자기 자신", "자기보다 앞에 있는 토큰", "자기보다 뒤에 있는 토큰", "가장 점수가 낮은 토큰"],
         2, "다음 단어를 맞히는 학습에서 뒤쪽 토큰은 정답에 해당한다. 그래서 뒤쪽의 가중치를 0으로 만든다."),
        ("마스크로 0 대신 -inf를 채우는 이유는?",
         ["0이 더 느리다", "softmax 이전이라 exp(-inf)=0이 되어 정규화 후 정확히 0이 되기 때문",
          "-inf가 메모리를 덜 쓴다", "PyTorch가 0을 허용하지 않는다"],
         1, "softmax 이후에 0을 넣으면 남은 값들의 합이 1이 아니게 된다. 마스크는 softmax 전에 적용한다."),
        ("dropout이 적용되는 위치는?",
         ["입력 임베딩", "attention weights(softmax 결과)", "Query 행렬", "출력 토큰 ID"],
         1, "책에서는 softmax를 지난 attention weights에 적용한다. 학습할 때만 동작한다."),
        (f"{C('register_buffer')}로 mask를 등록하는 이유는?",
         ["학습 파라미터로 만들려고", "학습 대상은 아니지만 모델과 함께 저장·이동되게 하려고",
          "메모리를 절약하려고", "mask를 매번 새로 만들려고"],
         1, "buffer는 파라미터가 아니라 학습되지 않지만, state_dict에 포함되고 device 이동도 함께 된다."),
        ("멀티헤드 어텐션에서 d_out=8, num_heads=4이면 head_dim은?",
         ["2", "4", "8", "32"],
         0, "head_dim = d_out // num_heads = 8 // 4 = 2. d_out이 num_heads로 나누어떨어져야 한다."),
        ("self-attention과 cross-attention의 차이는?",
         ["연산 속도", "같은 시퀀스 안이냐, 서로 다른 두 시퀀스 사이냐",
          "학습 여부", "softmax 사용 여부"],
         1, "self는 한 시퀀스 안에서 서로를 보고, cross는 예컨대 번역에서 원문과 번역문처럼 다른 두 시퀀스를 잇는다."),
    ],
}

for topic in (CH2, CH3):
    print("wrote", build_flashcards(topic), "|", build_quiz(topic))
