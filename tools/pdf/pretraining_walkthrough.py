# /// script
# dependencies = []
# ///
"""Chapter 5 line-by-line guide -> docs/Ch5_Pretraining_Line_by_Line.pdf

Run from anywhere:  uv run tools/pdf/pretraining_walkthrough.py

Same approach as gpt_model_walkthrough.py: code and outputs are read straight from
notebooks/05_pretraining.ipynb, explanations are keyed by cell number and line number,
and the build stops if a cell's first line no longer matches. Empty cells are skipped.

Every number in the explanations was checked against the notebook's saved outputs or
recomputed (token IDs with tiktoken, split sizes, softmax values, parameter counts,
checkpoint shapes with tf.train.list_variables).
"""
import html
import json
import subprocess
import tempfile
from pathlib import Path

from gpt_model_walkthrough import CHROME, CSS, code_block, inline

REPO = Path(__file__).resolve().parents[2]
NOTEBOOK = REPO / "notebooks" / "05_pretraining.ipynb"
OUT = REPO / "docs" / "Ch5_Pretraining_Line_by_Line.pdf"
TITLE = "Chapter 5 Line by Line: Pretraining on Unlabeled Data"
MAX_OUTPUT_LINES = 16

# ---------------------------------------------------------------------------
# Explanations: cell number -> details. "first" must equal the cell's first line.
# "lines" is a list of (line label, explanation); labels match the printed numbers.
# "max_out" overrides how many output lines are shown (long model printouts are cut).
# ---------------------------------------------------------------------------
CELLS = {
    1: {
        "first": "import sys", "title": "Imports", "section": "5.1",
        "intro": "Chapter 5 trains the model you built in chapter 4, so it starts by importing it from `src/`.",
        "lines": [
            ("1–2", "Python's settings module, and PyTorch."),
            ("3", ("The notebook runs inside `notebooks/`. Adding `\"..\"` (the repository root) to `sys.path` "
                  "lets Python find the `src` folder.")),
            ("5", ("`GPTModel` and `generate_text_simple` are the chapter 4 classes and function, copied to "
                  "`src/gpt_model.py` on Oct 17 so this chapter can import them instead of retyping them.")),
        ],
    },
    2: {
        "first": "GPT_CONFIG_124M = {", "title": "Settings and an untrained model", "section": "5.1",
        "intro": "The same GPT-2 small settings as chapter 4, with one change: a shorter context.",
        "lines": [
            ("1–9", ("The settings dictionary. Everything matches chapter 4 except `context_length`.")),
            ("3", ("`context_length` is 256 instead of 1,024. Training on a laptop is slow, and shorter inputs "
                  "make each step much cheaper. Section 5.5 sets it back to 1,024 for OpenAI's weights.")),
            ("10", ("`torch.manual_seed(123)` fixes the random starting weights, so your untrained model is "
                   "the same as the book's and prints the same output.")),
            ("11", "Builds the model with random weights."),
            ("12", ("`model.eval()` switches dropout off. The cell's output is the model printing its own "
                   "structure: `eval()` returns the model, and Jupyter shows the last value of a cell.")),
        ],
        "max_out": 8,
    },
    3: {
        "first": "import tiktoken", "title": "Text ↔ token IDs, and a first generation", "section": "5.1",
        "intro": "Two small helpers used for the rest of the chapter, then the untrained model is asked to "
              "continue a sentence.",
        "lines": [
            ("1", "The GPT-2 tokenizer library (BPE, chapter 2)."),
            ("2–5", ("`text_to_token_ids`: text → IDs → tensor. `allowed_special={'<|endoftext|>'}` lets that "
                    "marker be encoded as ID 50256 instead of raising an error. `unsqueeze(0)` adds a batch "
                    "axis: `[4]` → `[1, 4]`, because the model expects a batch.")),
            ("7–9", ("`token_ids_to_text`: the reverse. `squeeze(0)` removes the batch axis, `.tolist()` makes "
                    "a plain list, `decode` turns IDs back into text.")),
            ("11", "The prompt. Its IDs are 6109, 3626, 6100, 345."),
            ("12", "Loads the GPT-2 encoding."),
            ("14–19", ("Greedy generation from chapter 4: 10 new tokens, always the highest-scoring one. "
                      "`context_size` is 256, the longest input the model accepts.")),
            ("20", "Prints the prompt plus the 10 new tokens."),
        ],
        "output_note": "Random words, exactly as in the book. The weights are random, so the scores are too. "
                    "Training should turn this into English.",
    },
    4: {
        "first": "inputs = torch.tensor([[16833, 3626, 6100],", "title": "Inputs and targets",
        "section": "5.1",
        "intro": "To measure how good the model is, it needs the right answers. In pretraining the answer is "
              "simply the next token, so the targets are the inputs shifted by one.",
        "lines": [
            ("1–2", ("Two sentences of three tokens: `every effort moves` (16833, 3626, 6100) and "
                    "`I really like` (40, 1107, 588).")),
            ("3–4", ("The targets: the same sentences shifted one token to the left, with the next word added: "
                    "` effort moves you` (… 345) and ` really like chocolate` (… 11311).")),
        ],
        "note": "Position 0 sees `every` and should predict ` effort`; position 1 sees `every effort` and should "
             "predict ` moves`; and so on. Every position is one small exam question, so 6 positions give 6 "
             "answers to check.",
    },
    5: {
        "first": "with torch.no_grad():", "title": "Scores into probabilities", "section": "5.1",
        "lines": [
            ("1", ("`torch.no_grad()` tells PyTorch not to record the calculation for training. We are only "
                  "looking, so this saves memory and time.")),
            ("2", "`logits`: one score per vocabulary token, at each position: `[2, 3, 50257]`."),
            ("3", ("`softmax` over the last axis turns each row of 50,257 scores into probabilities that add up "
                  "to 1.")),
            ("4", "Same shape as the logits."),
        ],
    },
    6: {
        "first": "token_ids = torch.argmax(probas, dim=-1, keepdim=True)", "title": "The model's guesses",
        "section": "5.1",
        "lines": [
            ("1", ("`argmax` picks the most likely token at each position. `keepdim=True` keeps a last axis of "
                  "size 1: `[2, 3, 1]`.")),
            ("2", "Prints the guessed IDs."),
        ],
        "output_note": "16657 \" Armed\", 339 \" he\", 42826 \"Netflix\" for sentence 1, and \" pressuring\", "
                    "\" empowered\", \"faith\" for sentence 2. None of them is the right answer.",
    },
    7: {
        "first": 'print(f"Targets batch 1: {token_ids_to_text(targets[0], tokenizer)}")',
        "title": "Compare the guesses with the answers", "section": "5.1",
        "lines": [
            ("1", "Decodes the first sentence's targets: ` effort moves you`."),
            ("2–3", ("Decodes the first sentence's guesses. `flatten()` turns `[3, 1]` into `[3]` so "
                    "`token_ids_to_text` gets a flat list.")),
        ],
        "output_note": "\"Armed heNetflix\" instead of \"effort moves you\". The loss in the next cells turns "
                    "\"how wrong\" into one number.",
    },
    8: {
        "first": "text_idx = 0", "title": "Probability given to the right answer", "section": "5.1",
        "intro": "The key idea of the loss: look up how much probability the model gave to the *correct* next "
              "token at each position.",
        "lines": [
            ("1", "Sentence 1."),
            ("2", ("`probas[0, [0, 1, 2], targets[0]]` picks three numbers at once: position 0 with token 3626, "
                  "position 1 with token 6100, position 2 with token 345. These are the probabilities of the "
                  "right answers.")),
            ("3", "Prints them."),
            ("4–6", "The same for sentence 2."),
        ],
        "output_note": "About 0.00001 to 0.00007. Guessing uniformly among 50,257 tokens would give 1/50,257 ≈ "
                    "0.00002, so the untrained model is no better than chance. Training should push these "
                    "numbers toward 1.",
    },
    9: {
        "first": "log_probas = torch.log(torch.cat((target_probas_1, target_probas_2)))",
        "title": "Take the logarithm", "section": "5.1",
        "lines": [
            ("1", ("`torch.cat` joins the two 3-number tensors into one of 6. `torch.log` takes the natural "
                  "logarithm of each.")),
            ("2", "Prints them."),
        ],
        "note": "Why the log? Tiny probabilities become manageable numbers (7.45e-05 → -9.50), and multiplying "
             "probabilities becomes adding logs, which is easier and more stable for the computer. A "
             "probability of 1 gives log 0, so the best possible value is 0.",
    },
    10: {
        "first": "avg_log_probas = torch.mean(log_probas)", "title": "Average over all positions",
        "section": "5.1",
        "lines": [("1–2", "One number for the whole batch: the mean of the six logs, -10.7940.")],
    },
    11: {
        "first": "neg_avg_log_probas = avg_log_probas*-1", "title": "Flip the sign: the loss", "section": "5.1",
        "lines": [
            ("1–2", ("Multiplying by -1 gives 10.7940. By convention, training *minimizes* a number, so the "
                    "loss is the negative average log-probability. This is called **cross-entropy**.")),
        ],
    },
    12: {
        "first": 'print("Logits shape:", logits.shape)', "title": "The shapes cross_entropy needs",
        "section": "5.1",
        "lines": [("1–2", "Logits `[2, 3, 50257]`, targets `[2, 3]`.")],
    },
    13: {
        "first": "logits_flat = logits.flatten(0, 1)", "title": "Flatten the batch", "section": "5.1",
        "lines": [
            ("1", ("`flatten(0, 1)` merges axis 0 (sentences) and axis 1 (positions): `[2, 3, 50257]` → "
                  "`[6, 50257]`, six rows of scores.")),
            ("2", "`[2, 3]` → `[6]`, the six correct token IDs."),
            ("3–4", "Confirms the shapes."),
        ],
        "note": "PyTorch's `cross_entropy` expects a list of score rows and a list of answers. It does not care "
             "which sentence a position came from.",
    },
    14: {
        "first": "loss = torch.nn.functional.cross_entropy(logits_flat, targets_flat)",
        "title": "Cross-entropy in one call", "section": "5.1",
        "lines": [
            ("1", ("Does cells 5 and 8–11 in one step: softmax, pick the correct token's probability, log, "
                  "average, negate. It takes the raw logits, not the probabilities.")),
            ("2", "The same 10.7940 as the manual calculation."),
        ],
        "note": "Two reference points. A model that guesses uniformly scores ln(50,257) ≈ 10.825. The "
             "**perplexity** is e^loss: e^10.794 ≈ 48,700, meaning the model is about as unsure as if it were "
             "choosing among 48,700 equally likely tokens.",
    },
    15: {
        "first": 'file_path = "../data/the-verdict.txt"', "title": "Load the training text",
        "section": "5.1",
        "lines": [
            ("1", ("The short story from chapter 2. `../` because the notebook runs in `notebooks/` and the file "
                  "is in `data/`.")),
            ("2–3", "Opens it as UTF-8 text and reads it into one string."),
        ],
    },
    16: {
        "first": "from pathlib import Path", "title": "Where is the notebook running?", "section": "5.1",
        "lines": [
            ("1–2", ("`Path.cwd()` prints the current working directory. It confirms that relative paths in "
                    "this notebook start from `notebooks/`.")),
        ],
    },
    17: {
        "first": "total_characters = len(text_data)", "title": "How big is the dataset?", "section": "5.1",
        "lines": [
            ("1", "Characters in the story."),
            ("2", "BPE tokens in the story."),
            ("3–4", "Prints both."),
        ],
        "output_note": "20,479 characters and 5,145 tokens, as in the book. That is tiny: GPT-2 was trained on "
                    "billions of tokens. It is enough to watch training work on a laptop.",
    },
    18: {
        "first": "train_ratio = 0.90", "title": "Training and validation split", "section": "5.1",
        "intro": "Part of the text is kept aside. If the model also does well on text it never trained on, "
              "it has learned something general; if not, it has only memorized.",
        "lines": [
            ("1", "90% for training."),
            ("2", "`int(0.9 × 20,479)` = 18,431. The split is by characters, not tokens."),
            ("3", "The first 18,431 characters (4,612 tokens) for training."),
            ("4", "The remaining 2,048 characters (534 tokens) for validation."),
        ],
    },
    19: {
        "first": "from src.dataset import create_dataloader_v1", "title": "Data loaders", "section": "5.1",
        "intro": "Chapter 2's sliding-window data loader, now imported from `src/dataset.py`.",
        "lines": [
            ("1", "Imports `create_dataloader_v1`."),
            ("2", "Fixes the shuffle order, so the batches come out in the same order as in the book."),
            ("4–12", ("Training loader: batches of 2 chunks, each 256 tokens long. `stride` = `max_length` = "
                     "256 means the chunks do not overlap. `shuffle=True` mixes the order each epoch; "
                     "`drop_last=True` drops an incomplete last batch.")),
            ("13–21", ("Validation loader: same chunk size, but no shuffling (order does not matter when only "
                      "measuring) and no dropping (keep every chunk).")),
        ],
        "note": "4,612 training tokens give 18 chunks of 256 → 9 batches. 534 validation tokens give only 2 "
             "chunks → 1 batch. Each chunk's targets are the same 256 tokens shifted by one (cell 4's idea).",
    },
    20: {
        "first": 'print("Train loader:")', "title": "Check the batches", "section": "5.1",
        "lines": [
            ("1–3", "Prints the shape of every training batch: inputs and targets, both `[2, 256]`."),
            ("5–7", "The same for validation."),
        ],
        "output_note": "9 training batches and 1 validation batch.",
    },
    21: {
        "first": "def calc_loss_batch(input_batch, target_batch, model, device):",
        "title": "Loss of one batch", "section": "5.1",
        "lines": [
            ("1", "Takes one batch, the model, and the device (CPU or GPU) to compute on."),
            ("2–3", "Moves the data to the same device as the model; PyTorch refuses to mix devices."),
            ("4", "Runs the model: `[2, 256]` → `[2, 256, 50257]`."),
            ("5–7", "Cells 13–14 in one call: flatten both and compute cross-entropy over 512 positions."),
            ("8", ("Returns the loss as a tensor that still remembers how it was computed, so `backward()` can "
                  "work from it during training.")),
        ],
    },
    22: {
        "first": "def calc_loss_loader(data_loader, model, device, num_batches=None):",
        "title": "Average loss over a loader", "section": "5.1",
        "lines": [
            ("2", "Running total."),
            ("3–4", "An empty loader would divide by zero; return \"not a number\" instead."),
            ("5–6", "By default, use every batch."),
            ("7–8", ("Or only the first `num_batches`, but never more than exist. Training uses 5 to save "
                    "time (`eval_iter`, cell 27).")),
            ("9–16", ("Goes through the batches, adds each loss, and stops after `num_batches`. `.item()` turns "
                     "the one-number tensor into a plain Python number.")),
            ("17", "The average."),
        ],
    },
    23: {
        "first": 'device = torch.device("cuda" if torch.cuda.is_available() else "cpu")',
        "title": "Loss before training", "section": "5.1",
        "lines": [
            ("1", ("Uses an NVIDIA GPU if there is one, otherwise the CPU. On this Mac there is no CUDA, so it "
                  "is the CPU. Apple's GPU (`mps`) is available but this line does not ask for it.")),
            ("2", "Moves the model's weights to that device."),
            ("3–5", "Loss over all training batches and the validation batch, without recording for training."),
            ("6–7", "Prints both."),
        ],
        "output_note": "About 10.99 for both: no better than the uniform 10.825 from cell 14. This is the "
                    "starting point that training must bring down.",
    },
    24: {
        "first": "def train_model_simple(model, train_loader, val_loader,", "title": "The training loop",
        "section": "5.2",
        "intro": "The heart of the chapter. Each step: compute the loss, find out how every weight should change "
              "to reduce it, change the weights a little. Repeat.",
        "lines": [
            ("1–3", "Inputs: model, data, optimizer, device, and settings for how often to report."),
            ("4", "Lists to record the losses and how many tokens had been seen, for the plot."),
            ("5", ("`global_step` starts at -1 so the first step becomes step 0, and `0 % 5 == 0` reports "
                  "right after the first update.")),
            ("7", "One epoch = one pass over all 9 training batches."),
            ("8", ("`model.train()` turns dropout on. It is needed at the start of every epoch because "
                  "evaluation and sampling switch the model to `eval()`.")),
            ("9", "One batch at a time."),
            ("10", ("`zero_grad()` clears the previous step's gradients. PyTorch *adds* new gradients to old "
                   "ones by default, so without this each step would mix in all earlier steps.")),
            ("11–13", "The loss of this batch."),
            ("14", ("`backward()` computes, for each of the 162 million weights, how the loss would change if "
                   "that weight changed slightly (the gradient).")),
            ("15", "`optimizer.step()` moves every weight a small amount in the direction that lowers the loss."),
            ("16", "`numel()` = 2 × 256 = 512 tokens processed in this step."),
            ("17", "Counts steps."),
            ("19–24", "Every 5 steps: measure the losses (cell 25) and record them."),
            ("25–28", ("Prints a progress line. `{global_step:06d}` pads the step to six digits. A space is "
                      "missing after the comma on line 26, so the output reads `9.781,Val`.")),
            ("29–31", "After each epoch: let the model write 50 tokens so you can *see* the progress."),
            ("32", "Returns the recorded losses and token counts."),
        ],
    },
    25: {
        "first": "def evaluate_model(model, train_loader, val_loader, device, eval_iter):",
        "title": "Measure without training", "section": "5.2",
        "lines": [
            ("2", "Dropout off, so the measurement is not random."),
            ("3", "No recording for training; measuring must not change anything."),
            ("4–9", ("Average loss over the first `eval_iter` (5) training batches and validation batches. "
                    "Validation has only 1, so `min` in cell 22 uses 1.")),
            ("10", "Dropout back on for training."),
            ("11", "Returns both losses."),
        ],
    },
    26: {
        "first": "def generate_and_print_sample(model, tokenizer, device, start_context):",
        "title": "Show a sample", "section": "5.2",
        "lines": [
            ("2", "Dropout off."),
            ("3", ("The context size is read from the model itself: the number of rows of the position "
                  "embedding, 256.")),
            ("4", "Prompt → IDs, on the model's device."),
            ("5–9", "Greedy generation of 50 tokens."),
            ("10–11", "IDs → text. Newlines are replaced with spaces so each sample fits on one line."),
            ("12", "Dropout back on."),
        ],
    },
    27: {
        "first": "torch.manual_seed(123)", "title": "Train for 10 epochs", "section": "5.2",
        "lines": [
            ("1–2", "A fresh model with the same random start as the book."),
            ("3", "On the CPU (cell 23)."),
            ("4–7", ("**AdamW**: the optimizer that decides how far to move each weight. `lr=0.0004` is the "
                    "learning rate (step size). `weight_decay=0.1` gently pulls weights toward zero, which "
                    "discourages extreme values.")),
            ("8", "10 passes over the data."),
            ("9–13", ("Runs the loop: report every 5 steps (`eval_freq`), measuring on 5 batches "
                     "(`eval_iter`). 9 batches × 10 epochs = 90 steps, so 18 reports (steps 0, 5, …, 85).")),
        ],
        "max_out": 40,
        "output_note": "Your numbers match the book exactly. Read the samples top to bottom: commas only, then "
                    "\"and, and, and\", then real phrases, and by epoch 10 whole sentences from the story.",
        "warn": "Training loss falls to 0.391, but validation loss stops improving around 6.13 (step 55) and then "
             "rises to 6.452. This is **overfitting**: the model has memorized the 4,612 training tokens "
             "instead of learning English. The final sample is a sentence copied word for word from the story. "
             "With one short story and 10 epochs this is expected; the book says so too.",
    },
    28: {
        "first": "import matplotlib.pyplot as plt", "title": "A function to plot the losses", "section": "5.2",
        "lines": [
            ("1–2", "The plotting library, and a helper for whole-number axis ticks."),
            ("4", "A figure 5 × 3 inches with one set of axes."),
            ("5–6", "Training loss as a solid line, validation loss as dash-dot."),
            ("7–9", "Axis labels and a legend."),
            ("10", "Epoch ticks at whole numbers only."),
            ("11", "`twiny()` adds a second x-axis on top that shares the same y-axis."),
            ("12", ("Plots the training loss against tokens seen, but invisible (`alpha=0`). Its only job is to "
                   "give the top axis the right scale.")),
            ("13–15", "Labels the top axis, fixes the spacing, shows the figure."),
        ],
    },
    29: {
        "first": "epochs_tensor = torch.linspace(0, num_epochs, len(train_losses))", "title": "The loss plot",
        "section": "5.2",
        "lines": [
            ("1", "18 evenly spaced x-positions from 0 to 10, one for each recorded loss."),
            ("2", "Draws the plot."),
        ],
        "output_note": "The gap between the two lines is the picture of overfitting: training keeps falling, "
                    "while validation falls only slowly after epoch 2 and turns up again after epoch 7.",
    },
    30: {
        "first": 'model.to("cpu")', "title": "Back to CPU, prediction mode", "section": "5.3",
        "lines": [
            ("1", "Moves the weights to the CPU (they already were here, but on a GPU machine this matters)."),
            ("2", "Dropout off. The output is the model printing its structure again."),
        ],
        "max_out": 6,
    },
    31: {
        "first": 'tokenizer = tiktoken.get_encoding("gpt2")', "title": "Greedy generation after training",
        "section": "5.3",
        "lines": [
            ("1", "Recreates the tokenizer (the same one as before)."),
            ("2–7", "25 new tokens, greedy."),
            ("8", "Prints the result."),
        ],
        "output_note": "Greedy decoding always picks the top token, so it gives the same text every time, and "
                    "here that text is memorized from the story. Section 5.3 adds controlled randomness.",
    },
    32: {
        "first": "vocab = {", "title": "A toy vocabulary", "section": "5.3",
        "intro": "To see decoding clearly, the book switches to a 9-word vocabulary.",
        "lines": [
            ("1–11", "Each word gets an ID from 0 to 8."),
            ("12", "The reverse lookup, ID → word, built by swapping each pair."),
        ],
    },
    33: {
        "first": "next_token_logits = torch.tensor(", "title": "Made-up scores for the next word",
        "section": "5.3",
        "lines": [
            ("1–3", ("Pretend the model, given \"every effort moves you\", produced these 9 scores. The highest "
                    "are `forward` (6.75) and `toward` (6.28).")),
        ],
    },
    34: {
        "first": "probas = torch.softmax(next_token_logits, dim=0)", "title": "Greedy: always the top word",
        "section": "5.3",
        "lines": [
            ("1", ("Softmax over the only axis (`dim=0`). Probabilities: forward 0.572, toward 0.358, closer "
                  "0.061, all others under 0.005.")),
            ("2", "`argmax` → 3. `.item()` makes it a plain number."),
            ("3", "→ `forward`. Every run gives the same answer."),
        ],
    },
    35: {
        "first": "torch.manual_seed(123)", "title": "Sampling instead", "section": "5.3",
        "lines": [
            ("1", "Fixes the dice so the result matches the book."),
            ("2", ("`torch.multinomial` draws one ID at random, *in proportion* to the probabilities: "
                  "`forward` 57% of the time, `toward` 36%, and so on.")),
            ("3", "This draw gives `forward`."),
        ],
    },
    36: {
        "first": "def print_sampled_tokens(probas):", "title": "Sample 1,000 times", "section": "5.3",
        "lines": [
            ("2", "Same seed, so the same 1,000 draws each time."),
            ("3", "1,000 draws (`1_000` is just 1000 with a separator for readability)."),
            ("4", "`bincount` counts how often each ID appeared."),
            ("5–6", "Prints each count with its word."),
            ("8", "Runs it on cell 34's probabilities."),
        ],
        "output_note": "582 forward, 343 toward, 73 closer, matching 57%, 36%, 6%. `you` (ID 8) is missing: it "
                    "was never drawn, and `bincount` only counts up to the largest ID that appeared (7).",
    },
    37: {
        "first": "def softmax_with_temperature(logits, temperature):", "title": "Temperature", "section": "5.3",
        "lines": [
            ("2", ("Divides every score by the temperature. Above 1 the scores move closer together; below 1 "
                  "they spread apart.")),
            ("3", "Softmax of the scaled scores."),
        ],
    },
    38: {
        "first": "temperatures = [1, 0.1, 5]", "title": "Plot three temperatures", "section": "5.3",
        "lines": [
            ("1–2", "The probabilities at temperatures 1, 0.1 and 5."),
            ("3–4", "Bar positions 0 to 8, and a narrow bar width."),
            ("5–8", "Three bars per word, side by side: each temperature is shifted right by `i × 0.15`."),
            ("9–14", "Labels, word names under the bars, legend, show."),
        ],
        "output_note": "T = 0.1: `forward` gets 0.991, almost greedy. T = 1: unchanged. T = 5: much flatter "
                    "(`forward` 0.242, and even `pizza` gets 0.043), so nonsense becomes likely.",
    },
    39: {
        "first": "top_k = 3", "title": "Top-k: keep only the best k", "section": "5.3",
        "lines": [
            ("1", "Keep 3 candidates."),
            ("2", "`torch.topk` returns the 3 largest scores and their positions."),
            ("3–4", "6.75, 6.28, 4.51 at positions 3, 7, 0: forward, toward, closer."),
        ],
    },
    40: {
        "first": "new_logits = torch.where(", "title": "Mask the rest with -inf", "section": "5.3",
        "lines": [
            ("1–5", ("`torch.where(condition, a, b)`: where the condition is true take `a`, else `b`. Every "
                    "score below the third-best (4.51) becomes minus infinity; the top 3 stay.")),
            ("6", "Prints the masked scores."),
        ],
    },
    41: {
        "first": "topk_probas = torch.softmax(new_logits, dim=0)", "title": "Softmax after top-k",
        "section": "5.3",
        "lines": [("1–2", "e^(−∞) = 0, so the masked words get probability exactly 0.")],
        "output_note": "0.0615, 0.5775, 0.3610: the three survivors share all the probability. Compare cell 34 "
                    "(0.061, 0.572, 0.358): same order, slightly larger, since nothing is left for the others.",
    },
    42: {
        "first": "def generate(model, idx, max_new_tokens, context_size,",
        "title": "generate(): greedy, temperature and top-k together", "section": "5.3",
        "intro": "`generate_text_simple` from chapter 4 with three additions.",
        "lines": [
            ("1–2", ("New options: `temperature` (0 = greedy), `top_k` (None = no limit), `eos_id` (stop at "
                    "this token).")),
            ("3–7", "As in chapter 4: crop to the context size, run the model, keep only the last position."),
            ("8–15", ("Top-k as in cells 39–40: find the k-th best score and set everything below it to "
                     "-inf. `.to(logits.device)` puts the -inf on the same device as the scores.")),
            ("16–19", "Temperature > 0: scale, softmax, and *sample* (cells 35–37)."),
            ("20–21", "Temperature 0: greedy, exactly as `generate_text_simple`."),
            ("22–23", "Stop early if the model produced the end-of-text token."),
            ("24", "Append the new token and continue."),
            ("25", "Returns prompt + new tokens."),
        ],
        "note": "Lines 10 and 22 assume one sentence at a time. `top_logits[:, -1]` has shape `[batch]`, which "
             "only lines up with `[batch, 50257]` when the batch is 1; `top_logits[:, -1:]` would work for any "
             "batch. The book's code is the same, and every call in this chapter uses one sentence.",
    },
    43: {
        "first": "torch.manual_seed(123)", "title": "Generate with top-k 25 and temperature 1.4",
        "section": "5.3",
        "lines": [
            ("1", "Fixes the random draws."),
            ("2–9", "15 new tokens from the 25 best candidates, with a flatter distribution (T = 1.4)."),
            ("10", "Prints the result."),
        ],
        "output_note": "Matches the book. Unlike the greedy output, this is not a copied sentence: sampling lets "
                    "the overfitted model leave the memorized path.",
    },
    44: {
        "first": 'torch.save(model.state_dict(), "model.pth")', "title": "Save the weights", "section": "5.4",
        "lines": [
            ("1", ("`state_dict()` is a dictionary: each layer's name → its tensor. `torch.save` writes it to "
                  "`notebooks/model.pth`.")),
        ],
        "note": "The file is 653 MB: 162.4 million numbers × 4 bytes each, plus the 12 causal masks "
             "(256 × 256 each), which are saved too because they are registered buffers. `*.pth` is in "
             "`.gitignore`, so git never sees it.",
    },
    45: {
        "first": "model = GPTModel(GPT_CONFIG_124M)", "title": "Load the weights back", "section": "5.4",
        "lines": [
            ("1", "A new model with random weights."),
            ("2", ("`torch.load` reads the file; `map_location=device` puts the tensors on this machine's "
                  "device even if they were saved on another. `load_state_dict` copies them into the model by "
                  "name.")),
            ("3", "Dropout off, ready to generate."),
        ],
        "max_out": 6,
    },
    46: {
        "first": "torch.save({", "title": "Save the weights and the optimizer", "section": "5.4",
        "lines": [
            ("1–5", ("One file holding two dictionaries: the model's weights and the optimizer's state. Needed "
                    "if you want to *continue* training later.")),
        ],
        "note": "This file is 1.95 GB, three times the model alone. AdamW keeps two running averages for every "
             "weight (how it has been moving, and how much), so its state is twice the size of the model.",
    },
    47: {
        "first": 'checkpoint=torch.load("model_and_optimizer.pth", map_location=device)',
        "title": "Restore both, ready to train", "section": "5.4",
        "lines": [
            ("1", "Reads the combined file."),
            ("2–3", "A new model, filled with the saved weights."),
            ("4", "A new optimizer for that model."),
            ("5", ("Restores AdamW's running averages, and also its settings: the saved `lr=0.0004` replaces "
                  "the `5e-4` written on line 4.")),
            ("6", "Training mode, to continue where training stopped."),
        ],
        "max_out": 6,
    },
    48: {
        "first": "# gpt_download.py는 이제 저장소에 커밋되어 있어 다시 받지 않는다.",
        "title": "Downloading gpt_download.py (switched off)", "section": "5.5",
        "lines": [
            ("1–3", "Why the cell is commented out."),
            ("4–11", ("The original code. It downloaded Raschka's helper script from the main branch on "
                     "GitHub into `notebooks/`. Running it again would replace the committed copy with "
                     "whatever version is there that day, and run code you have not read.")),
        ],
    },
    49: {
        "first": "from gpt_download import download_and_load_gpt2", "title": "Download OpenAI's GPT-2 weights",
        "section": "5.5",
        "lines": [
            ("1", ("Imports the helper from `notebooks/gpt_download.py`. Python finds it because the notebook "
                  "runs in `notebooks/`.")),
            ("2–4", ("Downloads 7 files for the 124M model into `notebooks/gpt2/124M/` (skipping files already "
                    "there with the right size), reads them with TensorFlow, and returns `settings` and "
                    "`params`.")),
        ],
        "output_note": "The weights file is 498 MB and took 6.5 minutes. `notebooks/gpt2/` is in `.gitignore`.",
    },
    50: {
        "first": 'print("Settings:", settings)', "title": "What was downloaded", "section": "5.5",
        "lines": [
            ("1", ("OpenAI's names for familiar settings: `n_vocab` = vocab_size, `n_ctx` = context_length "
                  "(1,024), `n_embd` = emb_dim, `n_head` = n_heads, `n_layer` = n_layers.")),
            ("2", ("The weights: `blocks` (a list of 12, one per transformer block), `wte` (token "
                  "embeddings), `wpe` (position embeddings), and `g`/`b` (gain and bias of the final "
                  "LayerNorm).")),
        ],
    },
    51: {
        "first": 'print(params["wte"])', "title": "The token embedding table", "section": "5.5",
        "lines": [
            ("1", "A NumPy array. NumPy shortens the printout, putting `...` where rows and columns are left out."),
            ("2", "50,257 rows × 768 columns, the same shape as your `tok_emb`."),
        ],
    },
    52: {
        "first": "model_configs ={", "title": "The four GPT-2 sizes", "section": "5.5",
        "lines": [
            ("1–6", ("Width, depth and heads of each released size. Only the 124M model is used here; the "
                    "others need more memory and a longer download.")),
        ],
    },
    53: {
        "first": 'model_name = "gpt2-small (124M)"', "title": "Start from the training settings",
        "section": "5.5",
        "lines": [
            ("1", "The size to load."),
            ("2", ("`.copy()` makes a new dictionary. Without it, changes would also modify "
                  "`GPT_CONFIG_124M`.")),
            ("3", "Writes in that size's numbers (for 124M they are the same as before)."),
        ],
    },
    54: {
        "first": 'NEW_CONFIG.update({"context_length":1024})', "title": "Back to 1,024 positions",
        "section": "5.5",
        "lines": [
            ("1", ("OpenAI's position table `wpe` has 1,024 rows. The model's `pos_emb` must have the same "
                  "shape, or `assign` (cell 57) stops with a shape error.")),
        ],
    },
    55: {
        "first": 'NEW_CONFIG.update({"qkv_bias":True})', "title": "Turn on Q/K/V biases", "section": "5.5",
        "lines": [
            ("1", ("OpenAI's model has bias terms in the query, key and value layers, so the model needs "
                  "places to put them. This is why chapter 4 kept `qkv_bias` as a setting.")),
        ],
    },
    56: {
        "first": "gpt = GPTModel(NEW_CONFIG)", "title": "An empty model of the right shape", "section": "5.5",
        "lines": [
            ("1", "Builds the model with random weights."),
            ("2", "Dropout off."),
        ],
        "max_out": 12,
        "output_note": "Note `Embedding(1024, 768)` and `bias=True`. This model has 163,037,184 parameters; minus "
                    "the 38,597,376 shared with the output layer (cell 58, line 60), that is 124,439,808: the "
                    "official size of GPT-2 small.",
    },
    57: {
        "first": "def assign(left, right):", "title": "assign(): copy one weight safely", "section": "5.5",
        "lines": [
            ("1", "`left` is the model's current tensor, `right` the NumPy array from OpenAI."),
            ("2–3", "If the shapes differ, stop with a clear message instead of loading the wrong thing."),
            ("4", ("Converts NumPy → PyTorch tensor → `nn.Parameter`. A Parameter is what tells the model "
                  "\"this is a trainable weight\".")),
        ],
    },
    58: {
        "first": "import numpy as np", "title": "load_weights_into_gpt(): put every weight in its place",
        "section": "5.5",
        "intro": "OpenAI's names and layout differ from yours. This function is the translation table.",
        "lines": [
            ("4–5", "Position and token embeddings: `wpe` → `pos_emb`, `wte` → `tok_emb`."),
            ("7", "For each of the 12 blocks."),
            ("8–9", ("OpenAI stores query, key and value as one matrix `c_attn`, 768 × 2,304. `np.split(…, 3, "
                    "axis=-1)` cuts it into three 768 × 768 pieces.")),
            ("10–15", ("Copies them into `W_query`, `W_key`, `W_value`. `.T` (transpose) is needed because "
                      "OpenAI stores a layer as [inputs, outputs], while `nn.Linear` stores [outputs, "
                      "inputs].")),
            ("17–24", "The same split for the three biases: 2,304 → 3 × 768."),
            ("26–31", "The attention output layer: `c_proj` → `out_proj`, transposed."),
            ("33–38", ("The feed-forward network's first layer (768 → 3,072): `mlp.c_fc` → `ff.layers[0]`. "
                      "`layers[1]` is GELU, which has no weights.")),
            ("39–44", "The second layer (3,072 → 768): `mlp.c_proj` → `ff.layers[2]`."),
            ("46–57", ("The two LayerNorms of the block: `ln_1` → `norm1`, `ln_2` → `norm2`. OpenAI's `g` "
                      "(gain) is your `scale`, `b` (bias) is your `shift`.")),
            ("58–59", "The final LayerNorm, after all 12 blocks."),
            ("60", ("The output layer reuses the token embedding table (**weight tying**, chapter 4). A [50,257, "
                   "768] table fits `Linear(768, 50257)` because PyTorch stores that layer as [50,257, 768].")),
        ],
        "warn": "A forgotten `.T` on a 768 × 768 matrix (lines 11–15, 28) would not be caught: the transposed "
             "shape is the same, so `assign` accepts it, and the model silently produces nonsense. Only the "
             "generated text in cell 60 proves these are right. On the 768 × 3,072 layers a missing `.T` "
             "would fail the shape check.",
    },
    59: {
        "first": "load_weights_into_gpt(gpt, params)", "title": "Load the weights", "section": "5.5",
        "lines": [
            ("1", "Replaces every random weight with OpenAI's."),
            ("2", "Puts the model on the device (CPU)."),
        ],
        "max_out": 6,
    },
    60: {
        "first": "torch.manual_seed(123)", "title": "Generate with real GPT-2", "section": "5.5",
        "lines": [
            ("1", "Fixes the random draws."),
            ("2–9", ("25 tokens, top-k 50, temperature 1.5, context 1,024. `.to(device)` puts the prompt on "
                    "the model's device.")),
            ("10", "Prints the result."),
        ],
        "output_note": "Fluent English, identical to the book. Your 10 epochs on one short story produced "
                    "memorized fragments; OpenAI's training on about 40 GB of web text produced a model that "
                    "writes new sentences. Same architecture, different weights.",
    },
}

