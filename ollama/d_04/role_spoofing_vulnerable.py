"""예제 2 취약 경로: 클라이언트가 주장한 role을 권한 필터에 사용한다."""

from rag_acl_common import Verdict, keyword_search
from role_spoofing_common import CLAIMED_ROLE, CORPUS, QUERY, SERVER_VERIFIED_SESSIONS, SESSION_ID


def vulnerable_authorize(session_id: str, claimed_role: str, query: str) -> Verdict:
    """요청 필드만 신뢰하므로 guest 세션이 admin role을 주장할 수 있다."""
    scoped = [doc for doc in CORPUS if claimed_role in doc.allowed_roles]
    hits = keyword_search(query, scoped)
    actual_role = SERVER_VERIFIED_SESSIONS.get(session_id, "guest")
    leaked = [doc for doc in hits if actual_role not in doc.allowed_roles]
    text = "\n".join(f"[{doc.doc_id}] {doc.text}" for doc in hits) or "관련 문서를 찾을 수 없습니다."
    return Verdict(text, bool(leaked), [doc.doc_id for doc in leaked], f"claimed_role={claimed_role!r} 신뢰; 검증 role={actual_role!r}")


def main() -> None:
    result = vulnerable_authorize(SESSION_ID, CLAIMED_ROLE, QUERY)
    print("예제 2: 역할 위조 - 취약 경로")
    print(f"세션 검증 role={SERVER_VERIFIED_SESSIONS[SESSION_ID]!r}; 요청 주장 role={CLAIMED_ROLE!r}")
    print(f"응답: {result.text}\n사유: {result.reason}\n유출 문서: {result.leaked_items}\n판정: 유출 = {result.leaked}")
    assert result.leaked is True


if __name__ == "__main__":
    main()
