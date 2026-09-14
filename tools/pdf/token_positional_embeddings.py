# /// script
# dependencies = ["reportlab"]
# ///
"""Sections 2.7 / 2.8 explainer -> docs/Token_and_Positional_Embeddings_Explained.pdf

Run from anywhere:  uv run tools/pdf/token_positional_embeddings.py
"""
import math
from pathlib import Path

from reportlab.graphics.shapes import Circle, Drawing, Line, Polygon, Rect, String
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
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# macOS system font; needed because the built-in PDF fonts have no Hangul glyphs.
# AppleGothic has no bold weight, so emphasis is rendered with colour instead.
KOREAN_FONT = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
FONT = "KR"
FONT_B = "KR-Bold"
pdfmetrics.registerFont(TTFont(FONT, KOREAN_FONT))
pdfmetrics.registerFont(TTFont(FONT_B, KOREAN_FONT))
pdfmetrics.registerFontFamily(FONT, normal=FONT, bold=FONT_B, italic=FONT, boldItalic=FONT_B)

REPO = Path(__file__).resolve().parents[2]
OUT = str(REPO / "docs" / "Token_and_Positional_Embeddings_Explained.pdf")

INK = colors.HexColor("#1a1a1a")
GREY = colors.HexColor("#5a5a5a")
LINE = colors.HexColor("#c8c8c8")
FILL = colors.HexColor("#f3f3f3")
HEAD = colors.HexColor("#ececec")
ACCENT = "#2f4f76"
TOKEN_FILL = colors.HexColor("#e6ecf5")
POS_FILL = colors.HexColor("#f6eedd")
SUM_FILL = colors.HexColor("#e5f2e6")
HILITE = colors.HexColor("#fde9b8")

title_s = ParagraphStyle("T", fontName=FONT_B, fontSize=19, leading=25, textColor=INK)
sub_s = ParagraphStyle("S", fontName=FONT, fontSize=10, leading=14.5, textColor=GREY, spaceAfter=14)
part_s = ParagraphStyle("PART", fontName=FONT_B, fontSize=15, leading=20, textColor=INK,
                        spaceBefore=6, spaceAfter=10, keepWithNext=1)
h1 = ParagraphStyle("H1", fontName=FONT_B, fontSize=12.5, leading=17, spaceBefore=14,
                    spaceAfter=6, textColor=colors.HexColor(ACCENT), keepWithNext=1)
body = ParagraphStyle("B", fontName=FONT, fontSize=10, leading=16, spaceAfter=7)
item = ParagraphStyle("I", parent=body, leftIndent=12, spaceAfter=4)
note = ParagraphStyle("N", fontName=FONT, fontSize=9.6, leading=14.5, leftIndent=10,
                      textColor=colors.HexColor("#333333"), backColor=FILL, borderPadding=8,
                      spaceBefore=4, spaceAfter=10)
cap = ParagraphStyle("C", fontName=FONT, fontSize=8.6, leading=12, alignment=TA_CENTER,
                     textColor=GREY, spaceBefore=4, spaceAfter=10)
code_s = ParagraphStyle("CODE", fontName="Courier", fontSize=8.4, leading=11.8)
cell_s = ParagraphStyle("CELL", fontName=FONT, fontSize=8.8, leading=12.2)
cell_h = ParagraphStyle("CELLH", parent=cell_s, fontName=FONT_B)
take_s = ParagraphStyle("TK", fontName=FONT_B, fontSize=12, leading=18, alignment=TA_CENTER,
                        textColor=INK, spaceBefore=4, spaceAfter=4)

CONTENT_W = 166 * mm


def P(t, s=body):
    t = t.replace("<b>", f'<font color="{ACCENT}">').replace("</b>", "</font>")
    return Paragraph(t, s)


def table(rows, widths, header=True, highlight_rows=()):
    data = []
    for r, row in enumerate(rows):
        st = cell_h if (header and r == 0) else cell_s
        data.append([c if not isinstance(c, str) else P(c, st) for c in row])
    t = Table(data, colWidths=widths)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), HEAD))
    for r in highlight_rows:
        style.append(("BACKGROUND", (0, r), (-1, r), HILITE))
    t.setStyle(TableStyle(style))
    return KeepTogether([t])


