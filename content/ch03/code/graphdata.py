"""
3장 공통 데이터 생성기. 의존성 없음.
같은 사실을 표(SQLite)와 인접 리스트 두 가지로 만든다.
사람 200명, 한 사람당 평균 친구 12명. 시드를 고정해 매번 같은 그래프가 나온다.
"""
import random

N_PEOPLE = 200
AVG_FRIENDS = 12
SEED = 20260801


def make_edges(n=N_PEOPLE, avg=AVG_FRIENDS, seed=SEED):
    rnd = random.Random(seed)
    edges = set()
    for a in range(n):
        for _ in range(avg // 2):
            b = rnd.randrange(n)
            if a != b:
                edges.add((min(a, b), max(a, b)))
    return sorted(edges)


def adjacency(edges, n=N_PEOPLE):
    adj = {i: set() for i in range(n)}
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    return {k: sorted(v) for k, v in adj.items()}


if __name__ == "__main__":
    e = make_edges()
    adj = adjacency(e)
    deg = [len(v) for v in adj.values()]
    print(f"노드 {len(adj)}개, 엣지 {len(e)}개")
    print(f"평균 차수 {sum(deg)/len(deg):.1f}, 최대 {max(deg)}, 최소 {min(deg)}")
