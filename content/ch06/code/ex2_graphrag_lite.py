"""
예제 2 — 같은 질문을 GraphRAG 방식으로. 색인 시점에 접어 둔다.

    python3 ex2_graphrag_lite.py

의존성 없음. 커뮤니티 탐지는 라벨 전파(label propagation)를 직접 구현했다.
진짜 GraphRAG 는 요약문을 모델이 쓰지만, 여기서는 규칙으로 만든다.
보여 주려는 건 요약문의 품질이 아니라 «언제 접느냐»이다.
"""

from collections import Counter, defaultdict

from corpus import DOCS, GLOBAL_QUESTION, GROUND_TRUTH, TRIPLES


def build_graph(triples):
    adj = defaultdict(set)
    for s, p, o in triples:
        adj[s].add(o)
        adj[o].add(s)
    return adj


def label_propagation(adj, rounds=12):
    """이웃에서 제일 흔한 라벨을 가져온다. 몇 바퀴 돌면 뭉친다."""
    label = {n: i for i, n in enumerate(sorted(adj))}
    for _ in range(rounds):
        changed = False
        for n in sorted(adj):
            if not adj[n]:
                continue
            best = Counter(label[m] for m in adj[n]).most_common(1)[0][0]
            if label[n] != best:
                label[n] = best
                changed = True
        if not changed:
            break
    groups = defaultdict(list)
    for n, l in label.items():
        groups[l].append(n)
    return [sorted(v) for v in groups.values() if len(v) > 1]


def summarize(community, triples):
    """커뮤니티 요약. 규칙 기반이라 매번 같은 결과가 나온다."""
    members = set(community)
    causes = Counter(o for s, p, o in triples
                     if p == "원인" and s in members and o in members)
    docs = sorted(m for m in members if m.startswith("d"))
    top = ", ".join(f"{c}({n}건)" for c, n in causes.most_common(3))
    return {"문서": docs, "요약": f"문서 {len(docs)}건. 자주 나온 원인: {top or '없음'}",
            "원인분포": causes}


def main():
    adj = build_graph(TRIPLES)
    communities = label_propagation(adj)

    print("=== 색인 시점 (한 번만) ===")
    print(f"노드 {len(adj)}개 → 커뮤니티 {len(communities)}개\n")
    summaries = []
    for i, c in enumerate(communities, 1):
        s = summarize(c, TRIPLES)
        summaries.append(s)
        print(f"  커뮤니티 {i}: {s['요약']}")

    print(f"\n=== 질의 시점 ===\n질문: {GLOBAL_QUESTION}\n")
    total = Counter()
    for s in summaries:
        total.update(s["원인분포"])
    print("커뮤니티 요약을 합친 결과 — 원인 순위")
    for cause, n in total.most_common(5):
        print(f"  {cause}: {n}건")

    found = {c for c, n in total.most_common(2)}
    print(f"\n답: {sorted(found)}")
    print(f"정답: {sorted(GROUND_TRUTH)}")
    print(f"맞았나: {'예' if found == GROUND_TRUTH else '아니오'}")

    print(
        "\n달라진 건 «언제 세느냐»이다.\n"
        "조각 검색은 질의 시점에 k개만 본다. 전체를 셀 기회가 없다.\n"
        "GraphRAG 는 색인 시점에 전부 훑어 접어 두고, 질의 시점에는 접어 둔 것만 편다.\n"
        "\n대가도 분명하다. 색인이 비싸고, 문서가 바뀌면 다시 접어야 한다.\n"
        "그래서 자주 바뀌는 데이터에는 안 맞는다. 17장에서 이 손익을 따진다."
    )


if __name__ == "__main__":
    main()