def code(text):
    t = Table([[Preformatted(text, code_s)]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), FILL), ("BOX", (0, 0), (-1, -1), 0.5, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return t


def arrow(d, x1, y1, x2, y2, color=INK):
    d.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=1))
    ang = math.atan2(y2 - y1, x2 - x1)
    L = 5.5
    a1, a2 = ang + math.radians(152), ang - math.radians(152)
    d.add(Polygon([x2, y2, x2 + L * math.cos(a1), y2 + L * math.sin(a1),
                   x2 + L * math.cos(a2), y2 + L * math.sin(a2)],
                  fillColor=color, strokeColor=color))


# ------------------------------------------------------------ verified numbers
W = [
    [0.3374, -0.1778, -0.1690],
    [0.9178, 1.5810, 1.3010],
    [1.2753, -0.2010, -0.1606],
    [-0.4015, 0.9666, -1.1481],
    [-1.1589, 0.3255, -0.6315],
    [-2.8400, -0.7849, -1.4096],
]


def vec(v, nd=4):
    return "[" + ", ".join(f"{x:.{nd}f}" for x in v) + "]"


def lookup_diagram():
    d = Drawing(CONTENT_W, 172)
    cw, ch = 50, 19
    gx, gtop = 168, 132
    d.add(String(gx - 30, gtop + 18, "행 번호", fontName=FONT, fontSize=8, fillColor=GREY))
    for j, lab in enumerate(["열 0", "열 1", "열 2"]):
        d.add(String(gx + j * cw + 16, gtop + 6, lab, fontName=FONT, fontSize=7.5, fillColor=GREY))
    for i in range(6):
        y = gtop - (i + 1) * ch
        fill = HILITE if i == 3 else colors.white
        for j in range(3):
            d.add(Rect(gx + j * cw, y, cw, ch, fillColor=fill, strokeColor=LINE, strokeWidth=0.6))
            d.add(String(gx + j * cw + 7, y + 6, f"{W[i][j]:.4f}", fontName="Helvetica",
                         fontSize=7.6, fillColor=INK))
        d.add(String(gx - 14, y + 6, str(i), fontName="Helvetica-Bold", fontSize=8.5,
                     fillColor=colors.HexColor(ACCENT) if i == 3 else INK))
    ry = gtop - 4 * ch
    d.add(Rect(4, ry, 84, ch, fillColor=TOKEN_FILL, strokeColor=INK, strokeWidth=0.8))
    d.add(String(14, ry + 6, "token ID = 3", fontName="Helvetica-Bold", fontSize=8.5, fillColor=INK))
    arrow(d, 90, ry + ch / 2, gx - 20, ry + ch / 2, colors.HexColor(ACCENT))
    ox = gx + 3 * cw + 14
    arrow(d, gx + 3 * cw + 2, ry + ch / 2, ox + 6, ry + ch / 2, colors.HexColor(ACCENT))
    d.add(Rect(ox + 8, ry, 128, ch, fillColor=SUM_FILL, strokeColor=INK, strokeWidth=0.8))
    d.add(String(ox + 14, ry + 6, vec(W[3]), fontName="Helvetica", fontSize=7.8, fillColor=INK))
    d.add(String(gx - 2, 2, "embedding_layer.weight  (6 x 3)", fontName="Helvetica", fontSize=8,
                 fillColor=GREY))
    return d


