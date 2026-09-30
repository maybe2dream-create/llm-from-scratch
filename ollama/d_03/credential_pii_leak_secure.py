"""전송 전에 Context Redaction을 적용하는 보안 경로 실습.

이 파일은 예제 1의 보안 경로만 실행한다. 알려진 키·이메일 패턴을 user 입력에서
치환한 뒤 실제 Ollama 요청에 사용한다.
"""

from __future__ import annotations

import sys
from pathlib import Path

# 실행 위치가 달라도 공용 Ollama 클라이언트 경로를 찾을 수 있도록 ch04/d00-shared를 추가한다.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "d00-shared"))

from local_llm import DEFAULT_MODEL, ask_real, is_ollama_available  # noqa: E402
from credential_pii_common import find_sensitive, redact  # noqa: E402
from prompts import CODE_REVIEW_SYSTEM_INSTRUCTION, CREDENTIAL_EXTRACTION_REQUEST, USER_PASTE  # noqa: E402


def main() -> None:
    if not is_ollama_available():
        print("LLM 연결 안됨: Ollama 서버(http://localhost:11434)에 연결할 수 없습니다.")
        print("Ollama 설치/서버 실행 여부를 확인하세요.")
        return
    run_real()


def run_real(model: str = DEFAULT_MODEL) -> None:
    """마스킹한 더미 입력만 실제 Ollama에 보내 응답을 관찰한다.

    취약 파일과 동일한 system 지시와 추출 요청을 쓰되, user 본문만 마스킹한 상태로 비교한다.
    """
    print("=" * 70)
    print(f"예제 1: 자격증명/PII 유출 - 보안 경로 — Ollama ({model})")
    print("=" * 70)

    # 취약 실행과 같은 system 지시/추출 요청을 사용하되, 본문은 모델 호출 전에 마스킹한다.
    user_content = f"{redact(USER_PASTE)}\n\n{CREDENTIAL_EXTRACTION_REQUEST}"
    print(f"[실제 입력: system]\n{CODE_REVIEW_SYSTEM_INSTRUCTION}\n")
    print(f"[Context Redaction 적용 후 실제 입력: user]\n{user_content}\n")

    # 모델에 전달하는 값은 위에서 출력한 마스킹 완료 입력과 동일하다.
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
    # 빈 결과는 지정한 키/이메일 패턴이 없다는 뜻이다. 다른 민감정보 탐지까지 보장하지 않는다.
    print(f"응답에 남은 자격증명/이메일: {find_sensitive(result.text)}")


if __name__ == "__main__":
    main()
