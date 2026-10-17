# /// script
# dependencies = []
# ///
"""Line-by-line guides for src/ modules -> docs/Src_Tokenizer_Line_by_Line.pdf,
docs/Src_Attention_Line_by_Line.pdf

Run from anywhere:  uv run tools/pdf/src_walkthrough.py

Same approach as gpt_model_walkthrough.py (and it reuses that script's style and helpers):
the code is read from src/*.py at build time, the explanations are keyed by line number,
and each block records the text of its first line, so the build stops if the file has
changed instead of explaining the wrong lines.

Every example value was checked by running the modules (the-verdict.txt for the
tokenizer; a [2, 4, 768] input with seed 123 for attention).
"""
import html
import subprocess
import tempfile
from pathlib import Path

from gpt_model_walkthrough import CHROME, CSS, inline

REPO = Path(__file__).resolve().parents[2]

# Keep a block (heading + code + its table) and every table on one page when it fits,
# so a table header is never stranded at the bottom of a page.
EXTRA_CSS = """
.block { margin-top: 10pt; break-inside: avoid; }
table { break-inside: avoid; }
"""

# ---------------------------------------------------------------------------
# src/tokenizer.py
# ---------------------------------------------------------------------------
TOKENIZER = {
    "source": "src/tokenizer.py",
    "out": "Src_Tokenizer_Line_by_Line.pdf",
    "label": "src/tokenizer.py line by line",
    "title": "src/tokenizer.py Line by Line: A Word-Level Tokenizer",
    "front": """
<h2>What this file is</h2>
<p>The simple tokenizer of chapter 2 (sections 2.2–2.4), kept in <code>src/</code> so that notebooks and the tests in
<code>tests/test_tokenizer.py</code> can import it. It turns text into token IDs and back:</p>
<pre>text  --preprocess-->  tokens  --build_vocab-->  vocabulary {token: ID}
text  --encode------>  IDs     --decode------->  text</pre>
<p>On <code>data/the-verdict.txt</code>: 20,479 characters → <b>4,690 tokens</b> → a vocabulary of <b>1,130</b> different tokens.</p>
<p>It is a teaching tokenizer. From chapter 4 on, the model uses GPT-2's BPE tokenizer (<code>tiktoken</code>, 50,257 tokens),
which never fails on an unknown word because it can split any word into smaller pieces. The limits of this simple version
(listed at the end) are exactly why BPE exists.</p>
""",
    "blocks": [
        {"start": 1, "end": 3, "first": "import re", "title": "The splitting rule",
             "intro": "One regular expression decides where text is cut into tokens.",
             "lines": [
                 ("1", "`re` is Python's regular-expression module: a small language for describing text patterns."),
                 ("3", ("`SPLIT_PATTERN`, in capitals because it is a constant. The `r` in front makes a *raw string*: "
                       "backslashes are kept as they are, so the regex receives `\\s` intact.")),
                 ("3: ( … )", ("The outer parentheses form a *capturing group*. With a group, `re.split` keeps the "
                              "separators in its result instead of throwing them away: `re.split(r'(\\s)', 'a b')` "
                              "gives `['a', ' ', 'b']`; without the group, `['a', 'b']`. That is how punctuation "
                              "becomes tokens of its own.")),
                 ("3: [ … ]", ("A *character class*: any one of `, . : ; ? _ ! \" ( ) '`. Inside square brackets, "
                              "`.`, `?` and `(` lose their special regex meanings and stand for themselves. The "
                              "apostrophe is written `\\'` only because the whole string is enclosed in single quotes.")),
                 ("3: |--|\\s", ("`|` means \"or\". `--` is the double hyphen that *the-verdict* uses as a dash; `\\s` is "
                                "any whitespace (space, tab, newline). So the text is cut at punctuation, at `--`, and at "
                                "whitespace.")),
             ],
             "warn": "The long dash \"—\" (U+2014) is not in the pattern, so \"love—\" stays one token, unrelated to "
                  "\"love\". `test_em_dash_is_not_a_delimiter` records this on purpose."},
        {"start": 6, "end": 8, "first": "def preprocess(text):", "title": "preprocess: cut text into tokens",
             "intro": "Returns the list of tokens of a text.",
             "lines": [
                 ("6", "Takes one string, `text`."),
                 ("7", ("`re.split` cuts at every match of the pattern and, because of the capturing group, keeps the "
                       "separators. The raw result for `\"Hello, world. Is this-- a test?\"` is "
                       "`['Hello', ',', '', ' ', 'world', '.', '', ' ', 'Is', ' ', 'this', '--', '', ' ', 'a', ' ', "
                       "'test', '?', '']`: tokens mixed with spaces and empty strings.")),
                 ("8", ("A list comprehension cleans this up. `item.strip()` removes surrounding whitespace, so a space "
                       "becomes `''`; the condition `if item.strip()` keeps only items that are not empty after "
                       "stripping. Result: `['Hello', ',', 'world', '.', 'Is', 'this', '--', 'a', 'test', '?']`.")),
             ],
             "note": "Spaces are thrown away here, and so is the information about *where* they were. This is why "
                  "`decode` (line 27) can only guess the original spacing."},
        {"start": 11, "end": 13, "first": "def build_vocab(text):", "title": "build_vocab: give every distinct token an ID",
             "intro": "Builds the vocabulary: a dictionary from each different token to a whole number.",
             "lines": [
                 ("12", ("Three steps read from the inside out: `preprocess(text)` makes the token list (4,690 tokens "
                        "for the-verdict); `set(...)` keeps each token once (1,130); `sorted(...)` puts them in a fixed "
                        "order. Sorting compares character codes, so punctuation comes first and capitals come "
                        "before lowercase: `sorted(['apple', 'Banana', 'cat', 'Apple', '!'])` is "
                        "`['!', 'Apple', 'Banana', 'apple', 'cat']`.")),
                 ("13", ("A dictionary comprehension. `enumerate(all_words)` yields pairs (0, '!'), (1, '\"'), …; the "
                        "comprehension turns each pair around into `token: integer`. For the-verdict the vocabulary "
                        "starts `'!': 0, '\"': 1, \"'\": 2, '(': 3, ')': 4, ',': 5, '--': 6, '.': 7, …, 'A': 11` and "
                        "ends `'younger': 1127, 'your': 1128, 'yourself': 1129`.")),
             ],
             "note": "Why sort at all? A Python `set` has no reliable order: for strings it can even change from one run "
                  "of Python to the next. Without `sorted`, the same text could get different IDs each time. "
                  "`test_vocab_ids_are_contiguous` checks that the IDs are exactly 0, 1, …, N − 1."},
        {"start": 16, "end": 19, "first": "class SimpleTokenizerV1:", "title": "The tokenizer class and its two dictionaries",
             "intro": "Stores the vocabulary in both directions, so encoding and decoding are both a simple lookup.",
             "lines": [
                 ("16", "A plain class, not an `nn.Module`: a tokenizer has nothing to learn."),
                 ("17", "Receives a ready-made vocabulary, usually from `build_vocab`."),
                 ("18", "`str_to_int`: token → ID, used by `encode`."),
                 ("19", ("`int_to_str`: ID → token, used by `decode`. `vocab.items()` yields (token, ID) pairs, and "
                        "`{i: s for s, i in ...}` swaps each pair. This works because every token has exactly one ID "
                        "and every ID belongs to exactly one token. Here `int_to_str[0]` is `'!'`.")),
             ],
             "note": "Line 19 must use the parameter `vocab`. In session 03 an early version read a *global* variable "
                  "with a similar name instead. It worked in the notebook by accident and would have broken "
                  "anywhere else. Lesson: inside a function, use what was passed in."},
        {"start": 21, "end": 23, "first": "def encode(self, text):", "title": "encode: text → IDs",
             "intro": "",
             "lines": [
                 ("22", ("Splits the text with `preprocess` and looks up each token's ID. The book's example sentence "
                        "`\"It's the last he painted, you know,\" Mrs. Gisburn said with pardonable pride.` becomes 21 "
                        "IDs: `[1, 56, 2, 850, 988, 602, 533, 746, 5, 1126, 596, 5, 1, 67, 7, 38, 851, 1108, 754, 793, 7]`. "
                        "The first `1` is the opening `\"`; `5` is `,`; `7` is `.`.")),
                 ("23", "Returns the list."),
             ],
             "warn": "A token that is not in the vocabulary raises `KeyError`. \"Hello\" never occurs in the-verdict, so "
                  "`encode(\"Hello, do you like tea?\")` fails with `KeyError: 'Hello'`. Version 2 (section 2.4) "
                  "replaces unknown tokens with `<|unk|>`; `test_unknown_token_raises` documents the V1 behaviour."},
        {"start": 25, "end": 28, "first": "def decode(self, ids):", "title": "decode: IDs → text",
             "intro": "Turns IDs back into a readable string, as well as the lost spacing allows.",
             "lines": [
                 ("26", ("Looks up each ID's token and joins them with single spaces. For the example: "
                        "`\" It ' s the last he painted , you know , \" Mrs . Gisburn said with pardonable pride .`: "
                        "a space before every punctuation mark.")),
                 ("27", ("Removes those spaces. `\\s+` = one or more whitespace characters, followed by a captured "
                        "punctuation mark `([,.:;?_!\"()\\'])`; the replacement `\\1` is just the captured mark. So "
                        "`\"painted ,\"` becomes `\"painted,\"`. Result: "
                        "`\" It' s the last he painted, you know,\" Mrs. Gisburn said with pardonable pride.`")),
                 ("28", "Returns the text."),
             ],
             "note": "The result is close but not identical: `\" It' s` keeps a space after the opening quote and inside "
                  "\"It's\". The rule only removes spaces *before* punctuation, and preprocess already threw away "
                  "where the real spaces were. `test_encode_decode_roundtrip` passes because its sentence has only "
                  "commas and periods after words. BPE tokenizers keep the spaces inside the tokens (\" effort\"), so "
                  "they decode exactly."},
    ],
    "back": """
<h2>What the tests protect</h2>
<table><tr><th>Test (tests/test_tokenizer.py)</th><th>Checks</th></tr>
<tr><td><code>test_preprocess_keeps_punctuation_as_tokens</code></td><td><code>"a, b."</code> → <code>["a", ",", "b", "."]</code> (the capturing group, line 3)</td></tr>
<tr><td><code>test_vocab_ids_are_contiguous</code></td><td>IDs are exactly 0 … N − 1 (line 13)</td></tr>
<tr><td><code>test_encode_decode_roundtrip</code></td><td>decode(encode(text)) gives the text back, for a simple sentence (lines 22, 26–27)</td></tr>
<tr><td><code>test_encode_is_deterministic</code></td><td>The same text always gives the same IDs</td></tr>
<tr><td><code>test_unknown_token_raises</code></td><td>Unknown token → <code>KeyError</code> (line 22)</td></tr>
<tr><td><code>test_em_dash_is_not_a_delimiter</code></td><td>"—" is not a split point (line 3)</td></tr>
</table>

<h2>Limits of this tokenizer, and what replaces it</h2>
<table><tr><th>Limit</th><th>Where</th><th>Fixed by</th></tr>
<tr><td>Unknown words crash with <code>KeyError</code></td><td>line 22</td><td><code>&lt;|unk|&gt;</code> in V2 (2.4); BPE never needs it</td></tr>
<tr><td>Spacing cannot be restored exactly</td><td>lines 8, 27</td><td>BPE keeps spaces inside tokens</td></tr>
<tr><td>The vocabulary depends on one text (1,130 tokens)</td><td>line 12</td><td>GPT-2's fixed 50,257-token BPE vocabulary</td></tr>
<tr><td>Only the listed punctuation is split off</td><td>line 3</td><td>BPE learns its pieces from data</td></tr>
</table>

<h2>Questions to test yourself</h2>
<ol class="qa">
<li>Why does <code>SPLIT_PATTERN</code> need the outer parentheses?</li>
<li>Why does <code>preprocess</code> call <code>strip()</code>, and what would the token list contain without the <code>if</code>?</li>
<li>Why is the vocabulary sorted?</li>
<li>Why does the tokenizer keep two dictionaries?</li>
<li>What happens when you encode a word that is not in the vocabulary?</li>
<li>Why can <code>decode</code> not always restore the original text?</li>
</ol>
<p><b>Answers.</b> (1) A capturing group makes <code>re.split</code> keep the separators, so punctuation becomes tokens.
(2) To drop whitespace; without the condition the list would contain <code>''</code> items. (3) A set has no reliable
order; sorting gives the same IDs every run. (4) One lookup direction each: <code>encode</code> needs token → ID,
<code>decode</code> needs ID → token. (5) <code>KeyError</code>. (6) <code>preprocess</code> discarded where the spaces were;
the regex in line 27 only removes spaces before punctuation.</p>
""",
}

