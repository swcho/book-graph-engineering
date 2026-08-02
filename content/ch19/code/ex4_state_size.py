"""
예제 4 — 상태에 뭘 넣느냐가 값을 정한다. 체크포인트는 «매 슈퍼스텝» 저장된다.

    python3 ex4_state_size.py

의존성 없음.
"""

import json

# 흔히 상태에 넣는 것들과 대략적인 크기 (바이트)
FIELDS = [
    ("질문",            220,   "다음 노드가 읽는다",       True),
    ("검색 결과 원문",   84_000, "요약만 있으면 된다",       False),
    ("검색 결과 주소",       180, "필요하면 다시 읽는다",     True),
    ("검색 결과 요약",    1_800, "다음 노드가 읽는다",       True),
    ("모델 원본 응답",   12_000, "로그에만 쓴다",           False),
    ("중간 계산 캐시",    31_000, "같은 노드 안에서만 쓴다",   False),
    ("실행 로그",         6_400, "사람이 나중에 본다",       False),
    ("재시도 횟수",           8, "라우팅이 읽는다",         True),
    ("체크포인트 메타",     140,  "실행기가 쓴다",           True),
]

SUPERSTEPS = 14
RUNS_PER_DAY = 1_200
BYTES_PER_GB = 1024 ** 3
STORAGE_WON_PER_GB_MONTH = 25


def total(fields):
    return sum(sz for _, sz, _, _ in fields)


def main():
    print(f"{'필드':<16} {'크기':>9} {'다음 노드가 읽나':<22} 상태에 둘까")
    print("-" * 66)
    for name, size, why, need in FIELDS:
        print(f"{name:<16} {size:>8,}B {why:<22} {'예' if need else '아니오'}")

    all_b = total(FIELDS)
    lean_b = total([f for f in FIELDS if f[3]])
    print(f"\n전부 담으면 {all_b:,}B, 필요한 것만 담으면 {lean_b:,}B "
          f"({all_b/lean_b:.1f}배)")

    print(f"\n체크포인트는 슈퍼스텝마다 저장된다 ({SUPERSTEPS}회 가정)")
    for label, b in (("전부", all_b), ("필요한 것만", lean_b)):
        per_run = b * SUPERSTEPS
        per_day = per_run * RUNS_PER_DAY
        gb_month = per_day * 30 / BYTES_PER_GB
        print(f"    {label:<12} 실행당 {per_run/1e3:>8,.0f}KB  "
              f"하루 {per_day/1e9:>6.2f}GB  월 저장비 "
              f"{gb_month*STORAGE_WON_PER_GB_MONTH:>8,.0f}원")

    print(
        "\n«검색 결과 원문»이 84KB 다. 이게 슈퍼스텝마다 다시 저장된다.\n"
        "안 바뀌는데도 매번 통째로.\n"
        "\n두 가지 대처가 있다.\n"
        "  1. 상태에 안 넣는다 — 원문은 밖에 두고 상태에는 «주소»만 (24장 오프로딩)\n"
        "  2. 체크포인터가 «바뀐 것만» 저장하게 한다 — 구현이 지원해야 한다\n"
        "\n1번이 확실하다. 그리고 부수 효과가 하나 더 있다.\n"
        "상태가 작아지면 «이 노드가 무엇에 의존하는가»가 타입만 봐도 보인다.\n"
        "\n제 기준: 상태 하나가 8KB 를 넘으면 무엇을 뺄지 찾는다.\n"
        "\n한 가지 덧붙이면, 저장비 자체는 큰 돈이 아니다. 월 1,600원이다.\n"
        "진짜 값은 «직렬화 시간»이다. 1.9MB 를 슈퍼스텝마다 쓰고 읽으면\n"
        "지연이 붙고, 그게 사용자가 기다리는 시간이 된다.\n"
        "18장에서 잰 체크포인트 40~120ms 가 여기서 몇 배가 된다."
    )


if __name__ == "__main__":
    main()
