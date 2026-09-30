"""Vector DB Pre-filtering 미션 — 취약 경로: 조건 없이 검색한 뒤 코드에서 사후 필터링한다.

위협 모델
  - 자산: 다른 테넌트/다른 부서의 기밀 문서(계약 할인율, 연봉 조정안, 인사평가 명단).
  - 신뢰 경계: Vector DB ↔ 애플리케이션. 권한 판단을 코드에서 검색 "후"에 하면,
    권한 없는 문서가 이미 DB 경계를 넘어 애플리케이션 메모리에 들어온 뒤다.
  - 공격자 역량: 평범한 질문을 하는 인증된 사용자. 악의가 없어도 유출이 일어난다.

재현 절차
  .venv/bin/python ollama/d_05/vector-db-pre-filtering_vul.py

관찰 포인트 (d_04의 세 예제가 Vector DB 위에서 한꺼번에 나타난다)
  1. 경계 침범: DB가 권한 없는 문서까지 돌려준다 — 코드 필터가 정확해도 이미 늦었다.
  2. 존재 노출: 걸러낸 문서의 ID/건수를 응답에 알린다 (d_04 예제 1).
  3. fail-open: ACL 메타데이터가 없는 문서를 허용으로 처리한다 (d_04 예제 3).
  4. top-k 고갈: 상위 k개가 모두 걸러지면, 권한 있는 관련 문서가 있어도 0건이 된다.
"""

from __future__ import annotations

import json
import math
import zlib
from dataclasses import dataclass, field
from pathlib import Path

import chromadb
from chromadb.config import Settings

DOCS_PATH = Path(__file__).with_name("vector-db-pre-filter-docs.json")
TOP_K = 3
EMBED_DIM = 512


@dataclass
class Verdict:
    """d_04 rag_acl_common.Verdict 와 같은 네 필드에, Vector DB 관찰용 필드를 더했다.

    leaked는 최종 응답이 보호 대상(본문 또는 존재)을 노출했는지다.
    boundary_crossed는 응답과 별개로, DB가 권한 없는 문서를 애플리케이션에 넘겼는지다.
    """

    text: str
    leaked: bool
    leaked_items: list[str] = field(default_factory=list)
    reason: str = ""
    db_returned: list[str] = field(default_factory=list)
    boundary_crossed: list[str] = field(default_factory=list)
    final_items: list[str] = field(default_factory=list)
    starved: bool = False


def embed(text: str) -> list[float]:
    """공백을 뺀 문자 2-gram을 해시 버킷에 세어 만든 결정론적 임베딩 (L2 정규화).

    Chroma 기본 임베딩 모델은 영어 전용이라 한국어 문서 순위가 거의 무작위가 된다.
    이 미션의 비교 대상은 임베딩 품질이 아니라 필터가 걸리는 위치이므로, 결과를
    매번 똑같이 재현할 수 있는 단순 임베딩을 직접 계산해 Chroma에 넘긴다.
    취약/보안 두 파일의 이 함수는 반드시 같아야 공정한 비교가 된다.
    """
    chars = "".join(text.split())
    vector = [0.0] * EMBED_DIM
    for i in range(len(chars) - 1):
        # 내장 hash()는 실행마다 시드가 바뀌어 순위가 매번 달라진다. crc32는 고정값이다.
        vector[zlib.crc32(chars[i : i + 2].encode("utf-8")) % EMBED_DIM] += 1.0
    norm = math.sqrt(sum(x * x for x in vector)) or 1.0
    return [x / norm for x in vector]


def build_collection(documents: list[dict]) -> chromadb.Collection:
    """JSON 문서를 메타데이터(tenant_id/allowed_role/classification)와 함께 Chroma에 적재한다."""
    client = chromadb.EphemeralClient(settings=Settings(anonymized_telemetry=False))
    collection = client.create_collection("vector_db_prefilter_docs", embedding_function=None)
    collection.add(
        ids=[doc["doc_id"] for doc in documents],
        documents=[doc["text"] for doc in documents],
        metadatas=[doc["metadata"] for doc in documents],
        embeddings=[embed(doc["text"]) for doc in documents],
    )
    return collection


def is_authorized(metadata: dict, requester: dict, role_policy: dict) -> bool:
    """판정 기준(엄격): 세 메타데이터가 모두 있고 요청자 정책에 맞아야 허용이다."""
    policy = role_policy[requester["role"]]
    return (
        metadata.get("tenant_id") == requester["tenant_id"]
        and metadata.get("allowed_role") in policy["allowed_role"]
        and metadata.get("classification") in policy["classification"]
    )


def vulnerable_post_filter(metadata: dict, requester: dict, role_policy: dict) -> bool:
    """취약한 사후 필터: 값이 없는 필드는 검사를 통과시킨다 (d_04 예제 3과 같은 fail-open)."""
    policy = role_policy[requester["role"]]
    role = metadata.get("allowed_role")
    classification = metadata.get("classification")
    return (
        metadata.get("tenant_id") == requester["tenant_id"]
        and (role is None or role in policy["allowed_role"])
        and (classification is None or classification in policy["classification"])
    )


