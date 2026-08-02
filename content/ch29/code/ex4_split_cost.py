"""
예제 4 — 합치면 좋은데, 합치면 무엇이 나빠지나.

    python3 ex4_split_cost.py

의존성 없음. 한 저장소 대 두 저장소의 값을 네 축으로 비교한다.
합치는 게 공짜였으면 이 절이 없었을 것이다.
"""

# 워크로드 특성
KG_READ_QPS = 40          # 지식 조회
KG_WRITE_QPS = 3          # 지식 갱신
RUN_WRITE_QPS = 220       # 실행 상태 쓰기 — 슈퍼스텝마다 (21장)
RUN_READ_QPS = 90

SCENARIOS = {
    "따로 (그래프 DB + 상태 저장소)": {
        "write_amp": 1.0,
        "cross_query": False,
        "tx_across": False,
        "ops_units": 2,
        "note": "각자 최적화된 저장소",
    },
    "합침 (한 그래프 DB)": {
        "write_amp": 1.0,
        "cross_query": True,
        "tx_across": True,
        "ops_units": 1,
        "note": "쓰기가 전부 그래프로 몰린다",
    },
    "절충 (그래프 + 실행은 별도, 링크만 그래프에)": {
        "write_amp": 0.12,
        "cross_query": True,
        "tx_across": False,
        "ops_units": 2,
        "note": "링크 엣지만 그래프에 남긴다",
    },
}

GRAPH_WRITE_MS = 4.2      # 그래프 DB 쓰기 한 건
KV_WRITE_MS = 0.35        # 키-값 저장소 쓰기 한 건


def evaluate(name, s):
    graph_w = KG_WRITE_QPS + RUN_WRITE_QPS * s["write_amp"]
    kv_w = RUN_WRITE_QPS * (1 - s["write_amp"]) if s["write_amp"] < 1 else 0
    if name.startswith("따로"):
        graph_w, kv_w = KG_WRITE_QPS, RUN_WRITE_QPS
    load_ms = graph_w * GRAPH_WRITE_MS + kv_w * KV_WRITE_MS
    return graph_w, kv_w, load_ms


def main():
    print(f"워크로드: 지식 쓰기 {KG_WRITE_QPS}/s, 실행 상태 쓰기 {RUN_WRITE_QPS}/s")
    print(f"그래프 쓰기 {GRAPH_WRITE_MS}ms, 키-값 쓰기 {KV_WRITE_MS}ms\n")

    print(f"{'구성':<34}{'그래프 쓰기/s':>14}{'초당 부하(ms)':>14}"
          f"{'교차 질의':>10}{'한 트랜잭션':>12}{'운영 단위':>10}")
    print("-" * 96)
    for name, s in SCENARIOS.items():
        gw, kw, ms = evaluate(name, s)
        print(f"{name:<34}{gw:>14.0f}{ms:>14.0f}"
              f"{'○' if s['cross_query'] else '✗':>10}"
              f"{'○' if s['tx_across'] else '✗':>12}"
              f"{s['ops_units']:>10}")

    print("\n각 구성의 성격:")
    for name, s in SCENARIOS.items():
        print(f"  {name:<34}{s['note']}")

    print(
        "\n«합침»의 초당 부하가 937ms 다. «따로»의 90ms 보다 열 배가 넘는다.\n"
        "초당 1,000ms 가 한계니, 이 워크로드는 «합침» 구성에서 거의 포화 상태다.\n"
        "실행 상태 쓰기가 지식 쓰기보다 70배 많은데, 그걸 전부 그래프 DB 로 보내서다.\n"
        "\n그래프 DB 는 «관계를 따라가는» 데 최적화돼 있지\n"
        "«초당 수백 건의 작은 갱신»에 최적화돼 있지 않다.\n"
        "슈퍼스텝마다 상태를 통째로 쓰는 21장의 패턴과 특히 안 맞는다.\n"
        "\n그래서 «절충»이 실무의 답이다.\n"
        "실행 상태 본문은 빠른 저장소에 두고, 그래프에는 «링크만» 남긴다.\n"
        "  Run 노드 하나 + Reads/Writes 엣지 몇 개.\n"
        "  상태 본문(체크포인트)은 SQLite·Postgres 에.\n"
        "\n그러면 교차 질의는 되고(그래프에 링크가 있으니) 부하는 191ms 로 막힌다.\n"
        "«따로»의 두 배지만 «합침»의 5분의 1이다. 대신 «한 트랜잭션»은 포기한다.\n"
        "\n한 트랜잭션을 포기하면 예제 1의 문제가 다시 온다.\n"
        "그래서 31장의 낙관적 잠금과 30장의 이벤트 소싱이 필요해진다.\n"
        "«완전히 합치기»는 못 하고, 대신 «갈라진 것을 감지»한다."
    )


if __name__ == "__main__":
    main()
