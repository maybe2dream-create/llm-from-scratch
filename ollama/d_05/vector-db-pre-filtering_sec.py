"""Vector DB Pre-filtering 미션 — 보안 경로: 권한 조건을 Vector DB 검색 요청의 where 로 넘긴다.

위협 모델은 취약 경로(vector-db-pre-filtering_vul.py)와 같다. 차이는 한 곳뿐이다 —
권한 조건(tenant_id, allowed_role, classification)을 검색이 끝난 뒤 코드에서 거르지 않고,
collection.query(..., where=...) 의 조건으로 DB에 넘긴다. DB는 조건에 맞는 문서
안에서만 가까운 순으로 k개를 고르므로, 권한 없는 문서는 애플리케이션에 오지 않는다.

재현 절차
  .venv/bin/python ollama/d_05/vector-db-pre-filtering_sec.py

관찰 포인트
  1. DB가 돌려준 문서 중 권한 없는 문서 = 0 (경계 침범 없음).
  2. 결과 건수 = min(TOP_K, 권한 있는 문서 수) — 고갈 없음.
  3. 메타데이터가 없는 문서는 $eq/$in 조건을 만족하지 못해 자동 제외된다 (fail-closed).
  4. where 결과가 "권한 문서 안에서의 전수 top-k"와 같은지 코드로 따로 검증한다.
     같지 않다면 DB가 내부적으로 top-k를 먼저 뽑고 거른 것(사후 필터)이다.
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
    """취약 경로와 같은 필드. leaked/boundary_crossed 는 고정값이 아니라 실제 결과로 계산한다."""

    text: str
    leaked: bool
    leaked_items: list[str] = field(default_factory=list)
    reason: str = ""
    db_returned: list[str] = field(default_factory=list)
    boundary_crossed: list[str] = field(default_factory=list)
    final_items: list[str] = field(default_factory=list)
    starved: bool = False
    distances: list[float] = field(default_factory=list)


def embed(text: str) -> list[float]:
    """취약 경로와 동일한 결정론적 문자 2-gram 임베딩 (두 파일이 같아야 공정한 비교가 된다)."""
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


def build_where(requester: dict, role_policy: dict) -> dict:
    """핵심 통제: 권한 조건을 Chroma where 절로 만든다.

    값은 요청 본문이 아니라 서버가 검증한 세션의 tenant_id/role 에서만 가져온다
    (d_04 예제 2 — 클라이언트가 주장한 role 로 where 를 만들면 이 방어 전체가 무력해진다).
    """
    policy = role_policy[requester["role"]]
    return {
        "$and": [
            {"tenant_id": {"$eq": requester["tenant_id"]}},
            {"allowed_role": {"$in": policy["allowed_role"]}},
            {"classification": {"$in": policy["classification"]}},
        ]
    }


def secure_search(collection, requester: dict, query: str, role_policy: dict, n_authorized: int) -> Verdict:
    """보안: 검색 요청 자체에 where 를 넘겨, DB가 권한 문서 안에서만 top-k를 고르게 한다."""
    result = collection.query(
        query_embeddings=[embed(query)],
        n_results=TOP_K,
        where=build_where(requester, role_policy),
        include=["documents", "metadatas", "distances"],
    )
    ids, texts, metas = result["ids"][0], result["documents"][0], result["metadatas"][0]
    distances = result["distances"][0]

    # where 가 제대로 걸렸는지 코드의 엄격한 기준으로 다시 확인한다 (필터가 아니라 검증).
    boundary_crossed = [doc_id for doc_id, meta in zip(ids, metas) if not is_authorized(meta, requester, role_policy)]

    # 결과가 없을 때도 "권한 없는 문서가 있다"는 힌트를 주지 않는다 (d_04 예제 1의 존재 노출 방지).
    text = "\n".join(f"[{doc_id}] {text}" for doc_id, text in zip(ids, texts)) or "관련 문서를 찾을 수 없습니다."
    starved = len(ids) - len(boundary_crossed) < min(TOP_K, n_authorized)

    return Verdict(
        text=text,
        leaked=bool(boundary_crossed),
        leaked_items=boundary_crossed,
        reason="where 조건으로 DB 단계에서 사전 필터링 (tenant_id $eq, allowed_role $in, classification $in)",
        db_returned=ids,
        boundary_crossed=boundary_crossed,
        final_items=ids,
        starved=starved,
        distances=distances,
    )


def brute_force_top_k(requester: dict, query: str, documents: list[dict], role_policy: dict) -> list[float]:
    """검증용: Chroma 없이 권한 문서 전체와의 거리(제곱 L2)를 직접 계산해 가까운 k개를 구한다."""
    query_vector = embed(query)
    distances = sorted(
        sum((a - b) ** 2 for a, b in zip(query_vector, embed(doc["text"])))
        for doc in documents
        if is_authorized(doc["metadata"], requester, role_policy)
    )
    return distances[:TOP_K]


def main() -> None:
    data = json.loads(DOCS_PATH.read_text(encoding="utf-8"))
    role_policy, documents, cases = data["role_policy"], data["documents"], data["cases"]
    collection = build_collection(documents)

    print("=" * 72)
    print("Vector DB Pre-filtering — 보안 경로 (where 조건을 검색 요청에 포함)")
    print(f"ChromaDB {chromadb.__version__} | 문서 {len(documents)}건 | TOP_K={TOP_K}")
    print("=" * 72)

    results = []
    for case in cases:
        requester, query = case["requester"], case["query"]
        # 요청자 신원은 서버가 검증한 세션 값이라고 가정한다 (d_04 예제 2).
        n_authorized = sum(is_authorized(d["metadata"], requester, role_policy) for d in documents)
        verdict = secure_search(collection, requester, query, role_policy, n_authorized)
        expected = brute_force_top_k(requester, query, documents, role_policy)
        # 동점(거리 2.0 = 겹치는 2-gram 0개)끼리는 순서가 달라도 되므로 문서 ID가 아니라 거리값을 비교한다.
        prefilter_ok = [round(d, 4) for d in verdict.distances] == [round(d, 4) for d in expected]
        results.append((case, verdict, prefilter_ok))

        print(f"\n[{case['case_id']}] {case['description']}")
        print(f"  요청자: {requester} | 질문: {query}")
        print(f"  where: {build_where(requester, role_policy)}")
        print(f"  DB가 앱에 넘긴 문서: {verdict.db_returned}")
        print(f"  거리(작을수록 가까움, 2.0 = 관련성 0): {[round(d, 3) for d in verdict.distances]}")
        print(f"  그중 권한 없는 문서(경계 침범): {verdict.boundary_crossed}")
        print("  최종 응답:")
        for line in verdict.text.splitlines():
            print(f"    {line}")
        print(f"  사유: {verdict.reason}")
        print(f"  판정: 유출={verdict.leaked} | top-k 고갈={verdict.starved} | 권한 문서 전수 top-{TOP_K}와 일치={prefilter_ok}")

    print("\n요약 (보안 경로)")
    print("| case | DB 반환 | 경계 침범 | 최종 응답 | 유출 | top-k 고갈 | 전수 top-k 일치 |")
    print("|---|---|---|---|---|---|---|")
    for case, v, ok in results:
        print(f"| {case['case_id']} | {len(v.db_returned)} | {len(v.boundary_crossed)} | {len(v.final_items)} | {v.leaked} | {v.starved} | {ok} |")

    # 모두 실제 Chroma 결과로 계산된 값이다. where 가 빠지거나 잘못 만들어지면 이 assert 가 실패한다.
    assert not any(v.boundary_crossed for _c, v, _ok in results), "권한 없는 문서가 DB 경계를 넘으면 안 된다"
    assert not any(v.leaked for _c, v, _ok in results), "최종 응답에 유출이 없어야 한다"
    assert not any(v.starved for _c, v, _ok in results), "권한 문서가 충분하면 top-k를 채워야 한다"
    assert all(ok for _c, _v, ok in results), "where 결과가 권한 문서 전수 top-k와 같아야 한다 (진짜 사전 필터)"
    print("\nPASS: 경계 침범·유출·고갈 없음, where 결과 = 권한 문서 안에서의 전수 top-k")


if __name__ == "__main__":
    main()
