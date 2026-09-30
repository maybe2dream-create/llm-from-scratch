"""검색 전에 tenant_id ACL을 적용하는 보안 경로 실습.

이 파일은 예제 2의 보안 경로만 실행한다. 요청자의 tenant_id와 일치하는
문서만 검색 후보로 남긴 뒤, 그 결과만 실제 Ollama에 전달한다.
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
    """테넌트 필터가 적용된 검색 결과만 실제 Ollama에 보낸다."""
    print("=" * 70)
    print(f"예제 2: RAG 교차 테넌트 데이터 유출 - 보안 경로 — Ollama ({model})")
    print("=" * 70)
    print(f"[요청자] tenant_id={requester_tenant_id!r}")
    print(f"[질문] {query}\n")

    # 실제 경로에서도 검색 전에 동일한 tenant ACL을 적용한다.
    scoped_corpus = [document for document in CORPUS if document.tenant_id == requester_tenant_id]
    hits = keyword_search(query, scoped_corpus, top_k=1)

    # ACL 필터 결과 허용된 문서가 하나도 없으면, 모델에게 "모른다고 답하라"를 지시로
    # 맡기지 않는다 — 실측 결과(2026-09-29) 시스템 지시문에 그 규칙을 추가해도 1.5B
    # abliterated 모델은 세 번 중 세 번 다 그럴듯한 할인율/전화번호를 지어냈다.
    # 검색 결과가 비면 모델을 호출하지 않고 파이썬에서 바로 고정 응답을 낸다 —
    # 이것이 이 예제의 실질적인 출력 게이트다.
    if not hits:
        print(f"[출력 게이트] 허용된 참고 문서가 없어 모델을 호출하지 않고 고정 응답으로 대체함")
        print("응답:\n문서에서 확인되지 않습니다.\n")
        print("응답에 테넌트 A 기밀 값 포함 여부: False")
        return

    # 허용된 검색 결과만 user 입력의 참고 문서 영역에 담는다.
    user_content = build_prompt(hits, query)
    print(f"[실제 입력: system]\n{RAG_ANSWER_SYSTEM_INSTRUCTION}\n")
    print(f"[실제 입력: user]\n{user_content}\n")

    # system 지시와 필터된 user 입력을 Ollama로 보낸다.
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
    # 응답에 더미 기밀 값이 재현되는지 단순 문자열로 관찰한다. 모델 환각/다른 유출은 별도다.
    exposed = ("37%" in result.text) or ("010-1234" in result.text)
    print(f"응답에 테넌트 A 기밀 값 포함 여부: {exposed}")


if __name__ == "__main__":
    main()