def shape_flow_diagram():
    d = Drawing(CONTENT_W, 122)
    bh = 36

    def box(x, y, w, name, shape, fill):
        d.add(Rect(x, y, w, bh, fillColor=fill, strokeColor=INK, strokeWidth=0.8))
        d.add(String(x + w / 2, y + 22, name, fontName="Helvetica", fontSize=7.4,
                     fillColor=GREY, textAnchor="middle"))
        d.add(String(x + w / 2, y + 8, shape, fontName="Helvetica-Bold", fontSize=9,
                     fillColor=INK, textAnchor="middle"))

    y1, y2 = 78, 12
    c1, w1 = 0, 92
    c2, w2 = 110, 120
    c3, w3 = 248, 104
    box(c1, y1, w1, "inputs  (token IDs)", "[8, 4]", colors.white)
    box(c2, y1, w2, "token_embedding_layer", "50257 x 256", TOKEN_FILL)
    box(c3, y1, w3, "token_embeddings", "[8, 4, 256]", TOKEN_FILL)
    box(c1, y2, w1, "torch.arange(4)", "[0, 1, 2, 3]", colors.white)
    box(c2, y2, w2, "pos_embedding_layer", "4 x 256", POS_FILL)
    box(c3, y2, w3, "pos_embeddings", "[4, 256]", POS_FILL)
    for y in (y1, y2):
        arrow(d, c1 + w1 + 1, y + bh / 2, c2 - 2, y + bh / 2)
        arrow(d, c2 + w2 + 1, y + bh / 2, c3 - 2, y + bh / 2)
    px, py = 374, (y1 + y2 + bh) / 2
    d.add(Circle(px, py, 10, fillColor=colors.white, strokeColor=INK, strokeWidth=1))
    d.add(String(px, py - 4.5, "+", fontName="Helvetica-Bold", fontSize=13, fillColor=INK,
                 textAnchor="middle"))
    arrow(d, c3 + w3 + 1, y1 + bh / 2, px - 7, py + 7)
    arrow(d, c3 + w3 + 1, y2 + bh / 2, px - 7, py - 7)
    fx, fw = 396, CONTENT_W - 396
    arrow(d, px + 10, py, fx - 2, py)
    d.add(Rect(fx, py - bh / 2, fw, bh, fillColor=SUM_FILL, strokeColor=INK, strokeWidth=0.8))
    d.add(String(fx + fw / 2, py + 4, "input_embeddings", fontName="Helvetica", fontSize=6.6,
                 fillColor=GREY, textAnchor="middle"))
    d.add(String(fx + fw / 2, py - 10, "[8, 4, 256]", fontName="Helvetica-Bold", fontSize=8.6,
                 fillColor=INK, textAnchor="middle"))
    return d


# toy broadcasting example, computed rather than hand-typed
tok_vec = {"a": [1.0, 0.0], "cat": [0.0, 2.0], "dog": [0.0, 3.0], "sat": [2.0, 2.0]}
pos_vec = [[0.5, -0.5], [-0.5, 0.5], [0.0, 1.0]]
seqs = [["a", "cat", "sat"], ["dog", "a", "sat"]]


def v2(v):
    return "[" + ", ".join(f"{x:g}" for x in v) + "]"


toy_rows = [["문장", "자리", "토큰", "토큰 벡터", "+ 위치 벡터", "= 결과"]]
hl = []
for si, s in enumerate(seqs):
    for p, t in enumerate(s):
        res = [a + b for a, b in zip(tok_vec[t], pos_vec[p])]
        toy_rows.append([f"문장 {si + 1}", str(p), t, v2(tok_vec[t]), v2(pos_vec[p]), v2(res)])
        if t == "a":
            hl.append(len(toy_rows) - 1)

# ------------------------------------------------------------ story
S = []

S.append(P("토큰 임베딩과 위치 임베딩", title_s))
S.append(P("Raschka, <i>Build a Large Language Model (From Scratch)</i> 2.7절 · 2.8절 상세 해설 — "
           "2.8절을 입력하기 전에 읽는 자료", sub_s))
S.append(HRFlowable(width="100%", thickness=0.75, color=LINE, spaceAfter=12))

S.append(P("0. 한눈에 보기", h1))
S.append(P(
    "2.7절과 2.8절은 <b>같은 도구(nn.Embedding)를 두 번 쓰는 이야기</b>다. 첫 번째 표는 "
    "&ldquo;이 토큰이 무엇인가&rdquo;를, 두 번째 표는 &ldquo;이 토큰이 몇 번째 자리에 있는가&rdquo;를 "
    "벡터로 바꾼다. 둘을 더한 것이 LLM이 실제로 받는 입력이다."))