SECTIONS = [
    ("5.1", "Evaluating generative text models", "Cells 1–23"),
    ("5.2", "Training an LLM", "Cells 24–29"),
    ("5.3", "Decoding strategies to control randomness", "Cells 30–43"),
    ("5.4", "Loading and saving model weights", "Cells 44–47"),
    ("5.5", "Loading pretrained weights from OpenAI", "Cells 48–60"),
]

FRONT = """
<h1>{title}</h1>
<p class="sub">Every line of <code>notebooks/05_pretraining.ipynb</code>, explained. Code and outputs are taken
directly from the notebook; the explanations follow Raschka, <i>Build a Large Language Model (From Scratch)</i>,
chapter 5.</p>

<h2>How to use this document</h2>
<p>Keep the notebook open next to it. Each cell has the same number as its position in the notebook (cell 1 is the
first cell), its code with line numbers, a table explaining each line, and the cell's real output. Long printouts
of the model's structure are cut after a few lines. On a second reading, try to explain each line yourself before
looking at the table.</p>

<h2>The big picture</h2>
<p>Chapter 4 built a model that writes random words. Chapter 5 teaches it, using nothing but text: the right
answer at every position is simply the next token. One training step looks like this:</p>
<pre>text chunk (256 tokens)        inputs  [2, 256]    targets = inputs shifted by 1
 -> model                       logits  [2, 256, 50257]
 -> cross-entropy loss          one number          "how surprised was the model by the right answers?"
 -> loss.backward()             a gradient for each of 162 million weights
 -> optimizer.step()            every weight moves a little to lower the loss
 -> repeat: 9 batches x 10 epochs = 90 steps</pre>
<p>Then three more things: how to choose the next token less mechanically (temperature and top-k), how to save and
load weights, and how to load OpenAI's trained GPT-2 weights into your own model.</p>
<p>One sentence to remember: <b>the loss is the average of −log(probability given to the right next token), and
training is 90 small nudges that make those probabilities larger.</b></p>

<table><tr><th>Section</th><th>Topic</th><th>Notebook cells</th></tr>{sections}</table>
"""

