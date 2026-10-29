# /// script
# dependencies = []
# ///
"""Chapter 5 flashcards and quiz -> docs/Ch5_Pretraining_Flashcards.pdf, docs/Ch5_Pretraining_Quiz.pdf

Run from anywhere:  uv run tools/pdf/ch5_study_pack.py

Companion to pretraining_walkthrough.py (the line-by-line guide). Every number comes from
notebooks/05_pretraining.ipynb's saved outputs or was recomputed for that guide. Cards and
questions name the notebook cell they come from, so a wrong answer can be looked up.

Each quiz question is written with the correct option first; place_answers() rotates the
options so the right answers are spread evenly over ①–④.
"""
import subprocess
import tempfile
from pathlib import Path

from gpt_model_walkthrough import CHROME, inline

REPO = Path(__file__).resolve().parents[2]
DOCS = REPO / "docs"

CSS = """
@page {
  size: A4; margin: 17mm 18mm 19mm 18mm;
  @bottom-left { content: "LABEL"; font: 7.5pt 'Helvetica Neue'; color: #777; }
  @bottom-right { content: counter(page); font: 7.5pt 'Helvetica Neue'; color: #777; }
}
body { font: 9.7pt/1.55 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #1a1a1a; }
h1 { font-size: 19pt; margin: 0 0 2pt; }
h2 { font-size: 12.5pt; color: #2f4f76; margin: 14pt 0 4pt; break-after: avoid; }
.sub { color: #5a5a5a; margin: 0 0 10pt; }
p { margin: 0 0 6pt; }
code { font: 8.6pt Menlo, monospace; color: #2f4f76; }
.how { border-left: 3pt solid #2f4f76; background: #eef2f8; padding: 5pt 9pt; margin: 4pt 0 10pt; }
table { border-collapse: collapse; width: 100%; margin: 2pt 0 8pt; }
tr { break-inside: avoid; }
th, td { border: 0.5pt solid #d4d4d4; padding: 4pt 7pt; vertical-align: top; text-align: left; }
th { background: #ececec; font-size: 8.8pt; }
table.cards td:nth-child(1) { width: 5%; text-align: center; color: #2f4f76; }
table.cards td:nth-child(2) { width: 42%; border-right: 1.4pt solid #2f4f76; }
table.cards tr:nth-child(even) td { background: #f7f8fa; }
.cell { color: #7a7a7a; font-size: 8pt; }
.q { break-inside: avoid; margin: 9pt 0 4pt; }
.q ol { list-style: none; padding-left: 12pt; margin: 3pt 0 0; }
.q li { margin-bottom: 1pt; }
table.key td:nth-child(1) { width: 5%; text-align: center; }
table.key td:nth-child(2) { width: 30%; background: #ebf5ec; }
.newpage { break-before: page; }
.end { color: #777; font-size: 7.8pt; text-align: center; margin-top: 14pt; }
"""

