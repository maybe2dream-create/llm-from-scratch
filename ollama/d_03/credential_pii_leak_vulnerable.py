"""마스킹 없이 사용자 원문을 로그/모델 입력으로 보내는 취약 경로 실습.

이 파일은 예제 1의 취약 경로만 실행한다. 더미 원문(USER_PASTE)을 마스킹 없이
그대로 실제 Ollama 입력으로 보내, 응답에 API 키/이메일이 재현되는지 관찰한다.
"""

from __future__ import annotations

import sys
from pathlib import Path

# 실행 위치가 달라도 공용 Ollama 클라이언트 경로를 찾을 수 있도록 ch04/d00-shared를 추가한다.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "d00-shared"))

from local_llm import DEFAULT_MODEL, ask_real, is_ollama_available  # noqa: E402
from credential_pii_common import find_sensitive  # noqa: E402
from prompts import CODE_REVIEW_SYSTEM_INSTRUCTION, CREDENTIAL_EXTRACTION_REQUEST, USER_PASTE  # noqa: E402


def main() -> None:
    if not is_ollama_available():
        print("LLM 연결 안됨: Ollama 서버(http://localhost:11434)에 연결할 수 없습니다.")
        print("Ollama 설치/서버 실행 여부를 확인하세요.")
        return
    run_real()


def run_real(model: str = DEFAULT_MODEL) -> None:
    """더미 원문을 실제 Ollama에 보내 응답에서 값이 되풀이되는지 관찰한다.

    모델 응답에 값이 나타나는지는 확률적 관찰이다.
    """
    print("=" * 70)
    print(f"예제 1: 자격증명/PII 유출 - 취약 경로 — Ollama ({model})")
    print("=" * 70)

    # 같은 코드 리뷰 지시와 추출 요청을 사용하고, user 입력에는 마스킹 전 원문을 넣는다.
    user_content = f"{USER_PASTE}\n\n{CREDENTIAL_EXTRACTION_REQUEST}"
    print(f"[실제 입력: system]\n{CODE_REVIEW_SYSTEM_INSTRUCTION}\n")
    print(f"[실제 입력: user]\n{user_content}\n")

    # 이 호출에서만 네트워크 요청이 발생하며, USER_PASTE는 모두 가짜 테스트 데이터다.
    result = ask_real(
        CODE_REVIEW_SYSTEM_INSTRUCTION,
        user_content,
        model=model,
        temperature=0.2,
    )
    if not result.ok:
        print(f"호출 실패: {result.error}")
        return

    print(f"응답:\n{result.text}\n")
    # 응답에서 더미 값 형식이 재현되는지 관찰한다. 단순 패턴 검사라 전체 유출 판정은 아니다.
    print(f"응답에 남은 자격증명/이메일: {find_sensitive(result.text)}")


if __name__ == "__main__":
    main()
