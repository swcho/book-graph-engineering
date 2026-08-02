"""
예제 1 — 지식 그래프와 에이전트 상태를 «따로» 두면 무슨 일이 생기나.

    pip install kuzu
    python3 ex1_two_stores.py

같은 사실이 두 곳에 있고, 한쪽만 바뀐다. 흔한 시작이고 흔한 사고다.
"""

import shutil
import tempfile

import kuzu


class AgentState:
    """에이전트 실행 상태. 지금까지 알아낸 것을 여기 들고 다닌다(19장)."""

    def __init__(self):
        self.facts = {}
        self.step = 0

    def remember(self, k, v):
        self.facts[k] = v

    def get(self, k):
        return self.facts.get(k)


def build_kg(path):
    db = kuzu.Database(path)
    c = kuzu.Connection(db)
    c.execute("CREATE NODE TABLE N(name STRING, PRIMARY KEY(name))")
    c.execute("CREATE REL TABLE R(FROM N TO N, kind STRING)")
    for n in ("박민수", "이서연", "결제팀"):
        c.execute("CREATE (:N {name:$n})", {"n": n})
    c.execute("MATCH (a:N {name:'박민수'}),(b:N {name:'결제팀'}) "
              "CREATE (a)-[:R {kind:'이끔'}]->(b)")
    return c


def kg_leader(c):
    r = c.execute("MATCH (p:N)-[:R {kind:'이끔'}]->(:N {name:'결제팀'}) "
                  "RETURN p.name")
    return r.get_next()[0] if r.has_next() else None


def main():
    tmp = tempfile.mkdtemp()
    kg = build_kg(tmp + "/db")
    st = AgentState()

    print("[t0] 워크플로 시작. 지식 그래프에서 팀장을 읽어 상태에 담는다.")
    st.remember("팀장", kg_leader(kg))
    print(f"      지식 그래프: {kg_leader(kg)}    에이전트 상태: {st.get('팀장')}")

    print("\n[t1] 워크플로가 사람 승인을 기다린다(23장). 사흘 걸린다.")

    print("\n[t2] 그동안 다른 경로로 팀장이 바뀐다. 지식 그래프만 갱신된다.")
    kg.execute("MATCH (a:N {name:'박민수'})-[e:R {kind:'이끔'}]->"
               "(:N {name:'결제팀'}) DELETE e")
    kg.execute("MATCH (a:N {name:'이서연'}),(b:N {name:'결제팀'}) "
               "CREATE (a)-[:R {kind:'이끔'}]->(b)")
    print(f"      지식 그래프: {kg_leader(kg)}    에이전트 상태: {st.get('팀장')}")

    print("\n[t3] 승인이 나서 워크플로가 재개된다. 상태에 있던 값으로 실행한다.")
    print(f"      → 보고서를 «{st.get('팀장')}» 에게 보냈다.")
    print(f"      → 그런데 지금 팀장은 «{kg_leader(kg)}» 다.")

    print(
        "\n두 저장소가 갈라졌다. 그리고 아무 에러도 안 났다.\n"
        "\n에이전트 상태는 «그때 읽은 값»을 들고 있다. 그게 상태의 성질이다.\n"
        "체크포인트에 저장돼 사흘 뒤에도 그대로 살아 있다(21장).\n"
        "지식 그래프는 «지금 값»을 갖고 있다. 그것도 맞다.\n"
        "\n둘 다 자기 일을 제대로 했는데 결과가 틀렸다.\n"
        "\n이게 «두 그래프를 따로 두면» 생기는 문제다.\n"
        "그리고 이 문제는 코드를 잘 짜서 없앨 수 있는 게 아니다.\n"
        "같은 사실이 두 곳에 있는 한 언제나 갈라질 수 있다.\n"
        "\n선택지는 셋이다.\n"
        "  1. 상태에 담지 말고 매번 조회한다 → 느리고, 사흘짜리 워크플로는 중간에 값이 바뀐다\n"
        "  2. 상태에 담되 «읽은 시각»을 같이 담고, 쓰기 전에 다시 확인한다\n"
        "  3. 아예 한 저장소에 둔다 → 이 장의 주제\n"
        "\n2번이 실무의 절충이고 3번이 목표다. 그리고 3번은 생각보다 어렵다."
    )
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
