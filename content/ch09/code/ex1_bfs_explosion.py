"""
예제 1 — 홉이 하나 늘 때마다 방문 노드가 몇 배가 되나.

    python3 ex1_bfs_explosion.py

의존성 없음.
"""

from collections import deque

from graph import make

N = 200_000


def bfs_levels(adj, start, max_hop):
    seen = {start}
    frontier = [start]
    out = []
    for hop in range(1, max_hop + 1):
        nxt = []
        for u in frontier:
            for v in adj.get(u, ()):
                if v not in seen:
                    seen.add(v)
                    nxt.append(v)
        out.append((hop, len(nxt), len(seen)))
        frontier = nxt
        if not frontier:
            break
    return out


def main():
    adj = make(n=N)
    print(f"노드 {len(adj):,}  평균 차수 "
          f"{sum(len(v) for v in adj.values())/len(adj):.1f}\n")
    print(f"{'홉':>3} {'이번 홉 새 노드':>16} {'누적':>12} {'배수':>8} {'전체 대비':>10}")
    prev = 1
    for hop, new, total in bfs_levels(adj, 0, 8):
        print(f"{hop:>3} {new:>16,} {total:>12,} {new/max(prev,1):>7.1f}x "
              f"{total/len(adj)*100:>9.1f}%")
        prev = new

    print(
        "\n5홉이면 이미 그래프의 대부분에 닿는다.\n"
        "«6다리 건너면 다 안다»는 말이 이 표다. 재밌는 이야기인데,\n"
        "질의로 쓰면 «전체를 훑어라»와 같은 뜻이 된다.\n"
        "\n그래서 홉 수에 상한을 두지 않은 순회는 사실상 전체 스캔이다.\n"
        "서버가 죽는 건 알고리즘이 나빠서가 아니라 상한이 없어서다."
    )


if __name__ == "__main__":
    main()