# (topic, [(question, answer, cell)]). Text uses `code` and **bold** (see inline()).
CARDS = [
    ("The loss", [
        ("In pretraining, where do the targets come from?",
         "From the text itself: the inputs shifted one token to the left. No human labelling is needed.", "4"),
        ("Inputs `every effort moves` → targets?",
         "` effort moves you`. Each position's answer is the token that follows it.", "4"),
        ("How many predictions does a batch of shape `[2, 3]` produce?",
         "6, one per position. Every position is a small \"what comes next?\" question.", "4"),
        ("What does `probas[0, [0, 1, 2], targets[0]]` pick out?",
         "The probability the model gave to the **correct** next token at positions 0, 1 and 2 of sentence 1.", "8"),
        ("Why take the log of the probabilities?",
         ("Tiny numbers become manageable (7.45e-05 → -9.50), products become sums, and it is numerically "
         "stable. A perfect prediction (probability 1) gives log 0."), "9"),
        ("Cross-entropy loss in one sentence?",
         "The average of −log(probability given to the correct next token).", "11"),
        ("Why the minus sign?",
         ("Log-probabilities are negative and best at 0. Training minimizes, so the loss is their negative: "
         "positive, and best at 0."), "11"),
        ("The untrained model's loss on the 6 example positions?", "10.7940.", "11, 14"),
        ("What does ln(50,257) ≈ 10.825 mean?",
         "The loss of a model that spreads probability evenly over all 50,257 tokens: pure guessing.", "14"),
        ("What is perplexity?",
         ("e^loss. e^10.794 ≈ 48,700: the model is as unsure as if choosing among 48,700 equally likely "
         "tokens."), "14"),
        ("Why `flatten(0, 1)` before `cross_entropy`?",
         ("`cross_entropy` wants rows of scores and a list of answers: `[2, 3, 50257]` → `[6, 50257]`, "
         "`[2, 3]` → `[6]`."), "13"),
        ("Does `cross_entropy` take logits or probabilities?",
         "Raw **logits**. It applies softmax, log, picking, averaging and the minus sign itself.", "14"),
    ]),
    ("Data", [
        ("How big is `the-verdict.txt`?", "20,479 characters, 5,145 BPE tokens.", "17"),
        ("How is it split?",
         ("90 / 10 **by characters**: the first 18,431 characters (4,612 tokens) for training, the rest "
         "(534 tokens) for validation."), "18"),
        ("Why keep a validation set?",
         ("To tell learning from memorizing: only text the model never trained on shows whether it "
         "generalizes."), "18"),
        ("What does `max_length = stride = 256` mean?",
         "Chunks of 256 tokens that do not overlap.", "19"),
        ("How many batches does each loader give?",
         "Training: 18 chunks → 9 batches of `[2, 256]`. Validation: 2 chunks → 1 batch.", "19–20"),
        ("Why shuffle the training loader but not the validation loader?",
         "Mixing the order helps training. When only measuring, order does not matter.", "19"),
    ]),
    ("The training loop", [
        ("The four calls in every training step, in order?",
         "`optimizer.zero_grad()`, compute the loss, `loss.backward()`, `optimizer.step()`.", "24"),
        ("Why `optimizer.zero_grad()`?",
         ("PyTorch **adds** new gradients to old ones. Without clearing, each step would mix in all earlier "
         "steps."), "24"),
        ("What does `loss.backward()` compute?",
         "For every weight, how the loss would change if that weight changed slightly (its gradient).", "24"),
        ("What does `optimizer.step()` do?",
         "Moves every weight a small amount in the direction that lowers the loss.", "24"),
        ("Why `model.train()` at the start of every epoch?",
         ("`evaluate_model` and `generate_and_print_sample` switch the model to `eval()`; dropout must be "
         "turned back on."), "24–26"),
        ("Why `torch.no_grad()` when evaluating?",
         "No recording for training: saves memory and time, and measuring cannot change the weights.", "25"),
        ("Why does `global_step` start at -1?",
         "So the first step becomes step 0, and `0 % 5 == 0` reports right after the first update.", "24"),
        ("Steps and reports in the 10-epoch run?",
         "9 batches × 10 epochs = 90 steps; a report every 5 steps → 18 reports.", "27"),
        ("Tokens counted per step?", "`input_batch.numel()` = 2 × 256 = 512.", "24"),
        ("AdamW's settings in the notebook?",
         "`lr=0.0004` (step size) and `weight_decay=0.1` (gently pulls weights toward zero).", "27"),
        ("Losses after 10 epochs?", "Training 0.391, validation 6.452.", "27"),
        ("How do you recognize overfitting?",
         ("Training loss keeps falling while validation loss stalls or rises, and the samples copy the "
         "training text word for word."), "27, 29"),
    ]),
    ("Decoding", [
        ("What is greedy decoding?",
         ("Always taking the highest-probability token (`argmax`). The same prompt gives the same text every "
         "time."), "31, 34"),
        ("What does `torch.multinomial` do?",
         "Draws an index at random in proportion to the probabilities.", "35"),
        ("1,000 samples from the toy vocabulary gave?",
         "582 forward, 343 toward, 73 closer: close to the probabilities 0.572, 0.358, 0.061.", "36"),
        ("Why does `you` not appear in the 1,000-sample counts?",
         "It was never drawn, and `bincount` counts only up to the largest ID that appeared.", "36"),
        ("What does temperature do?",
         "Divides the logits by T before softmax. T < 1 sharpens the distribution, T > 1 flattens it.", "37"),
        ("`forward`'s probability at T = 0.1 and T = 5?",
         "0.991 (almost greedy) and 0.242 (even `pizza` gets 0.043).", "38"),
        ("What does top-k do?",
         "Keeps the k highest scores, sets the rest to -inf, then softmax gives them exactly 0.", "39–41"),
        ("Top-3 probabilities in the toy example?",
         "0.0615, 0.5775, 0.3610: the three survivors share all the probability.", "41"),
        ("In `generate`, what does `temperature=0` mean?",
         "Greedy, exactly like `generate_text_simple`.", "42"),
        ("In `generate`, in which order are top-k and temperature applied?",
         "Top-k first, then divide by the temperature, then softmax and sample.", "42"),
        ("What does `eos_id` do?", "Stops generating as soon as the model produces that token.", "42"),
    ]),
    ("Saving and loading", [
        ("What is a `state_dict`?",
         ("A dictionary: each layer's name → its tensor. It includes registered buffers such as the causal "
         "masks."), "44"),
        ("What does `map_location=device` do in `torch.load`?",
         "Puts the loaded tensors on this machine's device, even if they were saved on another.", "45"),
        ("Why save the optimizer too?", "To continue training later from exactly where it stopped.", "46"),
        ("Why is `model_and_optimizer.pth` (1.95 GB) three times `model.pth` (653 MB)?",
         "AdamW keeps two running averages for every weight.", "46"),
        ("Which learning rate is active after `optimizer.load_state_dict(...)`?",
         "The saved 0.0004. It replaces the `5e-4` written when the optimizer was created.", "47"),
    ]),
    ("OpenAI's GPT-2 weights", [
        ("Which two settings must change before loading OpenAI's weights?",
         ("`context_length` 1,024 (OpenAI's position table has 1,024 rows) and `qkv_bias` True (OpenAI's "
         "Q/K/V layers have biases)."), "54–55"),
        ("Why `GPT_CONFIG_124M.copy()`?",
         "Without it, `update` would also change the original training settings.", "53"),
        ("What is `c_attn`?",
         ("Query, key and value stored as one 768 × 2,304 matrix; `np.split(..., 3, axis=-1)` cuts it into "
         "three 768 × 768 pieces."), "58"),
        ("Why `.T` on OpenAI's weight matrices?",
         "OpenAI stores a layer as [inputs, outputs]; `nn.Linear` stores [outputs, inputs].", "58"),
        ("Why would a missing `.T` on `W_query` go unnoticed?",
         ("768 × 768 is square, so the transposed shape is the same and `assign`'s check passes. Only the "
         "generated text shows it."), "58, 60"),
        ("What are OpenAI's `g` and `b` in a LayerNorm?",
         "Gain and bias: your `scale` and `shift`.", "58"),
        ("What does `assign` do?",
         "Stops on a shape mismatch, otherwise turns the NumPy array into an `nn.Parameter`.", "57"),
        ("Why is `out_head` filled with `wte`?",
         "Weight tying: GPT-2 reuses the token embedding table as its output layer.", "58"),
        ("Where does \"124M\" come from?",
         "163,037,184 parameters minus the 38,597,376 shared with the output layer = 124,439,808.", "56"),
    ]),
]

