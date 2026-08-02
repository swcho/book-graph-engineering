"""
예제 3 — 그래프 스멜. 스키마로는 못 잡고 «세어 봐야» 보이는 것들.

    python3 ex3_graph_smells.py

의존성 없음. 2장에서 「안티패턴 카탈로그 = 그래프 스멜」이라고 했던 그것이다.
"""

from collections import Counter, defaultdict

NODES = {f"n{i}": {"label": "Part"} for i in range(1, 41)}
NODES.update({
    "hub":  {"label": "Category", "name": "미분류"},
    "cat1": {"label": "Category", "name": "체결"},
    "cat2": {"label": "Category", "name": "전자"},
    "orph": {"label": "Part", "name": "고아 부품"},
    "dupA": {"label": "Supplier", "name": "가온테크"},
    "dupB": {"label": "Supplier", "name": "가온테크(주)"},
})

EDGES = []
for i in range(1, 31):
    EDGES.append((f"n{i}", "IN_CATEGORY", "hub"))       # 슈퍼 노드
for i in range(31, 36):
    EDGES.append((f"n{i}", "IN_CATEGORY", "cat1"))
for i in range(36, 41):
    EDGES.append((f"n{i}", "IN_CATEGORY", "cat2"))
EDGES += [
    ("n1", "SUPPLIED_BY", "dupA"),
    ("n2", "SUPPLIED_BY", "dupB"),                       # 중복 엔티티
    ("n3", "REPLACES", "n4"), ("n4", "REPLACES", "n5"),
    ("n5", "REPLACES", "n3"),                            # 사이클
    ("n6", "IN_CATEGORY", "cat1"), ("n6", "IN_CATEGORY", "cat2"),
]


def degrees(edges):
    d = Counter()
    for a, _, b in edges:
        d[a] += 1; d[b] += 1
    return d


def smell_supernode(nodes, edges, factor=5):
    d = degrees(edges)
    if not d:
        return []
    avg = sum(d.values()) / len(d)
    return [(v, n) for v, n in d.most_common() if n > avg * factor]


def smell_orphan(nodes, edges):
    touched = {x for a, _, b in edges for x in (a, b)}
    return [v for v in nodes if v not in touched]


def smell_cycle(edges, rel):
    adj = defaultdict(list)
    for a, r, b in edges:
        if r == rel:
            adj[a].append(b)
    seen, stack, out = set(), set(), []

    def go(u, path):
        if u in stack:
            out.append(path[path.index(u):] + [u]); return
        if u in seen:
            return
        seen.add(u); stack.add(u)
        for v in adj[u]:
            go(v, path + [u])
        stack.discard(u)

    for u in list(adj):
        go(u, [])
    return out


def smell_duplicate(nodes):
    def norm(s):
        return (s or "").replace("(주)", "").replace(" ", "").strip()
    groups = defaultdict(list)
    for v, a in nodes.items():
        if "name" in a:
            groups[(a["label"], norm(a["name"]))].append(v)
    return {k: v for k, v in groups.items() if len(v) > 1}


def smell_multi_parent(edges, rel):
    cnt = Counter(a for a, r, _ in edges if r == rel)
    return [(v, n) for v, n in cnt.items() if n > 1]


def main():
    print(f"노드 {len(NODES)}개, 엣지 {len(EDGES)}개\n")

    sn = smell_supernode(NODES, EDGES)
    print(f"[슈퍼 노드] 평균 차수의 5배 초과 — {len(sn)}건")
    for v, n in sn:
        print(f"    {v} ({NODES[v].get('name','')}) 차수 {n}")

    orp = smell_orphan(NODES, EDGES)
    print(f"\n[고아 노드] 엣지가 하나도 없음 — {len(orp)}건")
    for v in orp:
        print(f"    {v} ({NODES[v].get('name','')})")

    cy = smell_cycle(EDGES, "REPLACES")
    print(f"\n[사이클] «대체» 관계에 순환 — {len(cy)}건")
    for c in cy:
        print(f"    {' → '.join(c)}")

    dup = smell_duplicate(NODES)
    print(f"\n[중복 의심] 이름을 정규화하면 같음 — {len(dup)}건")
    for (label, name), vs in dup.items():
        print(f"    {label} «{name}» : {', '.join(vs)}")

    mp = smell_multi_parent(EDGES, "IN_CATEGORY")
    print(f"\n[다중 소속] 카테고리가 둘 이상 — {len(mp)}건")
    for v, n in mp:
        print(f"    {v} 카테고리 {n}개")

    print(
        "\n이 다섯 가지는 SHACL 로 잡기 어렵다. 이유가 각각 다르다.\n"
        "  슈퍼 노드 — «평균의 5배»는 데이터 전체를 봐야 나오는 상대값이다\n"
        "  고아 노드 — 형태 제약으로 잡히긴 하는데, 종류가 많아 일일이 못 쓴다\n"
        "  사이클    — SHACL 에 «순환 없음» 제약이 없다\n"
        "  중복 의심 — «비슷하다»는 판정이라 참/거짓이 아니다\n"
        "  다중 소속 — 위반이 아닐 수도 있다. 도메인이 정한다\n"
        "\n그래서 검증은 두 겹으로 간다.\n"
        "  1층 SHACL — 참/거짓이 분명한 형태 제약\n"
        "  2층 스멜  — 세어 보고 «이상하면 사람이 본다»\n"
        "2층은 자동으로 고치지 않는다. 목록만 뽑아 주는 게 일이다."
    )


if __name__ == "__main__":
    main()
