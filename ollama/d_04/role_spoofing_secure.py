"""예제 2 보안 경로: 요청의 role 주장을 무시하고 서버 검증 role을 쓴다."""

from rag_acl_common import Verdict, keyword_search
from role_spoofing_common import CLAIMED_ROLE, CORPUS, QUERY, SERVER_VERIFIED_SESSIONS, SESSION_ID


def secure_authorize(session_id: str, claimed_role: str, query: str) -> Verdict:
    """서버 세션에서 role을 조회한 뒤에만 검색 범위를 정한다."""
    actual_role = SERVER_VERIFIED_SESSIONS.get(session_id)
    if actual_role is None:
        return Verdict("인증되지 않은 세션입니다.", False, reason="세션 검증 실패")
    scoped = [doc for doc in CORPUS if actual_role in doc.allowed_roles]
    hits = keyword_search(query, scoped)
    text = "\n".join(f"[{doc.doc_id}] {doc.text}" for doc in hits) or "관련 문서를 찾을 수 없습니다."
    return Verdict(text, False, reason=f"claimed_role={claimed_role!r} 무시; 서버 검증 role={actual_role!r} 적용")


def main() -> None:
    result = secure_authorize(SESSION_ID, CLAIMED_ROLE, QUERY)
    print("예제 2: 역할 위조 - 보안 경로")
    print(f"세션 검증 role={SERVER_VERIFIED_SESSIONS[SESSION_ID]!r}; 요청 주장 role={CLAIMED_ROLE!r}")
    print(f"응답: {result.text}\n사유: {result.reason}\n판정: 유출 = {result.leaked}")
    assert result.leaked is False


if __name__ == "__main__":
    main()
