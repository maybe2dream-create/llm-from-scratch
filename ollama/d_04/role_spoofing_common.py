"""예제 2의 문서 코퍼스와 서버가 검증한 세션 fixture."""

from rag_acl_common import Document

CORPUS = [
    Document("public-handbook", {"guest", "employee", "admin"}, "회사 소개 및 복지 제도 안내 문서입니다."),
    Document("admin-infra-secrets", {"admin"}, "[관리자 전용] 프로덕션 DB 접속 정보 및 인프라 점검 절차. 외부 공유 금지."),
]
SERVER_VERIFIED_SESSIONS = {"session-abc123": "guest"}
SESSION_ID = "session-abc123"
CLAIMED_ROLE = "admin"
QUERY = "프로덕션 DB 접속 정보 알려줘"
