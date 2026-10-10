# /// script
# dependencies = []
# ///
"""Chapter 4 line-by-line guide -> docs/Ch4_GPT_Model_Line_by_Line.pdf

Run from anywhere:  uv run tools/pdf/gpt_model_walkthrough.py

The code and outputs are read straight from notebooks/04_gpt_model.ipynb, so the PDF
always shows what is actually in the notebook. The explanations below are keyed by
cell number and line number; each entry records the cell's first line, and the build
stops if the notebook no longer matches (cells moved or edited), instead of printing
explanations next to the wrong code.

HTML -> headless Google Chrome, as in attention_worked_example.py. Every number in the
explanations was checked by running the notebook.
"""
import html
import json
import re
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
NOTEBOOK = REPO / "notebooks" / "04_gpt_model.ipynb"
OUT = REPO / "docs" / "Ch4_GPT_Model_Line_by_Line.pdf"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
TITLE = "Chapter 4 Line by Line: Building GPT-2 from Its Parts"

CSS = """
@page {
  size: A4; margin: 17mm 18mm 19mm 18mm;
  @bottom-left { content: "Chapter 4 line by line"; font: 7.5pt 'Helvetica Neue'; color: #777; }
  @bottom-right { content: counter(page); font: 7.5pt 'Helvetica Neue'; color: #777; }
}
body { font: 9.7pt/1.55 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #1a1a1a; }
h1 { font-size: 20pt; margin: 0 0 3pt; }
.sub { color: #5a5a5a; margin: 0 0 12pt; }
h2 { font-size: 14pt; color: #2f4f76; border-top: 1pt solid #2f4f76; padding-top: 8pt;
     margin: 18pt 0 6pt; break-after: avoid; }
h3 { font-size: 11.2pt; margin: 14pt 0 3pt; break-after: avoid; color: #1a1a1a; }
h3 .tag { color: #2f4f76; font-weight: normal; font-size: 9pt; margin-left: 6pt; }
p { margin: 0 0 6pt; }
.intro { margin: 2pt 0 6pt; }
pre { background: #f4f5f7; border: 0.5pt solid #cfcfcf; padding: 6pt 8pt; margin: 4pt 0 6pt;
      font: 8.3pt/1.42 Menlo, monospace; white-space: pre-wrap; break-inside: avoid; }
pre .ln { color: #9aa3ad; user-select: none; }
pre.output { background: #fbfbf4; border-color: #dedcc4; }
.outlabel { font-size: 8pt; color: #7a7650; margin: 6pt 0 0; break-after: avoid; }
code { font: 8.6pt Menlo, monospace; color: #2f4f76; }
table { border-collapse: collapse; width: 100%; margin: 4pt 0 8pt; }
tr { break-inside: avoid; }
th, td { border: 0.5pt solid #d4d4d4; padding: 3pt 6pt; vertical-align: top; text-align: left; }
th { background: #ececec; font-size: 8.8pt; }
table.lines td:first-child { width: 11%; white-space: nowrap; font: 8.3pt Menlo, monospace; color: #2f4f76; }
.note { border-left: 3pt solid #2f4f76; background: #eef2f8; padding: 5pt 9pt; margin: 6pt 0 8pt;
        break-inside: avoid; }
.warn { border-left: 3pt solid #b5651d; background: #fbf3ea; padding: 5pt 9pt; margin: 6pt 0 8pt;
        break-inside: avoid; }
.cell { break-before: auto; }
img.plot { width: 78%; display: block; margin: 4pt auto 8pt; }
.end { color: #777; font-size: 7.8pt; text-align: center; margin-top: 16pt; }
.qa li { margin-bottom: 4pt; }
"""


def inline(text):
    """Escape, then allow `code`, **bold** and *italic* (outside code spans) in explanations."""
    parts = re.split(r"(`[^`]+`)", html.escape(text, quote=False))
    for i, part in enumerate(parts):
        if part.startswith("`"):
            parts[i] = f"<code>{part[1:-1]}</code>"
        else:
            part = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", part)
            parts[i] = re.sub(r"\*([^*]+?)\*", r"<i>\1</i>", part)
    return "".join(parts)


