"""
예제 3 — 요약을 반복하면 무엇이 새는가.

    python3 ex3_summary_drift.py

의존성 없음. 요약을 «요약의 요약»으로 반복할 때
사실이 어떻게 사라지고, 어떤 종류가 먼저 사라지는지 본다.
"""

import random

KINDS = {
    # 종류        가중치  한 번 요약할 때 살아남을 확률
    "숫자":       (0.20, 0.55),   # 금액, 개수 — 요약이 «대략»으로 바꾼다
    "고유명사":   (0.20, 0.80),   # 이름 — 비교적 잘 남는다
    "결정":       (0.20, 0.90),   # «~하기로 했다» — 요약이 제일 잘 지킨다
    "이유":       (0.20, 0.45),   # «왜 그렇게 했나» — 제일 먼저 날아간다
    "제약":       (0.20, 0.50),   # «~는 하면 안 된다» — 이것도 잘 날아간다
}
N = 200


def make_facts(seed=5):
    rng = random.Random(seed)
    kinds = list(KINDS)
    return [{"id": i, "kind": rng.choice(kinds), "alive": True} for i in range(N)]


def compress(facts, rng):
    for f in facts:
        if f["alive"] and rng.random() > KINDS[f["kind"]][1]:
            f["alive"] = False
    return facts


def main():
    facts = make_facts()
    rng = random.Random(99)
    kinds = list(KINDS)

    print(f"사실 {N}개를 다섯 종류로 나눠 심었다. 요약을 반복한다.\n")
    header = f"{'요약 회차':>8}{'전체 생존':>10}" + "".join(f"{k:>9}" for k in kinds)
    print(header)
    print("-" * 62)

    for round_ in range(0, 6):
        if round_:
            compress(facts, rng)
        alive = sum(f["alive"] for f in facts)
        per = []
        for k in kinds:
            tot = sum(1 for f in facts if f["kind"] == k)
            liv = sum(1 for f in facts if f["kind"] == k and f["alive"])
            per.append(f"{liv / tot:>8.0%}")
        print(f"{round_:>8}{alive / N:>9.0%}" + "".join(per))

    print(
        "\n한 번 요약하면 68%가 남는다. 나쁘지 않아 보인다.\n"
        "다섯 번 반복하면 23%다. 회차마다 곱해지니까 그렇게 된다.\n"
        "\n더 중요한 건 «무엇이» 남느냐다. 오른쪽 칸들을 가로로 읽어 보시라.\n"
        "\n«결정»은 잘 남는다. 요약이 결론을 좋아하기 때문이다.\n"
        "«이유»와 «제약»은 빨리 사라진다. 네 번 만에 5%, 6%다. 다섯 번이면 0이다.\n"
        "요약이 근거를 군더더기로 보기 때문이다.\n"
        "\n이게 왜 위험한가. 결정만 남고 이유가 사라진 컨텍스트를 받은 에이전트는\n"
        "«그 결정을 왜 했는지» 모른 채로 그 결정을 뒤집는다.\n"
        "제약이 사라지면 «하면 안 되는 일»을 다시 시도한다.\n"
        "\n실무의 대응은 요약 프롬프트에 «반드시 보존할 종류»를 못 박는 것이다.\n"
        "  - 숫자는 원문 그대로 옮긴다 («약 300만 원» 금지)\n"
        "  - 결정에는 반드시 이유를 붙인다\n"
        "  - 금지 사항은 요약하지 않고 목록으로 따로 뺀다\n"
        "\n그리고 요약의 요약을 하지 않는다. 매번 «원문»에서 다시 요약한다.\n"
        "원문을 밖에 갖고 있어야 그게 가능하다. 그래서 오프로딩이 먼저다."
    )


if __name__ == "__main__":
    main()
