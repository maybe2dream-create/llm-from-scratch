# /// script
# dependencies = ["reportlab"]
# ///
"""Line-by-line walkthrough of experiments/ch02/embedding_exec/embed_exec.py -> docs/Embed_Exec_Line_by_Line.pdf

Run from anywhere:  uv run tools/pdf/embed_exec_walkthrough.py
Numbers in this file were checked by running embed_exec.py on 2026-09-14.
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
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# macOS system font; the built-in PDF fonts have no Hangul glyphs.
# AppleGothic has no bold weight, so emphasis is rendered with colour instead.
KOREAN_FONT = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
FONT = "KR"
pdfmetrics.registerFont(TTFont(FONT, KOREAN_FONT))

REPO = Path(__file__).resolve().parents[2]
OUT = str(REPO / "docs" / "Embed_Exec_Line_by_Line.pdf")
SOURCE = (REPO / "experiments" / "ch02" / "embedding_exec" / "embed_exec.py").read_text(
    encoding="utf-8"
).splitlines()

INK = colors.HexColor("#1a1a1a")
GREY = colors.HexColor("#5a5a5a")
LINE = colors.HexColor("#cfcfcf")
CODE_BG = colors.HexColor("#f3f4f6")
HEAD = colors.HexColor("#ececec")
ACCENT = "#2f4f76"
BUG_BG, BUG_BAR = colors.HexColor("#fdf3e6"), colors.HexColor("#d08a2e")
RULE_BG, RULE_BAR = colors.HexColor("#eaf0f8"), colors.HexColor(ACCENT)
FIND_BG, FIND_BAR = colors.HexColor("#ebf5ec"), colors.HexColor("#4f8a55")

CONTENT_W = 170 * mm

title_s = ParagraphStyle("T", fontName=FONT, fontSize=20, leading=26, textColor=INK)
sub_s = ParagraphStyle("S", fontName=FONT, fontSize=10, leading=14.5, textColor=GREY, spaceAfter=10)
part_s = ParagraphStyle("PART", fontName=FONT, fontSize=15.5, leading=21, textColor=INK,
                        spaceBefore=16, spaceAfter=4)
part_sub = ParagraphStyle("PSUB", fontName=FONT, fontSize=9.4, leading=13, textColor=GREY,
                          spaceAfter=10)
h2 = ParagraphStyle("H2", fontName=FONT, fontSize=12, leading=16, spaceBefore=12, spaceAfter=6,
                    textColor=colors.HexColor(ACCENT), keepWithNext=1)
body = ParagraphStyle("B", fontName=FONT, fontSize=10, leading=16, spaceAfter=6)
small = ParagraphStyle("SM", parent=body, fontSize=9.2, leading=14, spaceAfter=4)
cap = ParagraphStyle("C", fontName=FONT, fontSize=8.6, leading=12, alignment=TA_CENTER,
                     textColor=GREY, spaceBefore=4, spaceAfter=8)
box_title = ParagraphStyle("BT", fontName=FONT, fontSize=9.6, leading=13, spaceAfter=3)
box_body = ParagraphStyle("BB", fontName=FONT, fontSize=9.3, leading=14.2, spaceAfter=3)
code_s = ParagraphStyle("CODE", fontName="Courier", fontSize=8.4, leading=11.6)
strip_s = ParagraphStyle("STRIP", fontName="Courier", fontSize=8.8, leading=12)
cell_s = ParagraphStyle("CELL", fontName=FONT, fontSize=8.9, leading=12.4)
cell_code = ParagraphStyle("CELLC", fontName="Courier", fontSize=8.4, leading=11.6)
take_s = ParagraphStyle("TK", fontName=FONT, fontSize=12, leading=18, alignment=TA_CENTER,
                        textColor=INK, spaceBefore=6, spaceAfter=6)


R_MODE = '"r"'
ENC_ARG = 'encoding="utf-8"'
ERR_CALLABLE = "TypeError: 'Tensor' object is not callable"
ERR_NAME = "NameError: name 'input_ids' is not defined"


def accent(t):
    # AppleGothic has no glyph for U+2212 or é; swap in ASCII minus / a Helvetica é.
    t = t.replace("\u2212", "-").replace("é", '<font face="Helvetica">é</font>')
    return t.replace("<b>", f'<font color="{ACCENT}">').replace("</b>", "</font>")


def P(t, s=body):
    return Paragraph(accent(t), s)


def C(t):
    """Inline code inside Korean text. ASCII only — Courier has no Hangul."""
    return f'<font face="Courier" size="8.6">{escape(t)}</font>'


def table(rows, widths, header=True, code_cols=()):
    data = []
    for r, row in enumerate(rows):
        out = []
        for c, cell in enumerate(row):
            if not isinstance(cell, str):
                out.append(cell)
            elif c in code_cols and not (header and r == 0):
                out.append(Paragraph(escape(cell), cell_code))
            else:
                out.append(P(cell, cell_s))
        data.append(out)
    t = Table(data, colWidths=widths)
    st = [
        ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if header:
        st.append(("BACKGROUND", (0, 0), (-1, 0), HEAD))
    t.setStyle(TableStyle(st))
    return KeepTogether([t, Spacer(1, 6)])


def codebox(text):
    t = Table([[Preformatted(text, code_s)]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CODE_BG), ("BOX", (0, 0), (-1, -1), 0.5, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return KeepTogether([t, Spacer(1, 6)])


def wrap_code(code, limit=86):
    out, indent = [], " " * (len(code) - len(code.lstrip()) + 4)
    while len(code) > limit:
        cut = code.rfind(", ", 0, limit)
        if cut == -1:
            break
        out.append(code[:cut + 1])
        code = indent + code[cut + 2:]
    return out + [code]


def source_block(first, last):
    width = len(str(last))
    lines = []
    for n in range(first, last + 1):
        for k, piece in enumerate(wrap_code(SOURCE[n - 1])):
            lines.append(f"{(str(n) if k == 0 else ''):>{width}} | {piece}")
    return codebox("\n".join(lines))


def line(nums, paras, extras=()):
    """One code line (or a small run of lines) followed by its explanation."""
    if isinstance(nums, int):
        nums = (nums, nums)
    first, last = nums
    rows = []
    for n in range(first, last + 1):
        code = SOURCE[n - 1].rstrip()
        if not code.strip():
            continue
        rows.append(Paragraph(
            f'<font color="{ACCENT}">{n:>2}</font>&nbsp;&nbsp;{escape(code).replace("  ", "&nbsp;&nbsp;")}',
            strip_s))
    strip = Table([[r] for r in rows], colWidths=[CONTENT_W])
    strip.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CODE_BG),
        ("LINEBEFORE", (0, 0), (0, -1), 2.2, colors.HexColor(ACCENT)),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    head = [Spacer(1, 5), strip, Spacer(1, 4)]
    first_para = [P(paras[0])] if paras else []
    out = [KeepTogether(flatten(head + first_para))]
    out += [P(p) for p in paras[1:]]
    out += list(extras)
    return out


def callout(kind, title, paras):
    bg, bar, label = {
        "bug": (BUG_BG, BUG_BAR, "오늘 겪은 일"),
        "rule": (RULE_BG, RULE_BAR, "기억할 규칙"),
        "find": (FIND_BG, FIND_BAR, "오늘 발견한 것"),
    }[kind]
    inner = [P(f'<font color="{bar.hexval().replace("0x", "#")}">{label}</font> · {title}', box_title)]
    for p in paras:
        if isinstance(p, str):
            inner.append(P(p, box_body))
        elif isinstance(p, KeepTogether):
            # A KeepTogether inside a table cell has unbounded height and breaks layout.
            inner.extend(p._content)
        else:
            inner.append(p)
    t = Table([[inner]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LINEBEFORE", (0, 0), (0, -1), 3, bar),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return KeepTogether([Spacer(1, 4), t, Spacer(1, 8)])


def flatten(items):
    # Nested KeepTogether over-reports its height, which pushed every section to a new page.
    out = []
    for f in items:
        out.extend(flatten(f._content) if isinstance(f, KeepTogether) else [f])
    return out


def section(title, subtitle, *following):
    return KeepTogether([P(title, part_s), P(subtitle, part_sub),
                         HRFlowable(width="100%", thickness=0.6, color=LINE, spaceAfter=4),
                         *flatten(following)])


S = []

# ------------------------------------------------------------------ cover
S.append(P("embed_exec.py 한 줄씩 읽기", title_s))
S.append(P("Annabel Lee로 끝내는 Chapter 2 — 원본 텍스트에서 입력 임베딩까지 · 2026-09-14", sub_s))
S.append(HRFlowable(width="100%", thickness=0.8, color=LINE, spaceAfter=10))
S.append(P(
    "이 자료는 흐름도(Chapter2_Pipeline_Flowchart.pdf)를 <b>책에 없는 텍스트로 직접 통과시킨</b> "
    f"스크립트 {C('experiments/ch02/embedding_exec/embed_exec.py')}(46줄)를 한 줄씩 읽는다. 각 줄마다 무엇을 하는지, 그리고 "
    "오늘 그 줄에서 실제로 무슨 일이 있었는지를 함께 적었다. 모든 숫자는 스크립트를 실행해 확인한 값이다."))
S.append(table([
    ["항목", "내용"],
    ["입력 텍스트", "Edgar Allan Poe, <i>Annabel Lee</i> — experiments/ch02/embedding_exec/annabel_lee.txt (1,570자)"],
    ["실행 방법", f"저장소 루트에서 {C('python experiments/ch02/embedding_exec/embed_exec.py')}"],
    ["출력", C("torch.Size([8, 4, 128])")],
    ["상자 색의 뜻", "주황 = 오늘 겪은 버그·에러 · 파랑 = 기억할 규칙 · 초록 = 오늘 발견한 것"],
], [32 * mm, 138 * mm]))

S.append(section("0. 전체 지도", "46줄이 흐름도의 어느 단계에 해당하는가", table([
    ["줄", "하는 일", "흐름도"],
    ["1–3", "도구 가져오기", "—"],
    ["4–6", "토크나이저 준비, 텍스트 읽기", "2.1"],
    ["8–25", "GPTDatasetV1 — 토큰화하고 윈도우로 자르는 설계도", "2.5 · 2.6"],
    ["26–31", "create_dataloader_v1 — 데이터셋을 배치로 묶는 설계도", "2.6"],
    ["32–36", "설정값을 정하고 첫 배치 꺼내기", "2.6"],
    ["37–41", "토큰 임베딩", "2.7"],
    ["42–44", "위치 임베딩", "2.8"],
    ["45–46", "두 벡터를 더하고 결과 확인", "2.8"],
], [22 * mm, 118 * mm, 30 * mm])))

S.append(P("적힌 순서와 실행 순서는 다르다", h2))
S.append(P(
    "파이썬은 위에서 아래로 읽지만, 8~31번 줄은 <b>설계도를 적어두기만 하고 실행하지 않는다.</b> "
    "실제 일은 34번 줄에서 함수를 부를 때 시작되고, 그때 설계도 안으로 들어갔다가 돌아온다. "
    "이 순서를 알면 &ldquo;토큰화는 몇 번째 줄에서 일어나는가?&rdquo;에 답할 수 있다 — 적힌 곳은 13번 줄이지만 "
    "실행되는 순간은 34번 줄을 실행할 때다."))
S.append(table([
    ["순서", "줄", "일어나는 일"],
    ["1", "1–6", "도구를 가져오고 시를 문자열로 읽는다"],
    ["2", "8–31", "클래스와 함수를 <b>정의만</b> 한다 — 이 순간 아무것도 계산되지 않는다"],
    ["3", "32–33", "설정값 max_length, batch_size를 정한다"],
    ["4", "34 → 28–30", "함수가 실행되어 토크나이저·데이터셋·DataLoader를 만든다"],
    ["5", "29 → 9–19", "__init__이 실행된다 — 토큰화(13번 줄)와 윈도우 116개 생성이 여기서 일어난다"],
    ["6", "35", "배치를 꺼낼 준비만 한다"],
    ["7", "36 → 24–25 (8번)", "DataLoader가 __getitem__을 8번 불러 첫 배치를 만든다"],
    ["8", "37–46", "임베딩 두 개를 만들고 더한 뒤 shape를 출력한다"],
], [16 * mm, 34 * mm, 120 * mm]))

# ------------------------------------------------------------------ 1-3
S.append(section("1. 도구 가져오기 — 1~3번 줄", "코드 전체에서 쓸 라이브러리를 불러온다", source_block(1, 3)))
S += line(1, [
    "GPT-2가 쓰던 BPE 토크나이저를 제공하는 라이브러리를 불러온다. 2.5절의 도구다."])
S += line(2, [
    ("PyTorch를 불러온다. <b>텐서</b>(여러 차원으로 늘어놓은 숫자 덩어리)와 "
    f"{C('nn.Embedding')}이 여기에 들어 있다.")])
S += line(3, [
    (f"두 가지를 가져온다. {C('Dataset')}은 &ldquo;데이터 한 개를 어떻게 꺼내는가&rdquo;를 적는 틀이고, "
    f"{C('DataLoader')}는 그 데이터를 몇 개씩 묶을지, 섞을지 말지를 정해 차례로 내주는 역할이다."),
    "비유하면 Dataset은 창고의 물건 목록이고, DataLoader는 물건을 상자에 8개씩 담아 내보내는 컨베이어다."],
    [callout("rule", "import는 파일 맨 위에 모은다", [
        ("오늘 중간에 있던 import를 맨 위로 옮기셨다. 파이썬의 관례이고, 이 파일이 무엇에 의존하는지 "
        "첫 세 줄만 보면 알 수 있게 된다.")])])

# ------------------------------------------------------------------ 4-6
S.append(section("2. 텍스트 읽기 — 4~6번 줄", "흐름도 2.1 · 아직 숫자가 아니라 글자다", source_block(4, 6)))
S += line(4, [
    ("GPT-2와 똑같은 규칙의 토크나이저를 만든다. 이 토크나이저가 아는 토큰 종류는 <b>50,257개</b>이고, "
    "이 숫자가 37번 줄의 vocab_size가 된다."),
    ("다만 <b>현재 이 파일에서 4번 줄의 tokenizer는 쓰이지 않는다.</b> 파일에 tokenizer라는 이름이 세 번 "
    "나오지만 모두 다른 변수이기 때문이다.")],
    [table([
        ["줄", "어떤 tokenizer인가", "누가 쓰나"],
        ["4", "파일 맨 바깥에서 만든 변수", "아무도 안 씀 (예전 5번 줄의 enc_text가 쓰다가 지워짐)"],
        ["9 · 13", "__init__이 매개변수로 받은 값", "13번 줄 — 토큰화"],
        ["28", "함수 안에서 새로 만든 값", "29번 줄 — 데이터셋에 넘김"],
    ], [18 * mm, 62 * mm, 90 * mm])])
S += line(5, [
    (f"파일을 연다. {C(R_MODE)}은 읽기 모드, {C(ENC_ARG)}은 글자를 해석하는 규칙이다. "
    "이 시에는 영어 밖의 문자 — 대시 &lsquo;—&rsquo;(9개)와 wingéd의 &lsquo;é&rsquo; — 가 있어서 인코딩을 "
    f"지정해야 안전하다. {C('with')}로 열면 블록이 끝날 때 파일이 자동으로 닫힌다."),
    (f"경로 {C('experiments/ch02/embedding_exec/annabel_lee.txt')}는 <b>저장소 루트 기준 상대경로</b>다. 그래서 반드시 "
    "저장소 루트에서 실행해야 한다.")],
    [callout("bug", "경로 앞의 / 하나로 FileNotFoundError", [
        (f"처음에 {C('/experiments/ch02/embedding_exec/annabel_lee.txt')}라고 썼다가 에러가 났다. <b>/로 시작하면 절대경로</b>가 되어 "
        "디스크 꼭대기 폴더에서 찾기 때문이다."),
        table([
            ["쓴 경로", "찾는 곳"],
            ["/experiments/ch02/embedding_exec/annabel_lee.txt", "디스크 최상위 폴더(/) 바로 아래 — 없음"],
            ["experiments/ch02/embedding_exec/annabel_lee.txt", "지금 서 있는 폴더(= 저장소 루트) 아래 — 있음"],
        ], [95 * mm, 65 * mm], code_cols=(0,)),
        (f"지금 어디 서 있는지는 {C('print(os.getcwd())')}로 확인한다. 에러 메시지 속 경로를 한 글자씩 읽는 게 "
        "가장 빠른 확인 방법이다.")])])
S += line(6, [
    (f"파일 전체를 <b>문자열 하나</b>로 읽어 {C('raw_text')}에 담는다. 길이는 1,570자다(바이트로는 1,589 — "
    "&lsquo;—&rsquo;와 &lsquo;é&rsquo;가 UTF-8에서 여러 바이트를 차지한다). 이 단계에서는 아직 신경망이 "
    "계산할 수 있는 숫자가 아니다.")])

# ------------------------------------------------------------------ 8-25
S.append(section("3. GPTDatasetV1 — 8~25번 줄",
          "흐름도 2.5 · 2.6 · 이 18줄은 설계도다. 29번 줄에서 데이터셋을 만들 때 비로소 실행된다", source_block(8, 25)))
S += line(8, [
    (f"{C('Dataset')}을 물려받는 클래스를 선언한다. 물려받는다는 건 &ldquo;DataLoader가 기대하는 두 가지 — "
    f"{C('__len__')}과 {C('__getitem__')} — 를 내가 채워 넣겠다&rdquo;는 약속이다.")])
S += line(9, [
    ("데이터셋을 만들 때 <b>한 번</b> 실행되는 준비 작업이다. self는 만들어질 데이터셋 자기 자신이고, "
    "나머지 넷(txt, tokenizer, max_length, stride)은 바깥에서 받아 올 재료다.")],
    [callout("rule", "받은 값은 받은 대로 쓴다", [
        ("13번 줄은 매개변수로 받은 tokenizer를 쓴다. 바깥 4번 줄의 값을 몰래 쓰지 않는다. 세션 03의 "
        f"SimpleTokenizerV1은 {C('__init__(self, text)')}로 받아놓고 바깥 vocab을 썼다 — 그러면 클래스를 다른 "
        "파일로 옮기는 순간 죽는다. 오늘 코드는 그 교훈이 반영되어 있다.")])])
S += line((10, 11), [
    ("빈 목록 두 개를 만든다. 윈도우를 하나 만들 때마다 입력과 타깃이 여기에 하나씩 쌓인다. "
    f"앞에 {C('self.')}가 붙어 있어서 __init__이 끝난 뒤에도 남는다 — 21번과 24번 줄에서 다시 쓰기 위해서다.")])
S += line(13, [
    "<b>흐름도 2.5 — BPE 토큰화.</b> 1,570자의 문자열이 정수 467개로 바뀐다. 처음 네 개는 이렇다.",
], [table([
    ["위치", "토큰 ID", "조각", "눈여겨볼 점"],
    ["0", "18858", "Ann", "Annabel 한 단어가 두 조각으로 나뉜다"],
    ["1", "9608", "abel", ""],
    ["2", "5741", "' Lee'", "앞의 공백까지 한 토큰 — BPE는 공백을 단어 앞에 붙인다"],
    ["3", "198", "줄바꿈 (\\n)", "줄바꿈도 토큰이다"],
], [16 * mm, 22 * mm, 34 * mm, 98 * mm]),
    callout("find", "같은 시인데 토큰 수가 463과 467로 다르다", [
        ("저장소에 원래 있던 data/Annabel_Lee.txt는 463토큰, 오늘 쓴 파일은 467토큰이다. 제목·저자 줄의 유무와 "
        "함께, <b>들여쓰기 공백의 종류</b>가 다르다. 화면에서는 똑같은 공백으로 보이지만 BPE는 다른 토큰으로 본다."),
        table([
            ["들여쓰기", "BPE 결과"],
            ["일반 공백 3개 + In", "[220, 220, 554]"],
            ["\\xa0(줄바꿈 없는 공백) 3개 + In", "[4603, 1849, 818]"],
        ], [80 * mm, 80 * mm], code_cols=(1,)),
        ("영어 밖 문자도 조각난다: &lsquo;Lee—&rsquo;는 &lsquo; Lee&rsquo; + &lsquo;—&rsquo;로, &lsquo;wingéd&rsquo;는 "
        "&lsquo; wing&rsquo; + &lsquo;é&rsquo; + &lsquo;d&rsquo;로 나뉜다. 세션 02의 손상 코퍼스, 세션 03의 "
        "따옴표 문제와 같은 종류다 — <b>눈에 안 보이는 문자 차이가 숫자를 조용히 바꾼다.</b>")])])
S += line(15, [
    (f"<b>흐름도 2.6 — 윈도우 시작 위치.</b> 467토큰, max_length 4, stride 4를 넣으면 "
    f"{C('range(0, 463, 4)')}가 되어 i = 0, 4, 8, …, 460 — <b>116개</b>다."),
    (f"왜 {C('len(token_ids) - max_length')}까지인가: 타깃은 입력보다 한 칸 뒤까지 필요하다. 마지막 윈도우도 "
    "&ldquo;입력 4개 + 그다음 1개&rdquo;가 남아 있어야 하므로, 시작 위치는 끝에서 max_length칸보다 앞이어야 한다.")],
    [callout("rule", "range 개수 세는 요령 — 끝값은 포함되지 않는다", [
        ("작은 예: 토큰 14개, max_length 4, stride 4 → range(0, 10, 4) → 0, 4, 8 → 3개. 다음 12는 끝값 10 "
        "이상이라 멈춘다."),
        "요령: <b>끝값 ÷ 간격, 나머지가 있으면 +1.</b> 463 ÷ 4 = 115 나머지 3 → 116.",
        (f"같은 규칙이 슬라이싱에도 적용된다. 오늘 {C('enc_text[:50]')}의 개수를 51개로 세셨는데, 0번부터 49번까지 "
        "<b>50개</b>다. 여기서 한 칸 틀리면 윈도우 계산에서도 틀린다.")])])
S += line(16, [
    f"i번부터 네 개를 잘라 입력으로 삼는다. {C('[i:i + 4]')}는 i, i+1, i+2, i+3 — 끝 번호 i+4는 포함되지 않는다."])
S += line(17, [
    ("<b>한 칸 뒤</b>에서 네 개를 잘라 타깃으로 삼는다. 입력의 각 자리마다 &ldquo;바로 다음 토큰&rdquo;이 정답이 "
    "되어, 다음 토큰 맞히기 문제가 만들어진다. 첫 윈도우는 이렇다.")],
    [table([
        ["자리", "입력", "→ 맞혀야 할 타깃"],
        ["0", "18858  Ann", "9608  abel"],
        ["1", "9608  abel", "5741  ' Lee'"],
        ["2", "5741  ' Lee'", "198  줄바꿈"],
        ["3", "198  줄바꿈", "3886  By"],
    ], [20 * mm, 75 * mm, 75 * mm]),
        callout("bug", "세션 04 — i + i", [
            (f"처음 칠 때 {C('token_ids[i + i: ...]')}로 쳤다. <b>i=0일 때는 우연히 맞아서</b> 에러도, 이상한 "
            "결과도 없었다. 오늘은 한 번에 맞게 치셨다.")])])
S += line((18, 19), [
    ("잘라낸 파이썬 리스트를 텐서로 바꿔 목록에 쌓는다. 신경망은 리스트가 아니라 텐서를 받는다. 반복이 끝나면 "
    "두 목록에 116개씩 들어 있다.")])
S += line((21, 22), [
    (f"데이터셋의 크기, 즉 윈도우 개수(116)를 알려준다. DataLoader가 배치를 몇 개 만들 수 있는지 계산할 때 쓴다. "
    f"{C('len(dataset)')}을 부르면 이 함수가 실행된다.")])
S += line((24, 25), [
    (f"idx번째 윈도우 하나를 (입력, 타깃) 쌍으로 돌려준다. {C('dataset[0]')}은 "
    f"{C('([18858, 9608, 5741, 198], [9608, 5741, 198, 3886])')}이다. DataLoader는 배치 하나를 만들 때 이 "
    "함수를 8번 부른다.")],
    [callout("bug", "세션 04 — input_idss, ids", [
        (f"처음 칠 때 {C('self.input_idss[idx], self.target_ids[ids]')}였다. s 한 글자, 매개변수 이름 한 글자 "
        "차이다. 오늘은 둘 다 맞다.")])])

# ------------------------------------------------------------------ 26-31
S.append(section("4. create_dataloader_v1 — 26~31번 줄", "흐름도 2.6 · 데이터셋을 만들고 배치로 묶어 돌려준다", source_block(26, 31)))
S += line((26, 27), [
    (f"함수를 선언한다. {C('batch_size=4')}처럼 <b>=로 적힌 값은 기본값</b>이다. 부를 때 넘기지 않은 매개변수는 "
    "이 값을 쓴다."),
    ("기본값은 책의 실전용(긴 텍스트) 설정이라 오늘 설정과 다르다. 특히 <b>shuffle=True</b>와 "
    "<b>drop_last=True</b>가 기본이라는 점을 기억해야 한다 — 34번 줄에서 shuffle은 넘기고 drop_last는 넘기지 않았다.")])
S += line(28, [
    "함수 안에서 토크나이저를 새로 만든다. 4번 줄과 이름만 같고 별개의 변수다. 함수가 끝나면 사라진다."])
S += line(29, [
    ("<b>여기서 비로소 GPTDatasetV1의 __init__(9~19번 줄)이 실행된다.</b> 토큰화와 윈도우 116개 생성이 이 한 줄을 "
    "실행하는 순간 한꺼번에 일어난다.")])
S += line(30, [
    "데이터셋을 DataLoader에 넘긴다. 네 가지 옵션의 뜻은 이렇다."],
    [table([
        ["옵션", "뜻", "오늘 값"],
        ["batch_size", "한 번에 묶을 윈도우 수", "8"],
        ["shuffle", "윈도우 순서를 섞을지. 학습에서는 보통 True, 확인·디버깅에서는 False", "False"],
        ["drop_last", "마지막에 batch_size를 못 채운 윈도우를 버릴지", "True (기본값)"],
        ["num_workers", "데이터를 준비할 보조 프로세스 수. 0이면 메인 프로세스가 직접 한다", "0 (기본값)"],
    ], [28 * mm, 112 * mm, 30 * mm]),
        P(f"{C('shuffle=shuffle')} 모양에서 <b>왼쪽은 DataLoader의 옵션 이름, 오른쪽은 이 함수가 받은 매개변수</b>다. "
          "같은 이름이라 헷갈리지만 둘은 다른 것이다."),
        callout("bug", "매개변수를 받아놓고 쓰지 않았다 — 가장 찾기 어려웠던 버그", [
            (f"처음에는 이 줄이 {C('shuffle=True, drop_last=True, num_workers=0')}였다. 함수는 shuffle을 "
            "매개변수로 받아놓고 DataLoader에는 True를 <b>값 그대로</b> 넘긴 것이다."),
            (f"그래서 34번 줄에서 {C('shuffle=False')}를 넘겨도 <b>무시되었고</b>, 실행할 때마다 &ldquo;첫 배치&rdquo;가 "
            "달라졌다. 한번은 시의 396번 토큰 위치인 &lsquo; bright eyes&rsquo;가 첫 배치로 나왔다."),
            ("확인한 방법: 같은 스크립트를 여러 번 실행해 결과가 매번 다른지 봤다. 고친 뒤에는 첫 입력·타깃을 "
            "먼저 적어두고 실행해 세 번 연속 같은 값이 나오는지 확인했다."),
            ("34번 줄만 고치면 고쳐진 것처럼 보이는데 동작은 안 바뀐다. <b>고친 줄이 아니라 결과로 확인해야 하는</b> "
            "이유다.")])])
S += line(31, ["완성된 DataLoader를 돌려준다. 34번 줄의 dataloader에 담긴다."])

# ------------------------------------------------------------------ 32-36
S.append(section("5. 설정하고 첫 배치 꺼내기 — 32~36번 줄", "흐름도 2.6 · 여기서부터 실제 계산이 시작된다", source_block(32, 36)))
S += line(32, [
    ("윈도우 길이를 4로 정한다. <b>이 한 줄만 바꾸면</b> 34번 줄(max_length, stride)과 42번 줄(context_length)이 "
    "함께 따라간다.")])
S += line(33, ["배치 크기를 8로 정한다. 바꿀 수 있는 숫자를 변수로 올려 한곳에 모았다."])
S += line(34, [
    "함수를 불러 DataLoader를 만든다. 넘긴 값의 뜻은 이렇다.",
], [table([
    ["넘긴 값", "뜻"],
    ["stride=max_length", "윈도우를 겹치지 않게 자른다 (stride = max_length = 4)"],
    ["shuffle=False", "윈도우를 순서대로 내준다 — 첫 배치가 시의 맨 앞이 된다"],
    ["drop_last (넘기지 않음)", "기본값 True — 8개를 못 채운 끝부분은 버린다"],
], [50 * mm, 120 * mm], code_cols=()),
    table([
        ["계산", "결과"],
        ["윈도우 수", "range(0, 463, 4) → 116개"],
        ["배치 수 = len(dataloader)", "116 ÷ 8 = 14 나머지 4 → 배치 14개"],
        ["버려지는 윈도우", "4개"],
    ], [60 * mm, 110 * mm]),
    callout("find", "drop_last=True가 시의 마지막 두 줄을 버린다", [
        ("버려진 윈도우 4개(시작 위치 448, 452, 456, 460)와, 윈도우를 만들기에도 부족한 끝 토큰(464~466)을 합쳐 "
        "<b>토큰 448~466, 19개가 입력으로 한 번도 쓰이지 않는다.</b> 그 텍스트는 이렇다."),
        P("chre there by the sea— / In her tomb by the sounding sea.", box_body),
        ("마지막 연이 사라지고, sepulchre(무덤)라는 단어가 sepul과 chre 사이에서 잘린다. 에러도 경고도 없고, "
        "배치 shape [8, 4]만 보면 전혀 알 수 없다."),
        ("The Verdict(5,145토큰)에서도 같은 일이 있었지만 비율이 작아 보이지 않았다. <b>텍스트가 짧을수록 비율이 "
        "커진다</b> — 여기서는 467토큰 중 약 4%. drop_last=True 자체는 틀린 설정이 아니다. 무엇이 버려지는지 "
        "모르고 쓰는 것이 문제다.")]),
    callout("rule", "숫자를 직접 적지 말고 변수를 넘긴다", [
        (f"한동안 이 줄은 {C('max_length=4, stride=4')}였고 32번 줄에는 {C('max_length = 4')}가 따로 있었다. "
        "지금은 둘 다 4라 문제가 없지만, 32번 줄만 8로 바꾸면 배치는 길이 4로 잘리고 위치 표는 8행이 되어 "
        "<b>에러 없이 어긋난다.</b> 30번 줄의 shuffle 버그와 같은 구조다.")])])
S += line(35, [
    ("DataLoader에서 배치를 하나씩 꺼낼 수 있는 상태로 만든다. 책갈피를 꽂아두는 것과 같다 — <b>아직 아무것도 "
    "꺼내지 않았다.</b>")])
S += line(36, [
    ("첫 배치를 꺼낸다. 이 순간 DataLoader가 __getitem__을 0번부터 7번까지 8번 불러 결과를 쌓는다. 한 번에 "
    f"나오는 두 값(입력 묶음, 타깃 묶음)을 {C('inputs')}와 {C('targets')}에 나눠 담는다. 둘 다 shape는 "
    "<b>[8, 4]</b>다.")],
    [codebox(
        "inputs                                  targets\n"
        "[[18858,  9608,  5741,   198],           [[ 9608,  5741,   198,  3886],\n"
        " [ 3886, 29166, 31908, 34815],            [29166, 31908, 34815,   198],\n"
        " [  198,   198,  1026,   373],            [  198,  1026,   373,   867],\n"
        " [  867,   290,   867,   257],            [  290,   867,   257,   614],\n"
        " [  614,  2084,    11,   198],            [ 2084,    11,   198,   220],\n"
        " [  220,   220,   554,   257],            [  220,   554,   257, 13239],\n"
        " [13239,   416,   262,  5417],            [  416,   262,  5417,    11],\n"
        " [   11,   198,  2504,   257]]            [  198,  2504,   257, 34827]]"),
        P("이 배치에서 확인한 성질 두 가지:", small),
        P("① <b>각 행 타깃의 마지막 값 = 다음 행 입력의 첫 값</b> (예: 1행 타깃 끝 3886 = 2행 입력 첫 값 3886). "
          "stride와 max_length가 같아서 생긴다. stride=1이면 이렇게 되지 않는다.", small),
        P(f"② <b>반복되는 토큰</b>이 있다. 3행의 {C('198')}이 0번·1번 자리에 연달아 있고, {C('257')}(&lsquo; a&rsquo;)이 "
          "4·6·8행 모두 3번 자리에 있다. 45번 줄에서 위치 임베딩을 확인할 때 쓴다.", small)])

# ------------------------------------------------------------------ 37-41
S.append(section("6. 토큰 임베딩 — 37~41번 줄", "흐름도 2.7 · 의미 없는 정수를 학습 가능한 벡터로", source_block(37, 41)))
S += line(37, [
    ("토큰 표의 <b>행 개수</b>다. 표에는 토큰 ID가 가질 수 있는 모든 값마다 행이 하나씩 있어야 하므로, "
    "<b>텍스트가 아니라 토크나이저가 정한다.</b> gpt2를 쓰는 한 50,257이다.")],
    [callout("bug", "vocab_size = 463 → IndexError", [
        f"처음에 463을 넣었다가 {C('IndexError: index out of range in self')}가 났다. 오늘 나온 숫자들이 헷갈렸던 것이다.",
        table([
            ["숫자", "뜻", "vocab_size가 될 수 있나"],
            ["463", "윈도우 개수 (467 − 4)", "아니오"],
            ["467", "이 시의 토큰 개수", "아니오"],
            ["164", "이 시에 나오는 서로 다른 토큰 종류", "아니오"],
            ["50,257", "gpt2 토크나이저가 아는 토큰 종류 전체", "예"],
        ], [22 * mm, 92 * mm, 46 * mm]),
        ("164가 안 되는 이유가 핵심이다. 토큰 종류는 164개뿐이지만 <b>ID는 0~163으로 다시 매겨지지 않는다.</b> "
        "gpt2가 붙인 번호가 그대로 들어오고, 이 시에서 가장 큰 ID는 47897(&lsquo; wiser&rsquo;)이다. 행이 463개인 "
        "표에는 47897번 행이 없다. 첫 배치만 봐도 ID 32개 중 16개가 463 이상이었다.")])])
S += line(38, [
    "토큰 하나를 <b>몇 개의 숫자로 표현할지</b> 정한다. 설계자가 고르는 값이라 책의 256과 달라도 된다.",
    "단, 43번 줄의 위치 표도 <b>같은 128</b>을 써야 45번 줄에서 두 벡터를 더할 수 있다."])
S += line(39, [
    ("무작위 시작점을 123으로 고정한다. 40번과 43번 줄의 두 표가 <b>모두 이 뒤에 만들어지므로</b>, 실행할 때마다 "
    "두 표 모두 똑같은 값으로 채워진다(확인함)."),
    ("값이 책과 다른 건 정상이다. 시드가 같아도 표 크기(50,257×128 대 책의 6×3)가 다르면 같은 행에 들어가는 "
    "숫자가 달라진다. 이 스크립트에서 대조할 기준은 값이 아니라 shape다.")])
S += line(40, [
    ("<b>50,257행 × 128열</b>짜리 표를 만든다. 숫자가 6,432,896개 들어 있고, 처음에는 무작위이며 학습(5장)에서 "
    "의미를 갖도록 바뀐다. 이름 끝의 _layer는 &ldquo;이것은 표(레이어)다&rdquo;라는 표시다.")])
S += line(41, [
    ("<b>조회</b>한다. inputs의 ID 32개마다 표에서 해당 행을 꺼내 모양 그대로 쌓는다. "
    "[8, 4] → <b>[8, 4, 128]</b>.")],
    [callout("rule", "임베딩을 거치면 맨 뒤에 output_dim 차원이 붙는다", [
        "[4] → [4, 128], [8, 4] → [8, 4, 128]. 44번 줄의 위치 임베딩도 같은 규칙이다."]),
     callout("bug", "표와 결과를 헷갈린 에러 두 가지", [
         (f"① {C('token_embeddings(torch.tensor([3]))')} → {C(ERR_CALLABLE)}. "
         "결과 텐서에 괄호를 붙여 표처럼 호출했다. 조회는 표가 하는 일이다."),
         table([
             ["이름", "무엇인가", "( )로 호출"],
             ["token_embedding_layer", "표 — ID를 넣으면 벡터를 꺼내 준다", "가능"],
             ["token_embeddings", "표에서 꺼낸 결과 — [8, 4, 128] 숫자 덩어리", "불가"],
         ], [46 * mm, 90 * mm, 24 * mm], code_cols=(0,)),
         (f"② {C('token_embedding_layer(input_ids)')} → {C(ERR_NAME)}. "
         f"책에서 이 줄만 옮기고, 그 줄이 전제하는 {C('input_ids = torch.tensor([2, 3, 5, 1])')}는 옮기지 않았다. "
         "줄을 옮길 때는 <b>그 줄의 이름이 내 스크립트 어디서 만들어졌는지</b> 확인한다.")])])

# ------------------------------------------------------------------ 42-44
S.append(section("7. 위치 임베딩 — 42~44번 줄", "흐름도 2.8 · 자리 번호도 표에서 찾는다", source_block(42, 44)))
S += line(42, [
    ("위치 표의 <b>행 개수 = 자리 개수</b>다. 한 윈도우에 자리가 4개이므로 max_length를 그대로 쓴다. 토큰 표의 "
    "행 개수는 토크나이저가 정했고, 위치 표의 행 개수는 윈도우 길이가 정한다.")])
S += line(43, [
    ("<b>4행 × 128열</b>짜리 표를 만든다(숫자 512개). 40번 줄과 클래스도 원리도 같다. 달라지는 건 행 하나가 "
    "&ldquo;토큰&rdquo;이 아니라 &ldquo;자리&rdquo;를 뜻한다는 점뿐이다.")],
    [table([
        ["", "token_embedding_layer (40번 줄)", "pos_embedding_layer (43번 줄)"],
        ["표 크기", "50,257 × 128", "4 × 128"],
        ["행 하나의 뜻", "어휘 속 토큰 하나", "윈도우 속 자리 하나"],
        ["행 개수를 정하는 것", "토크나이저", "max_length"],
        ["조회에 쓰는 번호", "토큰 ID — inputs", "자리 번호 — torch.arange(4)"],
        ["결과 shape", "[8, 4, 128]", "[4, 128]"],
    ], [38 * mm, 66 * mm, 66 * mm])])
S += line(44, [
    (f"{C('torch.arange(4)')}는 자리 번호 목록 {C('[0, 1, 2, 3]')}이다. 이걸 표에 넣으면 0~3번 행이 꺼내져 "
    "[4] → <b>[4, 128]</b>이 된다."),
    ("토큰 쪽은 [8, 4, 128]인데 위치 쪽에 8이 없는 이유: 자리 번호는 문장과 무관하다. 8개 윈도우 모두 "
    "0·1·2·3번 자리로 똑같으니 한 벌만 만든다.")],
    [callout("rule", "표에 없는 행 번호를 요구하면 IndexError", [
        (f"4행 표에 {C('torch.arange(5)')}를 넣으면 {C('IndexError: index out of range in self')}가 난다. 37번 줄에서 "
        "vocab_size=463으로 만났던 에러, 세션 04에서 장난감 표에 2885를 넣었을 때의 에러와 <b>메시지도 원인도 같다.</b> "
        "이 에러를 보면 &ldquo;어느 표의 행 개수를 넘었나&rdquo;부터 의심한다.")])])

# ------------------------------------------------------------------ 45-46
S.append(section("8. 더하고 확인하기 — 45~46번 줄", "흐름도 2.8 · LLM이 실제로 받는 입력이 완성된다", source_block(45, 46)))
S += line(45, [
    ("두 텐서를 더한다. 모양이 [8, 4, 128]과 [4, 128]로 다른데 에러가 나지 않는 이유는 <b>브로드캐스팅</b> "
    "때문이다. PyTorch가 [4, 128] 한 벌을 8개 윈도우 각각에 복사해 더해 준다. 뒤쪽 차원부터 맞춰 보고, "
    "앞쪽에 없는 차원(8)은 늘려서 채운다. 결과는 <b>[8, 4, 128]</b>이다.")],
    [callout("find", "위치 정보가 실제로 들어갔는지 대조군과 함께 확인했다", [
        ("shape가 맞는다는 건 &ldquo;더하기가 에러 없이 됐다&rdquo;까지만 증명한다. 그래서 36번 줄에서 본 반복 토큰으로 "
        f"{C('torch.equal(a, b)')}를 확인했다(지금 스크립트에서는 이 비교 코드를 지운 상태)."),
        table([
            ["비교", "토큰 임베딩", "입력 임베딩"],
            ["3행의 198 — 0번 자리 vs 1번 자리 (같은 토큰, <b>다른 자리</b>)", "True", "False"],
            ["4행·6행의 257 — 둘 다 3번 자리 (같은 토큰, <b>같은 자리</b>)", "True", "True"],
        ], [110 * mm, 25 * mm, 25 * mm]),
        ("첫 줄만 있었다면 &ldquo;더하기가 뭔가를 바꿨다&rdquo;까지만 알 수 있다. 둘째 줄이 True라서 <b>바뀐 이유가 "
        "무작위가 아니라 자리 번호 때문</b>이라는 게 증명된다."),
        (f"다시 넣을 때는 전제를 코드로 확인해 둔다: {C('assert inputs[2, 0] == inputs[2, 1] == 198')}. 텍스트나 "
        "max_length가 바뀌면 인덱스가 다른 토큰을 가리키게 되고, 그때 에러 없이 의미 없는 비교를 하게 된다.")])])
S += line(46, [
    f"최종 shape를 출력한다. 결과는 {C('torch.Size([8, 4, 128])')} — 윈도우 8개 × 토큰 4개 × 128차원."])

# ------------------------------------------------------------------ summary
S.append(section("9. 한눈에 보기", "shape 추적과 오늘 만난 에러", P("데이터가 변해 가는 모습", h2), table([
    ["줄", "변수", "모양", "내용"],
    ["6", "raw_text", "문자열", "1,570자"],
    ["13", "token_ids", "정수 467개", "BPE 토큰 ID"],
    ["15–19", "self.input_ids", "텐서 116개", "각 [4]"],
    ["36", "inputs", "[8, 4]", "첫 배치 (전체는 배치 14개)"],
    ["41", "token_embeddings", "[8, 4, 128]", "무슨 토큰인가"],
    ["44", "pos_embeddings", "[4, 128]", "몇 번째 자리인가"],
    ["45", "input_embeddings", "[8, 4, 128]", "둘의 합 — 3장 어텐션의 입력"],
], [18 * mm, 42 * mm, 36 * mm, 74 * mm], code_cols=(1,))))

S.append(KeepTogether(flatten([P("오늘 만난 에러와 버그", h2), table([
    ["증상", "원인", "줄", "알아차린 방법"],
    ["FileNotFoundError", "경로 앞의 / — 절대경로가 됨", "5", "에러"],
    ["첫 배치가 실행마다 다름", "shuffle을 받아놓고 True를 값 그대로 넘김", "30", "<b>여러 번 실행해 비교</b>"],
    ["시의 마지막 두 줄이 빠짐", "drop_last=True (설정의 결과)", "34", "<b>버려진 텍스트를 직접 디코딩</b>"],
    ["IndexError", "vocab_size에 윈도우 수 463을 넣음", "37", "에러"],
    ["TypeError: not callable", "결과 텐서를 표처럼 호출", "41 뒤", "에러"],
    ["NameError: input_ids", "책에서 한 줄만 옮겨 옴", "41 뒤", "에러"],
    ["토큰 수 463 vs 467", "\\xa0 공백, 제목 줄의 차이", "5–6", "<b>두 파일 비교</b>"],
    ["&ldquo;51개&rdquo;", "[:50]은 끝을 포함하지 않아 50개", "—", "<b>셈 확인</b>"],
], [42 * mm, 66 * mm, 16 * mm, 46 * mm])])))
S.append(P(
    "강조한 네 줄은 <b>에러가 나지 않았다.</b> 결과를 의심하고 직접 확인해야만 보였다. 나머지 넷은 문법이 아니라 "
    "<b>이름과 대상이 어긋난</b> 경우다 — 세션 03·04에서 기록한 패턴이 오늘도 그대로 나타났다.", small))

BULLETS = [
    ("<b>45번 줄의 input_embeddings [8, 4, 128]이 3장 어텐션의 입력이다.</b> 윈도우(문장) 하나당 토큰 4개, 토큰 하나당 "
    "128개의 숫자."),
    ("어텐션은 이 벡터들끼리 내적으로 관련도를 재고, 그 비율대로 섞어 새 벡터를 만든다(QKV 자료). 위치 정보가 "
    "여기서 이미 더해져 있으므로 <b>같은 단어라도 자리가 다르면 다른 점수를 받을 수 있다</b> — 오늘 확인한 "
    "False가 그 근거다."),
    ("2장이 끝난 지금 두 표의 값은 아직 무작위다. &ldquo;cat과 mat이 비슷하다&rdquo; 같은 의미 있는 값은 학습(5장)에서 "
    "생긴다. 2장에서 만든 것은 <b>의미를 담을 그릇의 모양</b>이다."),
]
S.append(section("10. 3장으로 가져갈 것", "Chapter 2의 끝이 어텐션의 시작이다", *[P("· " + t) for t in BULLETS]))

S.append(Spacer(1, 10))
S.append(KeepTogether([
    HRFlowable(width="55%", thickness=0.7, color=LINE, hAlign="CENTER", spaceAfter=8),
    P("텍스트는 토큰 ID가 되고, ID는 윈도우로 잘리고, 윈도우는 &ldquo;무슨 토큰인가&rdquo;와 "
      "&ldquo;몇 번째 자리인가&rdquo;를 더한 벡터가 된다. 그 벡터가 어텐션으로 간다.", take_s),
]))

# ------------------------------------------------------------------ exercises
QUESTIONS = [
    "① 32번 줄을 max_length = 8로 바꾸면(stride도 따라서 8), 윈도우 수·배치 수·버려지는 윈도우 수는?",
    "② max_length는 4로 두고 34번 줄의 stride만 2로 바꾸면, 윈도우 수·배치 수·버려지는 윈도우 수는?",
    "③ 38번 줄을 output_dim = 256으로 바꾸면 token_embeddings, pos_embeddings, input_embeddings의 shape는?",
    "④ 44번 줄의 torch.arange(context_length)를 torch.arange(5)로 바꾸면 어떻게 되는가?",
    "⑤ 34번 줄을 shuffle=True로 바꾸면 len(dataloader)는 달라지는가?",
    "⑥ 37번 줄을 vocab_size = 50000으로 바꾸면 에러가 나는가? 난다면, 또는 나지 않는다면 그 이유는?",
]
S.append(section("11. 다시 풀어볼 문제", "코드를 바꾸기 전에 결과를 먼저 적어보세요 — 답은 마지막 페이지",
                 *[P(q) for q in QUESTIONS]))

S.append(PageBreak())
S.append(P("답", part_s))
S.append(HRFlowable(width="100%", thickness=0.6, color=LINE, spaceAfter=6))
S.append(table([
    ["문제", "답", "계산·이유"],
    ["①", "윈도우 58 · 배치 7 · 버림 2", "range(0, 467 − 8, 8) = range(0, 459, 8) → 459 ÷ 8 = 57 나머지 3 → 58. 58 ÷ 8 = 7 나머지 2"],
    ["②", "윈도우 232 · 배치 29 · 버림 0", "range(0, 463, 2) → 463 ÷ 2 = 231 나머지 1 → 232. 232 ÷ 8 = 29 나머지 0. 윈도우가 절반씩 겹친다"],
    ["③", "[8, 4, 256] · [4, 256] · [8, 4, 256]", "맨 뒤 차원만 output_dim을 따라간다. 두 표 모두 256이어야 더할 수 있다"],
    ["④", "IndexError: index out of range in self", "위치 표는 4행(0~3번)뿐인데 4번 행을 요구했다"],
    ["⑤", "아니오 — 14 그대로", "섞으면 순서만 바뀌고 개수는 같다. 다만 &ldquo;첫 배치&rdquo;의 내용은 실행마다 달라진다"],
    ["⑥", "이 시에서는 에러가 나지 않는다", ("이 시에서 가장 큰 ID가 47897이라 50,000행 안에 들어간다. 그러나 <b>틀린 설정이다</b> — "
           "50,000 이상의 ID가 나오는 텍스트에서는 IndexError가 난다. <b>에러가 안 난다고 맞는 것이 아니다.</b>")],
], [16 * mm, 54 * mm, 100 * mm]))
S.append(Spacer(1, 10))
S.append(P(
    "이 자료의 모든 수치는 embed_exec.py를 프로젝트 가상환경에서 실행해 확인했다. "
    "생성 스크립트: tools/pdf/embed_exec_walkthrough.py", cap))


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont(FONT, 8)
    canvas.setFillColor(GREY)
    canvas.drawString(20 * mm, 10 * mm, "embed_exec.py 한 줄씩 읽기")
    canvas.drawRightString(A4[0] - 20 * mm, 10 * mm, str(doc.page))
    canvas.restoreState()


doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                        topMargin=18 * mm, bottomMargin=18 * mm, title="embed_exec.py 한 줄씩 읽기")
doc.build(S, onFirstPage=footer, onLaterPages=footer)
print("wrote", OUT)