BACK = """
<h2>Numbers to remember</h2>
<table>
<tr><th>What</th><th>Value</th><th>Cell</th></tr>
<tr><td>Loss of an untrained model (6 positions)</td><td>10.7940</td><td>11, 14</td></tr>
<tr><td>Loss of uniform guessing, ln(50,257)</td><td>10.825</td><td>14</td></tr>
<tr><td>Training text / validation text</td><td>4,612 / 534 tokens → 9 / 1 batches</td><td>18–20</td></tr>
<tr><td>Losses before training (train / val)</td><td>10.988 / 10.981</td><td>23</td></tr>
<tr><td>Losses after 10 epochs (train / val)</td><td>0.391 / 6.452</td><td>27</td></tr>
<tr><td>Sampling 1,000 times: forward / toward / closer</td><td>582 / 343 / 73</td><td>36</td></tr>
<tr><td>Top-3 probabilities</td><td>0.0615 / 0.5775 / 0.3610</td><td>41</td></tr>
<tr><td><code>model.pth</code> / <code>model_and_optimizer.pth</code></td><td>653 MB / 1.95 GB</td><td>44, 46</td></tr>
<tr><td>GPT-2 small parameters (with weight tying)</td><td>124,439,808</td><td>56</td></tr>
</table>

<h2>Greedy, temperature, top-k</h2>
<table>
<tr><th>Setting in <code>generate</code></th><th>What it does</th><th>Result</th></tr>
<tr><td><code>temperature=0</code></td><td>always the top token</td><td>same text every time; repeats memorized text</td></tr>
<tr><td><code>temperature</code> below 1</td><td>sharpens the distribution</td><td>close to greedy</td></tr>
<tr><td><code>temperature</code> above 1</td><td>flattens the distribution</td><td>more variety, more nonsense</td></tr>
<tr><td><code>top_k=k</code></td><td>only the k best tokens can be drawn</td><td>keeps variety, removes absurd choices</td></tr>
</table>

<h2>Questions to test yourself</h2>
<ol class="qa">
<li>Where do the targets come from in pretraining, and why is no human labelling needed?</li>
<li>Why is the loss the <i>negative</i> average of log-probabilities?</li>
<li>What does <code>flatten(0, 1)</code> do to the logits, and why does <code>cross_entropy</code> need it?</li>
<li>Why does an untrained model have a loss of about 10.8?</li>
<li>What would go wrong without <code>optimizer.zero_grad()</code>?</li>
<li>Why is <code>model.train()</code> called at the start of every epoch?</li>
<li>Training loss 0.391, validation loss 6.452: what does this gap mean?</li>
<li>Why does <code>bincount</code> in cell 36 print 8 lines and not 9?</li>
<li>What does a temperature of 5 do to the probabilities, and why is that risky?</li>
<li>Why is <code>model_and_optimizer.pth</code> three times larger than <code>model.pth</code>?</li>
<li>Why must <code>context_length</code> be 1,024 and <code>qkv_bias</code> True before loading OpenAI's weights?</li>
<li>Why do the OpenAI weight matrices need <code>.T</code>, and why would a missing one go unnoticed?</li>
</ol>
<p><b>Answers.</b> (1) The text itself: the target is the next token, so any text is training data. (2) Training
minimizes; log-probabilities are negative and best at 0, so their negative is positive and best at 0. (3) It
merges sentences and positions into one list of score rows, <code>[6, 50257]</code>, matching a flat list of 6
answers. (4) Random weights spread probability almost evenly, and ln(50,257) ≈ 10.825. (5) Gradients would keep
adding up across steps, so every update would mix in all earlier ones. (6) Evaluation and sampling switch the model
to <code>eval()</code>; dropout must be turned back on for training. (7) Overfitting: the model memorized the
training text instead of learning patterns that carry over to new text. (8) <code>you</code> (ID 8) was never drawn,
and <code>bincount</code> counts only up to the largest ID seen. (9) It flattens them, so unlikely words such as
<code>pizza</code> start being picked. (10) AdamW stores two extra numbers per weight. (11) Every copied tensor must
have exactly the model's shape, and OpenAI's model has 1,024 positions and Q/K/V biases. (12) OpenAI stores layers as
[inputs, outputs] and <code>nn.Linear</code> as [outputs, inputs]; for a square 768 × 768 matrix both shapes are the
same, so the shape check passes.</p>
"""


