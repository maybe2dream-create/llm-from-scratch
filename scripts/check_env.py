import platform, sys, time
import torch

print("=" * 52)
print(f"Python   : {sys.version.split()[0]}  ({platform.machine()})")
print(f"macOS    : {platform.mac_ver()[0]}")
print(f"PyTorch  : {torch.__version__}")
print(f"MPS built     : {torch.backends.mps.is_built()}")
print(f"MPS available : {torch.backends.mps.is_available()}")
print("=" * 52)

assert platform.machine() == "arm64", \
    "Running under Rosetta emulation - reinstall Python natively"
assert torch.backends.mps.is_available(), \
    "No Metal GPU access - see troubleshooting"

device = torch.device("mps")

a_cpu = torch.randn(512, 512)
b_cpu = torch.randn(512, 512)
diff = (a_cpu @ b_cpu - (a_cpu.to(device) @ b_cpu.to(device)).cpu()).abs().max()
print(f"CPU vs GPU max difference: {diff:.2e}   (should be tiny)")

x = torch.randn(4096, 4096, device=device)
y = torch.randn(4096, 4096, device=device)
for _ in range(3):
    _ = x @ y
torch.mps.synchronize()

t0 = time.time()
for _ in range(20):
    z = x @ y
torch.mps.synchronize()
gpu_s = time.time() - t0

xc, yc = x.cpu(), y.cpu()
t0 = time.time()
for _ in range(3):
    zc = xc @ yc
cpu_s = (time.time() - t0) / 3 * 20

print(f"GPU  : {gpu_s:6.2f} s   ({20 * 2 * 4096**3 / gpu_s / 1e9:,.0f} GFLOP/s)")
print(f"CPU  : {cpu_s:6.2f} s   (estimated)")
print(f"Speedup: {cpu_s / gpu_s:.1f}x")
print("\nEnvironment is ready.")
