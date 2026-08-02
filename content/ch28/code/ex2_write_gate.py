"""
예제 2 — 쓰기 앞에 관문을 넷 세운다. 각각이 무엇을 잡나.

    pip install kuzu
    python3 ex2_write_gate.py

같은 추출 결과를 관문에 통과시키고, 관문별로 몇 개를 잡는지 센다.
"""

import shutil
import tempfile

import kuzu

# 스키마 — 무엇이 무엇에 붙을 수 있나
TYPES = {"박민수": "Person", "민수": "Person", "PM": "Person",
         "이서연": "Person", "결제팀": "Team", "정산팀": "Team",
         "채식": "Pref", "매운맛": "Pref"}
ALLOWED = {("이끔", "Person", "Team"), ("속함", "Person", "Team"),
           ("선호", "Person", "Pref")}
SINGLE = {"이끔"}          # 팀장은 한 명
CANON = {"관리": "이끔", "리드": "이끔", "소속": "속함"}
ALIAS = {"민수": "박민수", "PM": "박민수"}

CANDIDATES = [
    ("박민수", "이끔", "결제팀", 0.94),
    ("이서연", "속함", "결제팀", 0.91),
    ("민수",   "이끔", "결제팀", 0.88),
    ("이서연", "속함", "정산팀", 0.42),
    ("박민수", "이끔", "정산팀", 0.87),
    ("결제팀", "속함", "이서연", 0.92),
    ("박민수", "관리", "결제팀", 0.83),
    ("이서연", "속함", "결제팀", 0.90),
    ("PM",     "이끔", "결제팀", 0.71),
    ("이서연", "선호", "매운맛", 0.86),
    ("박민수", "선호", "결제팀", 0.88),
]

MIN_CONF = 0.65


def gate(c, s, k, o, conf):
    """관문 넷. 걸리면 (False, 어느 관문) 을 돌려준다."""
    # 1) 확신도
    if conf < MIN_CONF:
        return False, "1.확신도"
    # 2) 이름 정규화 — 여기서 «막지는» 않고 «고친다»
    s = ALIAS.get(s, s)
    k = CANON.get(k, k)
    # 3) 스키마 — 이 관계가 이 타입 사이에 올 수 있나
    ts, to = TYPES.get(s), TYPES.get(o)
    if (k, ts, to) not in ALLOWED:
        return False, "3.스키마"
    # 4) 단일 값 — 이미 다른 값이 있나
    if k in SINGLE:
        r = c.execute("MATCH (a:N {name:$s})-[e:R {kind:$k}]->(b:N) "
                      "RETURN b.name", {"s": s, "k": k})
        while r.has_next():
            if r.get_next()[0] != o:
                return False, "4.단일값충돌"
    # 5) 중복
    r = c.execute("MATCH (a:N {name:$s})-[e:R {kind:$k}]->(b:N {name:$o}) "
                  "RETURN 1", {"s": s, "k": k, "o": o})
    if r.has_next():
        return False, "5.중복"
    return True, (s, k, o)


def build(path):
    db = kuzu.Database(path)
    c = kuzu.Connection(db)
    c.execute("CREATE NODE TABLE N(name STRING, PRIMARY KEY(name))")
    c.execute("CREATE REL TABLE R(FROM N TO N, kind STRING)")
    for n in TYPES:
        c.execute("CREATE (:N {name:$n})", {"n": n})
    return c


def main():
    tmp = tempfile.mkdtemp()
    c = build(tmp + "/db")

    print(f"{'후보':<26}{'확신':>6}  판정")
    print("-" * 60)
    caught = {}
    written = 0
    for s, k, o, conf in CANDIDATES:
        ok, why = gate(c, s, k, o, conf)
        if ok:
            ns, nk, no = why
            c.execute("MATCH (a:N {name:$s}),(b:N {name:$o}) "
                      "CREATE (a)-[:R {kind:$k}]->(b)",
                      {"s": ns, "o": no, "k": nk})
            written += 1
            fixed = "  (정규화됨)" if (ns, nk) != (s, k) else ""
            verdict = f"통과{fixed}"
        else:
            caught[why] = caught.get(why, 0) + 1
            verdict = f"막힘 — {why}"
        print(f"{f'{s} -{k}-> {o}':<26}{conf:>6.2f}  {verdict}")

    print(f"\n후보 {len(CANDIDATES)}개 중 {written}개를 썼다.")
    print(f"관문별로 잡은 수: {caught}")

    r = c.execute("MATCH (a:N)-[e:R]->(b:N) RETURN a.name, e.kind, b.name "
                  "ORDER BY a.name")
    print("\n최종 그래프:")
    while r.has_next():
        a, k, b = r.get_next()
        print(f"  {a} -{k}-> {b}")

    print(
        "\n관문 넷이 각각 다른 것을 잡는다. 하나만 두면 나머지 셋이 샌다.\n"
        "\n확신도만 두면 «확신 있게 틀린 것»을 못 막는다.\n"
        "«결제팀 -속함-> 이서연»이 0.92 로 나왔다. 방향이 뒤집혔는데도 확신이 높다.\n"
        "추출기가 문장을 잘못 읽으면 «자신 있게» 잘못 읽는다. 확신도로는 못 잡는다.\n"
        "\n스키마가 그걸 잡는다. Team 이 Person 에 속할 수는 없으니까.\n"
        "«박민수 -선호-> 결제팀»(0.88)도 스키마에서 걸린다. Team 은 Pref 가 아니다.\n"
        "\n반대로 스키마만 두면 «박민수 -이끔-> 정산팀»(0.87)을 못 막는다.\n"
        "타입은 맞으니까(Person → Team). 이건 단일 값 관문이 잡는다.\n"
        "박민수는 이미 결제팀을 이끌고 있는데 정산팀도 이끈다고 하니 충돌이다.\n"
        "\n이름 정규화는 «막는» 관문이 아니라 «고치는» 관문이다.\n"
        "민수와 PM 을 박민수로 바꿔서 넣는다. 그래서 예제 1의 세 노드가 하나가 된다.\n"
        "\n민수·PM 은 정규화 뒤에 «박민수»가 되고, 그러면 중복 관문이 잡는다.\n"
        "정규화가 없으면 이 셋이 다 통과해서 예제 1처럼 노드가 셋이 된다.\n"
        "\n순서가 중요하다. 정규화를 먼저 하고 중복을 나중에 봐야 한다.\n"
        "거꾸로 하면 «민수»와 «박민수»가 다른 것으로 보여서 중복이 안 걸린다."
    )
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
