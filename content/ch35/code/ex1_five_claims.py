"""
예제 1 — 이 책의 주장 다섯 개를 「무엇이 참이면 틀리는가」로 적는다.

    python3 ex1_five_claims.py

의존성 없음. 주장을 반증 가능한 형태로 만드는 연습이다.
반증 조건을 못 쓰면 그건 주장이 아니라 의견이다.
"""

CLAIMS = [
    dict(
        n=1,
        claim="모델 호출이 응답 시간의 90% 넘게 차지한다",
        chapter="33장",
        falsifier="같은 작업의 모델 지연이 10분의 1이 되면 60% 아래로 내려간다",
        watch="분기마다 구간별 시간을 다시 잰다",
        confidence=0.35,
        note="지난 2년 추세가 이대로면 3년 안에 뒤집힌다",
    ),
    dict(
        n=2,
        claim="프롬프트 인젝션은 프롬프트 층에서 못 막는다",
        chapter="26장",
        falsifier="지시와 데이터를 «구조적으로» 나눈 모델이 나오면 틀린다",
        watch="모델 아키텍처 논문에서 «채널 분리»를 찾아본다",
        confidence=0.55,
        note="지금 구조에서는 맞는데, 구조가 안 바뀐다는 보장이 없다",
    ),
    dict(
        n=3,
        claim="에이전트가 스스로 넓힌 그래프는 관문 없이 못 쓴다",
        chapter="28장",
        falsifier="추출 정확도가 99.9% 가 되면 관문 넷 중 셋이 필요 없어진다",
        watch="추출 정확도를 분기마다 재고, 관문별 차단 건수를 본다",
        confidence=0.70,
        note="정확도가 올라도 «이름 정규화»는 남는다. 다른 문제라서",
    ),
    dict(
        n=4,
        claim="지식 그래프와 에이전트 상태는 따로 두는 게 옳다",
        chapter="29장",
        falsifier="그래프 DB 의 쓰기 성능이 키-값 저장소 수준이 되면 합쳐도 된다",
        watch="쓰기 지연 비율(그래프/키-값)을 반기마다 잰다",
        confidence=0.50,
        note="성능이 아니라 «수명이 다르다»는 이유는 안 바뀐다",
    ),
    dict(
        n=5,
        claim="「에이전트 그래프 엔지니어링」이라는 용어가 자리를 잡는다",
        chapter="서문",
        falsifier="3년 뒤에 아무도 이 말을 안 쓰면 틀린 것이다",
        watch="이 말을 쓰는 1차 출처가 늘어나는지 센다",
        confidence=0.20,
        note="제일 자신 없는 주장. 이름은 자주 바뀐다",
    ),
]


def bar(p, width=20):
    return "█" * int(p * width) + "░" * (width - int(p * width))


def main():
    print("이 책에서 3년 뒤에 틀렸을 가능성이 큰 주장 다섯 개.\n")
    print("«확신»은 3년 뒤에도 이 주장이 참일 것으로 보는 정도다.\n")

    for c in sorted(CLAIMS, key=lambda x: x["confidence"]):
        print(f"[{c['n']}] {c['claim']}  ({c['chapter']})")
        print(f"     확신     {bar(c['confidence'])} {c['confidence']:.0%}")
        print(f"     반증 조건 {c['falsifier']}")
        print(f"     지켜볼 것 {c['watch']}")
        print(f"     덧붙임   {c['note']}")
        print()

    avg = sum(c["confidence"] for c in CLAIMS) / len(CLAIMS)
    print(f"평균 확신 {avg:.0%}. 절반 아래다.")

    print(
        "\n주장을 이렇게 적으면 두 가지가 생긴다.\n"
        "\n첫째, «무엇을 지켜보면 되는지»가 정해진다.\n"
        "막연히 「나중에 바뀔 수도」가 아니라 「이 값이 이렇게 되면 틀린다」다.\n"
        "\n둘째, 반증 조건을 못 쓰는 주장이 걸러진다.\n"
        "「그래프가 중요하다」 같은 문장은 반증 조건을 못 쓴다.\n"
        "무엇이 참이면 그게 틀리는지 말할 수 없기 때문이다. 그건 주장이 아니라 의견이다.\n"
        "\n이 책을 쓰면서 반증 조건을 못 쓴 문장이 꽤 많이 나왔고, 그건 전부 뺐다.\n"
        "\n다섯 개 중 5번이 제일 자신 없다. 20% 다.\n"
        "그런데 그건 이 책의 부제이기도 하다. 그래서 서문에 미리 밝혀 뒀다."
    )


if __name__ == "__main__":
    main()
