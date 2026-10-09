# /// script
# dependencies = ["markdown", "latex2mathml"]
# ///
"""Worked self-attention example ("I love cats") -> docs/Self_Attention_Worked_Example.pdf

Run from anywhere:  uv run tools/pdf/attention_worked_example.py

Unlike the ReportLab scripts, this document is mostly LaTeX math, so the pipeline is
markdown -> HTML with the math converted to MathML -> headless Google Chrome prints the
PDF. Chrome renders MathML natively, so nothing is fetched from the network.

Every number in the added notes was checked with a short Python calculation.
"""
import re
import subprocess
from pathlib import Path

import markdown
from latex2mathml.converter import convert

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "docs" / "Self_Attention_Worked_Example.pdf"
HTML = REPO / "docs" / ".attention_worked_example.html"  # intermediate, deleted after printing
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
TITLE = "Self-Attention by Hand: “I love cats”"

CSS = """
@page {
  size: A4; margin: 18mm 20mm 20mm 20mm;
  @bottom-left { content: "Self-Attention by Hand"; font: 8pt 'Helvetica Neue'; color: #777; }
  @bottom-right { content: counter(page); font: 8pt 'Helvetica Neue'; color: #777; }
}
body { font: 10pt/1.55 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #1a1a1a; }
h1 { font-size: 21pt; margin: 0 0 2pt; }
.sub { color: #5a5a5a; font-style: italic; margin: 0 0 14pt; }
h2 { font-size: 14pt; color: #2f4f76; border-top: 0.6pt solid #cfcfcf; padding-top: 9pt;
     margin: 18pt 0 6pt; break-after: avoid; }
h3 { font-size: 11.5pt; margin: 12pt 0 4pt; break-after: avoid; }
h4 { font-size: 10.5pt; margin: 9pt 0 3pt; break-after: avoid; }
p { margin: 0 0 6pt; }
blockquote { margin: 4pt 0 9pt; padding: 6pt 10pt; background: #eef2f8; color: #243b5c;
             border-left: 3pt solid #2f4f76; break-inside: avoid; }
blockquote p { margin: 0; }
pre { background: #f4f5f7; border: 0.5pt solid #cfcfcf; padding: 7pt 9pt; font: 8.6pt/1.35 Menlo, monospace;
      break-inside: avoid; white-space: pre-wrap; }
code { font: 9pt Menlo, monospace; color: #2f4f76; }
pre code { color: #1a1a1a; font-size: inherit; }
table { border-collapse: collapse; margin: 4pt 0 10pt; break-inside: avoid; }
th, td { border: 0.5pt solid #cfcfcf; padding: 3pt 10pt; }
th { background: #f4f5f7; }
math { font-family: 'STIX Two Math'; font-size: 1.12em; }
math[display="block"] { margin: 5pt 0 8pt; break-inside: avoid; }
.boxed { border: 1.1pt solid #2f4f76; padding: 3pt 6pt; }
.note { border: 0.8pt solid #9fb6d3; background: #f6f9fd; padding: 7pt 11pt 3pt; margin: 12pt 0;
        break-inside: avoid; }
.note h4 { margin-top: 0; color: #2f4f76; }
.end { color: #777; font-size: 8pt; text-align: center; margin-top: 16pt; font-style: italic; }
"""