# (question, [correct, wrong, wrong, wrong], why, cell)
QUIZ = [
    ("The inputs are `every effort moves`. What are the targets?",
     ["` effort moves you`", "`every effort moves`", "only ` you`", "a label written by a person"],
     "Targets are the inputs shifted by one token; the text labels itself.", "4"),
    ("What loss does a model get if it spreads probability evenly over all 50,257 tokens?",
     ["about 10.8", "0", "1", "50,257"],
     "−log(1/50,257) = ln(50,257) ≈ 10.825. The untrained model's 10.79–10.99 is no better.", "14, 23"),
    ("What does `probas[0, [0, 1, 2], targets[0]]` return?",
     ["the probabilities of the correct next tokens at three positions",
      "the three most likely tokens", "the loss of sentence 1", "the logits of every vocabulary token"],
     "It pairs position 0 with target 0, position 1 with target 1, position 2 with target 2.", "8"),
    ("Why are the logits flattened to `[6, 50257]` before `cross_entropy`?",
     ["`cross_entropy` expects a list of score rows and a list of answers", "to save memory",
      "to shuffle the batch", "to remove the padding tokens"],
     "The function does not care which sentence a position came from; it needs `[N, classes]` and `[N]`.", "13"),
    ("What should be passed to `torch.nn.functional.cross_entropy`?",
     ["the raw logits", "probabilities after softmax", "log-probabilities after `torch.log`", "argmax token IDs"],
     "It applies softmax and log itself. Passing probabilities would apply softmax twice.", "14"),
    (("The training text has 4,612 tokens. With `max_length = stride = 256`, `batch_size=2` and "
     "`drop_last=True`, how many training batches are there?"),
     ["9", "18", "10", "4,612"],
     "18 non-overlapping chunks of 256, two per batch.", "19–20"),
    ("What happens if `optimizer.zero_grad()` is removed from the loop?",
     ["gradients from earlier steps keep adding up", "the loss can no longer be computed",
      "the weights are reset to random values", "dropout is switched off"],
     "PyTorch accumulates gradients by default; every update would mix in all earlier ones.", "24"),
    ("What does `loss.backward()` do?",
     ["computes a gradient for every weight", "changes the weights", "clears the old gradients",
      "measures the validation loss"],
     "`optimizer.step()` changes the weights; `backward()` only works out the direction.", "24"),
    ("Why is `model.train()` called at the start of every epoch?",
     ["evaluation and sampling switch the model to `eval()`", "to reset the weights",
      "to clear the gradients", "to reshuffle the training data"],
     "`evaluate_model` and `generate_and_print_sample` call `model.eval()`; dropout must be back on.", "24–26"),
    ("After 10 epochs: training loss 0.391, validation loss 6.452. What does this mean?",
     ["the model memorized the training text (overfitting)", "the model has not learned enough yet (underfitting)",
      "the validation data is corrupted", "the learning rate was too small"],
     "Training keeps improving while validation gets worse after step 55; the last sample copies the story.", "27"),
    ("What does greedy decoding give when run several times on the same prompt?",
     ["the same text every time", "different text every time", "only the end-of-text token",
      "random words"],
     "`argmax` has no randomness.", "31"),
    ("What does a temperature of 5 do?",
     ["flattens the probabilities, so unlikely words are picked more often", "sharpens the probabilities",
      "makes sampling identical to greedy", "keeps only the 5 best tokens"],
     "Dividing the logits by 5 brings them closer together; even `pizza` gets 0.043.", "38"),
    ("At temperature 0.1, what probability does `forward` get?",
     ["0.991", "0.572", "0.242", "0.111"],
     "Dividing by 0.1 spreads the scores far apart, so the top word takes almost everything.", "38"),
    ("After top-k with k = 3 and softmax, what probability do the other six words get?",
     ["exactly 0", "a small but non-zero value", "the same as before top-k", "a negative value"],
     "Their scores were set to -inf, and e^(−∞) = 0.", "40–41"),
    ("Why did the 1,000-sample count print 8 lines for a 9-word vocabulary?",
     ["`you` was never drawn, and `bincount` stops at the largest ID drawn",
      "the vocabulary dictionary has only 8 entries", "`bincount` always drops the last ID",
      "`multinomial` cannot draw the last index"],
     "`you` has ID 8; the largest ID drawn was 7 (`toward`).", "36"),
    ("Why is `model_and_optimizer.pth` three times the size of `model.pth`?",
     ["AdamW keeps two running averages for every weight", "the model is saved three times",
      "the optimizer stores weights in float64", "the data loaders are saved too"],
     "Weights + 2 × weights = 3 × weights.", "46"),
    ("Which settings must change before loading OpenAI's GPT-2 weights?",
     ["`context_length` 1,024 and `qkv_bias` True", "`drop_rate` 0 and `n_layers` 24",
      "`vocab_size` 50,000", "`emb_dim` 1,024"],
     "Every copied tensor must match the model's shape: 1,024 positions and Q/K/V biases.", "54–55"),
    ("OpenAI's `c_attn` weight is 768 × 2,304. Why?",
     ["query, key and value are stored side by side", "it has 3 attention heads",
      "it covers 3 transformer blocks", "it is for 2,304 tokens"],
     "2,304 = 3 × 768; `np.split` cuts it into the three matrices.", "58"),
    ("Why could a missing `.T` on `W_query` go unnoticed?",
     ["the matrix is square, so the shape check still passes", "`assign` transposes automatically",
      "PyTorch ignores the orientation of weights", "`W_query` is not used when generating"],
     "768 × 768 transposed is still 768 × 768. Only the generated text would reveal it.", "58, 60"),
    ("The model has 163,037,184 parameters. Why is GPT-2 small called \"124M\"?",
     ["the output layer shares the token embedding table", "biases are not counted",
      "the optimizer's state is included in 163M", "a shorter context length is used"],
     "Weight tying: 163,037,184 − 38,597,376 = 124,439,808.", "56, 58"),
]

