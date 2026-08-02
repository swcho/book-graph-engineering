"""
예제 5 — 문서가 바뀌면 트리플도 바뀐다. 무엇을 지우고 무엇을 남길까.

    python3 ex5_incremental.py

의존성 없음.
"""

V1 = {
    ("d01", "가온테크", "체결", "C-2025-118"),
    ("d01", "C-2025-118", "담당", "김하늘"),
    ("d01", "C-2025-118", "상대", "나루소프트"),
}
# 문서가 수정됐다. 담당자가 바뀌었고, 금액이 추가됐다.
V2 = {
    ("d01", "가온테크", "체결", "C-2025-118"),
    ("d01", "C-2025-118", "담당", "박서준"),
    ("d01", "C-2025-118", "상대", "나루소프트"),
    ("d01", "C-2025-118", "금액", "5000000"),
}
# 사람이 손으로 추가한 것 — 문서에는 없다
MANUAL = {
    ("manual", "C-2025-118", "비고", "갱신 협의 중"),
    ("manual", "C-2025-118", "담당", "김하늘"),   # 사람이 «김하늘이 맞다»고 정정
}


def naive_replace(old, new, doc):
    """흔한 방법: 그 문서에서 나온 것 전부 지우고 다시 넣는다."""
    kept = {t for t in old if t[0] != doc}
    return kept | new


def careful_merge(old, new, manual, doc):
    """사람이 손댄 것은 지키고, 나머지만 교체한다."""
    manual_keys = {(t[1], t[2]) for t in manual}
    kept = {t for t in old if t[0] != doc}
    incoming = {t for t in new if (t[1], t[2]) not in manual_keys}
    conflicts = {t for t in new if (t[1], t[2]) in manual_keys}
    return kept | incoming, conflicts


def show(title, s):
    print(f"\n{title}")
    for t in sorted(s):
        print(f"    [{t[0]:<7}] {t[1]:<12} {t[2]:<6} {t[3]}")


def main():
    old = V1 | MANUAL
    show("현재 상태 (문서 추출 + 사람 입력)", old)
    show("문서가 수정되어 다시 추출한 결과", V2)

    naive = naive_replace(old, V2, "d01")
    show("방법 A — 그 문서 것 전부 지우고 교체", naive)
    print("    → 사람이 정정한 «담당: 김하늘»이 살아 있다. 그런데...")
    dup = [t for t in naive if t[2] == "담당"]
    print(f"    → 담당이 {len(dup)}개가 됐다: "
          f"{[t[3] for t in dup]}  ← 충돌이 조용히 남는다")

    careful, conflicts = careful_merge(old, V2, MANUAL, "d01")
    show("방법 B — 사람이 손댄 항목은 지키고 충돌만 표시", careful)
    print(f"    → 충돌 {len(conflicts)}건을 사람에게 보낸다: "
          f"{[(t[2], t[3]) for t in conflicts]}")

    print(
        "\n방법 A 는 «담당»이 둘이 되고 아무도 모른다.\n"
        "질의가 둘 다 돌려주거나, 하나만 골라 주는데 어느 쪽인지 예측이 안 된다.\n"
        "\n방법 B 는 충돌을 드러낸다. 그리고 사람 입력을 함부로 덮지 않는다.\n"
        "\n핵심은 «출처를 트리플마다 저장해 두는 것»이다.\n"
        "출처가 없으면 무엇이 자동이고 무엇이 사람 것인지 구분할 수 없고,\n"
        "구분할 수 없으면 재추출할 때마다 사람 손댄 게 날아간다.\n"
        "\n제가 이걸 세 번 겪었다. 세 번째에야 출처를 저장하기 시작했다."
    )


if __name__ == "__main__":
    main()
