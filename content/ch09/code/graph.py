"""9장 공통 그래프. 의존성 없음. 시드 고정."""
import random
from collections import defaultdict

def make(n=200_000, avg_deg=12, seed=20260801):
    rnd = random.Random(seed)
    adj = defaultdict(list)
    for a in range(n):
        for _ in range(avg_deg // 2):
            b = rnd.randrange(n)
            if a != b:
                adj[a].append(b)
                adj[b].append(a)
    return {k: sorted(set(v)) for k, v in adj.items()}

def weighted(n=2_000, avg_deg=8, seed=7, allow_negative=False):
    rnd = random.Random(seed)
    edges = []
    for a in range(n):
        for _ in range(avg_deg // 2):
            b = rnd.randrange(n)
            if a == b:
                continue
            w = rnd.randint(1, 20)
            if allow_negative and rnd.random() < 0.05:
                w = -rnd.randint(1, 5)
            edges.append((a, b, w))
    return edges

if __name__ == "__main__":
    g = make(n=20_000)
    print(f"노드 {len(g):,} 평균 차수 {sum(len(v) for v in g.values())/len(g):.1f}")
