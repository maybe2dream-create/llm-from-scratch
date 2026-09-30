"""테넌트 ACL 없이 전체 코퍼스를 검색하는 취약 경로 실습.

이 파일은 예제 2의 취약 경로만 실행한다. tenant_id로 범위를 제한하지 않고
검색한 결과를 그대로 실제 Ollama 입력에 넣는다. 실습 데이터는 가짜이며
외부 RAG 저장소나 벡터 DB를 사용하지 않는다.
"""

from __future__ import annotations

import sys
from pathlib import Path

# 실행 위치가 어느 디렉터리든 ch04/d00-shared의 Ollama 클라이언트를 import할 수 있게 한다.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "d00-shared"))

from local_llm import DEFAULT_MODEL, ask_real, is_ollama_available  # noqa: E402
from multitenant_rag_common import CORPUS, build_prompt, keyword_search  # noqa: E402
from prompts import MULTITENANT_QUERY, RAG_ANSWER_SYSTEM_INSTRUCTION  # noqa: E402


def main() -> None:
    if not is_ollama_available():
        print("LLM 연결 안됨: Ollama 서버(http://localhost:11434)에 연결할 수 없습니다.")
        print("Ollama 설치/서버 실행 여부를 확인하세요.")
        return
    run_real("tenant_b", MULTITENANT_QUERY)


def run_real(requester_tenant_id: str, query: str, model: str = DEFAULT_MODEL) -> None:
    """ACL 없는 검색 결과를 실제 Ollama에 보내 문서 내용 노출을 관찰한다.

    ACL 없이 검색된 문서가 이미 user 입력에 들어간 상태에서, 응답에 더미
    기밀 문자열이 재현되는지 관찰한다.
    """
    print("=" * 70)
    print(f"예제 2: RAG 교차 테넌트 데이터 유출 - 취약 경로 — Ollama ({model})")
    print("=" * 70)
    print(f"[요청자] tenant_id={requester_tenant_id!r}")
    print(f"[질문] {query}\n")

    # 취약 경로: 실제 입력도 tenant 필터 없이 전체 코퍼스에서 검색한다.
    hits = keyword_search(query, CORPUS, top_k=1)
    # 검색 문서와 질문을 실제 모델의 user 메시지로 직렬화한다.
    user_content = build_prompt(hits, query)
    print(f"[실제 입력: system]\n{RAG_ANSWER_SYSTEM_INSTRUCTION}\n")
    print(f"[실제 입력: user]\n{user_content}\n")

    # system 지시와 위에서 출력한 user 입력을 지정 모델에 실제 전송한다.
    result = ask_real(
        RAG_ANSWER_SYSTEM_INSTRUCTION,
        user_content,
        model=model,
        temperature=0.2,
    )
    if not result.ok:
        print(f"호출 실패: {result.error}")
        return

    print(f"응답:\n{result.text}\n")
    # 문자열 일치만 관찰한다. 미검출이어도 다른 표현의 유출이 없음을 보장하지 않는다.
    exposed = ("37%" in result.text) or ("010-1234" in result.text)
    print(f"응답에 테넌트 A 기밀 값 포함 여부: {exposed}")


if __name__ == "__main__":
    main()