# ---------------------------------------------------------------------------
# Explanations: cell number -> details. "first" must equal the cell's first line.
# "lines" is a list of (line label, explanation). Line labels match the numbers
# printed next to the code.
# ---------------------------------------------------------------------------
CELLS = {
    1: {
        "first": "import sys", "title": "Make src/ importable", "section": "4.1",
        "intro": "Chapter 4 reuses your chapter 3 attention class. This cell makes the repository "
              "root visible to Python so that `src/attention.py` can be imported.",
        "lines": [
            ("1", ("`sys` is Python's own settings module. One of its settings is `sys.path`, the list of "
                  "folders Python searches when you write `import`.")),
            ("2", ("The notebook runs inside `notebooks/`. `\"..\"` means \"one folder up\", the repository "
                  "root. Adding it to `sys.path` lets Python find the `src` folder. Without this line you get "
                  "`ModuleNotFoundError: No module named 'src'`.")),
            ("4", ("Loads the `MultiHeadAttention` class from `src/attention.py`, the chapter 3 class you moved "
                  "there. It is used later inside `TransformerBlock` (cell 21).")),
        ],
        "note": "Python loads an imported file once per kernel session and keeps that copy. If you edit "
             "`src/attention.py`, restart the kernel, or the old version stays in use. This caused the "
             "`ImportError` on Oct 9.",
    },
    2: {
        "first": "GPT_CONFIG_124M = {", "title": "The model's settings", "section": "4.1",
        "intro": "All the sizes of the smallest GPT-2 model in one dictionary. Every class below receives this "
              "dictionary as `cfg` and reads only the entries it needs, so changing one number here "
              "resizes the whole model.",
        "lines": [
            ("1", ("Capital letters are a Python convention for a value that should not change. \"124M\" is "
                  "the model's nickname (124 million parameters; see cell 26).")),
            ("2", ("`vocab_size`: how many different tokens the GPT-2 tokenizer knows (50,257). It fixes the "
                  "number of rows in the token embedding table and the number of scores the model outputs.")),
            ("3", ("`context_length`: the longest input the model can read at once (1,024 tokens). It fixes "
                  "the rows of the position embedding table and the size of the causal mask (1,024 × 1,024).")),
            ("4", "`emb_dim`: the width of every token vector inside the model (768 numbers per token)."),
            ("5", "`n_heads`: attention heads per block. Each head works on 768 / 12 = 64 dimensions."),
            ("6", "`n_layers`: how many transformer blocks are stacked (12)."),
            ("7", ("`drop_rate`: dropout probability. During training 10% of the values are set to 0 and the "
                  "rest are multiplied by 1/0.9 ≈ 1.111 so the average stays the same.")),
            ("8", ("`qkv_bias`: whether the Query/Key/Value layers have a bias term. False here for simplicity; "
                  "in chapter 5, loading OpenAI's real GPT-2 weights needs True, because the original model "
                  "has these biases.")),
        ],
    },
    3: {
        "first": "import torch", "title": "DummyGPTModel: the skeleton", "section": "4.1",
        "intro": "The whole GPT structure with two parts left as placeholders. The data can already flow from "
              "token IDs to scores, so the shapes can be checked before any real part exists. In cell 23 "
              "the two dummies are replaced by the real `TransformerBlock` and `LayerNorm`.",
        "lines": [
            ("1–2", "PyTorch, and its neural-network toolbox under the short name `nn`."),
            ("3", ("`class DummyGPTModel(nn.Module)`: inheriting from `nn.Module` gives two things for free: "
                  "PyTorch keeps track of every parameter inside, and writing `model(x)` runs `forward(x)`.")),
            ("4", "`__init__` runs once when the model is created. It builds the parts; it does not process data."),
            ("5", ("`super().__init__()` sets up `nn.Module`'s internal bookkeeping. It must come first: assigning "
                  "a layer before it raises `AttributeError: cannot assign module before Module.__init__() call`.")),
            ("6", ("`tok_emb`: a lookup table of 50,257 rows × 768 columns, one row per token ID "
                  "(38,597,376 numbers). Looking up ID 6109 returns row 6109.")),
            ("7", ("`pos_emb`: a table of 1,024 rows × 768, one row per position 0, 1, 2, …, 1,023. It tells the "
                  "model *where* a token sits, which attention alone cannot see.")),
            ("8", "`drop_emb`: dropout applied to the embeddings."),
            ("9–11", ("`[DummyTransformerBlock(cfg) for _ in range(12)]` builds a list of 12 blocks; `_` means "
                     "\"I don't need the loop counter\". The `*` unpacks the list into 12 separate arguments, "
                     "and `nn.Sequential` runs them one after another, each output feeding the next.")),
            ("12", "`final_norm`: one last normalization after the 12 blocks."),
            ("13", ("`out_head`: a Linear layer from 768 to 50,257 without bias. It turns each token's 768-number "
                   "vector into 50,257 scores, one per vocabulary token. These scores are the *logits*.")),
            ("15", ("`forward` describes what happens to the data. `in_idx` is a tensor of token IDs, shape "
                   "[batch, seq_len].")),
            ("16", ("Reads the two sizes from the input's shape: here batch_size = 2, seq_len = 4. "
                   "(`batch_size` is not used later; it documents the shape.)")),
            ("17", "Token lookup: [2, 4] IDs become [2, 4, 768] vectors."),
            ("18", ("`torch.arange(seq_len)` = `tensor([0, 1, 2, 3])`, the positions. `device=in_idx.device` creates "
                   "it on the same device as the input (CPU or GPU), avoiding a device-mismatch error. "
                   "Result: [4, 768].")),
            ("19", ("Adds the two. [2, 4, 768] + [4, 768] works by *broadcasting*: the same four position "
                   "vectors are added to both sentences. (The missing space in `x=` is harmless.)")),
            ("20", "Dropout. It only acts in training mode; after `model.eval()` it does nothing."),
            ("21", "The 12 blocks. In this dummy version each returns its input unchanged."),
            ("22", "Final normalization (also a pass-through here)."),
            ("23", "[2, 4, 768] → [2, 4, 50,257]: a score for every vocabulary token at every position."),
            ("24", "Returns the logits."),
            ("26–31", ("`DummyTransformerBlock` accepts the config (so it can be swapped for the real class "
                      "without changing the caller) but its `forward` just returns `x`.")),
            ("33–38", ("`DummyLayerNorm` does the same. Its arguments `(normalized_shape, eps)` mirror the real "
                      "`LayerNorm`, again so the swap is painless.")),
        ],
        "note": "The two dummy classes are defined *after* `DummyGPTModel` in the same cell, yet it works. "
             "Python looks up the name `DummyTransformerBlock` only when `__init__` actually runs (in cell 5), "
             "and by then the whole cell has been executed.",
    },
    4: {
        "first": "import tiktoken", "title": "Two sentences as a batch of token IDs", "section": "4.1",
        "intro": "Converts two short texts into token IDs with the real GPT-2 tokenizer and stacks them into one "
              "batch tensor, the model's input.",
        "lines": [
            ("1", "`tiktoken` is OpenAI's fast BPE tokenizer library (chapter 2)."),
            ("3", "Loads the exact vocabulary GPT-2 was trained with (50,257 tokens)."),
            ("4", "An empty Python list to collect the two sentences."),
            ("5–6", "The two example texts."),
            ("8–9", ("`encode` turns text into a list of IDs; `torch.tensor` turns the list into a tensor; "
                    "`append` adds it to the list. \"Every effort moves you\" → 6109 \"Every\", 3626 \" effort\", "
                    "6100 \" moves\", 345 \" you\". The leading spaces belong to the tokens.")),
            ("10", ("`torch.stack(..., dim=0)` puts the two [4] tensors on top of each other, creating a new first "
                   "axis: shape [2, 4]. Stacking needs equal lengths, and both sentences happen to be 4 tokens. "
                   "Note that the name `batch` now changes from a list to a tensor.")),
            ("11", "Prints the batch."),
        ],
        "output_note": "Both rows start with 6109 because both sentences start with \"Every\". The second row: "
                    "1110 \" day\", 6622 \" holds\", 257 \" a\".",
    },
    5: {
        "first": "torch.manual_seed(123)", "title": "Run the skeleton once", "section": "4.1",
        "intro": "Creates the dummy model and pushes the batch through it to confirm the output shape.",
        "lines": [
            ("1", ("Fixes the random number generator so the random starting weights are the same every run, "
                  "and the same as the book's. It must come directly before the model is created.")),
            ("2", "Builds the model: the embedding tables and `out_head` are filled with random numbers."),
            ("3", "`model(batch)` calls `forward(batch)` (through `nn.Module`)."),
            ("4–5", "Shape and values."),
        ],
        "output_note": "[2, 4, 50257] = 2 sentences × 4 positions × one score per vocabulary token. "
                    "`grad_fn=<…>` means PyTorch recorded how these numbers were computed, which it needs "
                    "later for training (backpropagation). The values are meaningless: nothing is trained.",
    },
    6: {
        "first": "torch.manual_seed(123)", "title": "A small example to normalize", "section": "4.2",
        "intro": "Section 4.2 explains layer normalization on a tiny example before building the class. This cell "
              "makes that example: 2 rows with 6 numbers each.",
        "lines": [
            ("1", "Same seed, so the example matches the book."),
            ("2", "`torch.randn(2, 5)`: 2 examples with 5 features, drawn from a standard normal distribution."),
            ("3", "A tiny network: Linear (5 → 6) followed by ReLU, which sets every negative value to 0."),
            ("4", "`out` has shape [2, 6]. The zeros in the output are ReLU's work."),
            ("5", "Prints `out`."),
        ],
        "warn": "Cells 7 and 8 depend on the name `out`. Never reuse `out` for something else later, or rerunning "
             "cells 7–8 silently processes the wrong data. (That is why later cells use `out_ffn` and `token_ids`.)",
    },
    7: {
        "first": "mean = out.mean(dim=-1, keepdim=True)", "title": "Mean and variance before normalizing", "section": "4.2",
        "intro": "Measures each row's average and spread, the two numbers normalization will remove.",
        "lines": [
            ("1", ("`dim=-1` = the last axis: the 6 numbers *within* each row, one mean per row. `keepdim=True` keeps "
                  "the result as shape [2, 1] instead of [2], so it can later be subtracted from the [2, 6] tensor.")),
            ("2", ("Variance per row. By default `var` divides by N − 1 = 5 (the \"unbiased\" estimator from "
                  "statistics): 0.0231 and 0.0398. Divided by N = 6 it would be 0.0192 and 0.0332.")),
            ("3–4", "`\\n` starts a new line in the printout."),
        ],
    },
    8: {
        "first": "out_norm = (out - mean) / torch.sqrt(var)", "title": "Normalize by hand", "section": "4.2",
        "intro": "Standardizes each row: subtract its mean, divide by its standard deviation. Afterwards every "
              "row has mean 0 and variance 1.",
        "lines": [
            ("1", ("(value − mean) / standard deviation, the familiar z-score. [2, 6] − [2, 1] broadcasts each "
                  "row's mean across its 6 values.")),
            ("2–3", ("Mean and variance of the result, under **new names**. The cell reads `mean`/`var` and never "
                    "overwrites them, so it gives the same answer however often you rerun it.")),
            ("4–6", "Prints the normalized values and their statistics."),
        ],
        "output_note": "Mean −0.0000 and 0.0000: really tiny leftovers such as −5.96e−08 from floating-point "
                    "rounding. Variance exactly 1 because lines 1 and 3 both use the same N − 1 variance. "
                    "Measured with N instead (`unbiased=False`) it would be 5/6 = 0.8333.",
    },
    9: {
        "first": "torch.set_printoptions(sci_mode=False)", "title": "Readable printing", "section": "4.2",
        "intro": "Changes only how numbers are *displayed*, not their values.",
        "lines": [
            ("1", ("Turns off scientific notation, so −5.96e−08 prints as −0.0000. The setting lasts for the "
                  "rest of the session.")),
            ("2–3", ("Prints the after-normalization statistics. The book prints `mean`/`var` here because it "
                    "overwrote them; in your notebook those names still hold the *before* values, so this cell "
                    "uses `mean_norm`/`var_norm`.")),
        ],
        "output_note": "The minus sign in −0.0000 is the sign of the tiny rounding leftover; the value is zero.",
    },
    10: {
        "first": "class LayerNorm(nn.Module):", "title": "LayerNorm as a reusable class", "section": "4.2",
        "intro": "The steps of cells 7–8 packaged as a layer, plus a safety constant and two trainable parameters. "
              "The real model uses it twice in every block and once at the end.",
        "lines": [
            ("2", "`emb_dim`: how many features each token has (768 in GPT-2, 5 in the test)."),
            ("4", ("`eps = 1e-5`: a tiny number added to the variance so the division never divides by zero, "
                  "for example if all values in a row are equal.")),
            ("5", ("`scale`: starts as 1 for every feature. Wrapping it in `nn.Parameter` makes it trainable, so "
                  "PyTorch will adjust it during training.")),
            ("6", ("`shift`: starts as 0 for every feature, also trainable. With scale 1 and shift 0 the layer "
                  "starts as pure normalization; training can learn to stretch or move each feature if that "
                  "helps. Together: 2 × 768 = 1,536 parameters per LayerNorm.")),
            ("9", "Mean over the last axis: one mean per token."),
            ("10", ("Variance with `unbiased=False`, dividing by N. This copies the original GPT-2 code; with 768 "
                   "features the difference from N − 1 is negligible.")),
            ("11", "The z-score of cell 8, with `eps` inside the square root."),
            ("12", "Applies the learnable scale and shift feature by feature: [768] broadcasts over [..., 768]."),
        ],
        "note": "`mean`, `var` and `norm_x` inside `forward` are *local* variables: they exist only while "
             "`forward` runs and never touch the notebook's `mean` and `var` from cell 7.",
    },
    11: {
        "first": "ln = LayerNorm(emb_dim=5)", "title": "Test the LayerNorm class", "section": "4.2",
        "intro": "Applies the class to `batch_example` (5 features per row) and checks the result.",
        "lines": [
            ("1", "A LayerNorm for 5 features, matching `batch_example`'s 5 columns."),
            ("2", "Normalizes the [2, 5] input; `out_ln` is [2, 5]."),
            ("3–4", ("Checks mean and variance, again under new names (`mean_ln`, `var_ln`) so cells 7–8 stay "
                    "safe. `unbiased=False` measures the variance the same way the class computed it.")),
            ("5–6", "Prints the check."),
        ],
        "output_note": "Mean 0 and variance 1.0000 per row: the class works.",
    },
    12: {
        "first": "class GELU(nn.Module):", "title": "GELU activation", "section": "4.3",
        "intro": "The activation function GPT-2 uses inside its feed-forward network: a smooth version of ReLU.",
        "lines": [
            ("1–3", "A layer with no parameters, so `__init__` only calls `super().__init__()`."),
            ("5–6", ("GELU(x) ≈ 0.5 · x · (1 + tanh(√(2/π) · (x + 0.044715 · x³))). The `tanh` formula is a fast "
                    "approximation that GPT-2 used. `torch.tensor(2/torch.pi)` is needed because `torch.sqrt` "
                    "only accepts tensors; `torch.pow(x, 3)` is x³.")),
        ],
        "note": "How to read it: GELU multiplies x by a smooth \"how positive is x\" weight between 0 and 1. "
             "Values: GELU(3) = 2.9964 (almost x), GELU(1) = 0.8412, GELU(0) = 0, GELU(−0.75) = −0.17 "
             "(its lowest point), GELU(−3) = −0.0036 (almost 0). Your formula agrees with PyTorch's built-in "
             "`nn.GELU(approximate='tanh')` to within 0.0000002.",
    },
    13: {
        "first": "import matplotlib.pyplot as plt", "title": "Plot GELU next to ReLU", "section": "4.3",
        "intro": "Draws both activation functions from −3 to 3 to see the difference.",
        "lines": [
            ("1", "Matplotlib, the standard plotting library."),
            ("2", ("Creates one GELU layer and one ReLU layer. The `()` builds an object; without it you would have "
                  "the class itself (the bug of cell 16).")),
            ("4", "`torch.linspace(-3, 3, 100)`: 100 evenly spaced numbers from −3 to 3."),
            ("5–6", "Applies each function to all 100 points at once."),
            ("8", "A figure 8 inches wide and 3 inches tall."),
            ("9", "`subplot(1, 2, 1)`: a grid of 1 row × 2 columns, draw in panel 1 (left)."),
            ("10", ("`.detach()` takes the tensor out of gradient tracking and `.numpy()` converts it to a NumPy "
                   "array, the format matplotlib expects.")),
            ("11–13", "Title and axis labels."),
            ("15–19", "The same for panel 2 (right): ReLU."),
            ("21", "Shows the figure."),
        ],
        "output_note": "ReLU has a sharp corner at 0 and is exactly 0 for every negative input, so no gradient flows "
                    "back through those inputs. GELU is smooth everywhere and lets small negative values through, "
                    "which helps training. The name `x` is reused in cells 15 and 22; that is harmless, because "
                    "each of those cells creates a new `x` before using it.",
    },
    14: {
        "first": "class FeedForward(nn.Module):", "title": "FeedForward: each token thinks on its own", "section": "4.3",
        "intro": "The second sublayer of every transformer block. Attention moves information *between* tokens; "
              "the feed-forward network then processes *each token separately*, with the same weights at "
              "every position.",
        "lines": [
            ("4", "`nn.Sequential` chains three layers."),
            ("5", "Linear 768 → 3,072: widens each token vector 4 times."),
            ("6", ("`GELU()`: the non-linearity. Without it, two Linear layers in a row would collapse into a "
                  "single Linear layer.")),
            ("7", "Linear 3,072 → 768: back to the original width, so the output fits the next block."),
            ("10–11", ("`return self.layers(x)`. Without `return`, Python returns `None`, which caused the "
                      "`'NoneType' object has no attribute 'shape'` error on Oct 10.")),
        ],
        "note": "Parameters: (768 × 3,072 + 3,072) + (3,072 × 768 + 768) = 4,722,432, two-thirds of each block.",
    },
    15: {
        "first": "ffn = FeedForward(GPT_CONFIG_124M)", "title": "Test FeedForward", "section": "4.3",
        "intro": "Checks that the shape survives the widen-and-shrink.",
        "lines": [
            ("1", "Builds the network with GPT-2 sizes."),
            ("2", "Random input: 2 sequences × 3 tokens × 768."),
            ("3", "Inside: [2, 3, 768] → [2, 3, 3,072] → [2, 3, 768]. Stored as `out_ffn`, not `out` (see cell 6)."),
            ("4", "Prints the shape."),
        ],
        "output_note": "[2, 3, 768] in, [2, 3, 768] out. Equal shapes are what allow blocks to be stacked.",
    },
    16: {
        "first": "class ExampleDeepNeuralNetwork(nn.Module):", "title": "A deep network to test shortcuts", "section": "4.4",
        "intro": "A 5-layer toy network that can be built with or without shortcut connections, to compare how "
              "well the learning signal (the gradient) reaches the first layer.",
        "lines": [
            ("2", "`layer_sizes`: the width before and after each layer. `use_shortcut`: True or False."),
            ("4", "Stores the switch so `forward` can read it."),
            ("5", ("`nn.ModuleList`: a list that PyTorch *registers*. A plain Python list would hide the layers "
                  "from `model.parameters()` and from training.")),
            ("6–10", ("Five layers, each Linear + `GELU()`: 3→3, 3→3, 3→3, 3→3, 3→1. Note the `()` after GELU: "
                     "without it you pass the class instead of a layer, and PyTorch raises "
                     "`GELU is not a Module subclass` (Oct 10).")),
            ("14", "Goes through the five layers in order."),
            ("15", "The layer's output."),
            ("16", ("Adds a shortcut only if it is switched on **and** the shapes match. The last layer turns 3 "
                   "numbers into 1, so its output [1, 1] cannot be added to its input [1, 3].")),
            ("17", ("Shortcut: the input is added to the layer's output, so the original signal passes straight "
                   "through.")),
            ("19", "No shortcut: the output simply replaces the input."),
            ("20", "Returns the final output."),
        ],
    },
    17: {
        "first": "layer_sizes = [3, 3, 3, 3, 3, 1]", "title": "Build the model without shortcuts", "section": "4.4",
        "intro": "Creates the test input and the network without shortcuts.",
        "lines": [
            ("1", "Input width 3, three more widths of 3, final output width 1."),
            ("2", "One example, shape [1, 3]. The dots (`1.`) make the numbers floats, which `nn.Linear` requires."),
            ("3", "Seed, so the starting weights match the book."),
            ("4", "Builds the network with `use_shortcut=False`."),
        ],
    },
    18: {
        "first": "def print_gradients(model, x):", "title": "Measure the gradient at each layer", "section": "4.4",
        "intro": "Runs one forward and one backward pass, then prints how large the gradient is for each layer's "
              "weights. A gradient is the signal that tells a weight which way to move during training.",
        "lines": [
            ("2", "Forward pass: the model's output for `x`, shape [1, 1]."),
            ("3", "A target of 0, also [1, 1]: \"the right answer is 0\"."),
            ("5", "`nn.MSELoss()` creates a mean-squared-error loss object: (output − target)²."),
            ("6", "Computes the loss. The name `loss` now changes from the loss *object* to the loss *value*."),
            ("8", ("`backward()` computes, for every parameter, how the loss would change if that parameter changed "
                  "(∂loss/∂parameter), and stores it in `param.grad`.")),
            ("9", ("`named_parameters()` yields pairs like (\"layers.0.0.weight\", tensor). The name reads: `layers` "
                  "(the ModuleList) → item 0 (first Sequential) → item 0 (its Linear) → `weight`.")),
            ("10", ("Keeps the weights and skips the biases. The name contains `weight`, singular. With `'weights'` "
                   "nothing ever matched and the function printed nothing, with no error (Oct 10).")),
            ("11", ("`grad.abs().mean()`: the average size of the gradient, ignoring sign. `.item()` turns a "
                   "one-number tensor into an ordinary Python number.")),
        ],
        "warn": "PyTorch *adds* new gradients to old ones. Calling this function twice on the same model doubles "
             "every number. Rebuild the model (cell 17) before measuring again. In chapter 5 the same problem is "
             "handled by `optimizer.zero_grad()`.",
    },
    19: {
        "first": "print_gradients(model_without_shortcut, sample_input)", "title": "Result without shortcuts",
        "section": "4.4", "intro": "", "lines": [("1", "Measures the gradients of the network without shortcuts.")],
        "output_note": "From the last layer (0.0050) back to the first (0.0002), the gradient shrinks about 25 times. "
                    "The first layer would barely learn. This is the **vanishing gradient** problem: the signal "
                    "fades as it is passed backward through many layers.",
    },
    20: {
        "first": "torch.manual_seed(123)", "title": "Result with shortcuts", "section": "4.4",
        "intro": "The same network and the same starting weights, now with shortcuts.",
        "lines": [
            ("1", "Same seed, so the only difference from cell 17 is the shortcut switch."),
            ("2", "Builds the network with `use_shortcut=True`."),
            ("3", "Measures again."),
        ],
        "output_note": "The first layer now gets 0.2217 instead of 0.0002, about 1,100 times more signal, and every "
                    "layer gets a usable gradient. The shortcut gives the gradient a direct path back. That is why "
                    "every transformer block contains `x = x + shortcut` twice.",
    },
    21: {
        "first": "class TransformerBlock(nn.Module):", "title": "TransformerBlock: all parts together", "section": "4.5",
        "intro": "One block of GPT-2: attention (tokens exchange information) and feed-forward (each token processes "
              "what it received), each wrapped in LayerNorm, dropout and a shortcut. GPT-2 stacks 12 of these.",
        "lines": [
            ("4–10", ("The attention layer from `src/attention.py`. The config names and the parameter names differ, "
                     "so they are mapped by keyword: `d_in` and `d_out` ← `emb_dim` (768 in, 768 out), "
                     "`context_length` ← `context_length` (it builds the 1,024 × 1,024 causal mask), "
                     "`num_heads` ← `n_heads`, `dropout` ← `drop_rate`, `qkv_bias` ← `qkv_bias`.")),
            ("11", "The feed-forward network of cell 14."),
            ("12–13", "Two *separate* LayerNorms, one before each sublayer. Each has its own scale and shift."),
            ("14", "Dropout applied to each sublayer's output before it is added back."),
            ("18", "Saves the input: `shortcut` is the path that skips the sublayer."),
            ("19", ("Normalizes **first**. Normalizing before the sublayer is called *pre-LayerNorm*; GPT-2 does it "
                   "this way because it trains more stably in deep stacks.")),
            ("20", "Attention: each token gathers information from earlier tokens (the causal mask hides later ones)."),
            ("21", "Dropout on the attention output."),
            ("22", "Adds the saved input back: the shortcut connection of section 4.4."),
            ("24", ("Saves the input **again**. The second half must add back the output of the first half, not the "
                   "original input. Forgetting this line gives no error, only a wrong model.")),
            ("25–28", "The same pattern for the feed-forward half: normalize, process, dropout, add back."),
            ("29", "Returns the result, still [batch, tokens, 768]."),
        ],
        "note": "Parameters of one block: attention 2,360,064 (Q, K, V without bias: 3 × 768²; output projection "
             "with bias: 768² + 768) + feed-forward 4,722,432 + two LayerNorms 3,072 = 7,085,568 (cell 25).",
    },
    22: {
        "first": "torch.manual_seed(123)", "title": "Test one block", "section": "4.5",
        "intro": "Pushes random data through one block to confirm that the shape is preserved.",
        "lines": [
            ("1", "Seed."),
            ("2", "`torch.rand` (uniform between 0 and 1, unlike `randn`): 2 sequences × 4 tokens × 768."),
            ("3", "Builds one block with GPT-2 sizes."),
            ("4", "Runs it."),
            ("5–6", "Compares the shapes."),
        ],
        "output_note": "[2, 4, 768] in and out. Inside the attention the shapes are [2, 12, 4, 64] (12 heads × "
                    "64 dimensions) and the scores [2, 12, 4, 4]; inside the feed-forward [2, 4, 3,072].",
    },
    23: {
        "first": "class GPTModel(nn.Module):", "title": "GPTModel: the real thing", "section": "4.6",
        "intro": "Exactly `DummyGPTModel` (cell 3) with the two placeholders replaced. Everything else, including "
              "`forward`, is line for line the same, so see cell 3 for the shared lines.",
        "lines": [
            ("4–6", "Token embedding, position embedding, dropout: as in cell 3."),
            ("8–9", "12 real `TransformerBlock`s instead of dummies."),
            ("11", "The real `LayerNorm` instead of the dummy."),
            ("12", "`out_head` 768 → 50,257, as before."),
            ("14–24", ("`forward` as in cell 3. Line 18 must say `torch.arange` (\"a range\"); `torch.arrange` "
                      "raises `module 'torch' has no attribute 'arrange'` (Oct 10).")),
        ],
    },
    24: {
        "first": "torch.manual_seed(123)", "title": "Run the real model", "section": "4.6",
        "intro": "The same input as cell 5, now through 12 real blocks.",
        "lines": [
            ("1–2", "Seed and model: about 163 million random starting values."),
            ("4", "`logits = model(batch)`: named `logits` because that is what they are (and not `out`, cell 6)."),
            ("5–7", "Input, shape, values."),
        ],
        "output_note": "Same shape as the dummy, [2, 4, 50257], but different numbers: they now passed through 12 "
                    "real blocks. Still meaningless, because the weights are random until chapter 5.",
    },
    25: {
        "first": "print(sum(p.numel() for p in block.parameters()))", "title": "Parameters in one block",
        "section": "4.5", "intro": "Counts the numbers inside the single block built in cell 22.",
        "lines": [("1", ("`block.parameters()` yields every weight tensor; `p.numel()` is how many numbers each "
                     "contains; `sum(...)` adds them up."))],
        "output_note": "7,085,568, matching the breakdown under cell 21.",
    },
    26: {
        "first": "total_params = sum(p.numel() for p in model.parameters())", "title": "Parameters in the whole model",
        "section": "4.6", "intro": "Counts every number in the full model.",
        "lines": [
            ("1", "Same counting as cell 25, for the whole model."),
            ("2", "`{total_params:,}` prints the number with thousands separators."),
        ],
        "output_note": "163,009,536 = 12 blocks (85,026,816) + `tok_emb` (38,597,376) + `out_head` (38,597,376) + "
                    "`pos_emb` (786,432) + `final_norm` (1,536). The original GPT-2 shares one matrix between "
                    "`tok_emb` and `out_head` (*weight tying*); counted once, 163,009,536 − 38,597,376 = "
                    "124,412,160, the \"124M\". At 4 bytes per number the model needs 652,038,144 bytes "
                    "= 621.83 MB (the book divides by 1,024 × 1,024).",
    },
    27: {
        "first": "def generate_text_simple(model, idx, max_new_tokens, context_size):", "title": "Generate text, one token at a time",
        "section": "4.7",
        "intro": "A GPT model only ever predicts *one* next token. Text is produced by repeating: predict, append, "
              "predict again.",
        "lines": [
            ("1", ("`idx`: the token IDs so far, shape [batch, n]. `max_new_tokens`: how many to add. "
                  "`context_size`: the longest input the model accepts.")),
            ("2", "Repeats once per new token."),
            ("3", ("`idx[:, -context_size:]` keeps at most the last 1,024 tokens. Here the input is only 4–9 "
                  "tokens, so nothing is cut; with very long texts this keeps the input within the position table.")),
            ("4–5", ("`torch.no_grad()` switches off gradient bookkeeping: we are only predicting, not training, so "
                    "this saves time and memory. `logits` has shape [1, n, 50,257].")),
            ("7", ("`logits[:, -1, :]`: only the **last** position, shape [1, 50,257]. Only the last token's scores "
                  "predict what comes next.")),
            ("8", "`softmax` turns the scores into probabilities that sum to 1."),
            ("9", ("`argmax` picks the token with the highest probability (*greedy decoding*). `keepdim=True` keeps "
                  "the shape [1, 1] that `torch.cat` needs.")),
            ("10", ("Appends the new token along the sequence axis (`dim=1`): [1, 4] → [1, 5] → … The name `idx` is "
                   "overwritten, so the next round sees the longer sequence.")),
            ("11", "After the loop: [1, 4 + 6] = [1, 10]."),
        ],
        "note": "Softmax never changes which score is largest, so `argmax` of the logits gives the same token. The "
             "book keeps the softmax step to show the probabilities. For your untrained model the highest "
             "probability is only 0.0002 (0.02%), barely above a uniform guess of 1/50,257 = 0.00002: it has no "
             "idea yet.",
    },
    28: {
        "first": 'start_context = "Hello, I am"', "title": "Prepare the prompt", "section": "4.7",
        "intro": "Turns the starting text into the [batch, tokens] tensor the model expects.",
        "lines": [
            ("1", "The prompt."),
            ("2", "Token IDs: 15496 \"Hello\", 11 \",\", 314 \" I\", 716 \" am\"."),
            ("3", "Prints them."),
            ("4", "`unsqueeze(0)` adds a batch axis in front: [4] → [1, 4], a batch of one sentence."),
            ("5", "Confirms the shape."),
        ],
    },
    29: {
        "first": "model.eval()", "title": "Generate six tokens", "section": "4.7",
        "intro": "Switches the model to prediction mode and extends the prompt by six tokens.",
        "lines": [
            ("1", ("`model.eval()` turns dropout off. Without it, 10% of values would be randomly zeroed in every "
                  "pass, and the output would differ from run to run and from the book.")),
            ("2–7", ("Calls the function with keyword arguments: the model, the prompt, 6 new tokens, and a "
                    "context size of 1,024.")),
            ("8–9", "The result is named `token_ids` (not `out`, cell 6)."),
        ],
        "output_note": "The four prompt IDs followed by six new ones: 27018 \" Feature\", 24086 \"iman\", 47843 \" Bye\", "
                    "30961 \"swick\", 42348 \"attribute\", 7267 \" argue\". Length 10.",
    },
    30: {
        "first": "decoded_text = tokenizer.decode(token_ids.squeeze(0).tolist())", "title": "Back to text",
        "section": "4.7", "intro": "Converts the IDs back into readable text.",
        "lines": [
            ("1", ("`squeeze(0)` removes the batch axis ([1, 10] → [10]); `.tolist()` makes a plain Python list; "
                  "`decode` maps each ID back to its text piece and joins them.")),
            ("2", "Prints the text."),
        ],
        "output_note": "\"Featureiman Byeswickattribute argue\": the pieces run together because some tokens have no "
                    "leading space. Gibberish is the correct result for an untrained model. Chapter 5 trains it.",
    },
}

