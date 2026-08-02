"""
예제 1 — 스키마를 바꾸면 무엇이 깨지나. 바꾸기 «전»에 세어 본다.

    pip install kuzu
    python3 ex1_breaking_change.py

29장에서 만든 Reads 엣지가 여기서 값을 한다.
"이 필드를 읽는 실행이 몇 개인가"를 물을 수 있다.
"""

import shutil
import tempfile

import kuzu

CHANGES = [
    ("관계 이름 바꾸기",   "이끔 → 리드",        "깨짐", "쿼리가 못 찾는다"),
    ("속성 추가",         "Person.email 추가",  "안 깨짐", "옛 코드는 그냥 무시한다"),
    ("속성 제거",         "Person.nickname 제거", "깨짐", "읽던 코드가 죽는다"),
    ("속성 타입 변경",     "인원 STRING → INT64", "깨짐", "파싱이 달라진다"),
    ("필수 속성 추가",     "Team.owner 필수",     "깨짐", "기존 노드에 값이 없다"),
    ("관계 방향 뒤집기",   "속함 방향 반전",       "깨짐", "순회가 전부 어긋난다"),
    ("새 노드 종류 추가",  "Project 추가",        "안 깨짐", "안 쓰면 없는 것과 같다"),
    ("단일값 → 다중값",   "이끔 을 여러 개 허용",   "조건부", "읽는 쪽이 한 개를 기대하면 깨짐"),
]

# 어느 실행이 무엇을 읽는지 (29장의 Reads 엣지)
USAGE = {
    "이끔":       ["보고서 발송", "조직도 렌더", "권한 계산", "알림 라우팅"],
    "속함":       ["보고서 발송", "조직도 렌더", "권한 계산", "정산 배치",
                  "온보딩", "감사 리포트"],
    "nickname":  ["인사말 생성"],
    "인원":       ["정산 배치", "대시보드"],
}


def build(path):
    db = kuzu.Database(path)
    c = kuzu.Connection(db)
    c.execute("CREATE NODE TABLE Entity(id STRING, kind STRING, PRIMARY KEY(id))")
    c.execute("CREATE NODE TABLE Run(id STRING, wf STRING, PRIMARY KEY(id))")
    c.execute("CREATE REL TABLE Reads(FROM Run TO Entity, field STRING)")
    fields = sorted(USAGE)
    for f in fields:
        c.execute("CREATE (:Entity {id:$i, kind:'field'})", {"i": f})
    runs = sorted({r for v in USAGE.values() for r in v})
    for r in runs:
        c.execute("CREATE (:Run {id:$i, wf:$i})", {"i": r})
    for f, rs in USAGE.items():
        for r in rs:
            c.execute("MATCH (a:Run {id:$r}),(b:Entity {id:$f}) "
                      "CREATE (a)-[:Reads {field:$f}]->(b)", {"r": r, "f": f})
    return c


def readers(c, field):
    r = c.execute("MATCH (run:Run)-[:Reads]->(e:Entity {id:$f}) "
                  "RETURN run.wf ORDER BY run.wf", {"f": field})
    out = []
    while r.has_next():
        out.append(r.get_next()[0])
    return out


def main():
    tmp = tempfile.mkdtemp()
    c = build(tmp + "/db")

    print("스키마 변경 여덟 가지. 무엇이 깨지고 무엇이 안 깨지나.\n")
    print(f"{'변경':<20}{'예':<26}{'판정':<10}이유")
    print("-" * 82)
    for name, ex, verdict, why in CHANGES:
        print(f"{name:<20}{ex:<26}{verdict:<10}{why}")

    print("\n\n이제 «누가 읽고 있나»를 물어본다. (29장의 Reads 엣지)\n")
    print(f"{'필드':<12}{'읽는 실행 수':>12}  읽는 것들")
    print("-" * 76)
    for f in sorted(USAGE, key=lambda x: -len(USAGE[x])):
        rs = readers(c, f)
        print(f"{f:<12}{len(rs):>12}  {', '.join(rs)}")

    print(
        "\n«속함»을 바꾸면 실행 6개가 깨진다. «nickname»은 1개다.\n"
        "같은 «깨지는 변경»인데 값이 여섯 배 다르다.\n"
        "\n그런데 대부분의 팀은 이 표를 못 만든다.\n"
        "「이 필드를 누가 쓰는지」를 코드 검색으로 찾아야 하고,\n"
        "동적으로 만든 쿼리는 검색에 안 걸린다.\n"
        "\n29장에서 Reads 엣지를 만들어 둔 게 여기서 값을 한다.\n"
        "실제로 읽은 기록이라 «검색에 안 걸리는 것»도 잡힌다.\n"
        "\n순서는 이렇다.\n"
        "  1. 바꾸려는 필드를 «누가 읽는지» 센다\n"
        "  2. 그 수가 1~2 면 그냥 바꾼다\n"
        "  3. 여섯이면 다음 예제의 «확장-수축»으로 간다\n"
        "\n세는 데 5분 걸리고, 안 세면 배포하고 나서 안다."
    )
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
