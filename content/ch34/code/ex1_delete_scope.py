"""
예제 1 — 「저를 지워 주세요」. 그래프에서 무엇을 지워야 하나.

    pip install kuzu
    python3 ex1_delete_scope.py

노드 하나를 지우면 무엇이 남는지 본다. 남는 것들이 문제다.
"""

import shutil
import tempfile

import kuzu

NODES = [
    ("p1", "Person", "김도현"), ("p2", "Person", "이서연"),
    ("p3", "Person", "박민수"),
    ("t1", "Team", "결제팀"),
    ("d1", "Doc", "3분기 보고서"), ("d2", "Doc", "회식 정산"),
    ("m1", "Msg", "김도현: 마포에서 봐요"),
    ("r1", "Run", "보고서 발송 #4821"),
]
EDGES = [
    ("p1", "t1", "속함"), ("p2", "t1", "속함"), ("p3", "t1", "이끔"),
    ("p1", "d1", "작성"), ("p1", "d2", "승인"),
    ("p1", "m1", "발화"),
    ("r1", "p1", "읽음"),          # 29장의 Reads
    ("p2", "p1", "멘토"),           # 남이 나를 가리킨다
    ("d1", "p1", "언급"),           # 문서 본문 안에 이름이 있다
]


def build(path):
    db = kuzu.Database(path)
    c = kuzu.Connection(db)
    c.execute("CREATE NODE TABLE N(id STRING, kind STRING, label STRING, "
              "PRIMARY KEY(id))")
    c.execute("CREATE REL TABLE R(FROM N TO N, kind STRING)")
    for i, k, l in NODES:
        c.execute("CREATE (:N {id:$i, kind:$k, label:$l})",
                  {"i": i, "k": k, "l": l})
    for a, b, k in EDGES:
        c.execute("MATCH (x:N {id:$a}),(y:N {id:$b}) "
                  "CREATE (x)-[:R {kind:$k}]->(y)", {"a": a, "b": b, "k": k})
    return c


def rows(r):
    out = []
    while r.has_next():
        out.append(tuple(r.get_next()))
    return out


def survey(c, who="p1"):
    out = rows(c.execute(
        "MATCH (a:N {id:$w})-[e:R]->(b:N) RETURN 'out', e.kind, b.id, b.kind, "
        "b.label", {"w": who}))
    out += rows(c.execute(
        "MATCH (a:N)-[e:R]->(b:N {id:$w}) RETURN 'in', e.kind, a.id, a.kind, "
        "a.label", {"w": who}))
    return out


def main():
    tmp = tempfile.mkdtemp()
    c = build(tmp + "/db")

    print("「김도현(p1)을 지워 주세요」 요청이 들어왔다.\n")
    print(f"{'방향':<6}{'관계':<8}{'상대':<8}{'종류':<8}상대 라벨")
    print("-" * 58)
    for d, k, i, kind, label in survey(c):
        print(f"{('나가는' if d == 'out' else '들어오는'):<6}{k:<8}"
              f"{i:<8}{kind:<8}{label}")

    print("\n\n노드만 지우면 어떻게 되나. 지워 본다.\n")
    c.execute("MATCH (n:N {id:'p1'})-[e:R]->() DELETE e")
    c.execute("MATCH ()-[e:R]->(n:N {id:'p1'}) DELETE e")
    c.execute("MATCH (n:N {id:'p1'}) DELETE n")

    left = rows(c.execute("MATCH (n:N) RETURN n.id, n.kind, n.label "
                          "ORDER BY n.id"))
    print(f"{'남은 노드':<8}{'종류':<8}라벨")
    print("-" * 48)
    for i, k, l in left:
        mark = "  ← 이름이 그대로 남아 있다" if "김도현" in l else ""
        print(f"{i:<8}{k:<8}{l}{mark}")

    print(
        "\n노드는 지워졌는데 «김도현»이라는 이름이 m1 에 그대로 남아 있다.\n"
        "  m1 — 그 사람이 한 발화. 본문에 이름이 들어 있다\n"
        "  (그리고 실제 시스템에서는 로그·백업·이벤트 로그에도 남는다)\n"
        "\n관계형 DB 라면 «그 행을 지우면 끝»에 가깝다.\n"
        "그래프에서는 어렵다. 세 가지 이유가 있다.\n"
        "\n1. 들어오는 엣지가 있다.\n"
        "   «이서연이 김도현의 멘티였다»는 이서연 쪽 사실이기도 하다.\n"
        "   지우면 이서연의 이력이 사라진다.\n"
        "\n2. 자유 텍스트 안에 이름이 있다.\n"
        "   발화, 문서 본문, 요약. 이건 정규화된 필드가 아니라 그냥 글이다.\n"
        "\n3. 지운 «기록»이 남아야 한다.\n"
        "   30장의 이벤트 로그에는 「p1 을 지웠다」가 남는다.\n"
        "   그 기록 자체가 「p1 이 있었다」는 정보다.\n"
        "\n그래서 「지운다」를 한 가지로 다루면 안 된다.\n"
        "무엇을 어느 수준으로 지울지 나눠야 한다. 다음 예제에서 본다."
    )
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
