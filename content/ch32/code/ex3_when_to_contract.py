"""
예제 3 — 「아무도 안 쓴다」를 어떻게 확인하나.

    python3 ex3_when_to_contract.py

의존성 없음. 옛 스키마 사용 기록을 놓고
「지금 지워도 되나」를 세 가지 방법으로 판정한다.
"""

# 최근 90일간 옛 이름(이끔)을 읽은 기록
# (일자, 읽은 주체, 건수)
READS = [
    (1,  "정산 배치",   420), (1,  "조직도 렌더", 1200),
    (7,  "정산 배치",   410), (7,  "조직도 렌더", 1180),
    (14, "정산 배치",   405), (14, "조직도 렌더",   30),
    (21, "정산 배치",   400), (21, "조직도 렌더",    0),
    (30, "정산 배치",   395),
    (45, "정산 배치",   390),
    (60, "정산 배치",     2),
    (75, "정산 배치",     0),
    (82, "월말 마감",    340),      # 월말에만 도는 배치
    (88, "분기 결산",    210),      # 분기에 한 번 도는 배치
    (90, "정산 배치",     0),
]
TODAY = 140


def by_reader():
    d = {}
    for day, who, n in READS:
        d.setdefault(who, []).append((day, n))
    return d


def last_use(who, hist):
    used = [d for d, n in hist if n > 0]
    return max(used) if used else None


def main():
    d = by_reader()
    print(f"오늘은 {TODAY}일째. 옛 이름을 읽은 기록을 본다.\n")
    print(f"{'읽는 주체':<14}{'마지막 사용':>12}{'경과일':>8}{'최근 30일 건수':>14}")
    print("-" * 52)
    for who, hist in sorted(d.items()):
        lu = last_use(who, hist)
        recent = sum(n for day, n in hist if day > TODAY - 30)
        gap = TODAY - lu if lu else 999
        print(f"{who:<14}{lu if lu else '없음':>12}{gap:>8}{recent:>14}")

    print(f"\n{'판정 방법':<28}{'결론':<14}이유")
    print("-" * 74)

    # 1) 최근 30일 무사용
    quiet30 = all(sum(n for day, n in h if day > TODAY - 30) == 0
                  for h in d.values())
    print(f"{'최근 30일 건수가 0인가':<28}"
          f"{'지워도 됨' if quiet30 else '아직':<14}"
          f"{'월말 마감이 82일에 340건' if not quiet30 else '최근 창 안에는 아무도 안 읽었다'}")

    # 2) 모든 주체가 30일 이상 조용한가
    all_quiet = all((TODAY - last_use(w, h)) >= 30 if last_use(w, h) else True
                    for w, h in d.items())
    print(f"{'모든 주체가 30일 이상 조용':<28}"
          f"{'지워도 됨' if all_quiet else '아직':<14}"
          f"{'제일 최근이 52일 전' if all_quiet else '한 곳이 최근에 씀'}")

    # 3) 가장 긴 주기보다 오래 조용한가
    LONGEST_CYCLE = 92          # 제일 드문 것 — 분기 결산
    safe = all((TODAY - last_use(w, h)) > LONGEST_CYCLE if last_use(w, h)
               else True for w, h in d.items())
    print(f"{f'가장 긴 주기({LONGEST_CYCLE}일)보다 오래':<28}"
          f"{'지워도 됨' if safe else '아직':<14}"
          f"{'분기 결산이 52일 전. 아직 한 주기가 안 지났다' if not safe else ''}")

    print(
        "\n앞의 둘은 «지워도 됨»이라고 하고 세 번째만 «아직»이라고 한다.\n"
        "그리고 세 번째가 맞다.\n"
        "\n«최근 30일»은 흔히 쓰는 기준인데 함정이 있다.\n"
        "분기 결산처럼 «드물게 도는» 것을 놓친다.\n"
        "52일째 조용하니 안 쓰는 것처럼 보이지만, 이건 92일마다 도는 잡이다.\n"
        "40일 뒤에 깨어나서 없어진 이름을 찾는다.\n"
        "\n연말 정산이면 365일이다. 그러면 «1년 조용»해도 안 지워야 한다.\n"
        "\n그래서 기준은 «시간»이 아니라 «가장 긴 주기»여야 한다.\n"
        "시스템에서 제일 드물게 도는 잡의 주기를 찾고, 그보다 길게 기다린다.\n"
        "\n그런데 그 주기를 어떻게 아나. 크론 목록을 보면 된다.\n"
        "크론에 없는 것(사람이 손으로 도는 것)은 못 잡는다. 그래서 하나 더 둔다.\n"
        "\n  옛 이름을 읽으면 «경고 로그»를 남기게 하고, 그 로그를 본다.\n"
        "  지우기 전에 마지막 한 달은 «읽으면 알림»까지 켠다.\n"
        "\n그리고 지울 때는 «되돌릴 수 있게» 지운다.\n"
        "바로 DROP 하지 말고 이름만 바꿔 두고(이끔 → _deprecated_이끔)\n"
        "한 주기 더 기다린 다음 진짜로 지운다.\n"
        "\n조직도 렌더의 곡선을 보시라. 1,200 → 1,180 → 30 → 0 으로 떨어졌다.\n"
        "그게 «새 코드로 옮겨 간» 흔적이다. 이런 곡선이 보이면 이행이 잘 되고 있는 것이다."
    )


if __name__ == "__main__":
    main()