# Added notes, keyed by the section they follow. They connect the toy calculation to
# Raschka's chapter 3 code and correct the one rounding slip.
NOTES = {
    2: r"""
#### Added note: where this lives in Raschka's chapter 3

In the book, `SelfAttention_v1` stores the three matrices as `nn.Parameter(torch.rand(d_in, d_out))` and computes `queries = x @ self.W_query`. That is exactly \(Q = XW_Q\), with one token per row of \(X\). `SelfAttention_v2` swaps in `nn.Linear(d_in, d_out, bias=qkv_bias)`, which does the same multiplication (it stores the weight transposed and computes `x @ W.T`). The book's example uses \(d_{in}=3\) and \(d_{out}=2\); here both are 2, so identity matrices fit.

Watch the letter **I**: when section 26 writes \(W_Q=W_K=W_V=I\), that \(I\) is the identity matrix, not the token "I".
""",
    8: r"""
#### Added note: this matrix is symmetric only because Q = K

Here \(QK^T\) equals its own transpose: love → cats and cats → love are both 1. That happens only because this toy sets \(Q=K\). With learned \(W_Q \neq W_K\), the score a → b is \(q_a \cdot k_b\) and the score b → a is \(q_b \cdot k_a\), which are different numbers. "How much a listens to b" need not equal "how much b listens to a", so real attention matrices are generally **not** symmetric. (The exercise at the end lets you see this.)
""",
    10: r"""
#### Added note: what the scaling changes, in numbers

For the `cats` row, softmax without scaling gives softmax([1, 1, 2]) ≈ [0.212, 0.212, 0.576]. With scaling it gives ≈ [0.248, 0.248, 0.503]. Dividing by \(\sqrt{2}\) made the distribution flatter. With \(d_k=2\) the effect is mild; GPT-2 small has \(d_k=64\) per head, so its scores are divided by 8.

Why \(\sqrt{d_k}\) and not \(d_k\)? Suppose the components of \(q\) and \(k\) are independent with mean 0 and variance 1. Then \(q\cdot k\) is a sum of \(d_k\) terms, each with variance 1, so \(\operatorname{Var}(q\cdot k)=d_k\) and the standard deviation is \(\sqrt{d_k}\). Dividing by \(\sqrt{d_k}\) brings the standard deviation back to 1, whatever the head size. In Raschka's code: `attn_scores / keys.shape[-1]**0.5`.
""",
    14: r"""
#### Added note: which dimension softmax runs over, and rounding

Each **row** is one Query's distribution, so each row sums to 1. In PyTorch that is `torch.softmax(scores, dim=-1)`, the same point as your earlier question about `dim`. The columns do **not** sum to 1: the `cats` column is 0.401 + 0.401 + 0.503 = 1.305.

Exact values to four decimals:

$$
A=
\begin{bmatrix}
0.4011&0.1978&0.4011\\
0.1978&0.4011&0.4011\\
0.2483&0.2483&0.5035
\end{bmatrix}
$$

At three decimals row 3 adds up to 0.999. That is rounding, not an error.
""",
    19: r"""
#### Added note: one rounding slip, and a useful way to read O = AV

Exact outputs: \(o_I=[0.8022, 0.5989]\), \(o_{love}=[0.5989, 0.8022]\), \(o_{cats}=[0.7517, 0.7517]\). The text's 0.751 for `cats` comes from adding already-rounded weights (0.248 + 0.503). The exact value rounds to **0.752**.

Each row of \(A\) is nonnegative and sums to 1, so every output is a **weighted average** (a convex combination) of the Value vectors, like portfolio weights applied to asset returns. Every \(o\) therefore lies inside the triangle with corners \(v_I=[1,0]\), \(v_{love}=[0,1]\) and \(v_{cats}=[1,1]\). Attention blends the information that is there; by itself it cannot produce a vector outside that range.
""",
    28: r"""
#### Added note: the GPT version, with the causal mask

Everything above lets every token see every other token. GPT, and Raschka section 3.5, masks future positions before softmax: scores above the diagonal are set to \(-\infty\), so they become 0 after softmax.

$$
\frac{QK^T}{\sqrt2}\ \text{masked}=
\begin{bmatrix}
0.707&-\infty&-\infty\\
0&0.707&-\infty\\
0.707&0.707&1.414
\end{bmatrix}
$$

$$
A_{causal}\approx
\begin{bmatrix}
1&0&0\\
0.330&0.670&0\\
0.248&0.248&0.503
\end{bmatrix}
\qquad
O_{causal}\approx
\begin{bmatrix}
1&0\\
0.330&0.670\\
0.752&0.752
\end{bmatrix}
$$

- `I` sees only itself, so its output is its own Value, [1, 0].
- `love` cannot see `cats`, so its weights are softmax([0, 0.707]) = [0.330, 0.670].
- `cats` is last and already saw everything, so its row does not change.

The mask changes only the rows of earlier tokens. The last token's row is the same in both versions.
""",
    30: r"""
#### Added note: exercise for your notebook

The closing suggestion is a good next step. Type it yourself in `03_attention.ipynb`, and predict each tensor before you run the cell:

1. `X` as a 3×2 float tensor; `W_Q`, `W_K`, `W_V` as `torch.eye(2)`.
2. `scores`, then the scaled scores, then `weights` (softmax with `dim=-1`), then `output`.
3. Add the causal mask with `torch.triu(..., diagonal=1)` and `masked_fill(..., -torch.inf)`.
4. Change `W_K` to `[[1, 1], [0, 1]]` and look at `scores` again.

Check your results: the weights and outputs should match the matrices in the notes above to four decimals, and `weights.sum(dim=-1)` should be all ones. In step 4 the unscaled scores should become [[1, 0, 1], [1, 1, 2], [2, 1, 3]]. I → love is 0 but love → I is 1, so the matrix is no longer symmetric.
""",
}

