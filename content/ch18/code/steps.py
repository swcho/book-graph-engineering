"""
18장 공통 — 네 단계짜리 작업. 의존성 없음.

각 단계는 «실패할 수 있고», «시간이 걸리고», «토큰을 쓴다».
API 키 없이 돌리려고 결정론적 가짜로 만들었지만,
실패 확률과 비용은 제가 실제로 잰 값에 맞춰 두었다.
"""

import hashlib

STEPS = [
    # 이름, 걸리는 시간(초), 토큰, 실패 확률
    ("문서 찾기",   12, 3_200, 0.05),
    ("요약",         8, 5_100, 0.08),
    ("초안 작성",   31, 8_400, 0.18),
    ("검토",        14, 4_300, 0.10),
]

PRICE_PER_MTOK = 4_000     # 원


def fails(step_name, attempt, seed=0):
    """결정론적 «실패» 판정. 같은 입력이면 같은 결과가 나온다."""
    h = hashlib.sha256(f"{step_name}|{attempt}|{seed}".encode()).digest()
    r = int.from_bytes(h[:4], "big") / 0xFFFFFFFF
    p = dict((n, f) for n, _, _, f in STEPS)[step_name]
    return r < p


def cost(tokens):
    return tokens / 1_000_000 * PRICE_PER_MTOK
