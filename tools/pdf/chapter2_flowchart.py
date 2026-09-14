# /// script
# dependencies = ["reportlab"]
# ///
"""Chapter 2 pipeline flowchart -> docs/Chapter2_Pipeline_Flowchart.pdf

Run from anywhere:  uv run tools/pdf/chapter2_flowchart.py
"""
import math
from pathlib import Path

from reportlab.graphics.shapes import (
    Circle,
    Drawing,
    Line,
    Polygon,
    Rect,
    String,
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# macOS system font; needed because the built-in PDF fonts have no Hangul glyphs.
KOREAN_FONT = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
FONT = "KR"
pdfmetrics.registerFont(TTFont(FONT, KOREAN_FONT))

REPO = Path(__file__).resolve().parents[2]
OUT = str(REPO / "docs" / "Chapter2_Pipeline_Flowchart.pdf")

INK = colors.HexColor("#1a1a1a")
GREY = colors.HexColor("#5e5e5e")
LIGHT = colors.HexColor("#8a8a8a")
LINE = colors.HexColor("#c8c8c8")
ACCENT = colors.HexColor("#2f4f76")
F_TEXT = colors.HexColor("#eef2f8")
F_DATA = colors.HexColor("#f1eef8")
F_TOK = colors.HexColor("#e3eaf5")
F_POS = colors.HexColor("#f6eedd")
F_SUM = colors.HexColor("#e5f2e6")

CONTENT_W = 174 * mm

# ------------------------------------------------------------------ text helpers

def wrap(text, font, size, maxw):
    lines, cur = [], ""
    for word in text.split(" "):
        trial = (cur + " " + word).strip()
        if pdfmetrics.stringWidth(trial, font, size) <= maxw:
            cur = trial
            continue
        if cur:
            lines.append(cur)
        while pdfmetrics.stringWidth(word, font, size) > maxw:
            k = len(word)
            while k > 1 and pdfmetrics.stringWidth(word[:k], font, size) > maxw:
                k -= 1
            lines.append(word[:k])
            word = word[k:]
        cur = word
    if cur:
        lines.append(cur)
    return lines


def arrow(d, x1, y1, x2, y2, color=INK, dashed=False, width=1.0):
    d.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=width,
               strokeDashArray=[3, 2] if dashed else None))
    ang = math.atan2(y2 - y1, x2 - x1)
    L = 5.5
    a1, a2 = ang + math.radians(152), ang - math.radians(152)
    d.add(Polygon([x2, y2, x2 + L * math.cos(a1), y2 + L * math.sin(a1),
                   x2 + L * math.cos(a2), y2 + L * math.sin(a2)],
                  fillColor=color, strokeColor=color, strokeWidth=0.5))


PAD_T, PAD_B, PAD_X = 8, 7, 9
TITLE_SIZE, EX_SIZE, DESC_SIZE, DESC_LEAD = 10.5, 7.3, 8.3, 11.4
PARA_GAP = 3


def desc_blocks(spec, w):
    paras = spec["desc"] if isinstance(spec["desc"], list) else [spec["desc"]]
    return [wrap(p, FONT, DESC_SIZE, w - 2 * PAD_X) for p in paras]


def box_height(spec, w):
    blocks = desc_blocks(spec, w)
    n = sum(len(b) for b in blocks)
    ex = 17 if spec.get("ex") else 0
    return PAD_T + TITLE_SIZE + 4 + ex + n * DESC_LEAD + (len(blocks) - 1) * PARA_GAP + PAD_B