RAW_MD = r'''
Since you already understand linear algebra, I'll make this a **complete numerical example**, but I'll keep the arithmetic small. The goal is to make the entire pipeline feel mechanical:

**Input vectors → Q, K, V → Q·Kᵀ → scaling → softmax → weighted V → contextual vectors**

I'll use the sentence:

> **"I love cats"**

and calculate the self-attention output for **all three tokens**.

### 1. Start with three token representations

Suppose the tokenizer has produced:

```text
I      → token 1
love   → token 2
cats   → token 3
```

After the embedding layer, imagine we have these tiny **2-dimensional vectors**:

$$
X =
\begin{bmatrix}
1 & 0\\
0 & 1\\
1 & 1
\end{bmatrix}
$$

So:

$$
x_I = [1,0]
$$

$$
x_{love} = [0,1]
$$

$$
x_{cats} = [1,1]
$$

These are our **input representations**.

Important:

> These vectors are not yet the final contextual meanings.

At this point, `I`, `love`, and `cats` have their initial representations. Self-attention is about allowing them to exchange information.

---

# 2. Create Q, K, and V

This is the part that initially feels complicated.

The Transformer creates three different representations from \(X\):

$$
Q=XW_Q
$$

$$
K=XW_K
$$

$$
V=XW_V
$$

For our tiny example, let's make the matrices extremely simple.

We'll use:

$$
W_Q =
\begin{bmatrix}
1&0\\
0&1
\end{bmatrix}
$$

$$
W_K =
\begin{bmatrix}
1&0\\
0&1
\end{bmatrix}
$$

and:

$$
W_V =
\begin{bmatrix}
1&0\\
0&1
\end{bmatrix}
$$

These are identity matrices.

Therefore:

$$
Q=K=V=X
$$

So:

$$
Q=
\begin{bmatrix}
1&0\\
0&1\\
1&1
\end{bmatrix}
$$

$$
K=
\begin{bmatrix}
1&0\\
0&1\\
1&1
\end{bmatrix}
$$

$$
V=
\begin{bmatrix}
1&0\\
0&1\\
1&1
\end{bmatrix}
$$

In a real Transformer, \(W_Q,W_K,W_V\) are **learned matrices**, so Q, K and V would generally be different.

I'm deliberately making them identical here so we can focus on the attention mechanism itself.

---

# 3. What does Query actually mean?

Let's concentrate on the first token:

> **I**

Its vector is:

$$
q_I=[1,0]
$$

Think of this as:

> **"I am looking for something. What should I pay attention to?"**

Similarly:

$$
q_{love}=[0,1]
$$

means something like:

> "What information is relevant to me?"

And:

$$
q_{cats}=[1,1]
$$

is another learned query.

Don't interpret the actual numbers too literally. In a real Transformer, the dimensions don't have simple human labels like "subject" or "object."

The important conceptual point is:

> **Each token produces a Query that is used to search for relevant information among the Keys.**

---

# 4. What does Key mean?

Now look at the Keys.

We have:

$$
k_I=[1,0]
$$

$$
k_{love}=[0,1]
$$

$$
k_{cats}=[1,1]
$$

Think of each Key as describing:

> **"What kind of information do I contain?"**

So when `I`'s Query meets `love`'s Key, we ask:

$$
q_I \cdot k_{love}
$$

When `I`'s Query meets `cats`' Key:

$$
q_I \cdot k_{cats}
$$

This is the beginning of the important part.

---

# 5. Q → K matching

This is where self-attention really starts happening.

We calculate the **dot product** between every Query and every Key.

In matrix form:

$$
QK^T
$$

Let's calculate it.

We have:

$$
Q=
\begin{bmatrix}
1&0\\
0&1\\
1&1
\end{bmatrix}
$$

and:

$$
K^T=
\begin{bmatrix}
1&0&1\\
0&1&1
\end{bmatrix}
$$

Therefore:

$$
QK^T=
\begin{bmatrix}
1&0\\
0&1\\
1&1
\end{bmatrix}
\begin{bmatrix}
1&0&1\\
0&1&1
\end{bmatrix}
$$

Let's calculate each element.

---

## Query of "I"

First row of \(Q\):

$$
q_I=[1,0]
$$

Compare it with every Key.

### I → I

$$
[1,0]\cdot[1,0]
$$

$$
=1(1)+0(0)
$$

$$
=1
$$

### I → love

$$
[1,0]\cdot[0,1]
$$

$$
=1(0)+0(1)
$$

$$
=0
$$

### I → cats

$$
[1,0]\cdot[1,1]
$$

$$
=1(1)+0(1)
$$

$$
=1
$$

Therefore:

$$
\boxed{[1,0,1]}
$$

This means, before normalization, the Query for `I` has scores:

| Query | Key  | Score |
| ----- | ---- | ----: |
| I     | I    |     1 |
| I     | love |     0 |
| I     | cats |     1 |

---

# 6. Do the same thing for "love"

Query:

$$
q_{love}=[0,1]
$$

Compare against every Key.

### love → I

$$
[0,1]\cdot[1,0]=0
$$

### love → love

$$
[0,1]\cdot[0,1]=1
$$

### love → cats

$$
[0,1]\cdot[1,1]=1
$$

Therefore:

$$
\boxed{[0,1,1]}
$$

---

# 7. Do the same thing for "cats"

Query:

$$
q_{cats}=[1,1]
$$

### cats → I

$$
[1,1]\cdot[1,0]=1
$$

### cats → love

$$
[1,1]\cdot[0,1]=1
$$

### cats → cats

$$
[1,1]\cdot[1,1]=2
$$

Therefore:

$$
\boxed{[1,1,2]}
$$

---

# 8. We now have the attention-score matrix

Putting everything together:

$$
QK^T=
\begin{bmatrix}
1&0&1\\
0&1&1\\
1&1&2
\end{bmatrix}
$$

This matrix is extremely important.

Let's label it:

```text
             Keys
          I    love   cats
       ┌────────────────────
Query I│ 1     0      1
      love
       │ 0     1      1
      cats
       │ 1     1      2
```

Each **row** corresponds to one token asking:

> "How relevant is every token to me?"

For example:

$$
[1,0,1]
$$

means:

> `I` compared against `I`, `love`, and `cats`.

And:

$$
[1,1,2]
$$

means:

> `cats` compared against `I`, `love`, and `cats`.

---

# 9. But these aren't attention weights yet

This is a very important distinction.

We currently have:

$$
QK^T
$$

These are **attention scores**.

They aren't probabilities.

For example:

$$
[1,0,1]
$$

doesn't mean:

```text
I → I       1%
I → love    0%
I → cats    1%
```

Instead, these are raw compatibility scores.

We need to convert them into normalized weights.

That's where **softmax** comes in.

---

# 10. Why divide by \(\sqrt{d_k}\)?

The actual Transformer formula is:

$$
\text{Attention}(Q,K,V)
=
\operatorname{softmax}
\left(
\frac{QK^T}{\sqrt{d_k}}
\right)V
$$

Here:

$$
d_k=2
$$

because our Key vectors have two dimensions.

Therefore:

$$
\sqrt{d_k}=\sqrt2
$$

So:

$$
\frac{QK^T}{\sqrt2}
=
\begin{bmatrix}
1/\sqrt2&0&1/\sqrt2\\
0&1/\sqrt2&1/\sqrt2\\
1/\sqrt2&1/\sqrt2&2/\sqrt2
\end{bmatrix}
$$

Approximately:

$$
=
\begin{bmatrix}
0.707&0&0.707\\
0&0.707&0.707\\
0.707&0.707&1.414
\end{bmatrix}
$$

### Why do this?

As vector dimensions become large, dot products can become large.

Large numbers fed into softmax can make the distribution excessively sharp.

Dividing by:

$$
\sqrt{d_k}
$$

helps keep the values in a reasonable range.

You don't need to think of this as mysterious.

Simply remember:

> **Dot product gives the matching score; scaling keeps the score numerically well-behaved before softmax.**

---

# 11. Now apply softmax

This is the step that converts scores into attention weights.

The softmax function is:

$$
\operatorname{softmax}(x_i)
=
\frac{e^{x_i}}
{\sum_j e^{x_j}}
$$

The important property is:

> The numbers become positive and sum to 1.

Let's calculate the first row.

For `I`:

$$
[0.707,0,0.707]
$$

Softmax gives approximately:

$$
[0.401,0.198,0.401]
$$

So `I` distributes its attention approximately like this:

| Token receiving information | Attention |
| --------------------------- | --------: |
| I                           |     40.1% |
| love                        |     19.8% |
| cats                        |     40.1% |

Notice something important.

The original scores were:

$$
[0.707,0,0.707]
$$

After softmax:

$$
[0.401,0.198,0.401]
$$

The relative relationship has been preserved, but now we have normalized weights.

---

# 12. Softmax for "love"

For `love`:

$$
[0,0.707,0.707]
$$

Softmax gives approximately:

$$
[0.198,0.401,0.401]
$$

Therefore:

| Token | Attention |
| ----- | --------: |
| I     |     19.8% |
| love  |     40.1% |
| cats  |     40.1% |

---

# 13. Softmax for "cats"

For `cats`:

$$
[0.707,0.707,1.414]
$$

Softmax gives approximately:

$$
[0.248,0.248,0.503]
$$

So:

| Token | Attention |
| ----- | --------: |
| I     |     24.8% |
| love  |     24.8% |
| cats  |     50.3% |

Notice that `cats` pays the most attention to itself in this particular toy example.

---

# 14. Our complete attention-weight matrix

We can now write:

$$
A=
\operatorname{softmax}
\left(
\frac{QK^T}{\sqrt2}
\right)
$$

approximately:

$$
A=
\begin{bmatrix}
0.401&0.198&0.401\\
0.198&0.401&0.401\\
0.248&0.248&0.503
\end{bmatrix}
$$

This matrix is the **attention matrix**.

And this is one of the most important objects to understand in a Transformer.

---

# 15. Now comes the "V" part

We've used:

* Query → what am I looking for?
* Key → what kind of information do you have?

Now we need:

> **What actual information should I receive?**

That's the job of **Value**.

Remember:

$$
V=
\begin{bmatrix}
1&0\\
0&1\\
1&1
\end{bmatrix}
$$

Therefore:

$$
v_I=[1,0]
$$

$$
v_{love}=[0,1]
$$

$$
v_{cats}=[1,1]
$$

The attention weights tell us **how much of each Value to take**.

This is the critical transition:

$$
\boxed{\text{attention weights} \rightarrow \text{weighted Values}}
$$

---

# 16. Calculate the contextual vector for "I"

The first attention row is:

$$
[0.401,0.198,0.401]
$$

So `I` takes:

$$
40.1\%\text{ of }V_I
$$

plus:

$$
19.8\%\text{ of }V_{love}
$$

plus:

$$
40.1\%\text{ of }V_{cats}
$$

Therefore:

$$
o_I=
0.401[1,0]
+
0.198[0,1]
+
0.401[1,1]
$$

Calculate each vector:

$$
0.401[1,0]=[0.401,0]
$$

$$
0.198[0,1]=[0,0.198]
$$

$$
0.401[1,1]=[0.401,0.401]
$$

Add them:

$$
o_I=
[0.401,0]
+
[0,0.198]
+
[0.401,0.401]
$$

Therefore:

$$
\boxed{o_I=[0.802,0.599]}
$$

This is the new representation of `I` after self-attention.

---

# 17. Calculate the contextual vector for "love"

Attention weights:

$$
[0.198,0.401,0.401]
$$

Therefore:

$$
o_{love}
=
0.198[1,0]
+
0.401[0,1]
+
0.401[1,1]
$$

Calculate:

$$
=[0.198,0]
+
[0,0.401]
+
[0.401,0.401]
$$

Therefore:

$$
\boxed{o_{love}=[0.599,0.802]}
$$

---

# 18. Calculate the contextual vector for "cats"

Attention weights:

$$
[0.248,0.248,0.503]
$$

Therefore:

$$
o_{cats}
=
0.248[1,0]
+
0.248[0,1]
+
0.503[1,1]
$$

Calculate:

$$
=[0.248,0]
+
[0,0.248]
+
[0.503,0.503]
$$

Therefore:

$$
\boxed{o_{cats}=[0.751,0.751]}
$$

---

# 19. We have completed self-attention!

Our original representations were:

$$
X=
\begin{bmatrix}
1&0\\
0&1\\
1&1
\end{bmatrix}
$$

After self-attention:

$$
O\approx
\begin{bmatrix}
0.802&0.599\\
0.599&0.802\\
0.751&0.751
\end{bmatrix}
$$

So the transformation was:

$$
\boxed{
X
\rightarrow
Q,K,V
\rightarrow
QK^T
\rightarrow
\frac{QK^T}{\sqrt{d_k}}
\rightarrow
\operatorname{softmax}
\rightarrow
A
\rightarrow
AV
\rightarrow
O
}
$$

That is **self-attention**.

---

# 20. The most important thing: what actually happened?

Let's forget the arithmetic for a moment.

Suppose we focus only on `love`.

Originally:

$$
x_{love}=[0,1]
$$

The token `love` looked at every token.

It calculated:

```text
             relevance
love → I       0
love → love    1
love → cats    1
```

After softmax:

```text
love → I       19.8%
love → love    40.1%
love → cats    40.1%
```

Then it collected information:

```text
19.8% × Value(I)
+
40.1% × Value(love)
+
40.1% × Value(cats)
```

which produced:

$$
[0.599,0.802]
$$

So the new representation of `love` contains information gathered from **the other tokens**.

That is the essence of self-attention.

---

# 21. Here's the mental picture I want you to remember

Imagine three people sitting around a table:

```text
             I

          ↗     ↖
       attention
        ↙         ↘

      love  ←→  cats
```

But each token is simultaneously doing this.

For `I`:

```text
I asks:
"What information is relevant to me?"

        ↓

Compare my Query
with everybody's Key

        ↓

     scores

        ↓

   softmax

        ↓

 attention weights

        ↓

collect everybody's Values

        ↓

new representation of I
```

Then `love` does exactly the same thing.

Then `cats` does exactly the same thing.

So:

> **Self-attention is not one operation performed on one token. It is performed for every token simultaneously.**

---

# 22. Why are there three matrices Q, K, and V?

This is perhaps the most confusing conceptual point.

You might ask:

> "Why don't we simply calculate similarity between the embeddings and use that?"

We could construct a simpler mechanism that does something like that.

But Q/K/V gives the model three separate learned roles.

Think of a library.

### Query

A person walks into a library and says:

> "I'm looking for information about cats."

That's the **Query**.

### Key

Each book has an index describing what it contains:

> "This book is about animals."

That's the **Key**.

### Value

The actual content inside the book is the **Value**.

So:

$$
\boxed{\text{Query} \leftrightarrow \text{Key}}
$$

determines:

> **Which information is relevant?**

Then:

$$
\boxed{\text{Value}}
$$

provides:

> **What information should actually be retrieved?**

That's why the architecture separates them.

---

# 23. And why can Q, K and V all start from the same X?

This is another point worth understanding.

We begin with:

$$
X
$$

Then:

$$
Q=XW_Q
$$

$$
K=XW_K
$$

$$
V=XW_V
$$

All three come from the same input.

But because:

$$
W_Q \neq W_K \neq W_V
$$

in a real Transformer, they become three different representations.

Think of it like putting the same person through three different filters:

```text
                   X
                   │
          ┌────────┼────────┐
          ↓        ↓        ↓
       W_Q       W_K      W_V
          ↓        ↓        ↓
          Q        K        V
```

The model learns these matrices during training.

---

# 24. The matrix multiplication now becomes much easier to understand

You may see this line in Transformer code:

```python
scores = Q @ K.T
```

Now you know exactly what it means.

It means:

> Compare every Query with every Key.

The result is:

```text
             Key
          I   love  cats
       ┌────────────────
Query I│ 1    0     1
     love
       │ 0    1     1
     cats
       │ 1    1     2
```

Then:

```python
scores = scores / sqrt(d_k)
```

means:

> Scale the scores.

Then:

```python
weights = softmax(scores)
```

means:

> Turn the scores into normalized attention weights.

Then:

```python
output = weights @ V
```

means:

> Use those weights to take a weighted combination of the Values.

That's the entire mechanism.

---

# 25. The famous Transformer equation

Now the famous equation should look much less frightening:

$$
\boxed{
\operatorname{Attention}(Q,K,V)
=
\operatorname{softmax}
\left(
\frac{QK^T}{\sqrt{d_k}}
\right)V
}
$$

Let's translate every piece into English:

### \(QK^T\)

> "How relevant is every Key to every Query?"

### \(/\sqrt{d_k}\)

> "Keep the scores numerically well-scaled."

### softmax

> "Turn those scores into normalized attention weights."

### \(V\)

> "Take information from the Values."

### multiplication by \(V\)

> "Combine the information according to those weights."

So the whole equation means:

> **For every token, determine which other tokens are relevant, convert that relevance into weights, and use those weights to gather information from the other tokens.**

---

# 26. One subtle but VERY important point

You might now think:

> "So `I` looks at `love` and `cats`, and therefore understands the sentence."

Conceptually yes, but our toy example is **not actually a meaningful language model**.

Why?

Because I deliberately chose:

$$
W_Q=W_K=W_V=I
$$

and arbitrary tiny vectors.

In a real Transformer:

* embeddings are learned,
* \(W_Q\), \(W_K\), \(W_V\) are learned,
* dimensions are much larger,
* multiple attention heads exist,
* positional information is included,
* attention is combined with residual connections,
* normalization is used,
* feed-forward networks follow,
* many Transformer layers are stacked.

So don't attach linguistic meaning to our specific numbers.

The example exists to show the **mechanics**.

---

# 27. One more important point: self-attention is dynamic

This is perhaps the deepest idea.

Suppose we have:

> **I love cats**

The representation produced for `love` depends on the entire input sequence.

Now change the sentence:

> **I love dogs**

The Query/Key relationships and resulting contextual representations can change.

Change it again:

> **I don't love cats**

Now the representation of `love` can be influenced by `don't`, `cats`, and the other surrounding tokens.

Therefore:

$$
\boxed{\text{same token} \neq \text{same contextual representation}}
$$

The word `love` can receive a different contextual representation depending on the surrounding sequence.

This is why we call the resulting representation **contextual**.

---

# 28. One more thing: this is why it's called "self"-attention

It's called **self-attention** because:

> Q, K and V all originate from the **same sequence**.

For our sentence:

```text
"I love cats"
```

we have:

```text
             same sequence
                  │
        ┌─────────┼─────────┐
        ↓         ↓         ↓
        Q         K         V
```

The tokens are essentially communicating with **other tokens within themselves**.

Compare this with cross-attention:

```text
Sequence A → Q

Sequence B → K,V
```

That's a different mechanism.

---

# 29. Your entire calculation on one page

If I compress everything we just did:

### Step 1 — Input

$$
X=
\begin{bmatrix}
1&0\\
0&1\\
1&1
\end{bmatrix}
$$

### Step 2 — Create Q, K, V

$$
Q=XW_Q
$$

$$
K=XW_K
$$

$$
V=XW_V
$$

For our toy example:

$$
Q=K=V=X
$$

### Step 3 — Q/K matching

$$
QK^T=
\begin{bmatrix}
1&0&1\\
0&1&1\\
1&1&2
\end{bmatrix}
$$

### Step 4 — Scale

$$
\frac{QK^T}{\sqrt2}
=
\begin{bmatrix}
0.707&0&0.707\\
0&0.707&0.707\\
0.707&0.707&1.414
\end{bmatrix}
$$

### Step 5 — Softmax

$$
A\approx
\begin{bmatrix}
0.401&0.198&0.401\\
0.198&0.401&0.401\\
0.248&0.248&0.503
\end{bmatrix}
$$

### Step 6 — Aggregate Values

$$
O=AV
$$

giving approximately:

$$
\boxed{
O=
\begin{bmatrix}
0.802&0.599\\
0.599&0.802\\
0.751&0.751
\end{bmatrix}
}
$$

Done.

That's a complete self-attention calculation.

---

# 30. The one sentence I want you to remember

If you remember only one thing from this entire exercise, remember this:

$$
\boxed{
\text{Q asks}
\rightarrow
\text{K determines relevance}
\rightarrow
\text{softmax creates weights}
\rightarrow
\text{V provides information}
\rightarrow
\text{weighted sum creates context}
}
$$

Or even more simply:

> **Query finds what it needs, Key determines what matches, and Value provides the information.**

And mathematically:

$$
\boxed{
\text{Output}
=
\underbrace{
\operatorname{softmax}
\left(
\frac{QK^T}{\sqrt{d_k}}
\right)
}_{\text{who should I listen to, and how much?}}
\underbrace{V}_{\text{what information do I receive?}}
}
$$

You were right that self-attention is **not particularly difficult mathematically**. The difficulty is that several simple operations are chained together. Once you separate them into these six steps, the apparent complexity drops dramatically.

**The natural next step is to take this exact calculation and translate each line into a tiny PyTorch implementation**—so you can see that `Q @ K.T`, `softmax`, and `weights @ V` in actual Transformer code are literally the mathematics we just did by hand.
'''