# ---------------------------------------------------------------------------
# src/attention.py
# ---------------------------------------------------------------------------
ATTENTION = {
    "source": "src/attention.py",
    "out": "Src_Attention_Line_by_Line.pdf",
    "label": "src/attention.py line by line",
    "title": "src/attention.py Line by Line: Multi-Head Attention",
    "front": """
<h2>What this file is</h2>
<p>The efficient <code>MultiHeadAttention</code> of section 3.6.2, moved out of <code>03_attention.ipynb</code> so that
chapter 4 can import it. Every <code>TransformerBlock</code> contains one, so GPT-2 (124M) has twelve.</p>
<p>Running example throughout: GPT-2 sizes, <code>MultiHeadAttention(768, 768, 1024, 0.1, num_heads=12)</code> applied to an
input <code>x</code> of shape <b>[2, 4, 768]</b> (2 sequences, 4 tokens, 768 numbers per token), created after
<code>torch.manual_seed(123)</code>.</p>

<h2>The idea in one paragraph</h2>
<p>Each token makes a <b>query</b> (what am I looking for?), a <b>key</b> (what do I offer?) and a <b>value</b> (what do I
pass on?). Comparing every query with every key gives scores; the causal mask hides tokens that come later; softmax turns
the scores into weights; each token's output is the weighted sum of the values. <i>Multi-head</i> means this is done 12 times
in parallel on 12 slices of 64 numbers, so different heads can look for different relationships, and the results are glued
back together.</p>

<h2>Shapes, step by step</h2>
<table><tr><th>Lines</th><th>Step</th><th>Shape</th></tr>
<tr><td>24</td><td>input <code>x</code></td><td><code>[2, 4, 768]</code></td></tr>
<tr><td>25–27</td><td>keys, queries, values</td><td><code>[2, 4, 768]</code></td></tr>
<tr><td>29–31</td><td>split into 12 heads of 64</td><td><code>[2, 4, 12, 64]</code></td></tr>
<tr><td>33–35</td><td>heads to the front</td><td><code>[2, 12, 4, 64]</code></td></tr>
<tr><td>37</td><td>attention scores</td><td><code>[2, 12, 4, 4]</code></td></tr>
<tr><td>38–44</td><td>mask, scale, softmax, dropout</td><td><code>[2, 12, 4, 4]</code></td></tr>
<tr><td>46</td><td>weighted values, tokens back in front</td><td><code>[2, 4, 12, 64]</code></td></tr>
<tr><td>48–49</td><td>glue the heads back together</td><td><code>[2, 4, 768]</code></td></tr>
<tr><td>51</td><td>output projection</td><td><code>[2, 4, 768]</code></td></tr>
</table>
""",
    "blocks": [
        {"start": 1, "end": 3, "first": "import torch", "title": "Imports and the class",
             "intro": "",
             "lines": [
                 ("1–2", ("PyTorch and its neural-network toolbox `nn`. The file must import them itself: a `.py` file "
                         "does not see the notebook's imports.")),
                 ("3", ("`MultiHeadAttention` inherits from `nn.Module`, so PyTorch tracks its parameters and "
                       "`mha(x)` runs `forward(x)`.")),
             ]},
        {"start": 4, "end": 8, "first": "def __init__(self, d_in, d_out, context_length, dropout,",
             "title": "The settings, and a safety check",
             "intro": "",
             "lines": [
                 ("4–5", ("`d_in`: numbers per input token (768). `d_out`: numbers per output token (768). "
                         "`context_length`: the longest sequence the mask must cover (1,024). `dropout`: probability "
                         "for dropping attention weights (0.1). `num_heads`: 12. `qkv_bias`: whether the Q/K/V layers get "
                         "a bias term (default `False`). The line break inside the parentheses is allowed because the "
                         "bracket is still open.")),
                 ("6", "Sets up `nn.Module`'s bookkeeping. It must come before any layer is assigned."),
                 ("7–8", ("`assert condition, message` stops with `AssertionError` if the condition is false. `d_out` "
                         "must split evenly into heads: 768 % 12 = 0. With 5 heads it stops at once with "
                         "`AssertionError: d_out must be divisible by num_heads`, instead of failing later with a "
                         "confusing shape error at line 29. The `\\` at the end of line 7 continues the statement on "
                         "line 8. Without it the line ends in a comma, the `SyntaxError` you met on Sep 30.")),
             ],
             "warn": "Never write `assert (condition, \"message\")` with both inside one pair of parentheses: that is a "
                  "tuple, which is always true, so the check can never fail."},
        {"start": 10, "end": 12, "first": "self.d_out = d_out", "title": "Remember the sizes",
             "intro": "Saved so that `forward` can use them.",
             "lines": [
                 ("10", "`d_out` = 768, needed in line 49 to glue the heads back together."),
                 ("11", "`num_heads` = 12."),
                 ("12", "`head_dim` = 768 // 12 = **64** numbers per head. `//` is whole-number division."),
             ]},
        {"start": 13, "end": 17, "first": "self.W_query = nn.Linear(d_in, d_out, bias = qkv_bias)",
             "title": "The learnable layers",
             "intro": "",
             "lines": [
                 ("13–15", ("Three Linear layers 768 → 768 that turn each token into its query, key and value. Each "
                           "one holds the weights of **all 12 heads side by side**: columns 0–63 of the output belong "
                           "to head 0, 64–127 to head 1, and so on. That is what makes this version efficient: one "
                           "large matrix multiplication instead of twelve small ones (the `MultiHeadAttentionWrapper` "
                           "of 3.6.1 ran twelve separate heads). PyTorch stores the weight as [out, in] = [768, 768] "
                           "and computes `x @ W.T`.")),
                 ("16", ("`out_proj`: another Linear 768 → 768, this time with a bias (the default). After the heads "
                        "are glued together, it mixes the 12 heads' results. Without it, each head's 64 numbers would "
                        "stay separate.")),
                 ("17", "A dropout layer for the attention weights (line 44)."),
             ],
             "note": "Parameters: Q, K, V without bias 3 × 768 × 768 = 1,769,472; `out_proj` 768 × 768 + 768 = 590,592; "
                  "total **2,360,064**, one third of a transformer block's 7,085,568."},
        {"start": 18, "end": 21, "first": "self.register_buffer(", "title": "The causal mask, built once",
             "intro": "",
             "lines": [
                 ("20", ("`torch.ones(1024, 1024)`, then `torch.triu(..., diagonal=1)` keeps only the part strictly "
                        "above the diagonal: 1 where the column (key) comes *after* the row (query), the future; 0 "
                        "elsewhere. `diagonal=1` belongs to `triu`, not to `ones`. Putting it inside `ones(...)` was "
                        "the `TypeError` of Sep 30.")),
                 ("18–19", ("`register_buffer(\"mask\", ...)` stores the mask as `self.mask` and registers it with the "
                           "module. A *buffer* is saved with the model (it is the first entry of `state_dict()`) and "
                           "moves along with `.to(device)`, but it is **not** a parameter: it is not trained and not "
                           "counted in the 2,360,064.")),
             ],
             "note": "The mask is built once for the longest possible input (1,024 × 1,024) and cut to the actual length "
                  "in line 38. A plain attribute (`self.mask = ...`) would work on the CPU but would be left behind "
                  "when the model moves to a GPU."},
        {"start": 23, "end": 24, "first": "def forward(self, x):", "title": "forward: read the input's shape",
             "intro": "Everything from here runs every time data passes through.",
             "lines": [
                 ("23", "`x` has shape [batch, tokens, d_in] = [2, 4, 768]."),
                 ("24", ("Unpacks the three sizes: `b` = 2, `num_tokens` = 4, `d_in` = 768. `d_in` is not used again; "
                        "this local name has nothing to do with the `d_in` parameter of `__init__`.")),
             ]},
        {"start": 25, "end": 27, "first": "keys = self.W_key(x)", "title": "Queries, keys and values",
             "intro": "",
             "lines": [
                 ("25–27", ("Applies the three Linear layers. Each result is [2, 4, 768]: for every token, all 12 heads' "
                           "keys, queries or values in one row of 768 numbers. The order of the three lines does not "
                           "matter.")),
             ]},
        {"start": 29, "end": 31, "first": "keys = keys.view(b, num_tokens, self.num_heads, self.head_dim)",
             "title": "Split the 768 numbers into 12 heads",
             "intro": "",
             "lines": [
                 ("29–31", ("`view(2, 4, 12, 64)` reinterprets each row of 768 numbers as 12 groups of 64, without "
                           "copying anything. Head 1 is exactly columns 64–127 of the original row (checked: "
                           "`queries.view(...)[0, 0, 1]` equals `queries[0, 0, 64:128]`). Shape: [2, 4, 12, 64].")),
             ]},
        {"start": 33, "end": 35, "first": "keys = keys.transpose(1, 2)", "title": "Move the heads to the front",
             "intro": "",
             "lines": [
                 ("33–35", ("Swaps axes 1 and 2: [2, 4, 12, 64] → [2, 12, 4, 64]. `@` multiplies only the **last two** "
                           "axes and treats the others as a batch of independent problems. With the heads in front, "
                           "the last two axes are (tokens, 64), so one `@` handles all 2 × 12 = 24 attention problems at "
                           "once. `transpose` changes only the reading order, not the memory, so the result is no longer "
                           "*contiguous*. That matters again in line 48.")),
             ]},
        {"start": 37, "end": 37, "first": "attn_scores = queries @ keys.transpose(2, 3)", "title": "Attention scores",
             "intro": "",
             "lines": [
                 ("37", ("`keys.transpose(2, 3)` turns each head's keys from [4, 64] into [64, 4]. Then "
                        "[2, 12, 4, 64] @ [2, 12, 64, 4] = **[2, 12, 4, 4]**: for each sequence and each head, a 4 × 4 "
                        "table of dot products. Row i, column j measures how well token i's query matches token j's "
                        "key. `transpose(2, 3)` is the same as `transpose(-2, -1)` for 4-axis tensors.")),
             ]},
        {"start": 38, "end": 40, "first": "mask_bool = self.mask.bool()[:num_tokens, :num_tokens]",
             "title": "Hide the future",
             "intro": "",
             "lines": [
                 ("38", ("`.bool()` turns 1.0/0.0 into True/False; `[:4, :4]` cuts the 1,024 × 1,024 mask to the actual "
                        "4 tokens. True marks the positions to hide:")),
                 ("", ("`[[F, T, T, T], [F, F, T, T], [F, F, F, T], [F, F, F, F]]`. Token 0 may see only itself; "
                      "token 3 sees all four.")),
                 ("40", ("`masked_fill_` writes `-inf` wherever the mask is True. The trailing underscore means *in "
                        "place*: it changes `attn_scores` itself instead of returning a copy. The [4, 4] mask is "
                        "broadcast over all 2 × 12 score tables. Example (sequence 0, head 0, token 0): "
                        "`[-0.3811, -inf, -inf, -inf]`.")),
             ],
             "note": "Why `-inf` and not 0? Line 42 applies softmax, and e^(−inf) = 0. The hidden positions get weight "
                  "exactly 0, and the remaining weights still add up to 1."},
        {"start": 42, "end": 44, "first": "attn_weights = torch.softmax(", "title": "Scale, softmax, dropout",
             "intro": "",
             "lines": [
                 ("42–43", ("Divides by √64 = 8 (`keys.shape[-1]**0.5`; `**0.5` is the square root), then softmax "
                           "over the last axis, so each row becomes weights that sum to 1. For sequence 0, head 0: "
                           "`[1.0, 0, 0, 0]`, `[0.458, 0.542, 0, 0]`, `[0.315, 0.344, 0.341, 0]`, "
                           "`[0.240, 0.256, 0.244, 0.261]`. The first token can only attend to itself.")),
                 ("44", ("Dropout on the weights: during training 10% of them are zeroed at random (the rest scaled by "
                        "1/0.9). After `model.eval()` it does nothing, and the output is the same on every call "
                        "(checked: two calls in training mode give different results, in eval mode identical ones).")),
             ],
             "note": "Why divide by √d_k? A dot product of 64 numbers grows with their count; very large scores make "
                  "softmax put almost all weight on one token, and the gradients become tiny. Dividing by √64 keeps "
                  "the scores in a moderate range."},
        {"start": 46, "end": 46, "first": "context_vec = (attn_weights @ values).transpose(1, 2)",
             "title": "Weighted sum of the values",
             "intro": "",
             "lines": [
                 ("46", ("[2, 12, 4, 4] @ [2, 12, 4, 64] = [2, 12, 4, 64]: each token's new 64-number vector, per head, "
                        "is the weighted sum of the values it attends to. `transpose(1, 2)` puts the tokens back in "
                        "front: [2, 4, 12, 64].")),
             ]},
        {"start": 48, "end": 49, "first": "context_vec = context_vec.contiguous().view(",
             "title": "Glue the heads back together",
             "intro": "",
             "lines": [
                 ("48–49", ("The reverse of line 29: [2, 4, 12, 64] → [2, 4, 768], the 12 heads' 64 numbers placed side "
                           "by side again. `view` needs the numbers to lie in memory in reading order, which the "
                           "transpose of line 46 broke. `contiguous()` copies them into the right order first. Without "
                           "it: `RuntimeError: view size is not compatible with input tensor's size and stride ... "
                           "Use .reshape(...) instead.`")),
             ]},
        {"start": 51, "end": 52, "first": "context_vec = self.out_proj(context_vec)", "title": "Mix the heads and return",
             "intro": "",
             "lines": [
                 ("51", ("`out_proj` mixes the 768 numbers, letting the heads' findings combine. Still [2, 4, 768]: "
                        "the same shape as the input, which is what lets `TransformerBlock` add it back to the input "
                        "(the shortcut).")),
                 ("52", "Returns the context vectors."),
             ]},
    ],
    "back": """
<h2>Checking it against the book</h2>
<p>With the book's small example (<code>d_in=3, d_out=2, context_length=6, dropout=0.0, num_heads=2</code>, seed 123, the
6-token "Your journey starts with one step" input stacked twice) the module returns shape <code>[2, 6, 2]</code>, first rows
<code>[0.3190, 0.4858]</code>, <code>[0.2943, 0.3897]</code>, …, exactly the book's output.</p>

<h2>What is stored inside</h2>
<table><tr><th>Name in <code>state_dict()</code></th><th>Shape</th><th>Kind</th></tr>
<tr><td><code>mask</code></td><td><code>[1024, 1024]</code></td><td>buffer (saved, not trained)</td></tr>
<tr><td><code>W_query.weight</code>, <code>W_key.weight</code>, <code>W_value.weight</code></td><td><code>[768, 768]</code> each</td><td>parameters (no bias)</td></tr>
<tr><td><code>out_proj.weight</code>, <code>out_proj.bias</code></td><td><code>[768, 768]</code>, <code>[768]</code></td><td>parameters</td></tr>
</table>

<h2>Mistakes made along the way</h2>
<table><tr><th>When</th><th>What happened</th><th>Lesson</th></tr>
<tr><td>Sep 30</td><td><code>diagonal=1</code> placed inside <code>torch.ones(...)</code> → <code>TypeError</code></td><td>With nested calls, check which <code>(</code> each argument sits in.</td></tr>
<tr><td>Sep 30</td><td>Line 7 ended with a comma and no <code>\\</code> → <code>SyntaxError</code></td><td>A statement ends at the line end unless a bracket is open or the line ends in <code>\\</code>.</td></tr>
<tr><td>Oct 9</td><td><code>MultiHeadAttentionWrapper</code> copied into this file instead of <code>MultiHeadAttention</code> → <code>ImportError</code></td><td>Similar names: check that you copied the right one.</td></tr>
<tr><td>Oct 9</td><td>After the fix, the notebook still saw the old file</td><td>Restart the kernel after editing a <code>.py</code> file.</td></tr>
</table>

<h2>Questions to test yourself</h2>
<ol class="qa">
<li>What does <code>head_dim</code> equal for GPT-2, and why must <code>d_out % num_heads</code> be 0?</li>
<li>Why is the mask a buffer and not a parameter or a plain attribute?</li>
<li>What do <code>view</code> (line 29) and <code>transpose</code> (line 33) each do?</li>
<li>What is the shape of <code>attn_scores</code> for the running example, and what does one entry mean?</li>
<li>Why is the mask filled with <code>-inf</code> instead of 0?</li>
<li>Why is <code>contiguous()</code> needed in line 48?</li>
<li>What is <code>out_proj</code> for?</li>
<li>How many parameters does the module have, and where do they come from?</li>
</ol>
<p><b>Answers.</b> (1) 64; each head needs an equal whole-number slice. (2) It must be saved and moved with the model,
but not trained; a plain attribute would not move to the GPU. (3) <code>view</code> regroups 768 numbers into 12 × 64
without copying; <code>transpose</code> moves the heads in front of the tokens so one <code>@</code> serves all heads.
(4) [2, 12, 4, 4]: how well token i's query matches token j's key, for one sequence and one head. (5) softmax turns
<code>-inf</code> into exactly 0 and the other weights still sum to 1. (6) The transpose left the numbers out of reading
order; <code>view</code> requires reading order. (7) It mixes the 12 heads' results. (8) 2,360,064: Q, K, V 3 × 768²,
plus <code>out_proj</code> 768² + 768.</p>
""",
}