def cell_outputs(cell, max_lines):
    parts = []
    for o in cell.get("outputs", []):
        data = o.get("data", {})
        if "image/png" in data:
            parts.append(f'<img class="plot" src="data:image/png;base64,{data["image/png"]}">')
            continue
        if o.get("output_type") == "error":
            raise SystemExit(f"cell has an error output ({o['ename']}); rerun the notebook first")
        text = ("".join(o.get("text", "")) or "".join(data.get("text/plain", ""))).rstrip()
        if not text or text.startswith("<Figure"):
            continue
        lines = text.split("\n")
        if len(lines) > max_lines:
            lines = lines[:max_lines] + [f"… ({len(lines) - max_lines} more lines not shown)"]
        parts.append(f'<pre class="output">{html.escape(chr(10).join(lines))}</pre>')
    if not parts:
        return ""
    return '<p class="outlabel">Output</p>' + "".join(parts)


def build():
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    cells = [c for c in nb["cells"] if c["cell_type"] == "code" and "".join(c["source"]).strip()]
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
        if info["section"] != current:
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
        out.append(cell_outputs(cell, info.get("max_out", MAX_OUTPUT_LINES)))
        for key in ("output_note", "note"):
            if info.get(key):
                out.append(f'<div class="note">{inline(info[key])}</div>')
        if info.get("warn"):
            out.append(f'<div class="warn">{inline(info["warn"])}</div>')
        out.append("</div>")
        body.append("".join(out))
    body.append(BACK)
    body.append('<p class="end">Generated by tools/pdf/pretraining_walkthrough.py from '
                'notebooks/05_pretraining.ipynb</p>')

    css = CSS.replace('"Chapter 4 line by line"', '"Chapter 5 line by line"')
    page = (f'<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(TITLE)}</title>'
            f"<style>{css}</style></head><body>{''.join(body)}</body></html>")
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
