"""
예제 3 — depends_on 은 DAG 엣지다. 위상 정렬하면 슈퍼스텝이 나온다.

    python3 ex3_depends_on.py

의존성 없음. 오케스트레이터가 안에서 하는 일이 이게 전부다.
같은 층에 놓인 작업은 동시에 돌려도 된다. 그게 병렬화의 근거다.
"""

from collections import defaultdict, deque

TASKS = {
    "스키마 설계":       [],
    "샘플 데이터 준비":  [],
    "API 구현":         ["스키마 설계", "샘플 데이터 준비"],
    "마이그레이션 작성": ["스키마 설계"],
    "통합 테스트":       ["API 구현", "마이그레이션 작성"],
    "문서 갱신":         ["통합 테스트"],
}


def supersteps(tasks):
    """칸(Kahn) 알고리즘. 한 번에 꺼낼 수 있는 묶음이 곧 하나의 슈퍼스텝이다."""
    indeg = {t: len(deps) for t, deps in tasks.items()}
    children = defaultdict(list)
    for t, deps in tasks.items():
        for d in deps:
            children[d].append(t)

    ready = deque(sorted(t for t, n in indeg.items() if n == 0))
    steps, done = [], 0
    while ready:
        layer = list(ready)
        ready.clear()
        steps.append(layer)
        done += len(layer)
        for t in layer:
            for c in children[t]:
                indeg[c] -= 1
                if indeg[c] == 0:
                    ready.append(c)
        ready = deque(sorted(ready))

    if done != len(tasks):
        stuck = sorted(t for t, n in indeg.items() if n > 0)
        raise ValueError(f"사이클이 있다. 영원히 시작 못 하는 작업: {stuck}")
    return steps


def main():
    steps = supersteps(TASKS)
    total = sum(len(s) for s in steps)
    print(f"작업 {total}개 → 슈퍼스텝 {len(steps)}개\n")
    for i, layer in enumerate(steps, 1):
        print(f"  {i}차: {', '.join(layer)}   (동시 실행 가능 {len(layer)}개)")

    print(f"\n순서대로 하면 {total}단계, 층으로 묶으면 {len(steps)}단계.")

    # 사이클을 넣어 보면 어떻게 되는지도 눈으로 보고 넘어가자.
    broken = dict(TASKS)
    broken["스키마 설계"] = ["문서 갱신"]
    print("\n--- 의존을 하나 잘못 적으면 ---")
    try:
        supersteps(broken)
    except ValueError as e:
        print(f"  {e}")
        print("  오케스트레이터가 이 검사를 안 하면, 이 팀은 아무 일도 안 하고 멈춰 있는다.")


if __name__ == "__main__":
    main()