SECTIONS = [
    ("4.1", "A skeleton of the model", "Cells 1–5"),
    ("4.2", "Layer normalization", "Cells 6–11"),
    ("4.3", "GELU and the feed-forward network", "Cells 12–15"),
    ("4.4", "Shortcut connections", "Cells 16–20"),
    ("4.5", "The transformer block", "Cells 21–22 (and 25)"),
    ("4.6", "The full GPT model", "Cells 23–24, 26"),
    ("4.7", "Generating text", "Cells 27–30"),
]

FRONT = """
<h1>{title}</h1>
<p class="sub">Every line of <code>notebooks/04_gpt_model.ipynb</code>, explained. Code and outputs are taken
directly from the notebook; the explanations follow Raschka, <i>Build a Large Language Model (From Scratch)</i>,
chapter 4.</p>

<h2>How to use this document</h2>
<p>Keep the notebook open next to it. Each cell has the same number as its position in the notebook (cell 1 is the
first cell), its code with line numbers, a table explaining each line, and the cell's real output. On a second
reading, try to explain each line yourself before looking at the table.</p>

<h2>The big picture</h2>
<p>Chapter 4 adds few new ideas. It assembles parts you already know into one machine. This is what happens to the
batch of 2 sentences × 4 tokens:</p>
<pre>token IDs                    [2, 4]          chapter 2
 -> token embedding          [2, 4, 768]     chapter 2
 -> + position embedding     [2, 4, 768]     chapter 2
 -> dropout
 -> TransformerBlock x 12    [2, 4, 768]     4.5  (shape never changes)
      LayerNorm               4.2
      MultiHeadAttention      chapter 3       tokens exchange information
      dropout, + shortcut     4.4
      LayerNorm               4.2
      FeedForward + GELU      4.3             each token processes on its own
      dropout, + shortcut     4.4
 -> final LayerNorm          [2, 4, 768]     4.2
 -> out_head (Linear)        [2, 4, 50257]   4.6  one score per vocabulary token
 -> pick the best next token, append, repeat  4.7</pre>
<p>One sentence to remember: <b>attention lets tokens exchange information, the feed-forward network lets each
token process what it received, and the block repeats this 12 times.</b></p>

<table><tr><th>Section</th><th>Topic</th><th>Notebook cells</th></tr>{sections}</table>
"""

