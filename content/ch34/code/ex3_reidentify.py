"""
예제 3 — 이름을 지워도 특정될 수 있다.

    python3 ex3_reidentify.py

의존성 없음. 속성 몇 개를 조합하면 몇 명으로 좁혀지는지 센다.
k-익명성(k-anonymity)을 손으로 계산해 본다.
"""

import random
from collections import Counter

rng = random.Random(4)
N = 5000

TEAMS = [f"팀{i}" for i in range(40)]
CITIES = ["강남", "마포", "판교", "성수", "여의도"]
ROLES = ["개발", "기획", "디자인", "영업", "운영"]
YEARS = list(range(2015, 2027))


def make():
    return [{
        "team": rng.choice(TEAMS),
        "city": rng.choice(CITIES),
        "role": rng.choice(ROLES),
        "joined": rng.choice(YEARS),
        "birth_month": rng.randint(1, 12),
    } for _ in range(N)]


COMBOS = [
    ["team"],
    ["team", "city"],
    ["team", "city", "role"],
    ["team", "city", "role", "joined"],
    ["team", "city", "role", "joined", "birth_month"],
]


def k_anon(people, keys):
    c = Counter(tuple(p[k] for k in keys) for p in people)
    ks = sorted(c.values())
    unique = sum(1 for v in c.values() if v == 1)
    return ks[0], unique, len(c)


def main():
    people = make()
    print(f"사람 {N:,}명. 이름은 이미 지웠다. 남은 속성을 조합해 본다.\n")
    print(f"{'조합':<44}{'최소 그룹(k)':>14}{'혼자인 사람':>12}{'비율':>8}")
    print("-" * 80)
    for keys in COMBOS:
        k, uniq, groups = k_anon(people, keys)
        print(f"{' + '.join(keys):<44}{k:>14}{uniq:>12}{uniq / N:>7.1%}")

    print(
        "\n속성 하나로는 아무도 특정 안 된다. 팀 하나에 105명씩 있으니까.\n"
        "셋을 조합하면 벌써 30명이 혼자가 된다. 0.6% 다.\n"
        "넷이면 65.8%, 다섯이면 96.3% 가 혼자다.\n"
        "\n주목할 곳은 셋에서 넷으로 갈 때다. 0.6% 에서 65.8% 로 뛴다.\n"
        "속성을 하나 더 붙이는 것이 «두 배»가 아니라 «백 배»로 작동한다.\n"
        "조합의 수가 곱해지기 때문이다.\n"
        "\n이게 재식별이다. 이름을 지워도 «조합»으로 되찾을 수 있다.\n"
        "\nk-익명성은 «어떤 조합으로도 최소 k 명 이상으로 묶인다»는 성질이다.\n"
        "표의 «최소 그룹» 칸이 그 k 다. 1 이면 혼자인 사람이 있다는 뜻이다.\n"
        "\n대응은 셋이다.\n"
        "  일반화(generalization) — 「2019년 입사」를 「2015~2020년」으로 뭉갠다\n"
        "  억제(suppression)     — 혼자인 사람의 그 속성을 아예 뺀다\n"
        "  잡음(noise)          — 생월을 무작위로 ±2 흔든다\n"
        "\n셋 다 «정확도를 내주고 익명성을 산다». 공짜가 아니다.\n"
        "\n그런데 그래프에서는 하나 더 있다. «관계 자체가 식별자»다.\n"
        "속성을 전부 지워도 「이 사람은 이 팀에 속하고 저 문서를 작성했고\n"
        "그 사람의 멘티다」라는 «모양»이 남는다. 그 모양이 유일하면 특정된다.\n"
        "\n그래서 그래프의 익명화는 속성만 지워서는 안 되고\n"
        "«엣지의 조합»도 봐야 한다. 그리고 그건 훨씬 어렵다."
    )


if __name__ == "__main__":
    main()
