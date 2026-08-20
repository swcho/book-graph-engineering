# 필요 패키지: plotly, kaleido  (pip install plotly kaleido)
# %% [markdown]
# # state_hash — 승인한 내용과 실행할 내용이 같은가
#
# 중단점(`interrupt`)은 그래프를 정상적으로 멈춘다. 사람은 사흘 뒤에 답해도 된다.
# 그런데 그 사흘 사이에 상태가 바뀔 수 있다.
#
# ```
# t0  멈춤 ── 보여 준 것: 금액 300,000 / 미개봉 / 첫 환불
#       ↓  (사흘)
# t1  "승인" ── 실행할 것: 금액 4,200,000 / 개봉 / 3회차
# ```
#
# 승인은 t0의 화면에 대해 났는데, 실행은 t1의 상태로 일어난다.
# `state_hash`는 이 둘이 같은지 실행 직전에 검증하는 장치다.
#
# 구조적으로는 **낙관적 동시성 제어**(버전 번호 대신 내용 해시),
# HTTP의 **ETag / If-Match → 412 Precondition Failed**,
# 그리고 **TOCTOU**(검사 시점과 사용 시점 사이의 창)와 같은 모양이다.

# %%
import hashlib
import json
import random

import plotly.graph_objects as go


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


SEED = 42
print("준비 완료")
# 출력: 준비 완료

# %% [markdown]
# ## 1. 정규 직렬화 + SHA-256으로 지문 만들기
#
# $$h = \mathrm{SHA256}\big(\mathrm{canonical}(\{f_i : i \in D\})\big)$$
#
# $D$는 **결정에 영향을 주는 필드 집합**이다.
# 키 순서나 공백이 흔들리면 내용이 같아도 지문이 달라지므로 정규화(`sort_keys`,
# 공백 없는 separator)가 필수다.

# %%
DECISION_FIELDS = ("order_id", "amount", "currency", "recipient", "reason_code")


