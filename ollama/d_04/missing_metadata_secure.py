"""예제 3 보안 경로: ACL 누락 문서를 검색 전에 제외하는 fail-closed 정책."""

from rag_acl_common import Verdict, keyword_search
from missing_metadata_common import CORPUS, QUERY, REQUESTER_ROLE


def secure_retrieve(requester_role: str, query: str) -> Verdict:
    """명시적으로 허용된 role이 있는 문서만 검색 후보로 둔다."""
    scoped = [doc for doc in CORPUS if doc.allowed_roles is not None and requester_role in doc.allowed_roles]
    hits = keyword_search(query, scoped)
    text = "\n".join(f"[{doc.doc_id}] {doc.text}" for doc in hits) or "관련 문서를 찾을 수 없습니다."
    return Verdict(text, False, reason="ACL 메타데이터 누락 문서를 제외(fail-closed)")


def main() -> None:
    result = secure_retrieve(REQUESTER_ROLE, QUERY)
    print("예제 3: ACL 메타데이터 누락 - 보안 경로(fail-closed)")
    print(f"요청자 role={REQUESTER_ROLE!r}; 질문={QUERY}")
    print(f"응답: {result.text}\n사유: {result.reason}\n판정: 유출 = {result.leaked}")
    assert result.leaked is False


if __name__ == "__main__":
    main()
