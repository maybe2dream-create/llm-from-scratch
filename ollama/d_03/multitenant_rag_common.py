"""멀티테넌트 RAG 예제의 공통 문서와 결정론적 검색 도구."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class Document:
    """문서 본문과 별도로 접근 제어에 사용할 테넌트 메타데이터를 보관한다."""

    doc_id: str
    tenant_id: str
    text: str


# 고정 코퍼스: 실제 벡터 DB가 아닌 ACL 동작 확인용 교육 데이터.
CORPUS: List[Document] = [
    Document("faq-1", "tenant_a", "저희 서비스 이용 시간은 평일 09:00~18:00 입니다."),
    Document(
        "contract-secret",
        "tenant_a",
        "[테넌트 A 기밀] 계약 특별 할인율 37%, 담당자 직통 번호 010-1234-5678. 외부 공유 금지.",
    ),
    Document("faq-2", "tenant_b", "환불은 결제 후 7일 이내 가능합니다."),
]


def keyword_search(query: str, docs: List[Document], top_k: int = 1) -> List[Document]:
    """임베딩 대신 문자 겹침 점수를 사용하는 재현용 간이 검색."""
    scored = []
    query_characters = set(query)
    for document in docs:
        overlap = len(query_characters & set(document.text))
        if overlap >= 4:
            scored.append((overlap, document))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [document for _score, document in scored[:top_k]]


def build_prompt(hits: List[Document], query: str) -> str:
    """검색 결과를 실제 모델 user 입력의 참고 문서/질문 형식으로 만든다."""
    context = "\n".join(f"- {document.text}" for document in hits) if hits else "(참고할 문서 없음)"
    return f"[참고 문서]\n{context}\n\n[질문] {query}"
