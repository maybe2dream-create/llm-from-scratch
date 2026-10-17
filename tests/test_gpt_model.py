import pytest
import torch
import torch.nn as nn

from src.gpt_model import (
    GELU,
    FeedForward,
    GPTModel,
    LayerNorm,
    TransformerBlock,
    generate_text_simple,
)

# 구조만 보는 테스트는 작은 설정으로 돌린다. 124M 모델은 생성에만 0.6초가 걸려서,
# 매 테스트마다 만들면 테스트가 느려진다.
TINY_CONFIG = {
    "vocab_size": 100,
    "context_length": 16,
    "emb_dim": 16,
    "n_heads": 2,
    "n_layers": 2,
    "drop_rate": 0.0,
    "qkv_bias": False,
}

# 4장에서 쓴 GPT-2 124M 설정. 아래 "기준값" 테스트는 이 설정에 묶여 있다.
GPT_CONFIG_124M = {
    "vocab_size": 50257,
    "context_length": 1024,
    "emb_dim": 768,
    "n_heads": 12,
    "n_layers": 12,
    "drop_rate": 0.1,
    "qkv_bias": False,
}


@pytest.fixture
def x():
    torch.manual_seed(0)
    return torch.randn(4, 7, TINY_CONFIG["emb_dim"])


def test_gelu_matches_torch_tanh_approximation(x):
    # 책의 수식이 맞는지는 직접 검산하는 대신 PyTorch 내장 구현과 맞춰 본다.
    # 책은 tanh 근사를 쓰므로 기본 GELU(정확한 erf 버전)가 아니라 approximate="tanh"와 비교해야 한다.
    assert torch.allclose(GELU()(x), nn.GELU(approximate="tanh")(x), atol=1e-6)


def test_layernorm_matches_torch_layernorm(x):
    # scale=1, shift=0인 초기 상태라면 nn.LayerNorm과 같아야 한다.
    # 다르면 var의 unbiased 여부나 eps 위치가 틀렸다는 뜻이다.
    assert torch.allclose(LayerNorm(TINY_CONFIG["emb_dim"])(x), nn.LayerNorm(16, eps=1e-5)(x), atol=1e-6)


def test_layernorm_output_is_normalized(x):
    out = LayerNorm(TINY_CONFIG["emb_dim"])(x)
    assert out.mean().abs() < 1e-5
    assert torch.allclose(out.var(dim=-1, unbiased=False), torch.ones(4, 7), atol=1e-4)


def test_feedforward_expands_then_restores(x):
    # 4배로 넓혔다가 되돌리므로 입출력 모양이 같아야 한다.
    assert FeedForward(TINY_CONFIG)(x).shape == x.shape


def test_transformer_block_preserves_shape(x):
    # shortcut 연결 때문에 블록은 모양을 바꾸지 않는다. 쌓을 수 있는 근거다.
    assert TransformerBlock(TINY_CONFIG)(x).shape == x.shape


def test_gptmodel_logits_shape():
    model = GPTModel(TINY_CONFIG)
    idx = torch.randint(0, TINY_CONFIG["vocab_size"], (2, 5))
    # 토큰마다 어휘 전체에 대한 점수가 하나씩 나온다.
    assert model(idx).shape == (2, 5, TINY_CONFIG["vocab_size"])


def test_generate_appends_requested_number_of_tokens():
    model = GPTModel(TINY_CONFIG)
    model.eval()
    idx = torch.randint(0, TINY_CONFIG["vocab_size"], (1, 3))
    out = generate_text_simple(model, idx, max_new_tokens=4, context_size=TINY_CONFIG["context_length"])
    assert out.shape == (1, 7)
    # 앞부분은 입력 그대로 남고 뒤에만 붙는다.
    assert torch.equal(out[:, :3], idx)


def test_generate_crops_context_to_window():
    # idx가 context_length보다 길어도 마지막 context_size개만 보므로 위치 임베딩을 넘지 않는다.
    model = GPTModel(TINY_CONFIG)
    model.eval()
    idx = torch.randint(0, TINY_CONFIG["vocab_size"], (1, TINY_CONFIG["context_length"] + 5))
    out = generate_text_simple(model, idx, max_new_tokens=2, context_size=TINY_CONFIG["context_length"])
    assert out.shape[1] == idx.shape[1] + 2


def test_reference_parameter_count():
    # 4장 노트북과 책이 기록한 값. 레이어 구성이 바뀌면 여기서 먼저 깨진다.
    model = GPTModel(GPT_CONFIG_124M)
    assert sum(p.numel() for p in model.parameters()) == 163_009_536


def test_reference_generation_is_unchanged():
    # 학습 전 GPT-2 124M이 seed 123에서 내놓는 출력. 5장에서 이 모델을 학습시키므로,
    # 그 전에 "출발점이 4장과 같다"는 것을 고정해 둔다.
    # 토큰 ID로 비교하면 tiktoken 없이도 돌아간다.
    torch.manual_seed(123)
    model = GPTModel(GPT_CONFIG_124M)
    model.eval()
    encoded = [15496, 11, 314, 716]  # tiktoken gpt2로 인코딩한 "Hello, I am"
    out = generate_text_simple(
        model,
        torch.tensor(encoded).unsqueeze(0),
        max_new_tokens=6,
        context_size=GPT_CONFIG_124M["context_length"],
    )
    # 디코딩하면 "Hello, I am Featureiman Byeswickattribute argue"
    assert out.tolist()[0] == [15496, 11, 314, 716, 27018, 24086, 47843, 30961, 42348, 7267]
