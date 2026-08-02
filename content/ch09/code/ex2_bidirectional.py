"""
예제 2 — 양방향 탐색. 방문 노드 수가 제곱근으로 준다.

    python3 ex2_bidirectional.py

의존성 없음.
"""

import time
from collections import deque

from graph import make

N = 200_000


def bfs_path(adj, s, t, max_hop=8):
    if s == t:
        return [s], 1
    seen = {s: None}
    q = deque([(s, 0)])
    while q:
        u, d = q.popleft()
        if d >= max_hop:
            continue
        for v in adj.get(u, ()):
            if v in seen:
                continue
            seen[v] = u
            if v == t:
                path = [v]
                while seen[path[-1]] is not None:
                    path.append(seen[path[-1]])
                return list(reversed(path)), len(seen)
            q.append((v, d + 1))
    return None, len(seen)


def bidi_path(adj, s, t, max_hop=8):
    if s == t:
        return [s], 1
    fwd, bwd = {s: None}, {t: None}
    fq, bq = deque([s]), deque([t])
    for _ in range(max_hop):
        for q, seen, other in ((fq, fwd, bwd), (bq, bwd, fwd)):
            for _ in range(len(q)):
                u = q.popleft()
                for v in adj.get(u, ()):
                    if v in seen:
                        continue
                    seen[v] = u
                    if v in other:
                        return _join(v, fwd, bwd), len(fwd) + len(bwd)
                    q.append(v)
    return None, len(fwd) + len(bwd)


def _join(meet, fwd, bwd):
    left = [meet]
    while fwd[left[-1]] is not None:
        left.append(fwd[left[-1]])
    right = []
    cur = bwd[meet]
    while cur is not None:
        right.append(cur)
        cur = bwd[cur]
    return list(reversed(left)) + right


def main():
    adj = make(n=N)
    pairs = [(0, 199_999), (7, 150_000), (42, 99_999)]
    print(f"{'쌍':<20} {'단방향 방문':>14} {'양방향 방문':>14} {'절감':>8} {'경로 길이':>10}")
    print("-" * 70)
    for s, t in pairs:
        p1, v1 = bfs_path(adj, s, t)
        p2, v2 = bidi_path(adj, s, t)
        length = len(p1) - 1 if p1 else -1
        print(f"{f'{s} → {t}':<20} {v1:>14,} {v2:>14,} "
              f"{v1/max(v2,1):>7.1f}x {length:>10}")

    print(
        "\n왜 이렇게 차이가 나나. 단방향은 반지름 d 짜리 공을 그리고,\n"
        "양방향은 반지름 d/2 짜리 공 두 개를 그린다.\n"
        "공의 크기가 지수라서, 절반으로 줄이면 제곱근이 된다.\n"
        "\n조건이 하나 있다. 도착지를 알아야 한다.\n"
        "«이 사람과 3다리 안에 있는 사람 전부»는 양방향으로 못 푼다."
    )


if __name__ == "__main__":
    main()
