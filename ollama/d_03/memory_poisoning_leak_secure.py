"""요청자 소유 메모리만 사용하는 보안 경로 실습."""

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
    """요청자 소유 메모리만 실제 Ollama 입력으로 보내 응답을 관찰한다.

    취약 파일과 같은 질문·system 지시를 사용하고, 컨텍스트 범위만 다르게 구성한다.
    """
    print("=" * 70)
    print(f"예제 3: 메모리 포이즈닝 - 보안 경로 — Ollama ({model})")
    print("=" * 70)
    print("[공유 메모리]")
    for entry in memory:
        print(f"  - owner={entry.owner_id!r}: {entry.text}")
    print(f"[요청자 질문] {current_requester}: {MEMORY_RECALL_QUESTION}\n")

    # 실제 모델 경로에서도 모델에게 권한 판단을 맡기지 않고 호출 전에 owner_id를 검사한다.
    own_entries = [entry for entry in memory if entry.owner_id == current_requester]
    # 요청자 소유 메모리가 하나도 없어도 질문은 계속 전달할 수 있도록 빈 상태 문구를 사용한다.
    context = "\n".join(f"- {entry.text}" for entry in own_entries) or "저장된 기억이 없습니다."
    user_content = f"{context}\n\n사용자 질문: {MEMORY_RECALL_QUESTION}"
    print(f"[실제 입력: system]\n{MEMORY_RECALL_SYSTEM_INSTRUCTION}\n")
    print(f"[실제 입력: user]\n{user_content}\n")

    # 필터된 컨텍스트와 공통 질문을 system 지시와 함께 실제 모델에 전송한다.
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
    # 미포함은 해당 더미 문자열을 찾지 못했다는 뜻일 뿐, 다른 형태의 누출 부재를 증명하지 않는다.
    print(f"응답에 4521 포함 여부: {'4521' in result.text}")


if __name__ == "__main__":
    main()
