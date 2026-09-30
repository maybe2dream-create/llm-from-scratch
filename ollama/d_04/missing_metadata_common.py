"""예제 3의 ACL 메타데이터 누락 fixture."""

from rag_acl_common import Document

CORPUS = [
    Document("it-onboarding-guide", {"guest", "employee", "hr", "admin"}, "신규 입사자 IT 계정 발급 안내입니다."),
    Document("perf-review-2025-legacy", None, "[인사평가] 2025년 하반기 개인별 평가 등급 및 승진 대상자 명단 (레거시 인덱스, 태깅 누락)."),
]
REQUESTER_ROLE = "employee"
QUERY = "인사평가 승진 대상자 명단 보여줘"
