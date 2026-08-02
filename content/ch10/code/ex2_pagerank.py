"""
예제 2 — 페이지랭크. 유향 그래프에서 «중요한 것과 이어진 것»을 센다.
그리고 싱크 노드가 점수를 삼키는 함정을 본다.

    python3 ex2_pagerank.py

의존성 없음.
"""

from collections import defaultdict

from org import REPORTS

D = 0.85          # 감쇠 계수. 관례적으로 0.85
TOL = 1e-10


def pagerank(edges, damping=D, fix_sinks=True, rounds=200):
    nodes = sorted({x for a, b in edges for x in (a, b)})
    out = defaultdict(list)
    for a, b in edges:
        out[a].append(b)
    n = len(nodes)
    rank = {v: 1 / n for v in nodes}
    sinks = [v for v in nodes if not out[v]]

    for it in range(rounds):
        nxt = {v: (1 - damping) / n for v in nodes}
        leaked = sum(rank[v] for v in sinks) if fix_sinks else 0.0
        for v in nodes:
            if out[v]:
                share = damping * rank[v] / len(out[v])
                for w in out[v]:
                    nxt[w] += share
        if fix_sinks:
            for v in nodes:
                nxt[v] += damping * leaked / n
        diff = sum(abs(nxt[v] - rank[v]) for v in nodes)
        rank = nxt
        if diff < TOL:
            break
    return rank, it + 1, sum(rank.values())


def main():
    for fix in (True, False):
        rank, iters, total = pagerank(REPORTS, fix_sinks=fix)
        top = sorted(rank, key=lambda v: -rank[v])[:5]
        label = "싱크 보정 함" if fix else "싱크 보정 안 함"
        print(f"[{label}]  반복 {iters}회  점수 합계 {total:.6f}")
        for v in top:
            print(f"    {v:<8} {rank[v]:.4f}")
        print()

    print(
        "합계를 보라. 보정을 안 하면 1.0 이 아니다.\n"
        "나가는 엣지가 없는 노드(여기서는 «대표»)가 점수를 받기만 하고\n"
        "아무에게도 안 흘려보내서, 매 회 조금씩 새어 나간다.\n"
        "\n순위 자체는 크게 안 바뀔 때가 많다. 그래서 발견이 늦는다.\n"
        "그런데 점수 절댓값으로 임계를 정해 두었다면(예: 0.01 이상만 추천)\n"
        "그 임계가 조용히 의미를 잃는다.\n"
        "\n라이브러리를 쓸 때도 이 보정을 하는지 확인하는 게 좋다.\n"
        "대부분 한다. 안 하는 것도 있다."
    )


if __name__ == "__main__":
    main()