def restructure(text):
    """Even out the pasted heading levels and slot the added notes in after their sections.

    The source mixes '#' and '###' for numbered sections; those become h2, the few
    '##' sub-headings become h3 and the remaining '###' become h4.
    """
    out, in_code, section = [], False, 0

    def emit_note():
        if section in NOTES:
            out.extend(["", '<div class="note" markdown="1">', NOTES[section].strip(), "</div>", ""])

    for line in text.split("\n"):
        if line.startswith("```"):
            in_code = not in_code
        if in_code or line.startswith("```"):
            out.append(line)
            continue
        m = re.match(r"^#+ (\d+)\. ", line)
        if m:
            emit_note()
            section = int(m.group(1))
            out.append("## " + line.lstrip("#").strip())
        elif line.startswith("## "):
            out.append("### " + line[3:])
        elif line.startswith("### "):
            out.append("#### " + line[4:])
        elif line.strip() != "---":
            out.append(line)
    emit_note()
    return "\n".join(out)


def to_mathml(latex, display):
    ml = convert(latex.strip(), display="block" if display else "inline")
    # Chrome's MathML Core has no <menclose>; draw \boxed with a CSS border instead.
    ml = ml.replace('<menclose notation="box">', '<mrow class="boxed">').replace("</menclose>", "</mrow>")
    # MathML never line-wraps, and the long arrow chains (sections 19 and 30) are
    # slightly wider than the text column at the default size.
    if latex.count(r"\rightarrow") >= 4:
        ml = ml.replace("<math ", '<math style="font-size:0.88em" ', 1)
    return ml