S.append(table([
    ["단계", "하는 일", "결과"],
    ["2.2~2.5", "텍스트를 토큰으로 쪼개고 정수 ID로 바꾼다", "토큰 ID 나열"],
    ["2.6", "슬라이딩 윈도우로 (입력, 정답) 쌍을 만든다", "inputs [8, 4]"],
    ["<b>2.7</b>", "<b>토큰 ID를 벡터로 바꾼다</b>", "<b>[8, 4, 256]</b>"],
    ["<b>2.8</b>", "<b>자리 번호도 벡터로 바꿔 더한다</b>", "<b>[8, 4, 256]</b>"],
    ["3장", "어텐션이 이 벡터들을 받아 서로 섞는다", ""],
], [22 * mm, 100 * mm, 44 * mm]))

# ================================================================== 2.7
S.append(Spacer(1, 10))
S.append(P("1부 — 2.7 토큰 임베딩", part_s))

S.append(P("1-1. 왜 필요한가: 토큰 ID는 이름표일 뿐이다", h1))
S.append(P(
    "세션 03에서 확인한 사실이 출발점이다. 어휘 ID는 sorted()가 정한 우연한 순서라서 "
    "&ldquo;115번이 114번과 가깝다&rdquo;는 말에 아무 의미가 없다. 그런데 정수를 그대로 신경망에 넣으면 "
    "신경망은 115를 114보다 &lsquo;큰 수&rsquo;로 취급한다. <b>ID는 주소일 뿐이고, 의미를 담을 그릇이 따로 "
    "필요하다.</b> 그 그릇이 임베딩 벡터다."))

S.append(P("1-2. nn.Embedding은 표(table)다", h1))
S.append(P("책의 장난감 예제는 어휘 6개, 벡터 길이 3이다."))
S.append(code(
    "vocab_size = 6\n"
    "output_dim = 3\n"
    "torch.manual_seed(123)\n"
    "embedding_layer = torch.nn.Embedding(vocab_size, output_dim)"))
S.append(P(
    "이 코드가 만드는 것은 <b>6행 3열짜리 숫자 표 하나</b>(embedding_layer.weight)가 전부다. "
    "행 하나가 토큰 하나에 대응한다. 토큰 ID 3의 벡터가 필요하면 표의 3번 행을 꺼내 온다. "
    "계산이 아니라 <b>조회(lookup)</b>다."))
S.append(KeepTogether([lookup_diagram(), P("ID 3을 넣으면 3번 행(0부터 세므로 네 번째 줄)이 그대로 나온다 — 책 출력과 일치", cap)]))
S.append(P(
    "여러 ID를 한꺼번에 넣어도 원리는 같다. embedding_layer(torch.tensor([2, 3, 5, 1]))은 "
    "2번, 3번, 5번, 1번 행을 <b>넣은 순서대로</b> 꺼내 쌓는다."))
S.append(table([
    ["입력 순서", "토큰 ID", "꺼내 오는 행", "결과 벡터"],
    ["0", "2", "2번 행", vec(W[2])],
    ["1", "3", "3번 행", vec(W[3])],
    ["2", "5", "5번 행", vec(W[5])],
    ["3", "1", "1번 행", vec(W[1])],
], [24 * mm, 22 * mm, 30 * mm, 90 * mm]))
S.append(P(
    "입력이 ID 4개([4])였는데 결과는 [4, 3]이다. <b>규칙: 임베딩을 거치면 맨 뒤에 output_dim 차원이 "
    "하나 붙는다.</b> 이 규칙 하나로 2.8절의 모든 shape이 설명된다."))

S.append(P("1-3. 조회와 행렬 곱은 같은 일이다", h1))
S.append(P(
    "책은 &ldquo;임베딩 레이어는 원-핫 인코딩 뒤에 행렬 곱을 하는 것을 더 효율적으로 구현한 것&rdquo;이라고 "
    "짧게 언급한다. 실제로 확인해 보면 이렇다."))
S.append(code(
    "one-hot for ID 3   = [0, 0, 0, 1, 0, 0]\n"
    "one-hot  @  weight = [-0.4015, 0.9666, -1.1481]\n"
    "weight[3]          = [-0.4015, 0.9666, -1.1481]      torch.allclose -> True"))
