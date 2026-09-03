import re

SPLIT_PATTERN = r'([,.:;?_!"()\']|--|\s)'


def preprocess(text):
    preprocessed = re.split(SPLIT_PATTERN, text)
    return [item.strip() for item in preprocessed if item.strip()]


def build_vocab(text):
    all_words = sorted(set(preprocess(text)))
    return {token: integer for integer, token in enumerate(all_words)}


class SimpleTokenizerV1:
    def __init__(self, vocab):
        self.str_to_int = vocab
        self.int_to_str = {i: s for s, i in vocab.items()}

    def encode(self, text):
        ids = [self.str_to_int[s] for s in preprocess(text)]
        return ids

    def decode(self, ids):
        text = " ".join([self.int_to_str[i] for i in ids])
        text = re.sub(r'\s+([,.:;?_!"()\'])', r'\1', text)
        return text
