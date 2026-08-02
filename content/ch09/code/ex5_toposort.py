"""
예제 5 — 위상 정렬과 슈퍼스텝. 2장의 depends_on 이 여기로 이어진다.

    python3 ex5_toposort.py

의존성 없음.
"""

from collections import defaultdict, deque

TASKS = {
    "외부 API 예열": [],
    "데이터 적재": [],
    "스키마 검증": ["데이터 적재"],
    "엔티티 병합": ["데이터 적재"],
    "관계 추출": ["스키마 검증", "엔티티 병합"],
    "품질 검사": ["관계 추출"],
    "색인 생성": ["관계 추출"],
    "배포": ["품질 검사", "색인 생성", "외부 API 예열"],
}


def supersteps(tasks):
    indeg = {t: len(d) for t, d in tasks.items()}
    child = defaultdict(list)
    for t, deps in tasks.items():
        for d in deps:
            child[d].append(t)
    ready = deque(sorted(t for t, n in indeg.items() if n == 0))
    layers, done = [], 0
    while ready:
        layer = sorted(ready); ready.clear()
        layers.append(layer); done += len(layer)
        for t in layer:
            for c in child[t]:
                indeg[c] -= 1
                if indeg[c] == 0:
                    ready.append(c)
    if done != len(tasks):
        raise ValueError("사이클")
    return layers


def critical_path(tasks, cost):
    """제일 오래 걸리는 경로. 병렬로 돌려도 이 시간 밑으로는 못 내려간다."""
    memo = {}
    def go(t):
        if t in memo:
            return memo[t]
        best = max((go(d) for d in tasks[t]), default=0)
        memo[t] = best + cost[t]
        return memo[t]
    end = max(tasks, key=go)
    return go(end), end


def main():
    layers = supersteps(TASKS)
    cost = {"외부 API 예열": 40, "데이터 적재": 20, "스키마 검증": 5,
            "엔티티 병합": 30, "관계 추출": 15, "품질 검사": 8,
            "색인 생성": 25, "배포": 3}

    print(f"작업 {len(TASKS)}개 → 슈퍼스텝 {len(layers)}개\n")
    for i, l in enumerate(layers, 1):
        span = max(cost[t] for t in l)
        print(f"  {i}차 ({span}분): {', '.join(l)}")

    serial = sum(cost.values())
    parallel = sum(max(cost[t] for t in l) for l in layers)
    cp, end = critical_path(TASKS, cost)
    print(f"\n순차 실행     {serial}분")
    print(f"슈퍼스텝 실행 {parallel}분  ({serial/parallel:.1f}배 단축)")
    print(f"임계 경로     {cp}분 (끝나는 작업: {end})")

    print(
        "\n슈퍼스텝 실행이 임계 경로보다 느릴 수 있다는 게 요점이다.\n"
        "같은 층의 제일 느린 작업을 기다리기 때문이다.\n"
        "층 단위로 기다리지 않고 «의존이 풀리는 대로» 시작하면 임계 경로까지 내려간다.\n"
        "\n2장의 오케스트레이터가 실제로 고르는 지점이 이거다.\n"
        "층 단위는 구현이 쉽고, 의존 단위는 빠르다. 19장에서 다시 본다."
    )


if __name__ == "__main__":
    main()
