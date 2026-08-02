"""
예제 2 — 한 그래프에 «지식»과 «실행»을 같이 둔다.

    pip install kuzu
    python3 ex2_one_backbone.py

노드 종류를 나누되 저장소는 하나. 그러면 둘을 «엣지로» 이을 수 있다.
"""

import shutil
import tempfile

import kuzu

SCHEMA = """
CREATE NODE TABLE Entity(id STRING, kind STRING, name STRING,
                         PRIMARY KEY(id));
CREATE NODE TABLE Run(id STRING, wf STRING, status STRING, step INT64,
                      PRIMARY KEY(id));
CREATE REL TABLE Knows(FROM Entity TO Entity, kind STRING,
                       vfrom STRING, vto STRING, src STRING);
CREATE REL TABLE Reads(FROM Run TO Entity, at STRING, as_of STRING);
CREATE REL TABLE Writes(FROM Run TO Entity, at STRING, kind STRING);
CREATE REL TABLE About(FROM Run TO Entity, role STRING);
"""


def build(path):
    db = kuzu.Database(path)
    c = kuzu.Connection(db)
    for stmt in SCHEMA.strip().split(";"):
        if stmt.strip():
            c.execute(stmt)
    for i, k, n in [("e1", "Person", "박민수"), ("e2", "Person", "이서연"),
                    ("e3", "Team", "결제팀"), ("e4", "Doc", "3분기 보고서")]:
        c.execute("CREATE (:Entity {id:$i, kind:$k, name:$n})",
                  {"i": i, "k": k, "n": n})
    c.execute("MATCH (a:Entity {id:'e1'}),(b:Entity {id:'e3'}) "
              "CREATE (a)-[:Knows {kind:'이끔', vfrom:'2024-01-01', "
              "vto:'2026-03-31', src:'hr'}]->(b)")
    c.execute("MATCH (a:Entity {id:'e2'}),(b:Entity {id:'e3'}) "
              "CREATE (a)-[:Knows {kind:'이끔', vfrom:'2026-04-01', "
              "vto:'9999-12-31', src:'hr'}]->(b)")
    return c


def rows(r):
    out = []
    while r.has_next():
        out.append(tuple(r.get_next()))
    return out


def main():
    tmp = tempfile.mkdtemp()
    c = build(tmp + "/db")

    # 실행 하나를 그래프에 «노드로» 만든다
    c.execute("CREATE (:Run {id:'r1', wf:'보고서 발송', status:'실행중', step:2})")
    c.execute("MATCH (r:Run {id:'r1'}),(e:Entity {id:'e4'}) "
              "CREATE (r)-[:About {role:'대상'}]->(e)")
    # 읽을 때 «언제 기준으로 읽었는지»를 엣지에 적는다
    c.execute("MATCH (r:Run {id:'r1'}),(e:Entity {id:'e2'}) "
              "CREATE (r)-[:Reads {at:'2026-05-20T09:00', "
              "as_of:'2026-05-20'}]->(e)")
    # 3월에 시작해 아직 안 끝난 실행 하나가 더 있다. 그때 팀장은 박민수였다.
    c.execute("CREATE (:Run {id:'r2', wf:'연간 평가', status:'승인대기', step:4})")
    c.execute("MATCH (r:Run {id:'r2'}),(e:Entity {id:'e1'}) "
              "CREATE (r)-[:Reads {at:'2026-03-02T14:00', "
              "as_of:'2026-03-02'}]->(e)")

    print("한 그래프 안에 지식(Entity/Knows)과 실행(Run/Reads/Writes)이 같이 있다.\n")

    print("질문 1 — 이 실행은 무엇을 근거로 했나?")
    for name, at, asof in rows(c.execute(
            "MATCH (r:Run {id:'r1'})-[e:Reads]->(x:Entity) "
            "RETURN x.name, e.at, e.as_of")):
        print(f"  {name} 를 {at} 에 읽었다 (기준 시각 {asof})")

    print("\n질문 2 — 「이서연」을 근거로 삼은 실행이 몇 개인가?")
    n = rows(c.execute("MATCH (r:Run)-[:Reads]->(e:Entity {id:'e2'}) "
                       "RETURN count(r)"))[0][0]
    print(f"  {n}개")

    print("\n질문 3 — 재개하려는 실행들: 그때 읽은 값이 아직 유효한가?")
    now = rows(c.execute(
        "MATCH (p:Entity)-[e:Knows {kind:'이끔'}]->(:Entity {id:'e3'}) "
        "WHERE e.vfrom <= '2026-05-23' AND e.vto > '2026-05-23' "
        "RETURN p.name"))[0][0]
    print(f"  {'실행':<6}{'워크플로':<12}{'그때 읽은 값':<12}{'기준 시각':<14}"
          f"{'지금':<8}판정")
    print("  " + "-" * 62)
    for rid, wf, name, asof in rows(c.execute(
            "MATCH (r:Run)-[e:Reads]->(x:Entity) "
            "RETURN r.id, r.wf, x.name, e.as_of ORDER BY r.id")):
        ok = name == now
        print(f"  {rid:<6}{wf:<12}{name:<12}{asof:<14}{now:<8}"
              f"{'진행해도 된다' if ok else '멈춤 — 다시 확인'}")

    print(
        "\n세 질문이 전부 «같은 쿼리 언어»로 답해진다. 그게 합치는 값어치다.\n"
        "\n따로 뒀으면 질문 2는 아예 못 한다.\n"
        "지식 그래프는 자기를 누가 읽었는지 모르고,\n"
        "에이전트 상태는 다른 실행이 뭘 읽었는지 모른다.\n"
        "\n질문 3이 예제 1의 사고를 막는 방법이다.\n"
        "r2 가 걸렸다. 3월에 읽은 값으로 5월에 실행하려던 참이었다.\n"
        "Reads 엣지에 «기준 시각»이 적혀 있으니, 재개할 때 그 시각으로 다시 조회해서\n"
        "달라졌으면 멈춘다. 23장의 «상태 지문»과 같은 발상인데,\n"
        "여기서는 지문을 따로 안 만들고 그래프 자체로 비교한다.\n"
        "\n한 가지 더. Run 이 노드라서 «실행 사이의 관계»도 그릴 수 있다.\n"
        "어느 실행이 어느 실행을 낳았는지, 어느 실행들이 같은 문서를 건드렸는지."
    )
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