def draw_box(d, x, top, w, h, spec, fill, dashed=False, text_color=INK):
    d.add(Rect(x, top - h, w, h, rx=5, ry=5, fillColor=fill,
               strokeColor=LIGHT if dashed else INK, strokeWidth=0.9,
               strokeDashArray=[3, 2] if dashed else None))
    y = top - PAD_T - TITLE_SIZE + 1
    tx = x + PAD_X
    if spec.get("sec"):
        d.add(String(tx, y, spec["sec"], fontName="Helvetica-Bold", fontSize=9, fillColor=ACCENT))
        tx += pdfmetrics.stringWidth(spec["sec"], "Helvetica-Bold", 9) + 6
    d.add(String(tx, y, spec["title"], fontName=FONT, fontSize=TITLE_SIZE, fillColor=text_color))
    if spec.get("badge"):
        bw = pdfmetrics.stringWidth(spec["badge"], FONT, 7.8) + 10
        bx = x + w - PAD_X - bw
        d.add(Rect(bx, y - 3.5, bw, 13, rx=6, ry=6, fillColor=colors.white,
                   strokeColor=ACCENT, strokeWidth=0.7))
        d.add(String(bx + bw / 2, y, spec["badge"], fontName=FONT, fontSize=7.8,
                     fillColor=ACCENT, textAnchor="middle"))
    y -= 4
    if spec.get("ex"):
        y -= 11
        d.add(String(x + PAD_X, y, spec["ex"], fontName="Courier", fontSize=EX_SIZE, fillColor=GREY))
        y -= 6
    for bi, block in enumerate(desc_blocks(spec, w)):
        if bi:
            y -= PARA_GAP
        for line in block:
            y -= DESC_LEAD
            d.add(String(x + PAD_X, y + 2, line, fontName=FONT, fontSize=DESC_SIZE, fillColor=text_color))


def label(d, x, y, text, anchor="start", size=7.2, color=GREY):
    d.add(String(x, y, text, fontName=FONT, fontSize=size, fillColor=color, textAnchor=anchor))


# ------------------------------------------------------------------ content (numbers verified)

B1 = {
    "sec": "2.1",
    "title": "원본 텍스트",
    "badge": "20,479자",
    "ex": '"I HAD always thought Jack Gisburn rather a cheap genius--"',
    "desc": "모델이 읽을 재료인 the-verdict.txt. 이 단계에서는 아직 문자열일 뿐, "
            "신경망이 계산할 수 있는 숫자가 아니다.",
}
B2 = {
    "sec": "2.5",
    "title": "BPE 토큰화 → 토큰 ID",
    "badge": "ID 5,145개",
    "ex": '"I" " H" "AD" " always"  ->  [40, 367, 2885, 1464, ...]',
    "desc": "tiktoken(gpt2)이 텍스트를 어휘 50,257개짜리 조각으로 쪼개 정수 ID로 바꾼다. "
            "'HAD'가 ' H'와 'AD'로 나뉘듯, 모르는 단어도 아는 조각으로 쪼개므로 <|unk|>가 필요 없다.",
}
B3 = {
    "sec": "2.6",
    "title": "슬라이딩 윈도우 → 배치",
    "badge": "[8, 4]",
    "ex": "input [40, 367, 2885, 1464] -> target [367, 2885, 1464, 1807]",
    "desc": "ID 나열을 길이 4(max_length)로 자르고, 타깃은 입력을 한 칸 민 것으로 만든다 — "
            "‘다음 토큰 맞히기’ 문제가 된다. DataLoader가 8개씩 묶어 inputs와 targets를 내준다.",
}
B4 = {
    "sec": "2.7",
    "title": "토큰 임베딩",
    "badge": "[8, 4, 256]",
    "ex": "nn.Embedding(50257, 256)(inputs)",
    "desc": "50,257×256 표에서 ID마다 행 하나를 꺼낸다(조회). 의미 없는 정수가 학습 가능한 "
            "256차원 벡터가 된다. 단, 같은 토큰은 자리와 무관하게 같은 벡터다.",
}
S4 = {
    "sec": "2.8",
    "title": "위치 임베딩",
    "badge": "[4, 256]",
    "ex": "Embedding(4, 256)(arange(4))",
    "desc": "자리 번호 0~3을 4×256 표에서 꺼낸다. 토큰 임베딩이 ‘자리를 모른다’는 한계를 메우는 재료다.",
}
B5 = {
    "sec": "",
    "title": "입력 임베딩 (두 벡터의 합)",
    "badge": "[8, 4, 256]",
    "ex": "token_embeddings + pos_embeddings",
    "desc": "[4, 256]이 8개 문장 모두에 브로드캐스팅되어 더해진다. 같은 토큰도 자리가 다르면 "
            "다른 벡터가 된다 — 이것이 LLM이 실제로 받는 입력이다.",
}
LEARN = {
    "sec": "",
    "title": "학습 경로 · 2.2~2.4",
    "badge": "",
    "ex": "['I', 'HAD', 'always', ...]",
    "desc": [
        "정규식 토크나이저 — 원리를 배우는 우회로",
        "2.2  정규식으로 쪼개기 → 4,690 토큰",
        "2.3  등장한 단어로 어휘 → 1,130개",
        "2.4  <|unk|>, <|endoftext|> 추가 → 1,132개",
        "한계: 어휘 밖 단어는 전부 <|unk|> 하나로 뭉개진다. 그래서 2.5 BPE로.",
    ],
}