S.append(P(
    "원-핫 벡터는 3번 자리만 1이고 나머지가 0이다. 그래서 표와 곱하면 3번 행만 살아남는다. "
    "조회는 이 곱셈의 지름길일 뿐이다. 50,257개 중 하나만 1인 벡터를 매번 만드는 대신 행 번호로 바로 찾아간다."))
S.append(P(
    "이게 왜 중요한가: <b>행렬 곱이라는 것은 이 표가 평범한 신경망 층이라는 뜻이고, 따라서 역전파로 "
    "학습된다는 뜻이다.</b> 노트북 출력에 이미 그 표시가 찍혀 있다. 표를 출력하면 "
    "requires_grad=True, 조회 결과를 출력하면 grad_fn=&lt;EmbeddingBackward0&gt;가 붙는다. "
    "둘 다 &ldquo;이 숫자는 학습 중에 바뀐다&rdquo;는 표시다.", note))

S.append(KeepTogether([
    P("1-4. 두 숫자와 시드", h1),
    table([
        ["", "정하는 쪽", "표에서의 의미"],
        ["vocab_size", "토크나이저 (gpt2는 50,257로 고정)", "행 개수 — 표에 들어갈 토큰 수"],
        ["output_dim", "모델 설계자 (하이퍼파라미터)", "열 개수 — 토큰 하나를 몇 개의 숫자로 표현할지"],
        ["manual_seed(123)", "실험하는 사람", "표를 처음 채우는 무작위 값을 고정 — 책 숫자와 대조하려고"],
    ], [38 * mm, 54 * mm, 74 * mm]),
    Spacer(1, 4),
    P("(세 항목의 자세한 설명은 9월 6일 자료 LLM_Embedding_OutputDim_and_Seed_Explained.pdf에 있다.)",
      cap),
]))

S.append(P("1-5. 실전 규모로 키우면", h1))
S.append(P(
    f"gpt2 어휘 전체에 256차원을 쓰면 표는 50,257행 × 256열, <b>숫자 {50257 * 256:,}개</b>다. "
    f"실제 GPT-2(small)는 768차원이라 이 표 하나에만 {50257 * 768:,}개가 들어간다. "
    "모델 전체 파라미터의 상당 부분이 이 &lsquo;단어장&rsquo;에 있다."))
S.append(P(
    "2.6절에서 만든 배치 inputs는 [8, 4] — 문장 8개, 문장당 토큰 4개다. 1-2의 규칙대로 맨 뒤에 256이 "
    "붙어 token_embeddings는 <b>[8, 4, 256]</b>이 된다. 노트북 셀 21에서 이미 확인한 값이다."))

# ================================================================== 2.8
S.append(Spacer(1, 8))
S.append(P("2부 — 2.8 위치 임베딩", part_s))

S.append(P("2-1. 문제: 같은 토큰은 어디 있든 같은 벡터다", h1))
S.append(P(
    "조회는 행 번호만 본다. 문장의 몇 번째 자리에서 왔는지는 전혀 모른다. 이게 실제 데이터에서 어떻게 "
    "드러나는지 확인해 보면, 지금 쓰는 첫 배치 안에 <b>토큰 257(&ldquo; a&rdquo;)이 두 번</b> 나온다."))
S.append(code(
    "inputs =\n"
    "[[   40,   367,  2885,  1464],\n"
    " [ 1807,  3619,   402,   271],\n"
    " [10899,  2138,  [257], 7026],     row 2, position 2\n"
    " [15632,   438,  2016,  [257]],    row 3, position 3\n"
    " ...\n\n"
    "torch.equal(token_embeddings[2, 2], token_embeddings[3, 3])  ->  True"))
S.append(P(
    "한 번은 세 번째 자리, 한 번은 네 번째 자리인데 벡터가 소수점 끝까지 똑같다. 어텐션(3장)은 이 벡터만 "
    "받으므로 두 &ldquo; a&rdquo;를 구별할 방법이 없다. 9월 11일 QKV 자료 §7에서 &lsquo;The&rsquo;와 "
    "&lsquo;the&rsquo;가 똑같은 점수 0.11을 받았던 것과 같은 현상이다. <b>어순이 뜻을 바꾸는 언어에서 이건 "
    "치명적이다</b> — &ldquo;개가 사람을 문다&rdquo;와 &ldquo;사람이 개를 문다&rdquo;가 같은 재료가 된다."))