def vulnerable_search(collection, requester: dict, query: str, role_policy: dict, n_authorized: int) -> Verdict:
    """취약 지점: DB 검색 요청에 권한 조건이 없다. 권한 확인은 결과를 받은 뒤 코드에서 한다."""
    raw = collection.query(
        query_embeddings=[embed(query)],
        n_results=TOP_K,
        include=["documents", "metadatas", "distances"],
    )
    ids, texts, metas = raw["ids"][0], raw["documents"][0], raw["metadatas"][0]

    # 이 시점에 권한 없는 문서의 본문이 이미 애플리케이션 메모리(raw)에 들어와 있다.
    boundary_crossed = [doc_id for doc_id, meta in zip(ids, metas) if not is_authorized(meta, requester, role_policy)]

    kept = [(doc_id, text, meta) for doc_id, text, meta in zip(ids, texts, metas)
            if vulnerable_post_filter(meta, requester, role_policy)]
    dropped = [doc_id for doc_id in ids if doc_id not in {k[0] for k in kept}]

    lines = [f"[{doc_id}] {text}" for doc_id, text, _meta in kept]
    if dropped:
        # 사용자 친절 메시지처럼 보이지만, 비공개 문서의 존재와 ID를 알려준다 (d_04 예제 1).
        lines.append(f"관련 문서 {len(ids)}건 중 {len(dropped)}건({', '.join(dropped)})은 접근 권한이 없어 제외했습니다.")
    text = "\n".join(lines) or "관련 문서를 찾을 수 없습니다."

    content_leaks = [doc_id for doc_id, _text, meta in kept if not is_authorized(meta, requester, role_policy)]
    leaked_items = content_leaks + dropped
    reasons = []
    if content_leaks:
        reasons.append(f"메타데이터 누락 문서를 허용 처리(fail-open): {content_leaks}")
    if dropped:
        reasons.append(f"제외한 문서의 존재·ID를 응답에 노출: {dropped}")
    starved = len(kept) - len(content_leaks) < min(TOP_K, n_authorized)
    if starved:
        reasons.append(f"top-{TOP_K} 고갈: 권한 있는 문서가 {n_authorized}건 있는데 결과에는 {len(kept) - len(content_leaks)}건")

    return Verdict(
        text=text,
        leaked=bool(leaked_items),
        leaked_items=leaked_items,
        reason="; ".join(reasons) or "사후 필터 결과 이상 없음",
        db_returned=ids,
        boundary_crossed=boundary_crossed,
        final_items=[doc_id for doc_id, _text, _meta in kept],
        starved=starved,
    )


def main() -> None:
    data = json.loads(DOCS_PATH.read_text(encoding="utf-8"))
    role_policy, documents, cases = data["role_policy"], data["documents"], data["cases"]
    collection = build_collection(documents)

    print("=" * 72)
    print("Vector DB Pre-filtering — 취약 경로 (조건 없이 검색 → 코드에서 사후 필터)")
    print(f"ChromaDB {chromadb.__version__} | 문서 {len(documents)}건 | TOP_K={TOP_K}")
    print("=" * 72)

    results = []
    for case in cases:
        requester, query = case["requester"], case["query"]
        # 요청자 신원은 서버가 검증한 세션 값이라고 가정한다 (d_04 예제 2).
        n_authorized = sum(is_authorized(d["metadata"], requester, role_policy) for d in documents)
        verdict = vulnerable_search(collection, requester, query, role_policy, n_authorized)
        results.append((case, verdict))

        print(f"\n[{case['case_id']}] {case['description']}")
        print(f"  요청자: {requester} | 질문: {query}")
        print(f"  DB가 앱에 넘긴 문서: {verdict.db_returned}")
        print(f"  그중 권한 없는 문서(경계 침범): {verdict.boundary_crossed}")
        print("  최종 응답:")
        for line in verdict.text.splitlines():
            print(f"    {line}")
        print(f"  사유: {verdict.reason}")
        print(f"  판정: 유출={verdict.leaked} {verdict.leaked_items} | top-k 고갈={verdict.starved}")

    print("\n요약 (취약 경로)")
    print("| case | DB 반환 | 경계 침범 | 최종 응답 | 유출 | top-k 고갈 |")
    print("|---|---|---|---|---|---|")
    for case, v in results:
        print(f"| {case['case_id']} | {len(v.db_returned)} | {len(v.boundary_crossed)} | {len(v.final_items)} | {v.leaked} | {v.starved} |")

    # 이 assert는 고정 fixture에서 취약점이 실제 Chroma 검색 결과로 재현됐는지 확인한다.
    assert any(v.boundary_crossed for _c, v in results), "권한 없는 문서가 DB 경계를 넘는 경우가 재현돼야 한다"
    assert any(v.leaked for _c, v in results), "존재 노출 또는 fail-open 유출이 재현돼야 한다"
    assert any(v.starved for _c, v in results), "top-k 고갈이 재현돼야 한다"
    print("\nPASS: 사후 필터 경로에서 경계 침범·유출·top-k 고갈이 모두 재현됨")


if __name__ == "__main__":
    main()