def canonical(state: dict, fields: tuple) -> str:
    subset = {k: state[k] for k in fields if k in state}
    return json.dumps(subset, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def state_hash(state: dict, fields: tuple = DECISION_FIELDS) -> str:
    return hashlib.sha256(canonical(state, fields).encode("utf-8")).hexdigest()[:8]


# t0 — 사람에게 물어본 순간의 상태
state_t0 = {
    "order_id": "환불-A1024",
    "amount": 300_000,
    "currency": "KRW",
    "recipient": "kim-8821",
    "reason_code": "UNOPENED_FIRST",
    # 아래는 결정에 영향을 주지 않는 필드들
    "last_viewed_at": "2026-03-14T09:02Z",
    "session_id": "s-0001",
    "retry_count": 0,
    "render_ms": 47,
}

print("정규 직렬화:", canonical(state_t0, DECISION_FIELDS))
print("state_hash  :", state_hash(state_t0))
# 출력: 정규 직렬화: {"amount":300000,"currency":"KRW","order_id":"환불-A1024","reason_code":"UNOPENED_FIRST","recipient":"kim-8821"}
# 출력: state_hash  : 9fd1364a

# %% [markdown]
# ## 2. (a) 무관한 필드만 바뀐 경우 — 지문 동일
#
# 사람이 화면을 다시 열었고, 세션이 갱신됐고, 렌더링 시간이 달라졌다.
# 결정에는 아무 영향이 없다. 여기서 다시 물으면 그게 **경보 피로**의 시작이다.

# %%
state_noise = dict(state_t0)
state_noise.update({
    "last_viewed_at": "2026-03-17T11:40Z",
    "session_id": "s-9317",
    "retry_count": 3,
    "render_ms": 122,
})

print("t0 지문   :", state_hash(state_t0))
print("잡음 후   :", state_hash(state_noise))
print("같은가?   :", state_hash(state_t0) == state_hash(state_noise))
# 출력: t0 지문   : 9fd1364a
# 출력: 잡음 후   : 9fd1364a
# 출력: 같은가?   : True

# %% [markdown]
# ## 3. (b) 금액이 바뀐 경우 — 지문 변경
#
# 300,000원짜리 승인을 받아 놓고 4,200,000원을 내보내려는 상황이다.

# %%
state_t1 = dict(state_noise)
state_t1["amount"] = 4_200_000
state_t1["reason_code"] = "OPENED_THIRD"

print("t0 지문   :", state_hash(state_t0))
print("t1 지문   :", state_hash(state_t1))
print("같은가?   :", state_hash(state_t0) == state_hash(state_t1))

for k in DECISION_FIELDS:
    if state_t0[k] != state_t1[k]:
        print(f"  변경: {k}  {state_t0[k]!r} -> {state_t1[k]!r}")
# 출력: t0 지문   : 9fd1364a
# 출력: t1 지문   : 2ee11513
# 출력: 같은가?   : False
# 출력:   변경: amount  300000 -> 4200000
# 출력:   변경: reason_code  'UNOPENED_FIRST' -> 'OPENED_THIRD'

# %% [markdown]
# ## 4. 재개 지점의 검사 — 지문이 다르면 재질문
#
# HTTP로 치면 `If-Match` 불일치에 `412 Precondition Failed`를 돌려주는 자리다.
# 재질문할 때는 **무엇이 바뀌었는지 diff를 같이 보여 줘야** 한다.
# 「상태가 바뀌었습니다」만 띄우면 사람은 내용을 안 보고 다시 승인한다.

# %%
class ReAsk(Exception):
    pass


APPROVAL = {  # ex5_audit.py 의 approval 행 한 줄에 해당한다
    "thread_id": "환불-A1024",
    "actor": "kim",
    "decision": "승인",
    "shown": "금액 300,000 / 미개봉 / 첫 환불",
    "state_hash": state_hash(state_t0),
}


def resume(approval: dict, now: dict):
    h = state_hash(now)
    if h != approval["state_hash"]:
        diff = [(k, approval_state[k], now[k])
                for k in DECISION_FIELDS if approval_state[k] != now[k]]
        raise ReAsk(f"지문 불일치 {approval['state_hash']} != {h} / 변경 {diff}")
    return f"실행: {now['amount']:,}원 환불"


approval_state = state_t0

for label, st in (("잡음만 바뀐 상태", state_noise), ("금액이 바뀐 상태", state_t1)):
    try:
        print(f"{label}: {resume(APPROVAL, st)}")
    except ReAsk as e:
        print(f"{label}: 재질문 — {e}")
# 출력: 잡음만 바뀐 상태: 실행: 300,000원 환불
# 출력: 금액이 바뀐 상태: 재질문 — 지문 불일치 9fd1364a != 2ee11513 / 변경 [('amount', 300000, 4200000), ('reason_code', 'UNOPENED_FIRST', 'OPENED_THIRD')]

# %% [markdown]
# ## 5. 필드 범위를 넓히면 — 재질문율 폭증
#
# 필드 $i$가 대기 중에 바뀔 확률을 $p_i$, 서로 독립이라고 두면
# $k$개를 해시했을 때 재질문 확률은
#
# $$P_{\text{re-ask}}(k) = 1 - \prod_{i=1}^{k}(1 - p_i)$$
#
# $p_i$가 작아도 $k$가 커지면 곱이 빠르게 0으로 내려간다.
# 노이즈 필드 **하나**가 전체를 무력화한다.

# %%
# (필드명, 대기 중 변경 확률) — 앞쪽이 결정 필드, 뒤쪽이 무관 필드
FIELD_CHURN = [
    ("order_id",       0.000),
    ("currency",       0.001),
    ("recipient",      0.010),
    ("amount",         0.020),
    ("reason_code",    0.020),
    ("risk_score",     0.150),  # ← 여기서부터 결정과 무관
    ("retry_count",    0.450),
    ("session_id",     0.800),
    ("last_viewed_at", 0.950),
    ("render_ms",      0.990),
]

N_TRIALS = 20_000
rng = random.Random(SEED)

ks, sim_rates, ana_rates = [], [], []
for k in range(1, len(FIELD_CHURN) + 1):
    ps = [p for _, p in FIELD_CHURN[:k]]
    hits = sum(1 for _ in range(N_TRIALS) if any(rng.random() < p for p in ps))
    ana = 1.0
    for p in ps:
        ana *= (1 - p)
    ks.append(k)
    sim_rates.append(hits / N_TRIALS * 100)
    ana_rates.append((1 - ana) * 100)

print(f"{'k':>2} {'마지막 추가 필드':<16}{'시뮬%':>8}{'이론%':>8}")
for k, (name, _), s, a in zip(ks, FIELD_CHURN, sim_rates, ana_rates):
    print(f"{k:>2} {name:<16}{s:>8.2f}{a:>8.2f}")
# 출력:  k 마지막 추가 필드            시뮬%     이론%
# 출력:  1 order_id            0.00    0.00
# 출력:  2 currency            0.11    0.10
# 출력:  3 recipient           1.01    1.10
# 출력:  4 amount              2.97    3.08
# 출력:  5 reason_code         5.16    5.02
# 출력:  6 risk_score         19.15   19.26
# 출력:  7 retry_count        56.11   55.59
# 출력:  8 session_id         91.53   91.12
# 출력:  9 last_viewed_at     99.67   99.56
# 출력: 10 render_ms         100.00  100.00

# %% [markdown]
# 결정 필드 5개만 해시하면 재질문율은 약 5%다. 100건에 5건이면 사람이 실제로 읽는다.
#
# 여기에 `risk_score` 하나를 얹으면 19%, `retry_count`까지 넣으면 56%,
# 상태 전체를 해시하면 100%가 된다. **재개할 때마다 다시 묻는 시스템은
# 다시 묻지 않는 시스템과 결과가 같다** — 사람이 내용을 안 보고 승인하기 때문이다.
#
# 23.3의 「전부 사람이 보는 정책은 결국 아무도 안 보는 정책이 된다」와 같은 모양이다.

# %%
FATIGUE = 20.0  # 이 이상이면 경보 피로 구간으로 본다

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=ks, y=ana_rates, mode="lines+markers", name="이론값 1-∏(1-p)",
    line=dict(color="#2b6cb0", width=3), marker=dict(size=9),
))
fig.add_trace(go.Scatter(
    x=ks, y=sim_rates, mode="markers", name=f"시뮬레이션 (n={N_TRIALS:,}, seed={SEED})",
    marker=dict(size=13, symbol="x", color="#dd6b20"),
))
fig.add_hline(y=FATIGUE, line_dash="dash", line_color="#c53030",
              annotation_text=f"경보 피로 문턱 {FATIGUE:.0f}%",
              annotation_position="top left")
