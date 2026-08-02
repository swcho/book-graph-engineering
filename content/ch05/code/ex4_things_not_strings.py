"""
예제 4 — 문자열이 아니라 사물. 2012년 선언이 실제로 무슨 뜻이었나.

    python3 ex4_things_not_strings.py

의존성 없음.
"""

# 같은 이름을 가진 서로 다른 사물 셋. 각자 다른 술어를 갖는다.
THINGS = {
    "t1": {"name": "타지마할", "type": "건물", "props": {
        "위치": "인도 아그라", "완공": "1653", "입장료": "1,100루피"}},
    "t2": {"name": "타지마할", "type": "음악가", "props": {
        "장르": "블루스", "활동시작": "1968", "본명": "헨리 세인트클레어 프레드릭스"}},
    "t3": {"name": "타지마할", "type": "식당", "props": {
        "지역": "서울 이태원", "영업시간": "11:00-22:00", "평점": "4.2"}},
}

DOCS = [
    "타지마할은 인도 아그라에 있는 무굴 제국의 묘당이다.",
    "타지마할의 앨범은 블루스와 카리브 음악을 섞었다.",
    "이태원 타지마할은 저녁 예약이 어렵다.",
    "타지마할 입장료가 올해 인상되었다.",
]


def string_search(q):
    return [d for d in DOCS if all(w in d for w in q.split())]


def thing_search(q):
    """질문에 나온 낱말이 어느 사물의 «술어»와 겹치는지 본다."""
    words = q.split()
    scored = []
    for tid, t in THINGS.items():
        if t["name"] not in q:
            continue
        hit = sum(1 for w in words for k in t["props"] if k in w or w in k)
        scored.append((hit, tid, t))
    scored.sort(reverse=True, key=lambda x: x[0])
    return scored


def main():
    q = "타지마할 입장료"
    print(f"질문: {q}\n")

    print("문자열 검색 — 겹치는 문서를 준다")
    for d in string_search("타지마할"):
        print("  -", d)
    print("  → 건물, 음악가, 식당이 한 목록에 섞인다. 고르는 건 사람 몫이다.")

    print("\n사물 검색 — 어느 사물인지부터 정한다")
    for hit, tid, t in thing_search(q):
        mark = "★" if hit else " "
        print(f"  {mark} {tid} {t['type']:<4} 술어와 겹침 {hit}개  {list(t['props'])}")

    best = thing_search(q)[0]
    print(f"\n확정: {best[2]['type']}")
    for k, v in best[2]["props"].items():
        print(f"    {k}: {v}")

    print(
        "\n«입장료»라는 낱말을 술어로 가진 사물이 하나뿐이라 답이 정해졌다.\n"
        "문자열에는 이런 손잡이가 없다. 그래서 2012년 선언의 핵심은\n"
        "«더 많이 저장하자»가 아니라 «사물마다 다른 술어를 갖게 하자»였다.\n"
        "\n술어 목록이 곧 그 사물의 정체다. 이 생각은 4부에서 도구 라우팅으로 돌아온다.\n"
        "에이전트가 어떤 도구를 부를지 고르는 일도 «어떤 술어를 가졌나»를 보는 일이다."
    )


if __name__ == "__main__":
    main()