def build_html(md_text):
    maths = []

    def stash(display):
        def repl(m):
            maths.append(to_mathml(m.group(1), display))
            token = f"MATHTOKEN{len(maths) - 1:04d}X"
            return f"\n\n{token}\n\n" if display else token
        return repl

    # Only outside code fences (odd chunks are fenced code).
    chunks = re.split(r"(```.*?```)", md_text, flags=re.DOTALL)
    for i in range(0, len(chunks), 2):
        chunks[i] = re.sub(r"\$\$(.+?)\$\$", stash(True), chunks[i], flags=re.DOTALL)
        chunks[i] = re.sub(r"\\\((.+?)\\\)", stash(False), chunks[i])
    html = markdown.markdown("".join(chunks), extensions=["fenced_code", "tables", "md_in_html"])

    def unstash(m):
        return maths[int(m.group(1))]

    html = re.sub(r"<p>MATHTOKEN(\d{4})X</p>", unstash, html)
    html = re.sub(r"MATHTOKEN(\d{4})X", unstash, html)
    return (
        f'<!doctype html><html><head><meta charset="utf-8"><title>{TITLE}</title>'
        f"<style>{CSS}</style></head><body>"
        f"<h1>{TITLE}</h1>"
        '<p class="sub">A complete numerical walk-through: Q, K, V &#8594; scores &#8594; scaling '
        "&#8594; softmax &#8594; weighted Values. Boxed “Added note” sections were written "
        "during review and every number in them was checked in Python.</p>"
        f"{html}"
        '<p class="end">Generation script: tools/pdf/attention_worked_example.py</p>'
        "</body></html>"
    )


HTML.write_text(build_html(restructure(RAW_MD)), encoding="utf-8")
subprocess.run(
    [CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
     f"--print-to-pdf={OUT}", HTML.as_uri()],
    check=True, capture_output=True,
)
HTML.unlink()
print("wrote", OUT)
