"""8장 공통 그래프 생성기. 의존성 없음. 시드 고정."""
import random

def make(n=50_000, avg_deg=12, skew=False, seed=20260801):
    """skew=True 면 차수가 한쪽으로 쏠린 그래프를 만든다(선호적 연결)."""
    rnd = random.Random(seed)
    edges = set()
    if not skew:
        for a in range(n):
            for _ in range(avg_deg // 2):
                b = rnd.randrange(n)
                if a != b:
                    edges.add((min(a, b), max(a, b)))
        return sorted(edges)
    # 선호적 연결: 이미 차수가 높은 노드에 더 붙는다
    targets = [0, 1, 2]
    for a in range(3, n):
        for _ in range(avg_deg // 2):
            b = rnd.choice(targets)
            if a != b:
                edges.add((min(a, b), max(a, b)))
                targets.append(b)
        targets.append(a)
    return sorted(edges)

if __name__ == "__main__":
    for skew in (False, True):
        e = make(skew=skew)
        deg = {}
        for a, b in e:
            deg[a] = deg.get(a, 0) + 1
            deg[b] = deg.get(b, 0) + 1
        vals = sorted(deg.values(), reverse=True)
        print(f"skew={skew}: 엣지 {len(e):,}  평균 {sum(vals)/len(vals):.1f}  "
              f"최대 {vals[0]:,}  상위 10개 합 {sum(vals[:10]):,}")
