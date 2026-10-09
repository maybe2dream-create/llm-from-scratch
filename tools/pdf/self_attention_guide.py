# /// script
# dependencies = ["reportlab"]
# ///
"""Self-attention conceptual guide -> docs/Self_Attention_Conceptual_Guide.pdf

Run from anywhere:  uv run tools/pdf/self_attention_guide.py

The source text was pasted from a chat and lost its markdown: section titles are
plain "N. Title" lines and every prose sentence sits on its own line with no blank
line between. normalize() turns that back into headings and one-line paragraphs
before rendering. Fenced code blocks survived intact.
"""
import re
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
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

REPO = Path(__file__).resolve().parents[2]
OUT = str(REPO / "docs" / "Self_Attention_Conceptual_Guide.pdf")

INK = colors.HexColor("#1a1a1a")
GREY = colors.HexColor("#5a5a5a")
LINE = colors.HexColor("#cfcfcf")
CODE_BG = colors.HexColor("#f4f5f7")
ACCENT = colors.HexColor("#2f4f76")
QUOTE_BG = colors.HexColor("#eef2f8")

CONTENT_W = 170 * mm

# The base-14 PDF fonts (Helvetica, Courier) only cover WinAnsi. Arrows, box-drawing,
# check marks, subscripts and circled digits all render as blank boxes, so map them
# to ASCII. Multi-character sequences first, so "<->" wins over the single arrows.
ASCII_MAP = [
    ("←→", "<->"), ("↔", "<->"),
    ("→", "->"), ("←", "<-"), ("↓", "v"), ("↑", "^"),
    ("┌", "+"), ("┐", "+"), ("└", "+"), ("┘", "+"),
    ("├", "+"), ("┤", "+"), ("┬", "+"), ("┴", "+"), ("┼", "+"),
    ("─", "-"), ("│", "|"), ("▼", "v"), ("▲", "^"), ("►", ">"),
    ("✓", "Y"), ("✗", "N"),
    ("₁", "1"), ("₂", "2"), ("₃", "3"), ("₄", "4"),
    ("①", "(1)"), ("②", "(2)"), ("③", "(3)"),
    ("④", "(4)"), ("⑤", "(5)"), ("⑥", "(6)"),
]


def to_ascii(text):
    for u, a in ASCII_MAP:
        text = text.replace(u, a)
    return text


title_s = ParagraphStyle("T", fontName="Helvetica-Bold", fontSize=22, leading=28, textColor=INK)
sub_s = ParagraphStyle("S", fontName="Helvetica-Oblique", fontSize=11, leading=16, textColor=GREY,
                       spaceAfter=12)
h1_s = ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=14.5, leading=19, spaceBefore=16,
                      spaceAfter=7, textColor=ACCENT, keepWithNext=1)
h3_s = ParagraphStyle("H3", fontName="Helvetica-Bold", fontSize=10.8, leading=15, spaceBefore=8,
                      spaceAfter=3, textColor=INK, keepWithNext=1)
body_s = ParagraphStyle("B", fontName="Helvetica", fontSize=10, leading=15.5, spaceAfter=6)
quote_s = ParagraphStyle("Q", fontName="Helvetica-BoldOblique", fontSize=10.3, leading=15.5,
                         leftIndent=10, textColor=colors.HexColor("#243b5c"),
                         backColor=QUOTE_BG, borderPadding=8, spaceBefore=3, spaceAfter=9)
bullet_s = ParagraphStyle("BL", fontName="Helvetica", fontSize=10, leading=14.5, leftIndent=14,
                          spaceAfter=2)
code_s = ParagraphStyle("CODE", fontName="Courier", fontSize=8.6, leading=11.8)
cap_s = ParagraphStyle("C", fontName="Helvetica-Oblique", fontSize=8.4, leading=12,
                       alignment=TA_CENTER, textColor=GREY, spaceBefore=10)


def inline(text):
    text = escape(text.strip())
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r'<font face="Courier" size="9.2" color="#2f4f76">\1</font>', text)
    return text


def P(text, style=body_s):
    return Paragraph(inline(text), style)


