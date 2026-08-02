"""
예제 1 — 재시도를 어떻게 하느냐로 부하가 몇 배 달라진다.

    python3 ex1_backoff.py

의존성 없음. 클라이언트 200개가 동시에 실패를 겪었을 때
어느 초에 요청이 몰리는지 센다.
"""

import random

N_CLIENTS = 200
MAX_TRIES = 5
BASE = 1.0          # 초
CAP = 30.0
BUCKET = 0.25          # 이 간격으로 도착 요청을 센다
SERVER_CAPACITY = 10   # 한 구간에 이만큼만 받아 준다 (초당 40건)


def schedule_fixed(_rng):
    """고정 간격 — 1초마다 다시."""
    return [BASE * (i + 1) for i in range(MAX_TRIES)]


def schedule_exp(_rng):
    """지수 백오프 — 1, 2, 4, 8, 16초."""
    t, out = 0.0, []
    for i in range(MAX_TRIES):
        t += min(BASE * (2 ** i), CAP)
        out.append(t)
    return out


def schedule_jitter(rng):
    """지수 백오프 + 흔들기 — 0~대기시간 사이 무작위."""
    t, out = 0.0, []
    for i in range(MAX_TRIES):
        t += rng.uniform(0, min(BASE * (2 ** i), CAP))
        out.append(t)
    return out


def simulate(sched, seed):
    rng = random.Random(seed)
    buckets = {}
    for _ in range(N_CLIENTS):
        for t in sched(rng):
            k = int(t / BUCKET)
            buckets[k] = buckets.get(k, 0) + 1
    return buckets


def main():
    print(f"클라이언트 {N_CLIENTS}개가 «동시에» 실패했다.\n"
          f"{BUCKET}초 구간마다 도착한 요청을 센다. 서버는 한 구간에 {SERVER_CAPACITY}건까지 받는다.\n")
    print(f"{'전략':<22}{'구간 최대':>10}{'용량 초과 구간':>16}{'총 요청':>10}")
    print("-" * 64)

    for name, sched in (("고정 간격 1초", schedule_fixed),
                        ("지수 백오프", schedule_exp),
                        ("지수 백오프 + 흔들기", schedule_jitter)):
        b = simulate(sched, seed=42)
        peak = max(b.values())
        over = sum(1 for v in b.values() if v > SERVER_CAPACITY)
        total = sum(b.values())
        print(f"{name:<22}{peak:>10}{over:>16}{total:>10}")

    print(
        "\n총 요청 수는 셋 다 같다. 1000건이다.\n"
        "다른 건 «언제» 오느냐뿐인데, 그것만으로 서버가 죽고 산다.\n"
        "\n고정 간격은 200개가 같은 구간에 몰린다. 서버가 이미 아픈데 20배를 때린다.\n"
        "지수 백오프도 똑같이 몰린다. 다 같이 1초 뒤, 다 같이 3초 뒤에 온다.\n"
        "간격만 벌렸을 뿐 «다 같이»는 그대로다. 이게 함정이다.\n"
        "\n흔들기(jitter)가 이걸 푼다. 대기 시간을 0~계산값 사이에서 무작위로 뽑는다.\n"
        "한 줄인데 봉우리가 사라진다.\n"
        "\n한 가지 더. 흔들기를 쓰면 첫 재시도가 «더 빨리» 오기도 한다.\n"
        "0~1초 사이에서 뽑으니 평균 0.5초다. 고정 간격 1초보다 이르다.\n"
        "그래서 흔들기는 늦추는 장치가 아니라 «흩는» 장치다."
    )


if __name__ == "__main__":
    main()