# ------------------------------------------------------------------ layout

MAIN_X, MAIN_W = 0, 300
SIDE_X, SIDE_W = 324, CONTENT_W - 324
GAP = 30
GAP_SUM = 52
TERM_H = 26

h1 = box_height(B1, MAIN_W)
h2 = box_height(B2, MAIN_W)
hL = box_height(LEARN, SIDE_W)
if h1 + GAP + h2 < hL:
    h2 = hL - h1 - GAP
hL = h1 + GAP + h2
h3 = box_height(B3, MAIN_W)
h4 = max(box_height(B4, MAIN_W), box_height(S4, SIDE_W))
h5 = box_height(B5, MAIN_W)

H = 6 + h1 + GAP + h2 + GAP + h3 + GAP + h4 + GAP_SUM + h5 + GAP + TERM_H + 4
d = Drawing(CONTENT_W, H)

top1 = H - 6
top2 = top1 - h1 - GAP
top3 = top2 - h2 - GAP
top4 = top3 - h3 - GAP
top5 = top4 - h4 - GAP_SUM
top6 = top5 - h5 - GAP
xc = MAIN_X + MAIN_W / 2
xs = SIDE_X + SIDE_W / 2

draw_box(d, MAIN_X, top1, MAIN_W, h1, B1, F_TEXT)
draw_box(d, MAIN_X, top2, MAIN_W, h2, B2, F_TEXT)
draw_box(d, SIDE_X, top1, SIDE_W, hL, LEARN, colors.white, dashed=True, text_color=GREY)
draw_box(d, MAIN_X, top3, MAIN_W, h3, B3, F_DATA)
draw_box(d, MAIN_X, top4, MAIN_W, h4, B4, F_TOK)
draw_box(d, SIDE_X, top4, SIDE_W, h4, S4, F_POS)
draw_box(d, MAIN_X, top5, MAIN_W, h5, B5, F_SUM)

# terminal
tw = 150
d.add(Rect(xc - tw / 2, top6 - TERM_H, tw, TERM_H, rx=13, ry=13, fillColor=colors.white,
           strokeColor=ACCENT, strokeWidth=1.1))
label(d, xc, top6 - TERM_H + 9, "3장 — 어텐션으로", anchor="middle", size=9, color=ACCENT)

# main vertical arrows + data labels
def v_arrow(y_from, y_to, text):
    arrow(d, xc, y_from - 1, xc, y_to + 1)
    label(d, xc + 7, (y_from + y_to) / 2 - 3, text)

v_arrow(top1 - h1, top2, "문자열")
v_arrow(top2 - h2, top3, "토큰 ID 5,145개")
v_arrow(top3 - h3, top4, "inputs [8, 4]")

# learning-path detour (dashed)
y_r1 = top1 - h1 / 2
arrow(d, MAIN_X + MAIN_W + 1, y_r1, SIDE_X - 1, y_r1, color=LIGHT, dashed=True)
y_r2 = top2 - h2 / 2
arrow(d, SIDE_X - 1, y_r2, MAIN_X + MAIN_W + 1, y_r2, color=LIGHT, dashed=True)

