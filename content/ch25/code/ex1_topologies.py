"""
예제 1 — 같은 일을 여섯 가지 위상으로. 무엇이 달라지는가.

    python3 ex1_topologies.py

의존성 없음. 「문서 8편을 읽고 보고서 한 장을 쓴다」는 같은 작업을
여섯 가지 연결 방식으로 돌리고 지연·비용·품질을 나란히 놓는다.
"""

DOCS = 8
READ_MS, READ_TOK = 900, 2_400        # 문서 한 편 읽기
WRITE_MS, WRITE_TOK = 1_800, 3_200    # 보고서 한 장 쓰기
CHECK_MS, CHECK_TOK = 700, 1_100      # 검토 한 번
ROUTE_MS, ROUTE_TOK = 300, 400        # 라우팅 판단 한 번
PAR = 4                               # 동시에 돌릴 수 있는 수


def 경로():
    """파이프라인. 한 줄로 죽 이어진다."""
    ms = DOCS * READ_MS + WRITE_MS
    tok = DOCS * READ_TOK + WRITE_TOK
    return ms, tok, 0.71, "단순. 느리다."


def 이분합류():
    """팬아웃-팬인. 문서를 나눠 읽고 합친다."""
    waves = -(-DOCS // PAR)
    ms = waves * READ_MS + WRITE_MS
    tok = DOCS * READ_TOK + WRITE_TOK
    return ms, tok, 0.71, "빠르다. 토큰은 같다."


def 성형():
    """감독자-작업자. 감독자가 매번 다음 일을 정한다."""
    waves = -(-DOCS // PAR)
    ms = waves * (ROUTE_MS + READ_MS) + ROUTE_MS + WRITE_MS
    tok = (waves + 1) * ROUTE_TOK + DOCS * READ_TOK + WRITE_TOK
    return ms, tok, 0.78, "판단이 붙는다. 감독자가 병목."


def 순환():
    """생성-검증. 검토가 통과할 때까지 돈다(여기서는 3회)."""
    rounds = 3
    waves = -(-DOCS // PAR)
    ms = waves * READ_MS + rounds * (WRITE_MS + CHECK_MS)
    tok = DOCS * READ_TOK + rounds * (WRITE_TOK + CHECK_TOK)
    return ms, tok, 0.89, "품질이 오른다. 값이 비싸다."


def 동적엣지():
    """라우터. 문서 종류를 보고 다른 처리기로 보낸다."""
    waves = -(-DOCS // PAR)
    ms = ROUTE_MS + waves * READ_MS + WRITE_MS
    tok = ROUTE_TOK + DOCS * READ_TOK + WRITE_TOK
    return ms, tok, 0.81, "쉬운 건 싸게, 어려운 건 비싸게."


def 트리():
    """계층적 위임. 중간 관리자가 부분 보고서를 만든다."""
    groups = 2
    per = DOCS // groups
    ms = (ROUTE_MS + (-(-per // PAR)) * READ_MS + WRITE_MS) + WRITE_MS
    tok = groups * (ROUTE_TOK + per * READ_TOK + WRITE_TOK) + WRITE_TOK
    return ms, tok, 0.84, "부분 요약이 남는다. 중간 손실도."


def main():
    print(f"같은 작업(문서 {DOCS}편 → 보고서 1장)을 여섯 위상으로.\n")
    print(f"{'위상':<12}{'지연(ms)':>10}{'토큰':>9}{'품질':>7}"
          f"{'토큰당 품질':>13}  성격")
    print("-" * 82)
    rows = []
    for name, fn in (("경로", 경로), ("이분·합류", 이분합류), ("성형", 성형),
                     ("순환", 순환), ("동적 엣지", 동적엣지), ("트리", 트리)):
        ms, tok, q, note = fn()
        rows.append((name, ms, tok, q))
        print(f"{name:<12}{ms:>10,}{tok:>9,}{q:>7.2f}"
              f"{q / tok * 10000:>13.3f}  {note}")

    fast = min(rows, key=lambda r: r[1])
    cheap = min(rows, key=lambda r: r[2])
    best = max(rows, key=lambda r: r[3])
    print(f"\n제일 빠른 것 {fast[0]}, 제일 싼 것 {cheap[0]}, 품질 1등 {best[0]}.")
    print("(경로와 이분·합류는 토큰이 같다. 나눠 읽는다고 읽는 양이 주는 게 아니라서.)")

    print(
        "\n«좋은 위상»은 없다. 무엇을 포기할지가 다를 뿐이다.\n"
        "\n경로는 8번을 차례로 읽어서 8,  이분·합류는 나눠 읽어서 2 물결이다.\n"
        "토큰은 똑같다. 나눠 읽는다고 읽는 양이 줄지는 않으니까.\n"
        "\n순환만 품질이 크게 오른다. 그리고 토큰이 제일 많이 든다.\n"
        "«토큰당 품질» 칸으로 보면 순환이 오히려 아래쪽이다.\n"
        "품질을 돈으로 산 것이지 공짜로 얻은 게 아니다.\n"
        "\n고르는 순서는 이렇다.\n"
        "  1. 품질 하한이 있나 → 있으면 순환을 넣는다\n"
        "  2. 지연 상한이 있나 → 있으면 이분·합류로 편다\n"
        "  3. 입력 종류가 갈리나 → 갈리면 동적 엣지\n"
        "  4. 다 아니면 경로. 제일 단순한 게 제일 오래 산다."
    )


if __name__ == "__main__":
    main()