S.append(P("2-2. 해법: 자리 번호도 &lsquo;토큰&rsquo;처럼 표에서 찾는다", h1))
S.append(P(
    "2.8절의 핵심 아이디어는 놀랄 만큼 단순하다. <b>자리 번호 0, 1, 2, 3을 일종의 ID로 보고, "
    "nn.Embedding으로 표를 하나 더 만든다.</b>"))
S.append(code(
    "context_length = max_length                                   # 4\n"
    "pos_embedding_layer = torch.nn.Embedding(context_length, output_dim)   # 4 x 256"))
S.append(KeepTogether([
    P("클래스도 같고 원리도 같다. 달라지는 건 <b>첫 번째 인자가 무엇을 세느냐</b>뿐이다."),
    table([
        ["", "token_embedding_layer (2.7)", "pos_embedding_layer (2.8)"],
        ["표 크기", "50,257 × 256", "4 × 256"],
        ["행 하나의 뜻", "어휘 속 토큰 하나", "문장 속 자리 하나"],
        ["조회에 쓰는 번호", "토큰 ID — inputs", "자리 번호 — torch.arange(4)"],
        ["결과 shape", "[8, 4, 256]", "[4, 256]"],
        ["답하는 질문", "&ldquo;무슨 토큰인가?&rdquo;", "&ldquo;몇 번째 자리인가?&rdquo;"],
    ], [30 * mm, 68 * mm, 68 * mm]),
]))

S.append(P("2-3. torch.arange(max_length)는 자리 번호 목록이다", h1))
S.append(code(
    "torch.arange(4)                          ->  tensor([0, 1, 2, 3])\n"
    "pos_embedding_layer(torch.arange(4))     ->  shape [4, 256]"))
S.append(P(
    "arange(4)는 0부터 3까지의 정수 목록이다. 이걸 표에 넣으면 0번~3번 행이 꺼내져 [4, 256]이 된다. "
    "1-2의 규칙 그대로 — 입력 [4] 뒤에 256이 붙었다."))
S.append(P(
    "여기서 흔히 생기는 의문: <b>토큰 쪽은 [8, 4, 256]인데 왜 위치 쪽은 [4, 256]이고 8이 없는가?</b> "
    "자리 번호는 문장과 무관하기 때문이다. 8개 문장 모두 &ldquo;0번 자리, 1번 자리, 2번 자리, 3번 자리&rdquo;로 "
    "똑같다. 문장마다 따로 만들 이유가 없으니 한 벌만 만든다.", note))

S.append(P("2-4. 더하기 — 그리고 브로드캐스팅", h1))
S.append(code("input_embeddings = token_embeddings + pos_embeddings\n"
              "#                  [8, 4, 256]     +  [4, 256]   ->  [8, 4, 256]"))
S.append(P(
    "모양이 다른 두 텐서를 더했는데 에러가 나지 않는다. PyTorch가 <b>[4, 256]짜리 한 벌을 8개 문장 "
    "각각에 복사해서 더해 준다.</b> 이걸 브로드캐스팅이라 부른다. 규칙은 뒤쪽 차원부터 맞춰 보고, "
    "앞쪽에 없는 차원은 늘려서 채운다는 것이다. [4, 256]의 앞에 8이 없으니 8번 반복해 [8, 4, 256]처럼 쓴다."))