def codebox(text):
    # Preformatted draws text literally (no entity decoding), so it must not be escaped.
    t = Table([[Preformatted(text, code_s)]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CODE_BG), ("BOX", (0, 0), (-1, -1), 0.5, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return KeepTogether([t, Spacer(1, 6)])


# Short label lines that act as sub-headings inside a section.
SUBHEADINGS = {
    "Query", "Key", "Value",
    "Encoder-style self-attention", "GPT-style causal self-attention",
    "Self-attention", "Cross-attention",
}

# The core takeaway sentences; shown as highlighted call-outs.
KEY_LINES = {
    ("Self-attention allows every token to look at other tokens in the same sequence and decide "
    "which ones are relevant to understanding it."),
    "The same token is represented in three different roles for the purpose of attention.",
    ("A token's new representation is constructed by taking a weighted combination of information "
    "from other tokens."),
    "Attention is a learned information-routing mechanism.",
    "Self-attention is a learned information-routing system.",
    "A token can attend to itself and previous tokens, but not future tokens.",
    ("Self-attention is a mechanism that allows each token to dynamically gather relevant information "
    "from other tokens in the same sequence, producing a new context-aware representation of that "
    "token."),
    ("Query represents what a token is looking for, Key represents what each token can be matched on, "
    "and Value represents the information that each token contributes when it is considered relevant."),
    "Attention weights determine how much information to gather from each Value.",
}


def normalize(text):
    """Rebuild the lost markdown: headings, one paragraph per line, highlighted key lines."""
    out, in_code = [], False
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("```"):
            in_code = not in_code
            out.append(line)
            continue
        if in_code:
            out.append(line)
            continue
        if not s:
            continue
        if re.match(r"^\d+\.\s+\S", s) or s == "One particularly important insight for you":
            out += ["", "# " + s, ""]
        elif re.match(r"^\(\d\)\s", s) or s in SUBHEADINGS:
            out += ["", "### " + s, ""]
        elif s.startswith("* "):
            out.append(s)
        elif s in KEY_LINES:
            out += ["", "> " + s, ""]
        else:
            out += ["", s, ""]
    return "\n".join(out)


def parse_blocks(text):
    lines, blocks, buf, i = text.split("\n"), [], [], 0

    def flush():
        joined = " ".join(x.strip() for x in buf if x.strip())
        if joined:
            blocks.append(("para", joined))
        buf.clear()

    while i < len(lines):
        s = lines[i].strip()
        if s.startswith("```"):
            flush()
            i += 1
            code = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            blocks.append(("code", "\n".join(code)))
            continue
        if s.startswith("#"):
            flush()
            level = len(s) - len(s.lstrip("#"))
            blocks.append(("heading", level, s[level:].strip()))
        elif s.startswith("> "):
            flush()
            blocks.append(("quote", s[2:]))
        elif s.startswith("* "):
            flush()
            items = []
            while i < len(lines) and lines[i].strip().startswith("* "):
                items.append(lines[i].strip()[2:])
                i += 1
            blocks.append(("bullets", items))
            continue
        elif not s:
            flush()
        else:
            buf.append(s)
        i += 1
    flush()
    return blocks


def render(blocks):
    story = []
    for b in blocks:
        kind = b[0]
        if kind == "heading":
            _, level, text = b
            if level == 1:
                story.append(HRFlowable(width="100%", thickness=0.6, color=LINE, spaceBefore=6,
                                        spaceAfter=0))
                story.append(P(text, h1_s))
            else:
                story.append(P(text, h3_s))
        elif kind == "para":
            story.append(P(b[1]))
        elif kind == "quote":
            story.append(P(b[1], quote_s))
        elif kind == "code":
            # keepWithNext does not hold a heading to a KeepTogether, so pull a
            # directly preceding heading into the code box's group.
            box = codebox(b[1])
            # The heading is re-made without keepWithNext, which otherwise nests
            # KeepTogethers and pushes every such pair onto a fresh page.
            if story and getattr(story[-1], "style", None) in (h1_s, h3_s):
                head = story.pop()
                style = ParagraphStyle("nk", parent=head.style, keepWithNext=0)
                box = KeepTogether([Paragraph(head.text, style), *box._content])
            story.append(box)
        elif kind == "bullets":
            story += [P("• " + item, bullet_s) for item in b[1]]
            story.append(Spacer(1, 4))
    return story


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GREY)
    canvas.drawString(20 * mm, 10 * mm, "Self-Attention: A Conceptual Guide")
    canvas.drawRightString(A4[0] - 20 * mm, 10 * mm, str(doc.page))
    canvas.restoreState()


RAW_TEXT = r'''
Since you already understand the embedding layer and have a Linear Algebra background, we can now move to the heart of the Transformer: self-attention.
I'll deliberately keep the mathematics in the background. Instead, we'll focus on what each step means, why it exists, and what information is flowing through the mechanism.
The single most important idea is:
Self-attention allows every token to look at other tokens in the same sequence and decide which ones are relevant to understanding it.
Let's build that idea from the ground up.
1. Why do we need self-attention?
Consider:
The cat sat on the mat because it was tired.
What does "it" refer to?
Most likely:
the cat
To understand this sentence, the model needs to connect:

```text
it
│
└──────────────► cat
```

Now consider:
The cat sat on the mat because it was comfortable.
Here, "it" might refer to:
the mat
The meaning of a word depends on the other words around it.
That's the fundamental problem self-attention addresses.
2. The key idea
Imagine we have:

```text
The cat drank milk
```

Initially, after tokenization and embedding, we have something like:

```text
The  → vector
cat  → vector
drank → vector
milk → vector
```

The embedding gives each token its initial numerical representation.
But the embedding of `cat` by itself doesn't fully represent:
"cat as the subject of drank in this particular sentence."
Self-attention allows the representation of `cat` to be influenced by:

```text
The
drank
milk
```

So conceptually:

```text
Before attention:

cat
 ↓
initial representation


After attention:

cat
 ↓
looks at other tokens
 ↓
"The"     relevant?
"drank"   relevant?
"milk"    relevant?
 ↓
combines useful information
 ↓
context-aware representation of "cat"
```

That's the central idea.
3. The name "self-attention"
Why is it called self-attention?
Because the sequence attends to itself.
Suppose:

```text
The cat drank milk
```

There isn't a separate database of information.
The information being examined comes from the same sequence:

```text
The
cat
drank
milk
 ↑
 └── the sequence attends to itself
```

Compare that with some other attention mechanisms used in encoder-decoder architectures, where one sequence can attend to another sequence.
Here:
Tokens in a sequence attend to other tokens in that same sequence.
Hence:
self-attention.
4. The overall process
Let's first see the whole mechanism without worrying about the details.

```text
              Input tokens
                   ↓
             Token embeddings
                   ↓
          ┌──────────────────┐
          │                  │
          │  Self-Attention  │
          │                  │
          └──────────────────┘
                   ↓
       Context-aware representations
```

Inside self-attention:

```text
Input representations
        ↓
   Create Q, K, V
        ↓
Compare Q with K
        ↓
Determine relevance
        ↓
Normalize relevance
        ↓
Use relevance to combine V
        ↓
New representations
```

Those six steps are the heart of the mechanism.
Now let's examine each one carefully.
5. Step 1 — Start with token representations
Suppose our sentence is:
The cat drank milk
After tokenization and embedding:

```text
The   → vector
cat   → vector
drank → vector
milk  → vector
```

Let's call these representations:

```text
X₁ = representation of "The"
X₂ = representation of "cat"
X₃ = representation of "drank"
X₄ = representation of "milk"
```

At this point, these vectors contain the information produced by the embedding layer and positional mechanism.
But we want them to become context-aware.
That's what attention does.
6. Step 2 — Every token creates three different "views"
This is probably the most important conceptual step to understand.
For every token, the Transformer creates three representations:

```text
Query
Key
Value
```

or:

```text
Q
K
V
```

Don't think of these as three completely different pieces of information.
Instead, think:
The same token is represented in three different roles for the purpose of attention.
Those roles are:
Query
"What information am I looking for?"
Key
"What kind of information do I contain?"
Value
"What information should I provide if you decide I'm relevant?"
This is the conceptual heart of Q, K, and V.
7. A real-world analogy: a library
Imagine you're in a huge library.
You have a question:
"Where can I find information about cats?"
Your query is essentially:
"I'm looking for information about cats."
Every book has a key describing what kind of information it contains:

```text
Book A → physics
Book B → cats
Book C → cooking
Book D → history
```

You compare your query with the keys.
You discover:

```text
Book A → low relevance
Book B → high relevance
Book C → low relevance
Book D → low relevance
```

Then you actually retrieve information from the relevant book.
That's analogous to:

```text
Query
   ↓
compare with Keys
   ↓
determine relevance
   ↓
retrieve Values
```

That's essentially what attention does.
8. Query — "What am I looking for?"
Let's focus on one token:
cat
The query associated with `cat` represents something like:
"Given my current context, what information would be useful to me?"
It's not literally an English question.
It's a learned numerical representation.
But conceptually, you can think of it as a question vector.

```text
cat
 ↓
Query
 ↓
"What information should I pay attention to?"
```

9. Key — "What do I contain?"
Now consider the other tokens.

```text
The
cat
drank
milk
```

Each one has a key.
Conceptually:

```text
The    → "Here is information about..."
cat    → "Here is information about..."
drank  → "Here is information about..."
milk   → "Here is information about..."
```

Again, these aren't literal descriptions.
They're learned numerical representations that allow the model to determine relevance.
10. Value — "What information can I contribute?"
Each token also has a value.
The value represents the information that can actually be passed to another token if attention considers it relevant.
So:

```text
Token
 ├── Query → what am I looking for?
 ├── Key   → what kind of information do I contain?
 └── Value → what information can I provide?
```

This is an extremely useful mental model.
11. Why three representations?
You might reasonably ask:
Why can't we just use the token vector directly?
Because attention has three different conceptual jobs:

```text
Query → decide what I'm interested in
Key   → advertise what I contain
Value → provide the actual information
```

Separating these roles gives the Transformer much more flexibility.
It can learn:
"When I'm looking for this kind of information, tokens with these characteristics are relevant."
and then:
"Once I find them, here's the information I want to retrieve from them."
12. Step 3 — Compare the Query with every Key
Now we get to the actual attention.
Suppose we're processing:
The cat drank milk
and we're currently updating the representation of:
cat
The `cat` query is compared with the keys of all tokens:

```text
             cat's Query
                  │
       ┌──────────┼──────────┐
       ↓          ↓          ↓
    Key(The)   Key(drank)  Key(milk)
       ↓          ↓          ↓
    relevance  relevance   relevance
```

The model asks:
How relevant is each token to what `cat` currently needs?
For example, conceptually:

```text
The       → 0.10
cat       → 0.20
drank     → 0.40
milk      → 0.30
```

These numbers are just illustrative.
They don't mean "40% of the meaning."
They represent relative attention weights.
13. What does a high attention weight mean?
Suppose:

```text
cat → drank = high
cat → milk  = medium
cat → The   = low
```

It means:
While constructing the new representation of `cat`, information associated with `drank` is considered particularly relevant.
It does not necessarily mean:
"`cat` is looking at `drank` because `drank` is semantically related."
The mechanism learns whatever relationships help the model perform its training objective.
Those relationships can involve:

* syntax
* semantics
* grammatical relationships
* long-range dependencies
* positional relationships
* entity relationships
* other patterns

14. Attention is not simply "looking at nearby words"
This is important.
Consider:
The dog that chased the cat was hungry.
To understand:
was
the model may need to connect it strongly to:
dog
even though several words occur between them.
Conceptually:

```text
The dog that chased the cat was hungry.
    │                         │
    └─────────────────────────┘
             relationship
```

Self-attention allows direct interactions between tokens regardless of their distance within the allowed context.
This is one of the major strengths of the Transformer architecture.
15. Step 4 — Convert relevance into attention weights
The model has calculated many relevance scores.
Conceptually:

```text
cat → The       0.8
cat → cat       1.2
cat → drank     2.7
cat → milk      2.1
```

These raw scores aren't yet convenient as attention weights.
The model converts them into normalized values.
Conceptually:

```text
The       → 0.05
cat       → 0.10
drank     → 0.50
milk      → 0.35
```

Now they form a distribution.
The important idea is:
The model has transformed raw relevance into a set of weights indicating how much information to retrieve from each token.
16. Step 5 — Retrieve information from the Values
Now comes the second half of attention.
We have:

```text
attention weights
       +
values
```

For example:

```text
The       → 0.05
cat       → 0.10
drank     → 0.50
milk      → 0.35
```

The model takes:

```text
5% of The's value
+
10% of cat's value
+
50% of drank's value
+
35% of milk's value
```

and combines them.
The result becomes the new representation of `cat`.
This is the most important conceptual statement about attention:
A token's new representation is constructed by taking a weighted combination of information from other tokens.
17. The crucial distinction: Keys determine relevance, Values provide information
This is worth emphasizing.
Suppose:

```text
Query(cat)
       ↓
compared with
       ↓
Key(The), Key(drank), Key(milk)
       ↓
attention weights
       ↓
used to combine
       ↓
Value(The), Value(drank), Value(milk)
```

So:

```text
KEY
 ↓
helps determine
 ↓
"Should I pay attention to this token?"


VALUE
 ↓
provides
 ↓
"What information should I take from it?"
```

That's why we need both Keys and Values.
18. Every token does this
We just examined what happens to `cat`.
But every token performs the same process.
For:

```text
The cat drank milk
```

we can think:

```text
The
 ↓
looks at The, cat, drank, milk
 ↓
creates new representation


cat
 ↓
looks at The, cat, drank, milk
 ↓
creates new representation


drank
 ↓
looks at The, cat, drank, milk
 ↓
creates new representation


milk
 ↓
looks at The, cat, drank, milk
 ↓
creates new representation
```

Therefore, self-attention is happening for every token.
19. The attention matrix
This produces a very useful conceptual picture.
Imagine the tokens:

```text
The
cat
drank
milk
```

We can represent attention relationships as a matrix:

```text
             attends to
          The   cat   drank  milk
       ┌──────────────────────────
The    │  ?     ?      ?      ?
cat    │  ?     ?      ?      ?
drank  │  ?     ?      ?      ?
milk   │  ?     ?      ?      ?
```

Each row represents:
"For this token, how much attention does it give to every other token?"
For example:

```text
             The   cat   drank  milk
       ┌──────────────────────────
The    │ 0.40  0.30   0.20   0.10
cat    │ 0.05  0.10   0.50   0.35
drank  │ 0.10  0.40   0.20   0.30
milk   │ 0.05  0.45   0.40   0.10
```

Again, these numbers are purely illustrative.
The important thing is the structure.
Every token gets to decide how much attention to give every other token.
20. This is where the word "attention" comes from
Suppose:

```text
cat → drank = 0.50
cat → milk  = 0.35
cat → The   = 0.05
```

We can informally say:
"The `cat` token pays more attention to `drank` and `milk`."
That's why the mechanism is called attention.
But remember:
Attention isn't human consciousness or literal attention.
It is a learned mechanism for weighting information from different tokens.
21. Step 6 — Produce a new contextual representation
After combining the Values, we get a new representation.
Before:

```text
cat
 ↓
embedding + positional information
```

After:

```text
cat
 ↓
self-attention
 ↓
context-aware representation
```

The new representation now contains information influenced by other tokens.
Conceptually:

```text
cat
+
information from surrounding context
       ↓
contextualized cat representation
```

This is the transformation that makes attention so powerful.
22. Context changes representation
Consider:
The bank approved my loan.
versus:
I sat beside the bank of the river.
The initial token embedding for `bank` is the same.
But self-attention allows the representation of `bank` to interact with:

```text
approved
loan
```

in the first sentence, and:

```text
river
sat
beside
```

in the second.
Therefore:

```text
bank
 ↓
different contextual information
 ↓
different resulting representation
```

This is why Transformer representations are called contextual representations.
23. Self-attention doesn't "look up meaning"
Another subtle point.
It's tempting to think:

```text
Query = question
Key = dictionary index
Value = definition
```

That's a useful beginner analogy, but it isn't literally what happens.
The model isn't searching a dictionary.
There isn't a database saying:

```text
cat → feline animal
```

Instead, the Q, K, and V transformations are learned neural representations.
The model learns which patterns of interactions are useful for predicting text.
So:
Attention is a learned information-routing mechanism.
I think this is the most accurate conceptual description.
24. Where do Q, K, and V come from?
You might now ask:
Where did the Query, Key, and Value vectors come from?
They are produced by learned transformations of the input representation.
Conceptually:

```text
Input representation
       │
       ├────────► Query transformation ──► Q
       │
       ├────────► Key transformation ─────► K
       │
       └────────► Value transformation ────► V
```

These transformations contain learned parameters.
During training, the model learns how to construct useful Queries, Keys, and Values.
So the model learns:
"When I am in this kind of situation, this is what I should look for."
and:
"When another token is looking for this kind of information, this is what I should advertise."
and:
"If I'm selected, this is the information I should contribute."
25. Attention is information routing
Here's perhaps the best mental model:
Self-attention is a learned information-routing system.
Imagine every token is a person in a room.

```text
The     cat     drank     milk
```

Every person can ask:
"Whose information is useful to me?"
They examine the others.
Then each person creates a weighted mixture of information from the people they consider relevant.
After the process:

```text
The     → new representation
cat     → new representation
drank   → new representation
milk    → new representation
```

Every token has been enriched by information from other tokens.
26. Why is this better than simply averaging all tokens?
Suppose we simply averaged:

```text
The + cat + drank + milk
```

Then every token would receive roughly the same information.
But that's not useful.
Different tokens need different information.
For example:

```text
cat
```

may need information about:

```text
drank
```

while:

```text
milk
```

may need information about:

```text
drank
```

and:

```text
The
```

may be relatively less important.
Self-attention allows the model to dynamically choose the information flow.
27. Attention is dynamic
This is another important characteristic.
The same word can attend differently depending on its context.
For example:

```text
The dog chased the cat.
```

and:

```text
The dog slept beside the cat.
```

The relationships learned by attention can differ.
So attention isn't:

```text
cat always → dog = 70%
```

Instead:

```text
attention depends on
       ↓
current representations
       ↓
current context
       ↓
learned transformations
```

Therefore attention is context-dependent.
28. What happens during training?
Now let's connect attention to learning.
Initially, the Q/K/V transformations are essentially untrained.
The model makes poor predictions.
For example:

```text
Input:
The cat drank

Model predicts:
car  30%
house 20%
milk 5%
...
```

The correct next token might be:

```text
milk
```

The model calculates its loss.
Then backpropagation sends gradients through the entire network.
Those gradients update:

```text
embedding parameters
Q parameters
K parameters
V parameters
feed-forward parameters
output parameters
...
```

Over enormous amounts of training data, the model learns useful attention patterns.
29. Attention patterns emerge from the training objective
This is a fascinating point.
The model isn't directly told:
"Learn grammar."
Instead, it's often trained with a simple objective such as:
Predict the next token.
Yet to become good at prediction, the model may discover that it helps to learn relationships involving:

```text
subjects
verbs
objects
pronouns
entities
syntax
semantic relationships
long-distance dependencies
```

So sophisticated linguistic behavior can emerge from the optimization process.
30. Causal self-attention in GPT-style models
Now we need an important distinction.
In a GPT-style LLM, the model predicts the next token.
Suppose:

```text
The cat drank milk
```

When predicting `drank`, the model should not be allowed to see future tokens such as:

```text
milk
```

Otherwise it would be cheating.
Therefore GPT uses causal self-attention.
The rule is:
A token can attend to itself and previous tokens, but not future tokens.
31. Visualizing causal attention
Suppose the sequence is:

```text
The cat drank milk
```

The attention possibilities look conceptually like:

```text
             The   cat   drank   milk

The          ✓     ✗      ✗       ✗

cat          ✓     ✓      ✗       ✗

drank        ✓     ✓      ✓       ✗

milk         ✓     ✓      ✓       ✓
```

Why?
When the model is processing `cat`, it knows:

```text
The
cat
```

but not:

```text
drank
milk
```

because those are future tokens.
This is called a causal mask or attention mask.
32. Why the causal mask matters
Suppose we're training:

```text
The cat drank milk
```

The model is essentially trained on:

```text
The       → predict cat
The cat   → predict drank
The cat drank → predict milk
```

For the second prediction:

```text
The cat → drank
```

the model must not use:

```text
milk
```

as a clue.
Otherwise the training task wouldn't represent actual next-token generation.
So:

```text
Causal attention
        ↓
No information from the future
        ↓
Autoregressive generation
```

This is fundamental to GPT-style models.
33. Encoder self-attention vs decoder causal attention
This is useful terminology.
Encoder-style self-attention
A token can generally attend to all tokens:

```text
A B C D

A → A B C D
B → A B C D
C → A B C D
D → A B C D
```

This is common in models such as BERT.
GPT-style causal self-attention
A token can attend only backward:

```text
A → A
B → A B
C → A B C
D → A B C D
```

This is used in decoder-only autoregressive LLMs.
34. Self-attention vs cross-attention
Don't confuse these.
Self-attention

```text
Sequence
   ↓
attends to
   ↓
same sequence
```

Cross-attention

```text
Sequence A
    ↓
Query

Sequence B
    ↓
Keys + Values
```

The query comes from one sequence while Keys and Values come from another.
Cross-attention is important in encoder-decoder architectures.
For GPT-style models, the main attention mechanism is causal self-attention.
35. Why multiple attention heads?
Now we arrive at multi-head attention.
A single attention mechanism can learn useful relationships.
But there may be many different relationships in a sentence.
For example:

```text
The dog that chased the cat was hungry.
```

One attention pattern might focus on:

```text
dog ↔ was
```

Another might focus on:

```text
chased ↔ cat
```

Another might focus on:

```text
dog ↔ chased
```

Another might focus on positional relationships.
So instead of having one attention mechanism, the Transformer uses several:

```text
              Input
                │
       ┌────────┼────────┐
       ↓        ↓        ↓
    Head 1    Head 2    Head 3 ...
       ↓        ↓        ↓
 different  different  different
 relationships
       └────────┼────────┘
                ↓
             combine
```

This is multi-head attention.
36. What does "head" mean?
A head is essentially an independent attention mechanism with its own learned Q/K/V transformations.
So:

```text
Head 1
  ↓
learns one type of relationship


Head 2
  ↓
learns another


Head 3
  ↓
learns another
```

We don't explicitly tell the model:
Head 1 = grammar
Head 2 = meaning
The model discovers useful patterns during training.
37. A useful analogy for multi-head attention
Imagine a sentence being examined by several specialists.

```text
Sentence
   │
   ├── Linguist → grammatical relationships
   │
   ├── Semantic analyst → meaning relationships
   │
   ├── Entity analyst → who/what relates to whom
   │
   └── Position analyst → positional relationships
```

Again, this is an analogy rather than a literal description.
But it captures the idea that different attention heads can specialize in different patterns.
38. What happens after the attention heads?
Each head produces an output representation.
These outputs are combined:

```text
Head 1 ─┐
Head 2 ─┤
Head 3 ─┤
Head 4 ─┤
        ↓
     Combine
        ↓
Linear transformation
        ↓
Attention output
```

Then this output goes into the next parts of the Transformer block.
39. What happens after self-attention?
A simplified Transformer block looks like:

```text
Input
  ↓
Self-Attention
  ↓
Residual connection + normalization
  ↓
Feed-Forward Network
  ↓
Residual connection + normalization
  ↓
Output
```

So self-attention isn't the entire Transformer.
It's one major component.
The attention mechanism handles:
How information moves between tokens.
The feed-forward network performs additional transformations on each token's representation.
40. The deepest conceptual interpretation
Let's step back.
Before self-attention:

```text
Token representations
```

After self-attention:

```text
Each token has incorporated
relevant information from other tokens.
```

So self-attention performs:
contextual information exchange.
You can think of the Transformer as repeatedly doing:

```text
Token A ←→ Token B
Token A ←→ Token C
Token B ←→ Token D
...
```

Then another Transformer layer does it again.
And again.
And again.
This allows increasingly sophisticated representations to emerge.
41. Multiple Transformer layers
A real LLM doesn't have one attention layer.
It has many Transformer blocks:

```text
Embedding
   ↓
Transformer Block 1
   ↓
Transformer Block 2
   ↓
Transformer Block 3
   ↓
...
   ↓
Transformer Block N
   ↓
Output
```

At the beginning:

```text
representations are relatively simple
```

As information passes through layers:

```text
increasingly contextual
increasingly transformed
increasingly useful for prediction
```

42. A complete conceptual example
Let's use:
The cat drank the milk because it was hungry.
Suppose we're updating the representation of:
`it`
The model can examine:

```text
The
cat
drank
the
milk
because
it
was
hungry
```

The query associated with `it` interacts with the Keys of the other tokens.
Conceptually, it might assign relatively high relevance to:

```text
cat
hungry
```

and lower relevance to:

```text
the
because
milk
```

Then it combines information from the corresponding Values.
The resulting representation of `it` is therefore influenced by context.
Importantly, the actual learned attention pattern is not guaranteed to correspond neatly to a human interpretation like "pronoun resolution." Attention weights are not universally reliable explanations of model reasoning.
But conceptually, the mechanism makes these interactions possible.
43. The whole process in one picture
Here is the mental model I'd like you to keep:

```text
                 INPUT
                   │
                   ▼
          Token representations
                   │
                   ▼
        ┌─────────────────────┐
        │ Generate Q, K, V     │
        └─────────────────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │ Query vs Keys        │
        │                     │
        │ "Who is relevant?"  │
        └─────────────────────┘
                   │
                   ▼
          Attention weights
                   │
                   ▼
        ┌─────────────────────┐
        │ Retrieve information │
        │ from Values          │
        └─────────────────────┘
                   │
                   ▼
       Context-aware vectors
                   │
                   ▼
          Multi-head combine
                   │
                   ▼
        Transformer processing
                   │
                   ▼
              OUTPUT
```

44. The six questions to remember
When you look at self-attention code, ask yourself these six questions:
① What are the input representations?

```text
Where did X come from?
```

Usually:

```text
token embedding + positional information
```

② What is the Query?

```text
What information is this token looking for?
```

③ What are the Keys?

```text
What kind of information does each token advertise?
```

④ What are the attention weights?

```text
How relevant is each token to this Query?
```

⑤ What are the Values?

```text
What information does each relevant token actually contribute?
```

⑥ What is the output?

```text
A new representation containing
information gathered from relevant tokens.
```

If these six questions are clear, you've understood the conceptual mechanism.
45. Connecting this to what you already learned
You've now learned two very important pieces.
First:

```text
TOKEN ID
   ↓
Embedding lookup
   ↓
Initial vector
```

Now:

```text
Initial vectors
      ↓
     Q K V
      ↓
  Self-attention
      ↓
Contextual vectors
```

So the overall transformation is:

```text
Text
 ↓
Tokenizer
 ↓
Token IDs
 ↓
Embedding
 ↓
Initial representations
 ↓
Self-Attention
 ↓
Context-aware representations
 ↓
Feed-Forward Network
 ↓
More Transformer layers
 ↓
Final representation
 ↓
Prediction
```

This is the conceptual bridge from embedding to Transformer.
46. The one sentence I want you to remember
If someone asks you:
"What is self-attention?"
I'd answer:
Self-attention is a mechanism that allows each token to dynamically gather relevant information from other tokens in the same sequence, producing a new context-aware representation of that token.
And if they ask:
"What are Q, K, and V?"
I'd say:
Query represents what a token is looking for, Key represents what each token can be matched on, and Value represents the information that each token contributes when it is considered relevant.
And finally:
Attention weights determine how much information to gather from each Value.
That is the conceptual core of self-attention.
One particularly important insight for you
Because you already understand the embedding layer and Linear Algebra, I think you're now ready for the most illuminating next step: taking one tiny sentence such as
"I love cats"
and walking through one complete self-attention calculation by hand, using tiny 2-dimensional or 3-dimensional vectors—not to emphasize arithmetic, but to see exactly how Q → K matching → attention weights → V aggregation → contextual vector works.
Once you see that single example, the actual Transformer code becomes dramatically less mysterious.
'''

story = [
    P("Self-Attention: A Conceptual Guide", title_s),
    P("From embeddings to context-aware representations, with the mathematics kept in the "
      "background", sub_s),
    HRFlowable(width="100%", thickness=0.8, color=LINE, spaceAfter=10),
]
story += render(parse_blocks(normalize(to_ascii(RAW_TEXT))))
story.append(P("Generated from a pasted study document. Generation script: "
               "tools/pdf/self_attention_guide.py", cap_s))

doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                        topMargin=18 * mm, bottomMargin=18 * mm,
                        title="Self-Attention: A Conceptual Guide")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print("wrote", OUT)
