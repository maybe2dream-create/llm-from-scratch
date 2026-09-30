"""d04 RAG ACL 예제의 공용 데이터 형식과 간이 검색 도구.

여기 있는 함수는 Ollama/LLM이나 벡터 DB를 호출하지 않는다. 각 예제의 취약·보안
정책 함수가 같은 자료형과 같은 검색 동작을 쓰도록 공통 부분만 제공한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeVar

T = TypeVar("T")


@dataclass
class Verdict:
    """한 경로의 처리 결과와 실습 판정을 표현한다.

    Attributes:
        text: 정책 함수가 구성한 응답 또는 검색 결과 텍스트.
        leaked: 이 예제의 기준으로 보호 대상이 노출되었는지 여부.
        leaked_items: 노출 판정의 근거가 된 문서 ID 등 식별자.
        reason: 해당 결과가 나온 정책 처리 이유.

    이 값은 고정 fixture에 대한 규칙 기반 판정이다. 실제 LLM 응답의 안전성이나
    운영 환경의 접근제어를 검증한 결과로 해석하면 안 된다.
    """

    text: str
    leaked: bool
    leaked_items: list[str] = field(default_factory=list)
    reason: str = ""


@dataclass
class Document:
    """RAG ACL 실습에서 검색 대상으로 사용하는 문서 fixture.

    Attributes:
        doc_id: 결과나 누출 근거에 표시할 문서 식별자.
        allowed_roles: 문서에 접근할 수 있는 role 집합.
            None은 권한이 모두에게 허용된다는 뜻이 아니라 ACL 메타데이터 자체가
            누락된 상태다. d04 예제 3에서 fail-open/fail-closed 차이를 재현한다.
        text: 검색 점수와 응답 구성에 사용하는 가짜 문서 본문.
    """

    doc_id: str
    allowed_roles: set[str] | None
    text: str


def keyword_search(query: str, docs: list[T], top_k: int = 1) -> list[T]:
    """고정 fixture에 대해 재현 가능한 간이 키워드 검색을 수행한다.

    질문을 공백 기준으로 나눈 뒤 구두점을 걷어내고, 길이 2 이상의 각 용어가
    문서 본문에 포함되는지를 점수로 합산한다. 관련 용어가 하나도 없는 문서는
    결과에서 제외하고 점수가 높은 순서로 최대 top_k개를 반환한다.

    이 함수는 각 예제의 접근제어 정책을 구현하지 않는다. 호출자가 먼저 허용된
    문서 목록을 넘기느냐(Pre-filter), 전체 목록을 넘기느냐가 실습의 비교 지점이다.
    실제 임베딩, 벡터 DB, 의미 유사도 검색을 대신하지 않는 교육용 fixture다.
    """
    terms = [term.strip(".,?!:;()[]{}\"'") for term in query.split()]
    terms = [term for term in terms if len(term) >= 2]
    scored = [(sum(term in doc.text for term in terms), doc) for doc in docs]
    scored = [item for item in scored if item[0] > 0]
    scored.sort(key=lambda item: item[0], reverse=True)
    return [doc for _score, doc in scored[:top_k]]
