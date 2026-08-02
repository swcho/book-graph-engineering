"""
예제 4 — 남의 어휘를 가져다 쓸까, 우리 걸 만들까.

    python3 ex4_reuse_or_build.py

의존성 없음.
"""

# 우리가 필요한 개념과, 공개 어휘에 이미 있는 것
NEEDED = {
    "제품":      {"공개어휘": "schema.org/Product",      "적합도": 0.9},
    "공급사":    {"공개어휘": "schema.org/Organization", "적합도": 0.8},
    "부품":      {"공개어휘": "schema.org/Product",      "적합도": 0.4},
    "리콜":      {"공개어휘": None,                       "적합도": 0.0},
    "대체가능":  {"공개어휘": None,                       "적합도": 0.0},
    "납품":      {"공개어휘": "schema.org/seller",        "적합도": 0.5},
}

THRESHOLD = 0.7


def main():
    reuse, build, wrap = [], [], []
    for term, info in NEEDED.items():
        if info["공개어휘"] is None:
            build.append(term)
        elif info["적합도"] >= THRESHOLD:
            reuse.append((term, info["공개어휘"]))
        else:
            wrap.append((term, info["공개어휘"], info["적합도"]))

    print(f"그대로 가져다 쓴다 ({len(reuse)}개)")
    for t, v in reuse:
        print(f"  {t:<8} → {v}")

    print(f"\n비슷한데 안 맞는다 — 우리 것으로 만들고 «대략 같음»만 걸어 둔다 ({len(wrap)}개)")
    for t, v, s in wrap:
        print(f"  {t:<8} ~ {v}  (적합도 {s})")

    print(f"\n공개 어휘에 없다 — 만든다 ({len(build)}개)")
    for t in build:
        print(f"  {t}")

    print(
        "\n«부품»이 흥미롭다. schema.org 에도 Product 가 있지만 뜻이 다르다.\n"
        "우리에게 부품은 «다른 제품 안에 들어가는 것»이고, 판매 단위가 아니다.\n"
        "\n여기서 두 가지 실수가 가능하다.\n"
        "  (가) 억지로 맞춰 쓴다 → 나중에 «부품인데 왜 가격이 있지» 같은 혼란이 생긴다\n"
        "  (나) 아예 무시하고 다 새로 만든다 → 밖과 데이터를 주고받을 때 매번 변환한다\n"
        "\n중간이 답이다. 우리 것으로 만들되, 공개 어휘와 «대략 같음»을 걸어 둔다.\n"
        "RDF 라면 owl:sameAs 나 skos:closeMatch, LPG 라면 속성으로 매핑 표를 둔다.\n"
        "\n판단 기준 한 줄: 적합도 0.7 을 넘으면 가져다 쓰고, 아니면 만들고 이어 둔다.\n"
        "0.7 은 제 감이다. 중요한 건 «숫자를 정해 두고 매번 같은 기준으로 판단하는 것»이다."
    )


if __name__ == "__main__":
    main()
