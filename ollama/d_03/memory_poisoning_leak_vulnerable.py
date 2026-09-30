"""소유자 확인 없이 공유 메모리를 재사용하는 취약 경로 실습."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "d00-shared"))

from local_llm import DEFAULT_MODEL, ask_real, is_ollama_available  # noqa: E402
from memory_poisoning_common import MemoryEntry, build_memory_scenario  # noqa: E402
from prompts import MEMORY_RECALL_QUESTION, MEMORY_RECALL_SYSTEM_INSTRUCTION  # noqa: E402


def main() -> None:
    if not is_ollama_available():
        print("LLM 연결 안됨: Ollama 서버(http://localhost:11434)에 연결할 수 없습니다.")
        print("Ollama 설치/서버 실행 여부를 확인하세요.")
        return
    run_real(build_memory_scenario(), "user_charlie")


def run_real(memory: List[MemoryEntry], current_requester: str, model: str = DEFAULT_MODEL) -> None:
    """소유자 필터 없는 전체 메모리를 실제 Ollama에 보내 응답을 관찰한다."""
    print("=" * 70)
    print(f"예제 3: 메모리 포이즈닝 - 취약 경로 — Ollama ({model})")
    print("=" * 70)
    print("[공유 메모리]")
    for entry in memory:
        print(f"  - owner={entry.owner_id!r}: {entry.text}")
    print(f"[요청자 질문] {current_requester}: {MEMORY_RECALL_QUESTION}\n")

    # 취약 경로: owner_id를 확인하지 않고 모든 항목의 본문을 컨텍스트로 결합한다.
    context = "\n".join(f"- {entry.text}" for entry in memory)
    # 공통 질문을 붙여 실제 user 메시지를 만든다. 공격 지시와 질문이 동시에 전달된다.
    user_content = f"{context}\n\n사용자 질문: {MEMORY_RECALL_QUESTION}"
    print(f"[실제 입력: system]\n{MEMORY_RECALL_SYSTEM_INSTRUCTION}\n")
    print(f"[실제 입력: user]\n{user_content}\n")

    # system 지시와 취약 컨텍스트를 실제 로컬 모델에 전송한다.
    result = ask_real(
        MEMORY_RECALL_SYSTEM_INSTRUCTION,
        user_content,
        model=model,
        temperature=0.2,
    )
    if not result.ok:
        print(f"호출 실패: {result.error}")
        return

    print(f"응답:\n{result.text}\n")
    # 단순 문자열 포함 여부만 관찰한다. 다른 표현의 누출이나 의미상 노출은 포착하지 못한다.
    print(f"응답에 4521 포함 여부: {'4521' in result.text}")


if __name__ == "__main__":
    main()
