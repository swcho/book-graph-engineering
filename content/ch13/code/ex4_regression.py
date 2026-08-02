"""
예제 4 — 회귀 테스트. 스키마를 고쳤을 때 «조용히 달라지는 것»을 잡는다.

    python3 ex4_regression.py

의존성 없음.
«위반 0건»만 보면 놓치는 게 있다. 답이 달라지는 것.
"""

import json
from collections import Counter

# 골든 데이터셋 — 손으로 만든 작은 표본. 답을 사람이 확인해 뒀다.
GOLDEN = [
    {"id": "P1", "type": "부품", "category": "체결", "supplier": "가온테크"},
    {"id": "P2", "type": "부품", "category": "전자", "supplier": "나루소프트"},
    {"id": "P3", "type": "부품", "category": None,   "supplier": "가온테크"},
    {"id": "D1", "type": "제품", "parts": ["P1", "P2"], "recalled": True},
    {"id": "D2", "type": "제품", "parts": ["P2", "P3"], "recalled": False},
]

# 역량 질의 — 12장에서 뽑은 그것. 이 답이 바뀌면 안 된다.
def q_recalled_with(rows, part):
    return sorted(r["id"] for r in rows
                  if r["type"] == "제품" and r.get("recalled")
                  and part in r.get("parts", []))

def q_by_supplier(rows, sup):
    return sorted(r["id"] for r in rows
                  if r["type"] == "부품" and r.get("supplier") == sup)

def q_uncategorized(rows):
    return sorted(r["id"] for r in rows
                  if r["type"] == "부품" and not r.get("category"))

QUERIES = {
    "P2 를 쓴 리콜 제품":   lambda rows: q_recalled_with(rows, "P2"),
    "가온테크 납품 부품":    lambda rows: q_by_supplier(rows, "가온테크"),
    "카테고리 없는 부품":    q_uncategorized,
}

# 기대값 — 처음 만들 때 사람이 확인하고 고정한다
EXPECTED = {name: fn(GOLDEN) for name, fn in QUERIES.items()}

# 스키마 변경 — «카테고리 없음»을 None 대신 «미분류»로 채우기로 했다
def migrate(rows):
    out = []
    for r in rows:
        r = dict(r)
        if r.get("type") == "부품" and not r.get("category"):
            r["category"] = "미분류"
        out.append(r)
    return out


def shape_stats(rows):
    return {"노드 수": len(rows),
            "타입 분포": dict(Counter(r["type"] for r in rows))}


def main():
    after = migrate(GOLDEN)

    print("=== 1. SHACL 류 형태 검사 ===")
    bad = [r for r in after if r["type"] == "부품" and not r.get("category")]
    print(f"  카테고리 누락: {len(bad)}건  → 통과\n")

    print("=== 2. 노드·엣지 수 검사 ===")
    b, a = shape_stats(GOLDEN), shape_stats(after)
    print(f"  전:  {json.dumps(b, ensure_ascii=False)}")
    print(f"  후:  {json.dumps(a, ensure_ascii=False)}")
    print(f"  {'통과' if b == a else '차이 있음'}\n")

    print("=== 3. 역량 질의 검사 ===")
    failed = 0
    for name, fn in QUERIES.items():
        got, want = fn(after), EXPECTED[name]
        ok = got == want
        failed += 0 if ok else 1
        mark = "통과" if ok else "실패"
        print(f"  [{mark}] {name}")
        if not ok:
            print(f"        전: {want}")
            print(f"        후: {got}")

    print(
        f"\n앞의 두 검사는 통과했는데 세 번째에서 {failed}건이 걸렸다.\n"
        "\n«카테고리 없음»을 «미분류»로 채웠더니 «카테고리 없는 부품» 질의가 빈 답을 낸다.\n"
        "데이터는 더 깨끗해졌고, 형태 검사도 통과하고, 노드 수도 그대로다.\n"
        "그런데 그 질의에 기대던 화면이 조용히 비었다.\n"
        "\n이게 회귀 테스트에 «질의»가 들어가야 하는 이유다.\n"
        "형태만 검사하면 «모양은 맞는데 뜻이 달라진» 변경을 못 잡는다."
    )


if __name__ == "__main__":
    main()