fig.add_vrect(x0=0.5, x1=5.5, fillcolor="#38a169", opacity=0.10, line_width=0,
              annotation_text="결정 필드만", annotation_position="top left")

fig.update_layout(
    title="해시 대상 필드 수 대비 재질문 비율",
    xaxis_title="해시에 포함한 필드 수 k (누적)",
    yaxis_title="재개 시 재질문 비율 (%)",
    template="plotly_white", width=980, height=560,
    legend=dict(x=0.02, y=0.98, bgcolor="rgba(255,255,255,0.8)"),
)
fig.update_xaxes(
    tickmode="array", tickvals=ks,
    ticktext=[f"{k}<br>{n}" for k, (n, _) in zip(ks, FIELD_CHURN)],
)
fig.update_yaxes(range=[-3, 105])

_show(fig)
fig.write_image("expy.png", scale=2)
print("expy.png 저장 완료")
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 6. 정리
#
# | 장치 | 역할 | 대응 개념 |
# |---|---|---|
# | `shown` | 사후 감사 — 화면에 무엇이 떠 있었나 | 감사 추적(audit trail) |
# | `state_hash` | 사전 차단 — 승인한 대상과 같은가 | ETag / If-Match, 낙관적 동시성 제어 |
# | 결정 필드만 해시 | 무관한 변경은 무시 | 약한 ETag `W/"..."` |
# | 지문 불일치 → 재질문 | 창이 열린 사이의 변경 검출 | 412 Precondition Failed, TOCTOU 방어 |
#
# 중단점이 시간의 창을 열어 준 대가로, 그 창 동안 대상이 바뀌지 않았음을
# 실행 직전에 확인해야 한다. 범위를 좁게 잡아야 이 장치가 살아 있다.
