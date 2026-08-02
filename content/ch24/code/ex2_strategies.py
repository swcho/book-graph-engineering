"""
예제 2 — 컨텍스트를 줄이는 네 방법. 토큰과 «남는 사실»을 같이 잰다.

    python3 ex2_strategies.py

의존성 없음. 대화 안에 «사실» 40개를 심어 두고,
줄이기를 거친 뒤 몇 개가 살아남는지 센다.
줄어든 토큰만 자랑하고 잃은 사실을 안 세면 절반만 잰 것이다.
"""

import random

N_TURNS = 60
FACT_EVERY = 2          # 두 턴에 한 번 «나중에 쓸 사실»이 나온다
TOKENS_PER_TURN = 300


def make_conversation(seed=11):
    rng = random.Random(seed)
    turns = []
    fid = 0
    for t in range(N_TURNS):
        has_fact = (t % FACT_EVERY == 0)
        if has_fact:
            fid += 1
        turns.append({
            "turn": t,
            "tokens": TOKENS_PER_TURN + rng.randint(-60, 120),
            "fact": fid if has_fact else None,
            # 뒤에서 실제로 참조되는 사실인지 (전부가 쓰이지는 않는다)
            "needed": has_fact and rng.random() < 0.62,
        })
    return turns


def all_facts(turns):
    return {t["fact"] for t in turns if t["needed"]}


def keep_all(turns):
    return turns


def last_n(turns, n=15):
    return turns[-n:]


def summarize_old(turns, keep=15, ratio=0.12, fact_survival=0.6):
    """오래된 부분을 요약한다. 요약은 짧지만 사실을 일부 잃는다."""
    old, recent = turns[:-keep], turns[-keep:]
    rng = random.Random(3)
    kept = [t for t in old if t["fact"] and rng.random() < fact_survival]
    summary_tokens = int(sum(t["tokens"] for t in old) * ratio)
    block = [{"turn": -1, "tokens": summary_tokens, "fact": None, "needed": False}]
    # 요약 안에 살아남은 사실을 표시용으로 붙인다
    for t in kept:
        block.append({"turn": -1, "tokens": 0, "fact": t["fact"],
                      "needed": t["needed"]})
    return block + recent


def offload(turns, keep=15):
    """오래된 부분은 밖에 저장하고, 색인만 남긴다. 필요하면 꺼내 온다."""
    old, recent = turns[:-keep], turns[-keep:]
    index = [{"turn": -1, "tokens": 12, "fact": t["fact"], "needed": t["needed"]}
             for t in old if t["fact"]]
    return index + recent


def measure(name, turns, ref_facts):
    tokens = sum(t["tokens"] for t in turns)
    facts = {t["fact"] for t in turns if t["needed"]}
    return name, tokens, len(facts), len(ref_facts)


def main():
    conv = make_conversation()
    ref = all_facts(conv)
    base = sum(t["tokens"] for t in conv)

    print(f"{N_TURNS}턴 대화, 원본 {base:,} 토큰. "
          f"나중에 실제로 필요한 사실 {len(ref)}개.\n")
    print(f"{'방법':<22}{'토큰':>9}{'절감':>8}{'남은 사실':>10}{'사실 보존율':>12}")
    print("-" * 62)

    rows = [
        measure("아무것도 안 함", keep_all(conv), ref),
        measure("최근 15턴만", last_n(conv), ref),
        measure("오래된 것 요약", summarize_old(conv), ref),
        measure("밖에 저장 + 색인", offload(conv), ref),
    ]
    for name, tok, kept, total in rows:
        cut = 1 - tok / base
        print(f"{name:<22}{tok:>9,}{cut:>7.0%}{kept:>10}{kept / total:>11.0%}")

    print(
        "\n«최근 15턴만»이 제일 많이 줄인다. 그리고 제일 많이 잃는다.\n"
        "쓸 만한 방법처럼 보이는 이유는 대부분의 턴에서 «최근»만 쓰기 때문이다.\n"
        "필요한 사실이 30턴 전에 나온 그 한 번에 무너진다.\n"
        "\n요약은 중간이다. 토큰도 줄이고 사실도 어느 정도 남긴다.\n"
        "다만 «어느 정도»가 얼마인지는 요약 프롬프트에 달렸고, 재 보기 전에는 모른다.\n"
        "\n밖에 저장하기가 사실 보존에서 이긴다. 색인만 남기고 본문은 밖에 두니까.\n"
        "공짜는 아니다. 꺼내 오는 «조회»가 한 번 더 들어간다.\n"
        "그 조회가 틀리면(엉뚱한 걸 꺼내 오면) 요약보다 나쁠 수도 있다.\n"
        "\n표를 만들 때 «절감»만 보지 마시라. 오른쪽 두 칸이 없으면 절반만 잰 것이다."
    )


if __name__ == "__main__":
    main()