S.append(KeepTogether([shape_flow_diagram(), P("2.8절 코드 전체의 shape 흐름", cap)]))
S.append(KeepTogether([
    P("숫자로 보면 더 분명하다. 아래는 문장 2개 × 토큰 3개 × 벡터 길이 2로 줄인 예시다. "
      "위치 벡터는 모든 문장에 같은 것이 쓰인다."),
    table(toy_rows, [20 * mm, 14 * mm, 16 * mm, 32 * mm, 38 * mm, 46 * mm], highlight_rows=hl),
]))
S.append(Spacer(1, 6))
S.append(P(
    "강조한 두 줄을 보자. 토큰 &lsquo;a&rsquo;의 토큰 벡터는 둘 다 [1, 0]으로 같지만, 0번 자리와 1번 자리에 "
    "있으므로 결과는 [1.5, -0.5]와 [0.5, 0.5]로 <b>갈라진다.</b> 반대로 &lsquo;sat&rsquo;은 두 문장 모두 "
    "2번 자리라서 결과가 [2, 3]으로 같다. <b>같은 토큰 + 같은 자리 = 같은 벡터, 같은 토큰 + 다른 자리 = "
    "다른 벡터.</b> 이것이 2.8절이 원하는 성질이다."))
S.append(P(
    "주의: 위치 벡터 값에 &lsquo;0.1, 0.2, 0.3처럼 커지는&rsquo; 규칙은 없다. 토큰 표와 똑같이 무작위로 "
    "시작해서 학습으로 정해진다. 위 예시의 값도 일부러 규칙 없이 골랐다.", note))

S.append(P("2-5. 실제 데이터로 확인", h1))
S.append(code(
    "torch.equal(token_embeddings[2, 2], token_embeddings[3, 3])   ->  True   (before)\n"
    "torch.equal(input_embeddings[2, 2], input_embeddings[3, 3])   ->  False  (after)"))
S.append(P(
    "2-1의 두 &ldquo; a&rdquo;가 위치 임베딩을 더한 뒤 서로 다른 벡터가 됐다. 문제가 해결됐다는 직접 증거다."))

S.append(P("2-6. 왜 이어 붙이지 않고 더하는가", h1))
S.append(P(
    "토큰 벡터(256)와 위치 벡터(256)를 옆으로 이어 붙이면 512차원이 되고, 이후 모든 층이 그만큼 커진다. "
    "더하면 256차원 그대로다. 더하면 두 정보가 섞여 버릴 것 같지만, <b>두 표 모두 학습되기 때문에</b> 모델이 "
    "서로 방해하지 않도록 값을 조정해 나간다. GPT-2가 실제로 이 방식을 쓰고, 잘 작동한다는 것이 경험으로 "
    "확인된 선택이다."))

S.append(P("2-7. &lsquo;절대&rsquo; 위치 임베딩의 한계 — 그리고 익숙한 에러", h1))
S.append(P(
    "이 방식에서 위치 표의 행은 context_length개뿐이다. 그보다 긴 입력이 오면 꺼낼 행이 없다. "
    "실제로 4행짜리 표에 자리 번호 5개를 넣어 보면:"))
S.append(code("pos_embedding_layer(torch.arange(5))   ->  IndexError: index out of range in self"))
S.append(P(
    "<b>세션 04에서 본 바로 그 에러 메시지다.</b> 그때는 행이 6개뿐인 장난감 표(embedding_layer)에 "
    "2885 같은 실제 GPT-2 ID를 넣었다. 지금은 행이 4개뿐인 위치 표에 4번 자리를 요구했다. 원인이 같다 — "
    "<b>표에 없는 행 번호를 달라고 한 것.</b> 이 에러를 보면 &ldquo;어느 표의 행 개수를 넘었나&rdquo;부터 "
    "의심하면 된다."))
S.append(P(
    "그래서 GPT-2는 context_length를 1,024로 잡는다. 1,025번째 토큰부터는 원리상 처리할 수 없다. "
    "&lsquo;몇 번째 자리&rsquo; 대신 &lsquo;몇 칸 떨어졌나&rsquo;를 쓰는 상대 위치 방식(Llama의 RoPE 등)은 "
    "이 제약을 완화하려는 설계지만, 책은 GPT-2를 따라 절대 방식을 쓴다."))

# ================================================================== 입력 전 체크
S.append(Spacer(1, 8))
S.append(P("3부 — 2.8절을 입력하기 전에", part_s))

