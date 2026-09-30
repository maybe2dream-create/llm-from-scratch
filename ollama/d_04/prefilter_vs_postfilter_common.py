"""예제 1의 고정 문서 코퍼스."""

from rag_acl_common import Document

CORPUS = [
    Document("public-faq", {"guest", "employee", "hr", "admin"}, "휴가 신청은 사내 포털 근태관리 메뉴에서 할 수 있습니다."),
    Document("hr-salary-review", {"hr", "admin"}, "[HR 기밀] 2025년 3분기 연봉 조정안: 평균 인상률 4.2%, 대상자 명단 별첨."),
]
REQUESTER_ROLE = "employee"
QUERY = "연봉 조정 관련 자료 있어?"
