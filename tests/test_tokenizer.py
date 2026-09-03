import pytest

from src.tokenizer import SimpleTokenizerV1, build_vocab, preprocess

TEXT = "It was many and many a year ago, In a kingdom by the sea."


@pytest.fixture
def tokenizer():
    return SimpleTokenizerV1(build_vocab(TEXT))


def test_preprocess_keeps_punctuation_as_tokens():
    assert preprocess("a, b.") == ["a", ",", "b", "."]


def test_vocab_ids_are_contiguous():
    vocab = build_vocab(TEXT)
    assert sorted(vocab.values()) == list(range(len(vocab)))


def test_encode_decode_roundtrip(tokenizer):
    assert tokenizer.decode(tokenizer.encode(TEXT)) == TEXT


def test_encode_is_deterministic(tokenizer):
    assert tokenizer.encode(TEXT) == tokenizer.encode(TEXT)


def test_unknown_token_raises(tokenizer):
    # V1은 어휘 밖 토큰을 표현할 방법이 없다.
    # 2.4절에서 <|unk|>를 도입하면 이 테스트는 바뀐다.
    with pytest.raises(KeyError):
        tokenizer.encode('"Hello"')


def test_em_dash_is_not_a_delimiter():
    # 정규식이 '--'는 알지만 '—'(U+2014)는 모른다.
    # 그래서 'love'와 'love—'는 서로 무관한 두 어휘 항목이 된다.
    vocab = build_vocab("I love— you")
    assert "love—" in vocab
    assert "love" not in vocab