# Where the correct option ends up (0 = ①). Five answers per position.
ANSWER_SLOTS = [1, 3, 0, 2, 3, 1, 0, 2, 2, 0, 3, 1, 0, 3, 1, 2, 1, 2, 0, 3]
MARKS = ["①", "②", "③", "④"]


def place_answers(quiz):
    """Rotate each question's options (correct one written first) so the answer lands on its slot."""
    assert len(quiz) == len(ANSWER_SLOTS)
    out = []
    for (q, opts, why, cell), slot in zip(quiz, ANSWER_SLOTS):
        k = -slot % len(opts)
        out.append((q, opts[k:] + opts[:k], slot, why, cell))
    return out


def render(title, label, body, out_name):
    page = (f'<!doctype html><html><head><meta charset="utf-8"><title>{title}</title>'
            f'<style>{CSS.replace("LABEL", label)}</style></head><body>{body}'
            '<p class="end">Generated by tools/pdf/ch5_study_pack.py from '
            'notebooks/05_pretraining.ipynb</p></body></html>')
    out = DOCS / out_name
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(page)
        tmp = Path(f.name)
    try:
        subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", tmp.as_uri()], check=True, capture_output=True)
    finally:
        tmp.unlink()
    return out


def build_cards():
    total = sum(len(cards) for _, cards in CARDS)
    body = [(f"<h1>Chapter 5 Flashcards: Pretraining</h1><p class='sub'>{total} cards · question on the left, "
            "answer on the right · the small number is the notebook cell</p>"),
            ("<p class='how'><b>How to use:</b> cover the right column with a sheet of paper, answer each question "
            "out loud, then check. Write down the numbers of the cards you missed and start with those next "
            "time.</p>")]
    n = 0
    for topic, cards in CARDS:
        rows = []
        for q, a, cell in cards:
            n += 1
            rows.append(f"<tr><td>{n}</td><td>{inline(q)}</td>"
                        f"<td>{inline(a)} <span class='cell'>(cell {cell})</span></td></tr>")
        body.append(f"<h2>{topic}</h2><table class='cards'>{''.join(rows)}</table>")
    return render("Chapter 5 Flashcards", "Chapter 5 flashcards", "".join(body),
                  "Ch5_Pretraining_Flashcards.pdf")