BACK = """
<h2>Shapes at a glance</h2>
<table>
<tr><th>Stage</th><th>Shape</th><th>Cell</th></tr>
<tr><td>Token IDs (<code>batch</code>)</td><td><code>[2, 4]</code></td><td>4</td></tr>
<tr><td>Token embeddings</td><td><code>[2, 4, 768]</code></td><td>3/23, line 17/16</td></tr>
<tr><td>Position embeddings</td><td><code>[4, 768]</code> (broadcast to both sentences)</td><td>3/23, line 18</td></tr>
<tr><td>Inside attention: per head</td><td><code>[2, 12, 4, 64]</code>; scores <code>[2, 12, 4, 4]</code></td><td>src/attention.py</td></tr>
<tr><td>Inside feed-forward</td><td><code>[2, 4, 3072]</code></td><td>14</td></tr>
<tr><td>After each block and after <code>final_norm</code></td><td><code>[2, 4, 768]</code></td><td>21–23</td></tr>
<tr><td>Logits</td><td><code>[2, 4, 50257]</code></td><td>24</td></tr>
<tr><td>Generation: prompt → result</td><td><code>[1, 4]</code> → <code>[1, 10]</code></td><td>28–29</td></tr>
</table>

<h2>Mistakes made along the way, and what they teach</h2>
<p>All of these happened while typing this notebook (Oct 9–10). Rereading them is worth as much as rereading the code.</p>
<table>
<tr><th>What happened</th><th>Message</th><th>Lesson</th></tr>
<tr><td>Copied <code>MultiHeadAttentionWrapper</code> into <code>src/attention.py</code> instead of <code>MultiHeadAttention</code></td>
<td><code>ImportError: cannot import name</code></td><td>Similar names: check that you copied the right one.</td></tr>
<tr><td>Fixed the file, but the kernel still held the old copy</td><td>the same <code>ImportError</code></td>
<td>After editing a <code>.py</code> file, restart the kernel.</td></tr>
<tr><td>Cell 8 overwrote the <code>mean</code>/<code>var</code> it reads; running it twice undid the normalization</td>
<td>none (silently wrong)</td><td>A cell should not overwrite a name it reads.</td></tr>
<tr><td>Renamed in cell 7 instead of cell 8</td><td><code>NameError: name 'mean' is not defined</code></td>
<td>Rename the <i>results</i>, in the cell that produces them.</td></tr>
<tr><td>Printed <code>var</code> instead of <code>var_norm</code></td><td>none (showed 0.0231 instead of 1.0)</td>
<td>"No error" is not "correct": compare with what you expect.</td></tr>
<tr><td><code>FeedForward.forward</code> without <code>return</code></td><td><code>'NoneType' object has no attribute 'shape'</code></td>
<td><code>NoneType</code> almost always means a function returned nothing.</td></tr>
<tr><td><code>GELU</code> instead of <code>GELU()</code></td><td><code>GELU is not a Module subclass</code></td>
<td>The class is the blueprint; <code>()</code> builds the object.</td></tr>
<tr><td><code>'weights'</code> instead of <code>'weight'</code></td><td>none (printed nothing)</td>
<td>Check the actual names with <code>named_parameters()</code>.</td></tr>
<tr><td><code>torch.arrange</code></td><td><code>module 'torch' has no attribute 'arrange'</code></td>
<td>It is "a-range". English spelling pulls the fingers astray.</td></tr>
<tr><td>Renamed <code>out</code> to <code>token_ids</code> in cell 29 but not in cell 30</td>
<td><code>'list' object cannot be interpreted as an integer</code></td><td>Rename a variable everywhere it is used.</td></tr>
</table>

<h2>Questions to test yourself</h2>
<ol class="qa">
<li>Why does the notebook need <code>sys.path.append("..")</code>?</li>
<li>What do the three numbers in <code>[2, 4, 50257]</code> mean?</li>
<li>Why does <code>keepdim=True</code> matter in cell 7?</li>
<li>What are <code>scale</code> and <code>shift</code> in <code>LayerNorm</code>, and why do they start at 1 and 0?</li>
<li>Why is there a GELU between the two Linear layers of <code>FeedForward</code>?</li>
<li>What does the gradient table of cells 19–20 show?</li>
<li>Why must <code>shortcut = x</code> appear twice in <code>TransformerBlock.forward</code>?</li>
<li>Where does the difference between 163 million and 124 million parameters come from?</li>
<li>Why does <code>generate_text_simple</code> use only <code>logits[:, -1, :]</code>?</li>
<li>What happens if you forget <code>model.eval()</code> before generating?</li>
</ol>
<p><b>Answers.</b> (1) The notebook runs in <code>notebooks/</code>; <code>src/</code> is one folder up. (2) 2 sentences,
4 positions, 50,257 scores per position. (3) It keeps the mean as [2, 1] so it can be subtracted from [2, 6]. (4) Trainable
per-feature stretch and offset; 1 and 0 mean "no change" at the start. (5) Without a non-linearity, two Linear layers
collapse into one. (6) Without shortcuts the first layer's gradient is about 1,100 times smaller (vanishing gradients).
(7) The second half must add back the first half's output, not the original input. (8) Weight tying: <code>tok_emb</code>
and <code>out_head</code> share one 38.6M matrix in the original GPT-2. (9) Only the last position predicts the next token.
(10) Dropout stays on, so the output is random and differs from the book.</p>
"""


