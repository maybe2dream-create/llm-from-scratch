"""예제 1 보안 경로: 권한 범위를 먼저 제한한 뒤 검색한다."""

from rag_acl_common import Verdict, keyword_search
from prefilter_vs_postfilter_common import CORPUS, QUERY, REQUESTER_ROLE


def secure_pre_filter_search(requester_role: str, query: str) -> Verdict:
    """요청자에게 허용된 문서만 검색하므로 비공개 문서는 후보에 들지 않는다."""
    scoped = [doc for doc in CORPUS if requester_role in doc.allowed_roles]
    hits = keyword_search(query, scoped)
    if not hits:
        return Verdict("관련 문서를 찾을 수 없습니다.", False, reason="권한 범위 안에 검색 결과가 없음")
    doc = hits[0]
    return Verdict(f"[{doc.doc_id}] {doc.text}", False)


def main() -> None:
    result = secure_pre_filter_search(REQUESTER_ROLE, QUERY)
    print("예제 1: Pre-filter/Post-filter - 보안 경로")
    print(f"요청자 role={REQUESTER_ROLE!r}; 질문={QUERY}")
    print(f"응답: {result.text}\n사유: {result.reason}\n판정: 존재 여부 유출 = {result.leaked}")
    assert result.leaked is False


if __name__ == "__main__":
    main()
