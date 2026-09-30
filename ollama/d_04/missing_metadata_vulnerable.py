"""예제 3 취약 경로: ACL 누락 문서를 공개로 취급하는 fail-open 정책."""

from rag_acl_common import Verdict, keyword_search
from missing_metadata_common import CORPUS, QUERY, REQUESTER_ROLE


def vulnerable_retrieve(requester_role: str, query: str) -> Verdict:
    """allowed_roles가 None이면 누구나 접근 가능한 것으로 처리한다."""
    scoped = [doc for doc in CORPUS if doc.allowed_roles is None or requester_role in doc.allowed_roles]
    hits = keyword_search(query, scoped)
    leaked = [doc for doc in hits if doc.allowed_roles is None]
    text = "\n".join(f"[{doc.doc_id}] {doc.text}" for doc in hits) or "관련 문서를 찾을 수 없습니다."
    return Verdict(text, bool(leaked), [doc.doc_id for doc in leaked], "ACL 메타데이터 누락을 공개로 처리(fail-open)")


def main() -> None:
    result = vulnerable_retrieve(REQUESTER_ROLE, QUERY)
    print("예제 3: ACL 메타데이터 누락 - 취약 경로(fail-open)")
    print(f"요청자 role={REQUESTER_ROLE!r}; 질문={QUERY}")
    print(f"응답: {result.text}\n사유: {result.reason}\n판정: 유출 = {result.leaked}")
    assert result.leaked is True


if __name__ == "__main__":
    main()