def code_block(lines):
    width = len(str(len(lines)))
    rows = [f'<span class="ln">{str(n).rjust(width)}</span>  {html.escape(line)}'
            for n, line in enumerate(lines, start=1)]
    return "<pre>" + "\n".join(rows) + "</pre>"


def cell_outputs(cell):
    parts = []
    for o in cell.get("outputs", []):
        data = o.get("data", {})
        if "image/png" in data:
            parts.append(f'<img class="plot" src="data:image/png;base64,{data["image/png"]}">')
            continue
        text = "".join(o.get("text", "")) or "".join(data.get("text/plain", ""))
        if o.get("output_type") == "error":
            raise SystemExit(f"cell has an error output ({o['ename']}); rerun the notebook first")
        if text.strip() and not text.startswith("<Figure"):
            parts.append(f'<pre class="output">{html.escape(text.rstrip())}</pre>')
    if not parts:
        return ""
    return '<p class="outlabel">Output</p>' + "".join(parts)


def build():
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    cells = [c for c in nb["cells"] if c["cell_type"] == "code"]
    if len(cells) != len(CELLS):
        raise SystemExit(f"notebook has {len(cells)} code cells, explanations cover {len(CELLS)}")

    body = [FRONT.format(title=html.escape(TITLE), sections="".join(
        f"<tr><td>{n}</td><td>{t}</td><td>{c}</td></tr>" for n, t, c in SECTIONS))]
    current = None
    for number, cell in enumerate(cells, start=1):
        info = CELLS[number]
        lines = "".join(cell["source"]).rstrip("\n").split("\n")
        if lines[0].strip() != info["first"]:
            raise SystemExit(f"cell {number} starts with {lines[0]!r}, expected {info['first']!r}")
        if info["section"] != current and number not in (25,):
            current = info["section"]
            name = next(t for n, t, _ in SECTIONS if n == current)
            body.append(f"<h2>{current} {html.escape(name)}</h2>")
        out = [(f'<div class="cell"><h3>Cell {number}: {html.escape(info["title"])}'
               f'<span class="tag">section {info["section"]}</span></h3>')]
        if info.get("intro"):
            out.append(f'<p class="intro">{inline(info["intro"])}</p>')
        out.append(code_block(lines))
        out.append('<table class="lines"><tr><th>Line</th><th>What it does</th></tr>' + "".join(
            f"<tr><td>{label}</td><td>{inline(text)}</td></tr>" for label, text in info["lines"]) + "</table>")
        out.append(cell_outputs(cell))
        if info.get("output_note"):
            out.append(f'<div class="note">{inline(info["output_note"])}</div>')
        if info.get("note"):
            out.append(f'<div class="note">{inline(info["note"])}</div>')
        if info.get("warn"):
            out.append(f'<div class="warn">{inline(info["warn"])}</div>')
        out.append("</div>")
        body.append("".join(out))
    body.append(BACK)
    body.append('<p class="end">Generated by tools/pdf/gpt_model_walkthrough.py from '
                'notebooks/04_gpt_model.ipynb</p>')

    page = (f'<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(TITLE)}</title>'
            f"<style>{CSS}</style></head><body>{''.join(body)}</body></html>")
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
