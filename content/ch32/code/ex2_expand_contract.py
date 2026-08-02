"""
예제 2 — 확장-수축. 돌아가는 시스템의 스키마를 안 멈추고 바꾼다.

    pip install kuzu
    python3 ex2_expand_contract.py

「이끔 → 리드」로 관계 이름을 바꾸는 일을 여섯 단계로 나눈다.
각 단계에서 «옛 코드»와 «새 코드»가 둘 다 돌아가는지 확인한다.
"""

import shutil
import tempfile

import kuzu


def build(path):
    db = kuzu.Database(path)
    c = kuzu.Connection(db)
    c.execute("CREATE NODE TABLE N(name STRING, PRIMARY KEY(name))")
    c.execute("CREATE REL TABLE R(FROM N TO N, kind STRING)")
    for n in ("박민수", "이서연", "결제팀", "정산팀"):
        c.execute("CREATE (:N {name:$n})", {"n": n})
    for a, b in (("박민수", "결제팀"), ("이서연", "정산팀")):
        c.execute("MATCH (x:N {name:$a}),(y:N {name:$b}) "
                  "CREATE (x)-[:R {kind:'이끔'}]->(y)", {"a": a, "b": b})
    return c


def old_reader(c):
    """옛 코드 — «이끔» 만 안다."""
    r = c.execute("MATCH (p:N)-[e:R {kind:'이끔'}]->(t:N) RETURN p.name, t.name")
    out = []
    while r.has_next():
        out.append(tuple(r.get_next()))
    return out


def new_reader(c):
    """새 코드 — «리드» 만 안다."""
    r = c.execute("MATCH (p:N)-[e:R {kind:'리드'}]->(t:N) RETURN p.name, t.name")
    out = []
    while r.has_next():
        out.append(tuple(r.get_next()))
    return out


def counts(c):
    def n(kind):
        r = c.execute("MATCH ()-[e:R {kind:$k}]->() RETURN count(e)", {"k": kind})
        return r.get_next()[0]
    return n("이끔"), n("리드")


STEPS = [
    ("0. 시작",           None),
    ("1. 확장 — 새 이름을 «같이» 쓴다", "copy"),
    ("2. 새 코드 배포 (읽기만)",        None),
    ("3. 쓰기를 새 이름으로",           "newwrite"),
    ("4. 옛 코드 제거",               None),
    ("5. 수축 — 옛 이름 삭제",         "drop"),
]


def apply(c, action):
    if action == "copy":
        c.execute("MATCH (a:N)-[e:R {kind:'이끔'}]->(b:N) "
                  "CREATE (a)-[:R {kind:'리드'}]->(b)")
    elif action == "newwrite":
        # 새로 들어오는 것은 «리드» 로만 쓴다
        c.execute("MATCH (x:N {name:'이서연'}),(y:N {name:'결제팀'}) "
                  "CREATE (x)-[:R {kind:'리드'}]->(y)")
    elif action == "drop":
        c.execute("MATCH ()-[e:R {kind:'이끔'}]->() DELETE e")


def main():
    tmp = tempfile.mkdtemp()
    c = build(tmp + "/db")

    print("「이끔 → 리드」 관계 이름 변경을 여섯 단계로.\n")
    print(f"{'단계':<28}{'이끔':>6}{'리드':>6}{'옛 코드':>10}{'새 코드':>10}")
    print("-" * 62)
    for label, action in STEPS:
        apply(c, action)
        old, new = len(old_reader(c)), len(new_reader(c))
        a, b = counts(c)
        so = "동작" if old else "✗ 안 됨"
        sn = "동작" if new else "✗ 안 됨"
        print(f"{label:<28}{a:>6}{b:>6}{so:>10}{sn:>10}")

    print(
        "\n2단계와 3단계를 보시라. 옛 코드와 새 코드가 «둘 다» 동작한다.\n"
        "그 구간이 있어야 무중단 배포가 된다.\n"
        "\n한 번에 바꾸면 어떻게 되나. 배포 순간에 둘 중 하나가 죽는다.\n"
        "  DB 를 먼저 바꾸면 → 옛 코드가 죽는다\n"
        "  코드를 먼저 바꾸면 → 새 코드가 죽는다\n"
        "\n확장-수축은 그 사이에 «둘 다 되는» 구간을 만드는 방법이다.\n"
        "  확장(expand) — 새것을 «더한다». 옛것은 그대로 둔다\n"
        "  이행(migrate) — 읽기를 옮기고, 그다음 쓰기를 옮긴다\n"
        "  수축(contract) — 아무도 안 쓰는 게 확인되면 옛것을 지운다\n"
        "\n순서가 중요하다. «읽기 먼저, 쓰기 나중»이다.\n"
        "거꾸로 하면 새 이름으로 쓴 데이터를 옛 코드가 못 읽는다.\n"
        "\n그리고 5단계를 «언제» 하느냐가 실무의 어려움이다.\n"
        "「아무도 안 쓴다」를 어떻게 확인하나. 예제 3에서 본다."
    )
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
