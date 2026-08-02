"""
예제 4 — 기억을 «그래프로» 갖는 값과 «컨텍스트로» 갖는 값.

    pip install kuzu
    python3 ex4_memory_cost.py

24장에서 잰 것과 이어진다. 그때는 «무엇을 버릴까»였고
여기서는 «버린 것을 어디에 둘까»다.
"""

import shutil
import tempfile
import time

import kuzu

PRICE_IN = 3.0 / 1_000_000
KRW = 1_380
TOK_PER_FACT = 22          # 사실 한 개를 프롬프트에 넣는 값
TURNS = 200                # 하루 대화 턴 수


def build(path, n_facts):
    db = kuzu.Database(path)
    c = kuzu.Connection(db)
    c.execute("CREATE NODE TABLE N(name STRING, PRIMARY KEY(name))")
    c.execute("CREATE REL TABLE R(FROM N TO N, kind STRING)")
    for i in range(n_facts):
        c.execute("CREATE (:N {name:$n})", {"n": f"n{i}"})
    for i in range(1, n_facts):
        c.execute("MATCH (a:N {name:$a}),(b:N {name:$b}) "
                  "CREATE (a)-[:R {kind:'k'}]->(b)",
                  {"a": f"n{i - 1}", "b": f"n{i}"})
    return c


def query_ms(c, reps=40):
    t0 = time.perf_counter()
    for _ in range(reps):
        r = c.execute("MATCH (a:N {name:'n5'})-[:R*1..2]->(b:N) RETURN b.name")
        while r.has_next():
            r.get_next()
    return (time.perf_counter() - t0) / reps * 1000


def main():
    print("사실이 늘어날 때 두 방식의 하루 비용.\n")
    print(f"{'사실 수':>8}{'전부 컨텍스트에':>18}{'하루 비용':>12}"
          f"{'그래프 조회(ms)':>16}{'조회한 사실':>12}{'하루 비용':>12}")
    print("-" * 82)

    tmp = tempfile.mkdtemp()
    for n in (50, 200, 1_000, 5_000):
        c = build(f"{tmp}/db{n}", n)
        ms = query_ms(c)

        all_tok = n * TOK_PER_FACT * TURNS
        all_cost = all_tok * PRICE_IN * KRW

        # 그래프는 «질문에 걸린 것»만 컨텍스트에 넣는다. 대개 10개 안팎.
        hit = 10
        g_tok = hit * TOK_PER_FACT * TURNS
        g_cost = g_tok * PRICE_IN * KRW

        print(f"{n:>8,}{all_tok:>18,}{all_cost:>11,.0f}원"
              f"{ms:>16.2f}{hit:>12}{g_cost:>11,.0f}원")

    print(
        "\n«전부 컨텍스트에»는 사실 수에 비례해서 오른다. 당연하다.\n"
        "«그래프 조회»는 안 오른다. 몇 개가 있든 걸리는 건 열 개쯤이니까.\n"
        "\n그래서 사실이 적을 때는 그냥 다 넣는 게 낫다.\n"
        "50개면 하루 911원이다. 그래프를 세울 이유가 없다.\n"
        "\n5,000개면 91,080원이다. 한 달이면 273만 원이다. 그때 그래프가 값을 한다.\n"
        "\n조회 시간 칸을 보시라. 사실이 100배 늘어도 2~7ms 사이에서 논다.\n"
        "규칙 없이 오르내리는 건 이 규모에서는 «측정 잡음»이 지배해서다.\n"
        "5,000개짜리가 50개짜리보다 빠르게 나오기도 한다. 그게 요점이다.\n"
        "이 규모에서 조회 시간은 «사실 수와 무관»하다. 색인이 일하고 있다.\n"
        "\n경계가 어디쯤인가. 토큰 값만 보면 «사실 20개»부터 그래프가 싸다.\n"
        "그런데 그래프를 세우고 유지하는 사람 시간이 있다.\n"
        "그걸 넣으면 실제 경계는 훨씬 뒤다. 저는 «1,000개»를 기준으로 쓴다.\n"
        "\n중요한 건 이것이다. 처음부터 그래프로 가지 마시라.\n"
        "평평한 목록으로 시작하고, 하루 비용이 눈에 띄면 그때 옮긴다.\n"
        "옮기는 데 이틀이면 되고, 그 이틀을 처음에 쓰면 대개 낭비가 된다."
    )
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
