"""
예제 4 — 노드 번호를 다시 매기면 이웃이 가까이 모인다.

    python3 ex4_relabel.py

의존성 없음. 지역성(locality)을 «이웃 번호 차이의 평균»으로 잰다.
이 값이 작을수록 한 번 읽어 온 캐시 줄을 여러 번 쓴다.
"""

from array import array
from collections import defaultdict, deque

from graphgen import make

N = 30_000


def locality(edges):
    """엣지 양 끝 번호 차이의 평균. 작을수록 좋다."""
    return sum(abs(a - b) for a, b in edges) / len(edges)


def bfs_order(edges, n):
    """BFS 로 만난 순서대로 번호를 다시 매긴다. 제일 싼 재배치 방법."""
    adj = defaultdict(list)
    for a, b in edges:
        adj[a].append(b); adj[b].append(a)
    new, cnt = {}, 0
    for seed in range(n):
        if seed in new:
            continue
        q = deque([seed]); new[seed] = cnt; cnt += 1
        while q:
            u = q.popleft()
            for v in adj[u]:
                if v not in new:
                    new[v] = cnt; cnt += 1
                    q.append(v)
    return new


def clustered(n=N, groups=60, avg_deg=12, seed=7):
    """커뮤니티가 뚜렷한 그래프. 실제 소셜·웹·도로망이 이쪽에 가깝다.
    단, 번호는 일부러 뒤섞어 둔다. 적재 순서가 구조와 무관한 현실을 흉내 낸다."""
    import random
    rnd = random.Random(seed)
    perm = list(range(n)); rnd.shuffle(perm)
    size = n // groups
    edges = set()
    for g in range(groups):
        members = [perm[i] for i in range(g * size, min((g + 1) * size, n))]
        for a in members:
            for _ in range(avg_deg // 2):
                b = rnd.choice(members)
                if a != b:
                    edges.add((min(a, b), max(a, b)))
    # 커뮤니티 사이를 잇는 다리 몇 개
    for _ in range(n // 50):
        a, b = rnd.randrange(n), rnd.randrange(n)
        if a != b:
            edges.add((min(a, b), max(a, b)))
    return sorted(edges)


def report(label, edges):
    before = locality(edges)
    mapping = bfs_order(edges, N)
    after = locality([(mapping[a], mapping[b]) for a, b in edges])
    print(f"{label:<22} 전 {before:>10,.0f}  후 {after:>10,.0f}  "
          f"개선 {before/after:>6,.1f}배")
    return after


def main():
    print(f"노드 {N:,} 기준, 이웃 번호 차이 평균 (작을수록 좋다)\n")
    report("무작위 그래프", make(n=N, avg_deg=12))
    after = report("커뮤니티 있는 그래프", clustered())

    # 4바이트 정수, 캐시 한 줄 64바이트 = 16개가 한 번에 온다
    print(
        f"\n캐시 한 줄(64바이트)에 4바이트 정수 16개가 들어온다.\n"
        f"이웃 번호가 평균 {after:,.0f} 만큼 떨어져 있으면 "
        f"{'같은 줄에 들어올 확률이 있다' if after < 16 else '거의 매번 새 줄을 가져온다'}.\n"
        "\n무작위 그래프에서는 재배치 효과가 크지 않다. 원래 구조가 없으니까.\n"
        "커뮤니티가 뚜렷한 실제 그래프(소셜, 웹, 도로망)에서는 훨씬 크게 준다.\n"
        "그래서 대용량 그래프 처리 도구들이 적재할 때 재배치를 먼저 한다."
    )


if __name__ == "__main__":
    main()
