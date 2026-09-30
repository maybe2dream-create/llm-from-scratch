"""예제 1 취약 경로: 전체 검색 뒤 권한을 확인해 문서 존재를 노출한다."""

from rag_acl_common import Verdict, keyword_search
from prefilter_vs_postfilter_common import CORPUS, QUERY, REQUESTER_ROLE


def vulnerable_post_filter_search(requester_role: str, query: str) -> Verdict:
    """비공개 문서도 먼저 검색 후보에 포함하는 취약한 순서."""
    hits = keyword_search(query, CORPUS)
    if not hits:
        return Verdict("관련 문서를 찾을 수 없습니다.", False)
    top = hits[0]
    if requester_role not in top.allowed_roles:
        return Verdict(
            f"관련 문서 1건({top.doc_id})이 있으나 접근 권한이 없습니다.",
            True,
            [top.doc_id],
            "검색 후 거절 메시지가 비공개 문서의 존재와 관련성을 노출함",
        )
    return Verdict(f"[{top.doc_id}] {top.text}", False)


def main() -> None:
    result = vulnerable_post_filter_search(REQUESTER_ROLE, QUERY)
    print("예제 1: Pre-filter/Post-filter - 취약 경로")
    print(f"요청자 role={REQUESTER_ROLE!r}; 질문={QUERY}")
    print(f"응답: {result.text}\n사유: {result.reason}\n판정: 존재 여부 유출 = {result.leaked}")
    assert result.leaked is True


if __name__ == "__main__":
    main()