# max_length feeds the position table
y_el = top3 - h3 + 14
d.add(Line(MAIN_X + MAIN_W, y_el, xs, y_el, strokeColor=ACCENT, strokeWidth=0.9, strokeDashArray=[3, 2]))
arrow(d, xs, y_el, xs, top4 + 1, color=ACCENT, dashed=True)
label(d, MAIN_X + MAIN_W + 6, y_el + 4, "max_length = 4", size=7, color=ACCENT)
label(d, xs + 5, (y_el + top4) / 2 - 3, "자리 번호 0, 1, 2, 3", size=7, color=ACCENT)

# merge at "+"
cy = top5 + GAP_SUM / 2
r = 9
arrow(d, xc, top4 - h4 - 1, xc, cy + r + 1)
label(d, xc + 7, (top4 - h4 + cy + r) / 2 - 3, "[8, 4, 256]")
d.add(Line(xs, top4 - h4, xs, cy, strokeColor=INK, strokeWidth=1))
arrow(d, xs, cy, xc + r + 1, cy)
label(d, xs + 5, (top4 - h4 + cy) / 2 - 3, "[4, 256]")
d.add(Circle(xc, cy, r, fillColor=colors.white, strokeColor=INK, strokeWidth=1.1))
d.add(String(xc, cy - 4.5, "+", fontName="Helvetica-Bold", fontSize=13, fillColor=INK, textAnchor="middle"))
arrow(d, xc, cy - r - 1, xc, top5 + 1)

v_arrow(top5 - h5, top6, "[8, 4, 256]")

# ------------------------------------------------------------------ page

title_s = ParagraphStyle("T", fontName=FONT, fontSize=17, leading=22, textColor=INK)
sub_s = ParagraphStyle("S", fontName=FONT, fontSize=9.2, leading=13, textColor=GREY, spaceAfter=2)
cap_s = ParagraphStyle("C", fontName=FONT, fontSize=8.3, leading=12, textColor=GREY, alignment=TA_CENTER)
cell_s = ParagraphStyle("CL", fontName=FONT, fontSize=8.2, leading=11, alignment=TA_CENTER)

story = [
    Paragraph("Chapter 2 흐름도 — 원본 텍스트에서 입력 임베딩까지", title_s),
    Paragraph("Raschka, <i>Build a Large Language Model (From Scratch)</i> 2장 정리 · "
              "실선은 실제 GPT-2 파이프라인, 점선은 원리를 배우는 경로와 보조 연결", sub_s),
    HRFlowable(width="100%", thickness=0.7, color=LINE, spaceBefore=6, spaceAfter=10),
    d,
    Spacer(1, 10),
]

strip = Table(
    [[Paragraph(t, cell_s) for t in
      ["문자열<br/>20,479자", "→", "토큰 ID<br/>5,145개", "→", "배치<br/>[8, 4]", "→",
       "토큰 벡터<br/>[8, 4, 256]", "+", "위치 벡터<br/>[4, 256]", "→", "입력 임베딩<br/>[8, 4, 256]"]]],
    colWidths=[26 * mm, 5 * mm, 24 * mm, 5 * mm, 20 * mm, 5 * mm, 24 * mm, 5 * mm, 22 * mm, 5 * mm, 28 * mm],
)
strip.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("BOX", (0, 0), (-1, -1), 0.6, LINE),
    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f7f7f7")),
    ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ("LEFTPADDING", (0, 0), (-1, -1), 2), ("RIGHTPADDING", (0, 0), (-1, -1), 2),
]))
story.append(strip)
story.append(Spacer(1, 6))
story.append(Paragraph(
    "모든 숫자는 프로젝트 가상환경에서 data/the-verdict.txt로 직접 실행해 확인한 값이다 "
    "(batch_size=8, max_length=4, stride=4, output_dim=256).", cap_s))

doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                        topMargin=15 * mm, bottomMargin=12 * mm, title="Chapter 2 흐름도")
doc.build(story)
print("wrote", OUT, "drawing height", round(H))
