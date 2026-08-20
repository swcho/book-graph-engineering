# %% [markdown]
# # `ex1_backoff.py`의 세 재시도 전략
#
# 질문: `ex1_backoff.py`의 세 재시도 전략은 무엇인가?
#
# 답: **고정 간격 1초**, **지수 백오프(1·2·4·8·16초)**, **지수 백오프 + 흔들기(0~계산값 사이 무작위)**.
#
# 클라이언트 200개가 «동시에» 실패한 뒤 각자 5번 재시도한다고 하자.
# 세 전략 모두 총 요청 수는 $200 \times 5 = 1000$건으로 같다.
# 다른 것은 오직 «언제 도착하느냐»다. 그 차이만으로 서버가 죽고 산다.
#
# | 전략 | $i$번째 재시도까지의 누적 대기 | 특징 |
# |---|---|---|
# | 고정 간격 | $t_i = 1 \cdot (i+1)$ | 매초 200개가 한꺼번에 |
# | 지수 백오프 | $t_i = \sum_{k=0}^{i} \min(2^k, \text{CAP})$ | 간격은 벌어지지만 «다 같이»는 그대로 |
# | 지수 백오프 + 흔들기 | $t_i = \sum_{k=0}^{i} U\big(0,\ \min(2^k, \text{CAP})\big)$ | 봉우리가 흩어짐 |

# %%
# 필요 패키지: plotly, kaleido (시각화·PNG 저장용. 시뮬레이션 자체는 표준 라이브러리만 사용)
import random


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# ex1_backoff.py와 같은 상수
N_CLIENTS = 200        # 동시에 실패한 클라이언트 수
MAX_TRIES = 5          # 각자 5번 재시도
BASE = 1.0             # 기본 대기 (초)
CAP = 30.0             # 대기 상한
BUCKET = 0.25          # 이 간격(초)으로 도착 요청을 센다
SERVER_CAPACITY = 10   # 한 구간에 이만큼만 받아 준다 (초당 40건)

# %% [markdown]
# ## 1. 세 전략의 재시도 시각표
#
# 각 함수는 한 클라이언트의 «재시도 도착 시각» 5개를 돌려준다.

# %%
def schedule_fixed(_rng):
    """고정 간격 — 1초마다 다시. 1, 2, 3, 4, 5초."""
    return [BASE * (i + 1) for i in range(MAX_TRIES)]


def schedule_exp(_rng):
    """지수 백오프 — 대기 1, 2, 4, 8, 16초 (누적 1, 3, 7, 15, 31초)."""
    t, out = 0.0, []
    for i in range(MAX_TRIES):
        t += min(BASE * (2 ** i), CAP)
        out.append(t)
    return out


def schedule_jitter(rng):
    """지수 백오프 + 흔들기 — 0~계산값 사이 무작위로 뽑는다."""
    t, out = 0.0, []
    for i in range(MAX_TRIES):
        t += rng.uniform(0, min(BASE * (2 ** i), CAP))
        out.append(t)
    return out


print("고정 간격  :", schedule_fixed(None))
print("지수 백오프:", schedule_exp(None))
print("흔들기 예시:", [round(t, 2) for t in schedule_jitter(random.Random(42))])
# 출력:
# 고정 간격  : [1.0, 2.0, 3.0, 4.0, 5.0]
# 지수 백오프: [1.0, 3.0, 7.0, 15.0, 31.0]
# 흔들기 예시: [0.64, 0.69, 1.79, 3.58, 15.36]

# %% [markdown]
# 흔들기의 첫 재시도는 $U(0,1)$에서 뽑으니 평균 $0.5$초 —
# 고정 간격 1초보다 **더 빨리** 오기도 한다.
# 흔들기는 늦추는 장치가 아니라 «흩는» 장치다.

# %% [markdown]
# ## 2. 시뮬레이션 — 클라이언트 200개 × 재시도 5회
#
# 0.25초 구간마다 도착 요청을 세고, 구간 최대(봉우리)와
# 서버 용량(구간당 10건)을 넘긴 구간 수를 비교한다.