def build_quiz():
    quiz = place_answers(QUIZ)
    qs = "".join(
        f"<div class='q'><b>{i}.</b> {inline(q)}<ol>"
        + "".join(f"<li>{MARKS[j]} {inline(o)}</li>" for j, o in enumerate(opts)) + "</ol></div>"
        for i, (q, opts, _, _, _) in enumerate(quiz, start=1))
    key = "".join(
        f"<tr><td>{i}</td><td>{MARKS[c]} {inline(opts[c])}</td>"
        f"<td>{inline(why)} <span class='cell'>(cell {cell})</span></td></tr>"
        for i, (_, opts, c, why, cell) in enumerate(quiz, start=1))
    body = (f"<h1>Chapter 5 Quiz: Pretraining</h1><p class='sub'>{len(QUIZ)} multiple-choice questions · "
            "answers and explanations on the last pages</p>"
            f"<p>Score: ______ / {len(QUIZ)}</p>{qs}"
            "<h1 class='newpage'>Answers</h1>"
            f"<table class='key'><tr><th>#</th><th>Answer</th><th>Why</th></tr>{key}</table>")
    return render("Chapter 5 Quiz", "Chapter 5 quiz", body, "Ch5_Pretraining_Quiz.pdf")


if __name__ == "__main__":
    for build in (build_cards, build_quiz):
        print("wrote", build())
