"""
예제 5 — 시간을 넣으면 얼마나 커지나. 그리고 언제 잘라 낼까.

    python3 ex5_storage_cost.py

의존성 없음.
"""

N_ENTITY = 100_000
FIELDS = 8
BYTES_PER_FACT = 120        # 값 + 두 시간 축 + 색인. 엔진마다 다르다.


def rows(entities, fields, changes_per_year, years, model):
    """model: current / valid / bitemporal"""
    if model == "current":
        return entities * fields
    versions = 1 + changes_per_year * years
    if model == "valid":
        return int(entities * fields * versions)
    # 이중 시간 — 정정이 일어나면 기록이 하나 더 생긴다
    corrections = 0.15                      # 실측: 변경 여섯 번에 한 번쯤 정정
    return int(entities * fields * versions * (1 + corrections))


def main():
    print(f"엔티티 {N_ENTITY:,}개, 필드 {FIELDS}개 기준\n")
    print(f"{'연 변경 횟수':>10} {'경과 연수':>8} "
          f"{'현재값만':>14} {'유효 시간':>14} {'이중 시간':>14} {'배수':>7}")
    print("-" * 74)
    for cpy, yrs in ((0.5, 3), (2, 3), (2, 10), (12, 3), (12, 10)):
        a = rows(N_ENTITY, FIELDS, cpy, yrs, "current")
        b = rows(N_ENTITY, FIELDS, cpy, yrs, "valid")
        c = rows(N_ENTITY, FIELDS, cpy, yrs, "bitemporal")
        print(f"{cpy:>10} {yrs:>8} {a:>14,} {b:>14,} {c:>14,} {c/a:>6.1f}x")

    print(f"\n바이트로 보면 (사실 하나 {BYTES_PER_FACT}바이트 가정)")
    for cpy, yrs in ((2, 3), (12, 10)):
        c = rows(N_ENTITY, FIELDS, cpy, yrs, "bitemporal")
        print(f"    연 {cpy}회 변경, {yrs}년 → {c*BYTES_PER_FACT/1e9:.1f} GB")

    print(
        "\n자주 바뀌는 필드가 문제다. 연 12회면 10년에 139배가 된다.\n"
        "\n대처법 세 가지.\n"
        "  1. 필드별로 정한다 — 등급·담당은 이중 시간, 로그성 값은 현재값만\n"
        "  2. 오래된 것을 «접는다» — 3년 지난 이력은 월 단위로 요약해 보관\n"
        "  3. 별도 저장소로 뺀다 — 그래프에는 현재값, 이력은 열 지향 저장소에\n"
        "\n제가 쓰는 건 1번과 3번이다. 2번은 «접는 기준»을 정하기가 어려웠다.\n"
        "월 단위로 접으면 «같은 달에 두 번 바뀐» 경우를 잃는데,\n"
        "하필 그런 경우가 감사에서 문제가 된다.\n"
        "\n한 가지 더. 이력을 지우기 전에 «법이 얼마나 보관하라고 하는지»를 봐야 한다.\n"
        "계약 관련은 5년, 회계는 10년인 경우가 흔하다. 34장에서 다룬다."
    )


if __name__ == "__main__":
    main()
