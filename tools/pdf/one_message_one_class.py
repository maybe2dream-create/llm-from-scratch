# /// script
# dependencies = ["markdown"]
# ///
"""Chapter 6 concept note -> docs/Ch6_One_Message_One_Class_Decision.pdf

Run from anywhere:  uv run tools/pdf/one_message_one_class.py

Explains "One message produces one class decision" by contrasting chapter 5
(pretraining: one decision per token) with chapter 6 (classification: one decision per
message). Token IDs were checked with tiktoken's gpt2 encoding. Rendering reuses the
style of gpt_model_walkthrough.py (markdown -> HTML -> headless Chrome).
"""
import subprocess
import tempfile
from pathlib import Path

import markdown
from gpt_model_walkthrough import CHROME, CSS

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "docs" / "Ch6_One_Message_One_Class_Decision.pdf"
TITLE = "One Message, One Class Decision"

EXTRA_CSS = """
blockquote { margin: 6pt 0 9pt; padding: 6pt 10pt; background: #eef2f8; color: #243b5c;
             border-left: 3pt solid #2f4f76; break-inside: avoid; }
blockquote p { margin: 0; }
h3 { color: #2f4f76; }
ol, ul { margin: 0 0 7pt; padding-left: 18pt; }
table { break-inside: avoid; }
"""

TEXT = r'''
# One Message, One Class Decision

<p class="sub">What this sentence from chapter 6 (fine-tuning for classification) means for how the model is built,
explained by contrast with what you already did in chapter 5 (pretraining).</p>

## What you know: one message gives *many* decisions

In pretraining (chapter 5), every position in a text is a small exam question: "what is the next token?"

```text
input:   Every   effort  moves   you
target:  effort  moves   you     forward
         |       |       |       |
         4 predictions, 4 answers, 4 contributions to the loss
```

A sequence of 256 tokens therefore gives 256 decisions, and the model's output keeps one row per token:
`[batch, tokens, 50257]`.

## What the sentence says: one message gives *one* decision

In classification, for example SMS spam detection, the question is no longer about each word. It is about the
**whole message**:

```text
"You won a free prize! Call now"   ->   spam      (one label)
"Are we still meeting at 6?"       ->   not spam  (one label)
```

Whether the message has 5 tokens or 50, it gets **one answer from a fixed set of classes**. Think of a clerk who reads
an entire letter and stamps one verdict on it, instead of grading each word.

## What this changes when building the model

### 1. The output layer shrinks: 50,257 scores → 2 scores

The model no longer chooses among all vocabulary tokens, only between "not spam" and "spam". So `out_head` is replaced:

```python
model.out_head = torch.nn.Linear(768, 2)    # was Linear(768, 50257)
```

Everything else (embeddings, 12 transformer blocks, final LayerNorm) is kept, already trained. In the book most of it is
also *frozen* (not trained further); only the new `out_head`, the last transformer block and the final LayerNorm are
updated.

### 2. The model still answers at every token, but only one answer is used

The transformer works exactly as before, so for "Do you have time" (4 tokens: 5211, 345, 423, 640) the output is
`[1, 4, 2]`: two scores at each of the 4 positions. One message needs only one decision, so only **the last token's**
row is kept:

```python
logits = model(input_ids)[:, -1, :]    # [1, 4, 2] -> [1, 2]
```

### 3. Why the last token: the causal mask you built

Remember the mask from chapter 3: each token can see only itself and the tokens *before* it.

```text
           sees:   Do   you  have  time
  Do               x
  you              x    x
  have             x    x    x
  time             x    x    x     x     <- the only one that has seen everything
```

The first token's output knows only "Do". Only the last token has read the whole message, so it is the one qualified to
give the verdict. It is the same reasoning as `logits[:, -1, :]` in `generate_text_simple` (chapter 4): the last
position is the one that has seen everything before it.

### 4. The labels look different

| | Pretraining (chapter 5) | Classification (chapter 6) |
|---|---|---|
| Target | the input shifted by one token | one class number per message (0 = not spam, 1 = spam) |
| Target shape | `[batch, tokens]` | `[batch]` |
| Where it comes from | free, from the text itself | **a person must provide it** |

That is why chapter 6 needs a labeled dataset.

### 5. The loss and the accuracy are counted per message

The loss compares the 2 scores with the 1 label:

```python
loss = torch.nn.functional.cross_entropy(logits[:, -1, :], target)
```

In pretraining it compared every position with its next token. Accuracy now means "what fraction of *messages* got the
right label", using `argmax` over the 2 scores.

### 6. Fewer learning signals, so start from a pretrained model

One message now gives one learning signal instead of hundreds. Learning English from scratch that way would need far too
much labeled data. So chapter 6 starts from GPT-2's pretrained weights, the ones downloaded in chapter 5: the model
already understands language and only has to learn the new verdict.

### 7. A small detail about padding

Messages in a batch must be the same length, so shorter ones are filled up with token 50256 (`<|endoftext|>`). The "last
token" may then be a padding token. It still works: thanks to the causal mask, the last position, even if it is padding,
attends to every real token before it.

## Side by side

| | Pretraining (chapter 5) | Classification (chapter 6) |
|---|---|---|
| Question | "What is the next token?" at every position | "Which class is this message?" once |
| Decisions per message | one per token | **one** |
| Output layer | `Linear(768, 50257)` | `Linear(768, 2)` |
| Output used | all positions `[batch, tokens, 50257]` | last position only `[batch, 2]` |
| Labels | free (shifted text) | human-made, one per message |
| Starting weights | random | pretrained GPT-2 |

## In one line

> **Pretraining:** a message is many "next word?" questions. **Classification:** a message is one "which class?"
> question. So you keep one output row (the last token's), use a 2-class output layer, need one human label per
> message, and score per message.
'''


def build():
    body = markdown.markdown(TEXT, extensions=["fenced_code", "tables"])
    css = CSS.replace('"Chapter 4 line by line"', '"One message, one class decision"') + EXTRA_CSS
    page = (f'<!doctype html><html><head><meta charset="utf-8"><title>{TITLE}</title>'
            f"<style>{css}</style></head><body>{body}"
            '<p class="end">Generated by tools/pdf/one_message_one_class.py</p></body></html>')
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
