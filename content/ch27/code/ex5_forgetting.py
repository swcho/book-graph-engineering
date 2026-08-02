"""
예제 5 — 잊는 법. 무엇을 지우고 무엇을 남길 것인가.

    python3 ex5_forgetting.py

의존성 없음. 세 가지 «잊기» 정책을 같은 기억에 적용하고
「나중에 필요했던 것」이 몇 개 살아남는지 센다. 24장의 지표와 같다.
"""

import random

N = 400
DAYS = 180


def make_memory(seed=17):
    rng = random.Random(seed)
    out = []
    for i in range(N):
        age = rng.randint(0, DAYS)
        # 참조 횟수는 나이와 약하게 관련 있다
        used = rng.choices([0, 1, 2, 5, 20], [50, 25, 15, 8, 2])[0]
        kind = rng.choices(["일회성", "선호", "관계", "제약"],
                           [55, 20, 18, 7])[0]
        # 나중에 실제로 필요해지는가
        need_p = {"일회성": 0.03, "선호": 0.55, "관계": 0.62, "제약": 0.88}[kind]
        out.append({"id": i, "age": age, "used": used, "kind": kind,
                    "needed": rng.random() < need_p})
    return out


def keep_recent(m, days=30):
    return [x for x in m if x["age"] <= days]


def keep_used(m, k=1):
    return [x for x in m if x["used"] >= k]


def keep_typed(m, days=30):
    # 종류별로 다르게 잊는다
    keep_days = {"일회성": 7, "선호": 365, "관계": 365, "제약": 3650}
    return [x for x in m if x["age"] <= keep_days[x["kind"]] or x["used"] >= 2]


def report(name, kept, total_needed, total):
    n = len(kept)
    got = sum(1 for x in kept if x["needed"])
    print(f"{name:<22}{n:>8}{n / total:>9.0%}{got:>10}"
          f"{got / total_needed:>12.0%}")


def main():
    m = make_memory()
    needed = sum(1 for x in m if x["needed"])
    print(f"기억 {N}개, 그중 나중에 필요해지는 것 {needed}개.\n")
    print(f"{'정책':<22}{'남긴 수':>8}{'남긴 비율':>9}"
          f"{'필요한 것':>10}{'보존율':>12}")
    print("-" * 62)
    report("전부 남긴다", m, needed, N)
    report("최근 30일만", keep_recent(m), needed, N)
    report("한 번이라도 쓴 것", keep_used(m), needed, N)
    report("종류별로 다르게", keep_typed(m), needed, N)

    print("\n종류별 보존율:\n")
    typed = keep_typed(m)
    print(f"{'종류':<10}{'전체':>7}{'남김':>7}{'필요한 것':>10}{'그중 남김':>10}")
    print("-" * 46)
    for k in ("일회성", "선호", "관계", "제약"):
        tot = [x for x in m if x["kind"] == k]
        kept = [x for x in typed if x["kind"] == k]
        nd = [x for x in tot if x["needed"]]
        got = [x for x in kept if x["needed"]]
        print(f"{k:<10}{len(tot):>7}{len(kept):>7}{len(nd):>10}{len(got):>10}")

    print(
        "\n«최근 30일만»은 83% 를 버리면서 필요한 것의 81% 도 같이 버린다.\n"
        "그럴 수밖에 없다. 나이는 «중요도»와 별 관계가 없기 때문이다.\n"
        "\n«한 번이라도 쓴 것»은 낫지만 여전히 55% 를 잃는다.\n"
        "쓴 적이 있다는 건 신호이긴 한데, «아직 한 번도 안 쓴 제약»을 버린다.\n"
        "그게 제일 아픈 종류다.\n"
        "«이 API 는 부르면 안 된다»는 40번 대화 동안 한 번도 안 쓰이다가\n"
        "41번째에 결정적으로 필요하다.\n"
        "\n«종류별로 다르게»는 62% 를 남기고 필요한 것의 97% 를 지킨다.\n"
        "«한 번이라도 쓴 것»보다 더 많이 남기는데 보존율은 두 배가 넘는다.\n"
        "덜 버려서 이긴 게 아니다. «버릴 것을 골라서» 이겼다.\n"
        "\n아래 표를 보시라. 일회성 226개 중 76개만 남기고 150개를 버렸다.\n"
        "그러면서 잃은 «필요한 것»은 3개뿐이다. 선호·관계·제약은 하나도 안 버렸다.\n"
        "\n종류마다 낡는 속도가 다르기 때문이다.\n"
        "  일회성 — 7일. «어제 그 파일 경로»는 일주일이면 쓸모없다\n"
        "  선호·관계 — 1년. 사람은 잘 안 바뀐다\n"
        "  제약 — 사실상 영구. 지우면 사고가 난다\n"
        "\n그런데 이 표를 만들려면 기억에 «종류»를 붙여야 한다.\n"
        "그게 이 방식의 값이다. 넣을 때 한 번 더 판단해야 한다.\n"
        "\n다행히 그 판단은 규칙으로 상당 부분 된다.\n"
        "«~하지 마»,«~는 안 됩니다»,«절대» → 제약.\n"
        "«좋아합니다»,«싫어합니다»,«선호» → 선호.\n"
        "«팀장»,«소속»,«담당» → 관계. 나머지는 일회성."
    )


if __name__ == "__main__":
    main()