# %%
def simulate(sched, seed):
    rng = random.Random(seed)
    buckets = {}
    for _ in range(N_CLIENTS):
        for t in sched(rng):
            k = int(t / BUCKET)
            buckets[k] = buckets.get(k, 0) + 1
    return buckets


STRATEGIES = [
    ("고정 간격 1초", schedule_fixed),
    ("지수 백오프", schedule_exp),
    ("지수 백오프 + 흔들기", schedule_jitter),
]

results = {name: simulate(sched, seed=42) for name, sched in STRATEGIES}

print(f"{'전략':<16}{'구간 최대':>8}{'용량 초과 구간':>10}{'총 요청':>8}")
print("-" * 48)
for name, b in results.items():
    peak = max(b.values())
    over = sum(1 for v in b.values() if v > SERVER_CAPACITY)
    total = sum(b.values())
    print(f"{name:<16}{peak:>10}{over:>12}{total:>10}")
# 출력:
# 전략                 구간 최대  용량 초과 구간    총 요청
# ------------------------------------------------
# 고정 간격 1초               200           5      1000
# 지수 백오프                 200           5      1000
# 지수 백오프 + 흔들기            83          27      1000

# %% [markdown]
# 총 요청은 셋 다 1000건으로 같다. 그런데:
#
# - **고정 간격**: 200개가 같은 구간에 몰린다. 용량 10짜리 서버에 20배를 때린다.
# - **지수 백오프**: 간격만 벌렸을 뿐, 다 같이 1초 뒤·3초 뒤에 온다. 봉우리 높이는 그대로 200. 이게 함정이다.
# - **흔들기**: 무작위 한 줄로 봉우리가 200 → 83으로 내려간다. 초과 구간 수는 늘지만 초과 «폭»이 작아 서버가 버틴다.
#   (여기서 83도 첫 재시도가 0~1초 좁은 구간에 몰린 탓이다. 이후 재시도부터는 봉우리가 급격히 낮아진다.)

# %% [markdown]
# ## 3. 시간축 도착 히스토그램 — 봉우리 비교

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

X_MAX = 32.0  # 지수 백오프 마지막 재시도(31초)까지 보이게

fig = make_subplots(
    rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.07,
    subplot_titles=[name for name, _ in STRATEGIES],
)

colors = ["#4269D0", "#EFB118", "#3CA951"]
for row, ((name, _), color) in enumerate(zip(STRATEGIES, colors), start=1):
    b = results[name]
    xs = [k * BUCKET for k in sorted(b)]
    ys = [b[k] for k in sorted(b)]
    fig.add_trace(
        go.Bar(x=xs, y=ys, width=BUCKET, marker_color=color, name=name, showlegend=False),
        row=row, col=1,
    )
    hline_kw = dict(y=SERVER_CAPACITY, line_dash="dot", line_color="#D9534F", row=row, col=1)
    if row == 1:
        hline_kw.update(annotation_text="서버 용량(구간당 10건)", annotation_position="top right")
    fig.add_hline(**hline_kw)

fig.update_layout(
    title="세 재시도 전략의 부하 봉우리 — 클라이언트 200개 × 재시도 5회",
    height=720, width=900, template="plotly_white",
    margin=dict(t=90),
)
fig.update_xaxes(range=[0, X_MAX], row=3, col=1, title_text="시간 (초)")
for row in (1, 2, 3):
    fig.update_yaxes(title_text="도착 요청 수", row=row, col=1)

_show(fig)

import os
_here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else "."
fig.write_image(os.path.join(_here, "expy.png"), scale=2)
print("expy.png 저장 완료")
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 4. 정리
#
# - `ex1_backoff.py`의 세 전략: **고정 간격 1초**, **지수 백오프(1·2·4·8·16초)**,
#   **지수 백오프 + 흔들기(0~계산값 사이 무작위)**.
# - 지수 백오프는 재시도 «간격»을 벌릴 뿐, 동시에 실패한 무리를 흩지는 못한다.
#   봉우리 높이는 고정 간격과 똑같이 200이다.
# - 흔들기(jitter)는 대기 시간을 $U(0, \min(2^k, \text{CAP}))$에서 뽑아
#   «다 같이»를 깨뜨린다. 봉우리가 200 → 83으로 내려가 재시도 폭풍(retry storm)을 막는다.