S.append(P("3-1. 값이 아니라 shape을 대조한다", h1))
S.append(P(
    "2.8절의 두 레이어에는 <b>torch.manual_seed가 없다.</b> 그래서 실행할 때마다 표의 값이 달라지고, "
    "책의 숫자와 일치할 수가 없다. 이 절에서 대조할 기준은 값이 아니라 shape이다. "
    "&ldquo;실행 전 예측&rdquo; 습관대로 먼저 적어 두고 실행하길 권한다."))
S.append(table([
    ["코드", "예측할 shape", "책 출력"],
    ["inputs.shape", "", "[8, 4]"],
    ["token_embeddings.shape", "", "[8, 4, 256]"],
    ["torch.arange(max_length)", "", "tensor([0, 1, 2, 3])"],
    ["pos_embeddings.shape", "", "[4, 256]"],
    ["input_embeddings.shape", "", "[8, 4, 256]"],
], [62 * mm, 44 * mm, 60 * mm]))

S.append(P("3-2. 이름 함정 — 지금 노트북에 이미 있다", h1))
S.append(P(
    "현재 bpe.ipynb는 레이어를 <b>token_embedding</b>, 결과 텐서를 <b>token_embeddings</b>로 저장했다. "
    "<b>s 한 글자 차이</b>로 레이어와 텐서가 갈린다. 책은 레이어를 token_embedding_layer로 부른다."))
S.append(table([
    ["역할", "책의 이름", "지금 노트북"],
    ["토큰 레이어", "token_embedding_layer", "token_embedding"],
    ["토큰 결과 텐서", "token_embeddings", "token_embeddings"],
    ["위치 레이어", "pos_embedding_layer", "(아직 없음)"],
    ["위치 결과 텐서", "pos_embeddings", "(아직 없음)"],
    ["합산 결과", "input_embeddings", "(아직 없음)"],
], [36 * mm, 64 * mm, 66 * mm], highlight_rows=(1, 2)))
S.append(Spacer(1, 6))
S.append(P(
    "2.8절을 치면 비슷한 이름이 다섯 개로 늘어난다. 세션 03·04의 버그 대부분이 &lsquo;문법은 맞는데 이름이 "
    "어긋난&rsquo; 유형이었다는 기록에 비추면, 여기가 다음 버그가 날 가능성이 가장 높은 자리다. "
    "<b>레이어에는 _layer를 붙이는 책의 규칙으로 통일해 두면</b> 레이어(표)와 텐서(조회 결과)가 이름만으로 "
    "구별된다.", note))

S.append(P("3-3. 에러가 나면 먼저 볼 곳", h1))
S.append(table([
    ["증상", "가장 먼저 의심할 것"],
    ["IndexError: index out of range in self", "표의 행 개수보다 큰 번호를 조회했다 — 어느 표에 무엇을 넣었나"],
    ["NameError", "레이어 이름과 텐서 이름을 바꿔 썼다 — 3-2의 표"],
    ["shape이 [8, 4, 256]이 아니다", "pos_embeddings를 arange 없이 만들었거나, 다른 max_length를 썼다"],
    ["책과 값이 다르다", "정상이다 — 2.8에는 시드가 없다 (3-1)"],
], [60 * mm, 106 * mm]))

S.append(Spacer(1, 12))
S.append(KeepTogether([
    HRFlowable(width="55%", thickness=0.75, color=LINE, hAlign="CENTER", spaceAfter=10),
    P("토큰 임베딩은 &ldquo;무슨 토큰인가&rdquo;를 한 표에서 찾고, 위치 임베딩은 &ldquo;몇 번째 자리인가&rdquo;를 "
      "또 다른 표에서 찾는다. 둘을 더한 것이 LLM의 입력이다.", take_s),
    Spacer(1, 6),
    P("이 자료의 모든 숫자는 프로젝트 가상환경(torch 2.13.0)에서 직접 실행해 확인했고, "
      "책 노트북(ch02.ipynb)의 출력과 대조했다.", cap),
]))

doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=22 * mm, rightMargin=22 * mm,
                        topMargin=20 * mm, bottomMargin=18 * mm,
                        title="토큰 임베딩과 위치 임베딩 (2.7 · 2.8)")
doc.build(S)
print("wrote", OUT)
