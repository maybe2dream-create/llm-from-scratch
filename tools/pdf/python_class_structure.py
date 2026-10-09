# /// script
# dependencies = ["reportlab"]
# ///
"""Python class anatomy -> docs/Python_Class_Structure.pdf

Run from anywhere:  uv run tools/pdf/python_class_structure.py
Every output shown in the document was produced by running the examples (2026-09-22).
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
KOREAN_FONT = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
FONT = "KR"
pdfmetrics.registerFont(TTFont(FONT, KOREAN_FONT))

REPO = Path(__file__).resolve().parents[2]
OUT = str(REPO / "docs" / "Python_Class_Structure.pdf")

INK = colors.HexColor("#1a1a1a")
GREY = colors.HexColor("#5a5a5a")
LINE = colors.HexColor("#cfcfcf")
CODE_BG = colors.HexColor("#f4f5f7")
HEAD = colors.HexColor("#ececec")
ACCENT = "#2f4f76"
WARN_BG, WARN_BAR = colors.HexColor("#fdf3e6"), colors.HexColor("#d08a2e")
RULE_BG, RULE_BAR = colors.HexColor("#eaf0f8"), colors.HexColor(ACCENT)
OUT_BG, OUT_BAR = colors.HexColor("#ebf5ec"), colors.HexColor("#4f8a55")

CONTENT_W = 170 * mm

title_s = ParagraphStyle("T", fontName=FONT, fontSize=20, leading=26, textColor=INK)
sub_s = ParagraphStyle("S", fontName=FONT, fontSize=10, leading=14.5, textColor=GREY, spaceAfter=12)
part_s = ParagraphStyle("PART", fontName=FONT, fontSize=15, leading=20, textColor=INK,
                        spaceBefore=14, spaceAfter=4)
part_sub = ParagraphStyle("PSUB", fontName=FONT, fontSize=9.4, leading=13, textColor=GREY,
                          spaceAfter=8)
h2 = ParagraphStyle("H2", fontName=FONT, fontSize=11.5, leading=15.5, spaceBefore=11, spaceAfter=5,
                    textColor=colors.HexColor(ACCENT), keepWithNext=1)
body = ParagraphStyle("B", fontName=FONT, fontSize=10, leading=16, spaceAfter=7)
small = ParagraphStyle("SM", parent=body, fontSize=9.2, leading=14, spaceAfter=4)
item = ParagraphStyle("I", parent=body, leftIndent=13, spaceAfter=4)
cap = ParagraphStyle("C", fontName=FONT, fontSize=8.6, leading=12, alignment=TA_CENTER,
                     textColor=GREY, spaceBefore=3, spaceAfter=8)
box_title = ParagraphStyle("BT", fontName=FONT, fontSize=9.6, leading=13, spaceAfter=3)
box_body = ParagraphStyle("BB", fontName=FONT, fontSize=9.3, leading=14.2, spaceAfter=3)
code_s = ParagraphStyle("CODE", fontName="Courier", fontSize=8.5, leading=11.8)
anno_code = ParagraphStyle("AC", fontName="Courier", fontSize=8.5, leading=12.4)
anno_label = ParagraphStyle("AL", fontName=FONT, fontSize=8.4, leading=12.4,
                            textColor=colors.HexColor(ACCENT))
cell_s = ParagraphStyle("CELL", fontName=FONT, fontSize=8.9, leading=12.4)
cell_h = ParagraphStyle("CH", parent=cell_s, fontName=FONT)
cell_code = ParagraphStyle("CC", fontName="Courier", fontSize=8.3, leading=11.6)
take_s = ParagraphStyle("TK", fontName=FONT, fontSize=11.5, leading=17, alignment=TA_CENTER,
                        textColor=INK, spaceBefore=5, spaceAfter=5)


ERR_ATTR = "AttributeError: 'GPTDatasetV1' object has no attribute 'input_idss'"
MK_CALL = 'a = Vocabulary(["cat", "sat"])'
MK_INIT = '__init__(a, ["cat", "sat"])'


def accent(t):
    return t.replace("<b>", f'<font color="{ACCENT}">').replace("</b>", "</font>")


def P(t, s=body):
    return Paragraph(accent(t), s)


def C(t):
    """Inline code inside Korean text (Courier has no Hangul, so ASCII only)."""
    return f'<font face="Courier" size="8.6">{escape(t)}</font>'


def flatten(items):
    out = []
    for f in items:
        out.extend(flatten(f._content) if isinstance(f, KeepTogether) else [f])
    return out


def table(rows, widths, header=True, code_cols=()):
    data = []
    for r, row in enumerate(rows):
        out = []
        for c, x in enumerate(row):
            if not isinstance(x, str):
                out.append(x)
            elif c in code_cols and not (header and r == 0):
                out.append(Paragraph(escape(x), cell_code))
            else:
                out.append(P(x, cell_h if (header and r == 0) else cell_s))
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


def code(text):
    t = Table([[Preformatted(text, code_s)]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CODE_BG), ("BOX", (0, 0), (-1, -1), 0.5, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return KeepTogether([t, Spacer(1, 6)])


def annotated(pairs, code_w=96 * mm):
    """Code on the left, a Korean label pointing at it on the right."""
    rows, styles = [], [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (0, -1), CODE_BG),
        ("LINEBEFORE", (0, 0), (0, -1), 2, colors.HexColor(ACCENT)),
        ("LEFTPADDING", (0, 0), (0, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (1, 0), (1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
    ]
    for i, (line, label) in enumerate(pairs):
        left = Paragraph(escape(line).replace("  ", "&nbsp;&nbsp;") or "&nbsp;", anno_code)
        right = Paragraph(accent(f"&#8592; {label}") if label else "", anno_label)
        rows.append([left, right])
        if label:
            styles.append(("BACKGROUND", (1, i), (1, i), colors.HexColor("#f7f9fc")))
    t = Table(rows, colWidths=[code_w, CONTENT_W - code_w])
    t.setStyle(TableStyle(styles))
    return KeepTogether([t, Spacer(1, 8)])


def callout(kind, title, paras):
    bg, bar, label = {
        "warn": (WARN_BG, WARN_BAR, "주의"),
        "rule": (RULE_BG, RULE_BAR, "규칙"),
        "out": (OUT_BG, OUT_BAR, "실행 결과"),
    }[kind]
    inner = [P(f'<font color="{bar.hexval().replace("0x", "#")}">{label}</font> · {title}', box_title)]
    for p in paras:
        if isinstance(p, str):
            inner.append(P(p, box_body))
        elif isinstance(p, KeepTogether):
            inner.extend(flatten(p._content))
        else:
            inner.append(p)
    t = Table([[inner]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LINEBEFORE", (0, 0), (0, -1), 3, bar),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return KeepTogether([Spacer(1, 3), t, Spacer(1, 8)])


def section(title, subtitle, *following):
    return KeepTogether([P(title, part_s), P(subtitle, part_sub),
                         HRFlowable(width="100%", thickness=0.6, color=LINE, spaceAfter=4),
                         *flatten(following)])


S = []

S.append(P("파이썬 클래스의 구조", title_s))
S.append(P("구성요소를 하나씩 — 선언, 클래스 변수, 인스턴스 변수, 메서드, 던더 메서드까지 · 2026-09-22", sub_s))
S.append(HRFlowable(width="100%", thickness=0.8, color=LINE, spaceAfter=12))
S.append(P(
    "클래스는 <b>같은 종류의 데이터와, 그 데이터를 다루는 함수를 한 덩어리로 묶는 장치</b>다. "
    "이 자료는 예제 클래스 하나를 끝까지 따라가며 구성요소를 하나씩 뜯어본다. "
    "문서에 적힌 실행 결과는 모두 직접 돌려서 확인한 값이다."))

# ------------------------------------------------------------------ 0
S.append(section(
    "0. 이 자료가 쓰는 예제", "어휘(단어 목록)를 담는 작은 클래스 — 구성요소를 모두 한 번씩 쓴다",
    code('''class Vocabulary:
    """A small vocabulary: a list of words."""
    UNKNOWN = "<|unk|>"
    count = 0

    def __init__(self, words):
        self.words = list(words)
        self._index = {w: i for i, w in enumerate(self.words)}
        Vocabulary.count += 1

    def __len__(self):
        return len(self.words)

    def __getitem__(self, idx):
        return self.words[idx]

    def __repr__(self):
        return f"Vocabulary(size={len(self)})"

    def id_of(self, word):
        return self._index.get(word, -1)

    @property
    def size(self):
        return len(self.words)

    @classmethod
    def from_text(cls, text):
        return cls(sorted(set(text.split())))

    @staticmethod
    def normalize(word):
        return word.strip().lower()''')))

S.append(P("쓰는 모습과 실행 결과는 이렇다.", small))
S.append(code('''a = Vocabulary(["cat", "sat", "mat"])
b = Vocabulary.from_text("the cat sat on the mat")

repr(a)            ->  Vocabulary(size=3)
repr(b)            ->  Vocabulary(size=5)
len(a)             ->  3
a[0]               ->  cat
a.id_of("sat")     ->  1
a.id_of("dog")     ->  -1
a.size             ->  3
Vocabulary.normalize("  Cat ")  ->  cat
Vocabulary.count   ->  2'''))

# ------------------------------------------------------------------ 1
S.append(section(
    "1. 구조 한눈에 보기", "같은 코드에 이름표를 붙였다. 각 항목은 2부에서 하나씩 설명한다",
    annotated([
        ("class Vocabulary:", "클래스 선언 — 새 종류(타입)를 만든다"),
        ('    """A small vocabulary: ..."""', "독스트링 — 이 클래스의 설명"),
        ("", ""),
        ('    UNKNOWN = "<|unk|>"', "클래스 변수 — 모든 인스턴스가 공유"),
        ("    count = 0", "클래스 변수 — 만들어진 개수를 센다"),
        ("", ""),
        ("    def __init__(self, words):", "초기화 메서드 — 인스턴스를 만들 때 한 번 실행"),
        ("        self.words = list(words)", "인스턴스 변수 — 인스턴스마다 따로 가진다"),
        ("        self._index = {...}", "인스턴스 변수 — 앞의 _ 는 내부용이라는 표시"),
        ("        Vocabulary.count += 1", "클래스 변수 갱신 — 클래스 이름으로 접근"),
        ("", ""),
        ("    def __len__(self):", "던더 메서드 — len(a)가 이것을 부른다"),
        ("    def __getitem__(self, idx):", "던더 메서드 — a[0]이 이것을 부른다"),
        ("    def __repr__(self):", "던더 메서드 — 화면에 찍히는 모습"),
        ("", ""),
        ("    def id_of(self, word):", "인스턴스 메서드 — self로 자기 데이터를 쓴다"),
        ("", ""),
        ("    @property", "데코레이터 — 아래 메서드의 성격을 바꾼다"),
        ("    def size(self):", "프로퍼티 — 괄호 없이 a.size로 쓴다"),
        ("", ""),
        ("    @classmethod", ""),
        ("    def from_text(cls, text):", "클래스 메서드 — 첫 인자가 cls(클래스 자신)"),
        ("", ""),
        ("    @staticmethod", ""),
        ("    def normalize(word):", "정적 메서드 — self도 cls도 받지 않는다"),
    ])))

S.append(callout("rule", "들여쓰기가 소속을 정한다", [
    (f"{C('class')} 줄 아래로 들여쓴 것이 모두 이 클래스의 내용이다. 들여쓰기를 한 칸 잘못하면 "
    "메서드가 클래스 밖으로 빠져나가 <b>문법 오류 없이 다른 뜻</b>이 된다.")]))

# ------------------------------------------------------------------ 2
S.append(section("2. 구성요소 하나씩", "각 항목: 무엇인가 · 어떻게 쓰나 · 주의할 점"))

S.append(P("2-1. 클래스 선언", h2))
S.append(code("class Vocabulary:              # name only\nclass GPTDatasetV1(Dataset):   # inherits from Dataset"))
S.append(P(
    f"{C('class')} 뒤에 이름을 쓰면 <b>새로운 종류(타입)</b>가 하나 생긴다. 관례상 이름은 대문자로 시작하고 "
    "단어를 붙여 쓴다(Vocabulary, GPTDatasetV1). 괄호 안에 다른 클래스를 적으면 그 클래스의 기능을 물려받는다 — "
    "5부에서 다룬다."))
S.append(P(
    f"중요한 구분: <b>클래스는 설계도이고, 인스턴스는 그 설계도로 만든 실제 물건</b>이다. "
    f"{C('Vocabulary')}는 설계도, {C('a = Vocabulary([...])')}의 {C('a')}가 물건이다. 설계도 하나로 물건을 "
    "여러 개 만들 수 있고, 각 물건은 자기 데이터를 따로 가진다."))

S.append(P("2-2. 독스트링", h2))
S.append(P(
    f"클래스나 함수의 첫 줄에 오는 문자열이다. 주석({C('#')})과 달리 실행 후에도 남아 있어서 "
    f"{C('help(Vocabulary)')}나 {C('Vocabulary.__doc__')}로 꺼내 볼 수 있다. 편집기가 이름 위에 마우스를 "
    "올렸을 때 보여주는 설명도 이것이다."))

S.append(P("2-3. 클래스 변수 (class variable)", h2))
S.append(P(
    f"{C('class')} 바로 아래, 메서드 밖에 적은 변수다. <b>클래스 하나에 딱 하나만 존재하고, 모든 인스턴스가 "
    "같은 것을 본다.</b> 어휘의 특수 토큰처럼 인스턴스마다 달라질 이유가 없는 값, 또는 개수 세기처럼 전체를 "
    "가로질러 공유할 값에 쓴다."))
S.append(callout("out", "공유된다는 것의 의미", [
    code("a = Vocabulary([...]);  b = Vocabulary.from_text(...)\n\n"
         "Vocabulary.count  ->  2\n"
         "a.count           ->  2       # read via an instance\n"
         "b.count           ->  2"),
    (f"인스턴스 두 개를 만들었더니 {C('count')}가 2다. {C('__init__')} 안에서 "
    f"{C('Vocabulary.count += 1')}로 <b>클래스 쪽 값</b>을 올렸기 때문이다.")]))

S.append(P("2-4. __init__ 과 self", h2))
S.append(P(
    f"{C('__init__')}은 <b>인스턴스를 만들 때 자동으로 한 번 실행되는 준비 작업</b>이다. "
    f"{C(MK_CALL)}라고 쓰면 파이썬이 빈 인스턴스를 만든 뒤 "
    f"{C(MK_INIT)}처럼 부른다."))
S.append(P(
    f"첫 번째 매개변수 {C('self')}가 바로 <b>지금 만들어지는(또는 지금 다뤄지는) 그 인스턴스</b>다. "
    f"이름이 self인 것은 관례일 뿐 문법은 아니지만, 바꾸지 않는 편이 좋다. 호출할 때 self 자리에 아무것도 "
    "넣지 않는데도 채워지는 이유는, 파이썬이 <b>점 앞의 객체를 자동으로 첫 인자로 넘기기</b> 때문이다."))
S.append(code("a.id_of(\"sat\")             # what we write\nVocabulary.id_of(a, \"sat\")  # what Python actually does (same result: 1)"))
S.append(callout("warn", "self를 빠뜨리면", [
    code('class NoSelf:\n    def method():      # no self\n        return "ok"\n\n'
         'NoSelf().method()\n'
         '->  TypeError: NoSelf.method() takes 0 positional arguments but 1 was given'),
    ("에러 메시지가 이상해 보이지만 정확하다. 우리는 인자를 0개 넘겼는데 파이썬이 인스턴스를 하나 자동으로 "
    "넣었으니, 받는 쪽은 1개를 받은 셈이다.")]))

S.append(P("2-5. 인스턴스 변수 (instance variable)", h2))
S.append(P(
    f"{C('self.name = value')} 형태로 만든다. <b>인스턴스마다 따로 존재한다.</b> a의 words와 b의 words는 "
    "이름만 같고 완전히 다른 목록이다(확인: 두 목록은 서로 다른 객체다)."))
S.append(P(
    f"{C('__init__')} 안에서 만든 인스턴스 변수는 그 함수가 끝난 뒤에도 남는다. {C('self.')}가 붙었기 "
    f"때문이다. 반대로 {C('self.')} 없이 만든 변수는 그 메서드가 끝나면 사라지는 <b>임시 변수</b>다."))
S.append(callout("out", "인스턴스가 실제로 가진 것만 보기", [
    code('a.__dict__.keys()            ->  [\'words\', \'_index\']\n'
         '"UNKNOWN" in a.__dict__      ->  False\n'
         '"UNKNOWN" in Vocabulary.__dict__  ->  True'),
    (f"{C('a.__dict__')}는 그 인스턴스가 자기 것으로 들고 있는 값의 목록이다. 클래스 변수 UNKNOWN은 "
    "여기에 없다 — 클래스 쪽에 있기 때문이다. 4부의 '찾는 순서'로 이어진다.")]))

S.append(P("2-6. 인스턴스 메서드", h2))
S.append(P(
    f"첫 인자로 {C('self')}를 받는 보통의 메서드다. 자기 인스턴스의 데이터를 읽거나 바꾼다. "
    f"예제의 {C('id_of')}는 {C('self._index')}를 들여다본다."))
S.append(callout("rule", "받은 값을 쓰고, 바깥을 훔쳐보지 않는다", [
    ("메서드가 필요한 값은 <b>매개변수나 self를 통해</b> 들어와야 한다. 함수 바깥(모듈 전역)에 있는 변수를 "
    "직접 쓰면 같은 파일 안에서는 우연히 돌아가지만, 그 클래스를 다른 파일로 옮기는 순간 죽는다. "
    "세션 03에서 SimpleTokenizerV1이 정확히 이 문제였다.")]))

S.append(P("2-7. 클래스 메서드 (@classmethod)", h2))
S.append(P(
    f"첫 인자가 {C('self')}가 아니라 {C('cls')}(클래스 자신)다. 인스턴스가 없어도 부를 수 있다. "
    "가장 흔한 쓰임은 <b>다른 방식으로 인스턴스를 만드는 또 하나의 생성 통로</b>다."))
S.append(code('@classmethod\ndef from_text(cls, text):\n    return cls(sorted(set(text.split())))\n\n'
              'b = Vocabulary.from_text("the cat sat on the mat")   ->  Vocabulary(size=5)'))
S.append(P(
    f"{C('cls(...)')}는 {C('Vocabulary(...)')}를 부르는 것과 같다. 클래스 이름을 직접 쓰지 않고 cls를 쓰는 "
    "이유는, 나중에 이 클래스를 물려받은 자식 클래스에서 불러도 <b>자식 클래스의 인스턴스</b>가 만들어지기 "
    "때문이다."))

S.append(P("2-8. 정적 메서드 (@staticmethod)", h2))
S.append(P(
    f"{C('self')}도 {C('cls')}도 받지 않는다. 인스턴스나 클래스의 데이터가 전혀 필요 없지만 "
    "<b>내용상 이 클래스와 함께 두는 게 자연스러운</b> 함수에 쓴다. 예제의 normalize는 단어 하나를 "
    "다듬을 뿐 어휘를 건드리지 않는다."))
S.append(table([
    ["", "첫 인자", "무엇에 접근하나", "부르는 방법"],
    ["인스턴스 메서드", "self", "그 인스턴스의 데이터 + 클래스 변수", "a.id_of(\"sat\")"],
    ["클래스 메서드", "cls", "클래스 변수만", "Vocabulary.from_text(...)"],
    ["정적 메서드", "없음", "둘 다 아님 (받은 인자만)", "Vocabulary.normalize(...)"],
], [32 * mm, 18 * mm, 62 * mm, 58 * mm]))

S.append(P("2-9. 프로퍼티 (@property)", h2))
S.append(P(
    f"메서드인데 <b>괄호 없이 변수처럼</b> 쓰게 만든다. {C('a.size()')}가 아니라 {C('a.size')}다. "
    "겉보기는 변수, 실제로는 계산이다. 값이 다른 값에서 자동으로 따라 나올 때 쓴다 — size는 words의 길이라서 "
    "따로 저장해 두면 words가 바뀔 때 어긋난다."))

S.append(P("2-10. 던더 메서드 (__이름__)", h2))
S.append(P(
    "앞뒤에 밑줄 두 개가 붙은 특별한 이름들이다(dunder = double underscore). 직접 부르지 않고, "
    "<b>파이썬 문법이 대신 불러 준다.</b>"))
S.append(table([
    ["던더 메서드", "이것이 불리는 순간", "예제에서"],
    ["__init__", "인스턴스를 만들 때", "Vocabulary([...])"],
    ["__len__", "len(객체)를 쓸 때", "len(a) -> 3"],
    ["__getitem__", "객체[인덱스]를 쓸 때", "a[0] -> cat"],
    ["__repr__", "화면에 객체를 찍을 때", "Vocabulary(size=3)"],
], [34 * mm, 62 * mm, 74 * mm], code_cols=(0,)))
S.append(P(
    f"{C('__repr__')}이 없으면 객체를 출력했을 때 {C('<__main__.Vocabulary object at 0x10a...>')}처럼 나온다. "
    "디버깅할 때 무엇이 들어 있는지 한눈에 보이도록 적어두면 편하다."))

S.append(P("2-11. 이름 앞의 밑줄 — _x 와 __x", h2))
S.append(table([
    ["표기", "뜻", "파이썬이 강제하나"],
    ["name", "공개 — 밖에서 써도 되는 것", "—"],
    ["_name", "내부용이라는 <b>약속</b> — 밖에서 건드리지 말라는 표시", "아니오"],
    ["__name", "이름이 <b>_클래스명__name</b>으로 바뀐다(name mangling)", "예"],
], [30 * mm, 102 * mm, 38 * mm], code_cols=(0,)))
S.append(callout("out", "__가 붙으면 이름이 실제로 바뀐다", [
    code('class Secret:\n    def __init__(self):\n        self._soft = 1\n        self.__hard = 2\n\n'
         "sec.__dict__.keys()   ->  ['_soft', '_Secret__hard']\n"
         "sec.__hard            ->  AttributeError: 'Secret' object has no attribute '__hard'\n"
         "sec._Secret__hard     ->  2"),
    ("감추려는 장치가 아니라 <b>자식 클래스에서 같은 이름을 써도 충돌하지 않게</b> 하려는 장치다. "
    f"보통은 {C('_')} 하나로 충분하다.")]))

# ------------------------------------------------------------------ 3
S.append(section(
    "3. 클래스 변수 vs 인스턴스 변수", "가장 헷갈리는 지점 — 하나는 공유, 하나는 개별",
    table([
        ["", "클래스 변수", "인스턴스 변수"],
        ["어디에 적나", "class 아래, 메서드 밖", "메서드 안, self. 을 붙여서"],
        ["몇 개 존재하나", "클래스당 1개", "인스턴스당 1개"],
        ["누가 보나", "모든 인스턴스가 같은 값을 본다", "그 인스턴스만"],
        ["예제에서", "UNKNOWN, count", "words, _index"],
    ], [28 * mm, 70 * mm, 72 * mm])))
S.append(callout("warn", "읽기는 공유, 쓰기는 개별 — 가장 혼란스러운 규칙", [
    code('a.UNKNOWN = "<|mine|>"     # creates a private copy on a\n\n'
         'a.UNKNOWN           ->  <|mine|>\n'
         'b.UNKNOWN           ->  <|unk|>\n'
         'Vocabulary.UNKNOWN  ->  <|unk|>\n'
         "a.__dict__.keys()   ->  ['words', '_index', 'UNKNOWN']"),
    (f"{C('a.UNKNOWN')}에 값을 넣는 순간 클래스 쪽 값이 바뀌는 게 아니라 <b>a의 개인 값이 새로 생긴다.</b> "
    f"그래서 b와 클래스는 그대로다. 클래스 변수를 정말 바꾸려면 {C('Vocabulary.UNKNOWN = ...')}처럼 "
    "클래스 이름으로 써야 한다.")]))
S.append(callout("warn", "가변 클래스 변수 — 초보자가 가장 많이 걸리는 함정", [
    code('class Bad:\n    items = []                     # class variable - shared!\n    def add(self, x): self.items.append(x)\n\n'
         'class Good:\n    def __init__(self): self.items = []   # instance variable\n    def add(self, x): self.items.append(x)\n\n'
         'p, q = Bad(), Bad();   p.add(1); q.add(2)\n'
         'r, s = Good(), Good(); r.add(1); s.add(2)\n\n'
         'p.items, q.items  ->  [1, 2] [1, 2]      # one shared list\n'
         'r.items, s.items  ->  [1] [2]            # separate lists'),
    (f"{C('self.items.append(x)')}는 <b>값을 넣는 게 아니라 이미 있는 리스트를 고치는 것</b>이라, 위의 "
    "'쓰기는 개별' 규칙이 적용되지 않는다. 클래스 쪽 리스트가 그대로 수정된다."),
    "<b>규칙: 인스턴스마다 달라져야 하는 값, 특히 리스트·딕셔너리는 반드시 __init__ 안에서 만든다.</b>"]))

# ------------------------------------------------------------------ 4
S.append(section(
    "4. 속성을 찾는 순서", "a.무엇 이라고 썼을 때 파이썬이 어디를 뒤지는가",
    table([
        ["순서", "어디를 보나", "예"],
        ["1", "인스턴스 자신 (a.__dict__)", "words, _index"],
        ["2", "클래스 (Vocabulary.__dict__)", "UNKNOWN, count, 모든 메서드"],
        ["3", "부모 클래스들 — MRO 순서대로", "Dataset, object"],
        ["없으면", "AttributeError", "—"],
    ], [18 * mm, 78 * mm, 74 * mm])))
S.append(P(
    f"메서드도 이 규칙으로 찾는다. {C('a.id_of')}는 인스턴스에 없으니 클래스에서 찾아 쓰는 것이다. "
    f"찾는 순서는 {C('Vocabulary.__mro__')}로 볼 수 있다 — 예제는 "
    f"{C('[Vocabulary, object]')}이고, 파이썬의 모든 클래스는 결국 object를 물려받는다."))
S.append(callout("warn", "세션 04에서 난 에러가 바로 이 규칙이다", [
    (f"{C('self.input_idss[idx]')}라고 쳤을 때 1번(인스턴스)에도 2번(클래스)에도 그런 이름이 없어서 "
    f"{C(ERR_ATTR)}가 났다. "
    "s 한 글자 때문에 세 군데를 다 뒤지고도 못 찾은 것이다.")]))

# ------------------------------------------------------------------ 5
S.append(section(
    "5. 상속과 super()", "이미 있는 클래스의 기능을 물려받아 필요한 곳만 바꾼다",
    code('''class Base:
    def __init__(self, n):
        self.n = n
    def hello(self):
        return f"Base {self.n}"

class Child(Base):                # inherits from Base
    def __init__(self, n, extra):
        super().__init__(n)       # run the parent setup first
        self.extra = extra        # then add my own
    def hello(self):              # overrides the parent method
        return f"Child {self.n}/{self.extra}"''')))
S.append(callout("out", "확인한 결과", [
    code("c = Child(1, \"x\")\n\n"
         "c.hello()        ->  Child 1/x\n"
         "c.__dict__       ->  {'n': 1, 'extra': 'x'}\n"
         "isinstance(c, Base)  ->  True\n"
         "Child.__mro__    ->  [Child, Base, object]"),
    (f"{C('n')}은 부모의 {C('__init__')}이 넣어준 것이다. {C('super().__init__(n)')}을 빠뜨리면 그 줄이 "
    "실행되지 않아 나중에 n을 쓸 때 AttributeError가 난다.")]))
S.append(P(
    f"<b>왜 상속하나:</b> 부모가 요구하는 약속을 지키면 부모를 받아들이는 도구가 내 클래스도 받아준다. "
    f"{C('GPTDatasetV1(Dataset)')}이 그 예다 — DataLoader는 Dataset이기를 요구하고, 그 대가로 배치 묶기, "
    "섞기, 버리기를 대신 해준다."))

# ------------------------------------------------------------------ 6
S.append(section(
    "6. 인스턴스가 만들어지는 순서", "a = Vocabulary([...]) 한 줄에서 실제로 일어나는 일",
    table([
        ["순서", "무슨 일", "메서드"],
        ["1", "빈 인스턴스를 만든다 (메모리 확보)", "__new__ — 보통 건드리지 않는다"],
        ["2", "그 인스턴스를 self로 받아 값을 채운다", "__init__ — 우리가 쓰는 것"],
        ["3", "완성된 인스턴스가 a에 담긴다", "—"],
    ], [18 * mm, 86 * mm, 66 * mm])))
S.append(callout("out", "직접 확인", [
    code('class Trace:\n    def __new__(cls, *args):\n        print("__new__ first"); return super().__new__(cls)\n'
         '    def __init__(self, v):\n        print("__init__ second"); self.v = v\n\n'
         "Trace(3)\n->  __new__ first\n->  __init__ second"),
    (f"{C('__init__')}은 이름과 달리 '만드는' 메서드가 아니라 <b>이미 만들어진 것을 채우는</b> 메서드다. "
    "그래서 아무것도 return 하지 않는다.")]))

# ------------------------------------------------------------------ 7
S.append(section(
    "7. 내 코드에서 보기 — GPTDatasetV1", "2.6절에서 직접 친 클래스를 같은 이름표로 읽으면",
    annotated([
        ("class GPTDatasetV1(Dataset):", "선언 + 상속 — Dataset의 약속을 지키겠다"),
        ("    def __init__(self, txt, tokenizer,", "초기화 — 데이터셋을 만들 때 한 번"),
        ("                 max_length, stride):", "매개변수 넷 — 바깥에서 받아 온다"),
        ("        self.input_ids = []", "인스턴스 변수"),
        ("        self.target_ids = []", "인스턴스 변수"),
        ("        token_ids = tokenizer.encode(txt)", "임시 변수 — self. 없으니 이 메서드 안에서만 산다"),
        ("        for i in range(...):", ""),
        ("            self.input_ids.append(...)", "인스턴스 변수에 쌓는다"),
        ("", ""),
        ("    def __len__(self):", "던더 — DataLoader가 배치 수 계산에 쓴다"),
        ("        return len(self.input_ids)", ""),
        ("", ""),
        ("    def __getitem__(self, idx):", "던더 — DataLoader가 배치마다 8번 부른다"),
        ("        return self.input_ids[idx], \\", ""),
        ("               self.target_ids[idx]", "튜플 하나로 (입력, 타깃)을 돌려준다"),
    ])))
S.append(P(
    "<b>이 클래스에는 클래스 변수가 없다.</b> 윈도우 목록은 데이터셋마다 달라야 하므로 전부 인스턴스 변수다. "
    "3부의 함정(가변 클래스 변수)을 피한 구조이기도 하다 — 만약 input_ids를 클래스 변수로 뒀다면 "
    "데이터셋 두 개가 같은 목록에 윈도우를 쌓았을 것이다."))

# ------------------------------------------------------------------ 8
S.append(section(
    "8. 자주 나는 실수", "세션 03·04·05에서 실제로 겪은 것들",
    table([
        ["증상", "원인", "고치는 법"],
        ["TypeError: takes 0 positional arguments", "메서드 첫 인자 self를 빠뜨림", "def method(self):"],
        ["AttributeError: no attribute 'xxx'", "self.이름 오타, 또는 __init__에서 만들지 않음",
         "__init__에 있는 이름과 대조"],
        ["NameError: name 'vocab' is not defined", "매개변수로 받지 않고 바깥 변수를 씀",
         "필요한 값은 인자나 self로 받는다"],
        ["인스턴스 두 개가 같은 리스트를 공유", "리스트를 클래스 변수로 둠", "__init__ 안에서 만든다"],
        ["부모의 값이 없다고 나옴", "super().__init__() 호출 누락", "자식 __init__ 첫 줄에 추가"],
    ], [58 * mm, 62 * mm, 50 * mm])))

S.append(Spacer(1, 8))
S.append(KeepTogether([
    HRFlowable(width="55%", thickness=0.7, color=LINE, hAlign="CENTER", spaceAfter=8),
    P("클래스는 설계도, 인스턴스는 물건. self는 &ldquo;지금 다루는 그 물건&rdquo;. "
      "클래스 변수는 설계도에 적힌 값이고, 인스턴스 변수는 물건마다 따로 가진 값이다.", take_s),
]))

# ------------------------------------------------------------------ 9
S.append(section(
    "9. 확인해볼 문제", "답은 마지막 쪽 — 먼저 적어보고 직접 실행해서 맞춰보기",
    *[P(q) for q in [
        "① Vocabulary 인스턴스를 세 개 만들면 Vocabulary.count는 얼마인가?",
        "② a.words.append(\"dog\")를 하면 len(a)와 a.size는 각각 어떻게 되는가? 왜 그런가?",
        "③ Vocabulary.UNKNOWN = \"???\" 를 실행하면 이미 만들어 둔 a.UNKNOWN은 어떻게 되는가?",
        "④ from_text를 @staticmethod로 바꾸면 무엇이 문제가 되는가?",
        "⑤ __len__을 지우면 len(a)는 어떻게 되는가?",
        "⑥ GPTDatasetV1에서 self.input_ids = [] 두 줄을 클래스 변수로 옮기면 무슨 일이 생기는가?",
    ]]))

S.append(PageBreak())
S.append(P("답", part_s))
S.append(HRFlowable(width="100%", thickness=0.6, color=LINE, spaceAfter=6))
S.append(table([
    ["문제", "답"],
    ["①", "3. 클래스 변수는 클래스당 하나뿐이고 __init__이 실행될 때마다 1씩 오른다."],
    ["②", ("둘 다 4. size는 저장된 값이 아니라 len(self.words)를 그때그때 계산하는 프로퍼티라서 "
          "words가 바뀌면 자동으로 따라온다. 만약 __init__에서 self.size = len(words)로 저장했다면 "
          "3으로 남아 어긋났을 것이다.")],
    ["③", ("a.UNKNOWN도 \"???\"로 바뀐다 — a가 자기 UNKNOWN을 따로 가진 적이 없다면. 찾는 순서 "
          "1번(인스턴스)에 없으니 2번(클래스)에서 읽어오기 때문이다.")],
    ["④", ("정적 메서드는 cls를 받지 않아서 cls(...)로 인스턴스를 만들 수 없다. Vocabulary(...)라고 "
          "이름을 직접 써야 하고, 그러면 이 클래스를 물려받은 자식에서 불러도 항상 Vocabulary가 만들어진다.")],
    ["⑤", ("TypeError: object of type 'Vocabulary' has no len(). len()은 __len__을 부르는 문법이라, "
          "그 메서드가 없으면 길이를 구할 방법이 없다.")],
    ["⑥", ("모든 데이터셋이 같은 리스트를 공유하게 되어, 두 번째 데이터셋을 만들면 첫 번째의 윈도우 위에 "
          "계속 쌓인다. 에러는 나지 않고 개수만 조용히 틀린다 — 3부의 함정과 같은 구조다.")],
], [16 * mm, 154 * mm]))
S.append(Spacer(1, 10))
S.append(P("이 자료의 모든 실행 결과는 프로젝트 가상환경에서 직접 실행해 확인했다. "
           "생성 스크립트: tools/pdf/python_class_structure.py", cap))


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont(FONT, 8)
    canvas.setFillColor(GREY)
    canvas.drawString(20 * mm, 10 * mm, "파이썬 클래스의 구조")
    canvas.drawRightString(A4[0] - 20 * mm, 10 * mm, str(doc.page))
    canvas.restoreState()


doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                        topMargin=18 * mm, bottomMargin=18 * mm, title="파이썬 클래스의 구조")
doc.build(S, onFirstPage=footer, onLaterPages=footer)
print("wrote", OUT)