def code_block(lines, start):
    width = len(str(start + len(lines) - 1))
    rows = [f'<span class="ln">{str(n).rjust(width)}</span>  {html.escape(line)}'
            for n, line in enumerate(lines, start=start)]
    return "<pre>" + "\n".join(rows) + "</pre>"


def build(spec):
    source = (REPO / spec["source"]).read_text(encoding="utf-8").split("\n")
    body = [f"<h1>{html.escape(spec['title'])}</h1>",
            (f'<p class="sub">Every line of <code>{spec["source"]}</code>, explained. The code is read from the file '
            "itself; line numbers match the file.</p>"), spec["front"],
            f"<h2>The code, block by block</h2><p>Full file: {len(source) - (source[-1] == '')} lines.</p>"]
    for block in spec["blocks"]:
        lines = source[block["start"] - 1:block["end"]]
        if lines[0].strip() != block["first"]:
            raise SystemExit(f"{spec['source']} line {block['start']} is {lines[0].strip()!r}, "
                             f"expected {block['first']!r}; update the explanations")
        out = [f'<div class="block"><h3>Lines {block["start"]}–{block["end"]}: {html.escape(block["title"])}</h3>'
               if block["start"] != block["end"] else
               f'<div class="block"><h3>Line {block["start"]}: {html.escape(block["title"])}</h3>']
        if block.get("intro"):
            out.append(f'<p class="intro">{inline(block["intro"])}</p>')
        out.append(code_block(lines, block["start"]))
        out.append('<table class="lines"><tr><th>Line</th><th>What it does</th></tr>' + "".join(
            f"<tr><td>{html.escape(label)}</td><td>{inline(text)}</td></tr>" for label, text in block["lines"])
            + "</table>")
        for kind in ("note", "warn"):
            if block.get(kind):
                out.append(f'<div class="{kind}">{inline(block[kind])}</div>')
        out.append("</div>")
        body.append("".join(out))
    body.append(spec["back"])
    body.append(f'<p class="end">Generated by tools/pdf/src_walkthrough.py from {spec["source"]}</p>')

    css = CSS.replace('"Chapter 4 line by line"', f'"{spec["label"]}"') + EXTRA_CSS
    page = (f'<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(spec["title"])}</title>'
            f"<style>{css}</style></head><body>{''.join(body)}</body></html>")
    out_path = REPO / "docs" / spec["out"]
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(page)
        tmp = Path(f.name)
    try:
        subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={out_path}", tmp.as_uri()], check=True, capture_output=True)
    finally:
        tmp.unlink()
    print("wrote", out_path)


if __name__ == "__main__":
    for spec in (TOKENIZER, ATTENTION):
        build(spec)
