# %% [markdown]
# # FOREVER 센티널 부등호 함정 — `query()`에서 한 시간 헤맨 이유
#
# 이중 시간(bi-temporal) 저장소는 각 사실(fact)에 **기록 시간 구간**을 붙인다.
# 아직 정정·갱신되지 않은 "열린" 기록은 `tx_to = FOREVER`(= 9999-12-31)로 표시한다.
#
# 기록 시간 필터는 반열린 구간으로 검사한다:
#
# $$tx\_from \le tx\_at < tx\_to$$
#
# 함정: "지금 아는 대로"를 조회하려고 `tx_at = FOREVER`를 넣으면,
# 열린 기록의 `tx_to`도 FOREVER라서 $FOREVER < FOREVER$ 가 **거짓**이 되고,
# 정작 살아 있는 기록이 전부 걸러진다.

# %%
# 필요 패키지: plotly, kaleido (시각화 셀에서만 사용. 나머지는 표준 라이브러리)
from datetime import date

FOREVER = date(9999, 12, 31)


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# 미니 저장소: (s, p)에 대한 사실 두 건.
# 첫 기록은 3/10에 정정되어 닫혔고(tx_to=3/10), 정정본은 아직 열려 있다(tx_to=FOREVER).
facts = [
    {"value": "김대리", "tx_from": date(2024, 3, 1), "tx_to": date(2024, 3, 10)},
    {"value": "박과장", "tx_from": date(2024, 3, 10), "tx_to": FOREVER},
]

# %% [markdown]
# ## 1. 함정 재현 — `tx_at=FOREVER`를 부등호에 그대로 태우면

# %%
def query_naive(facts, tx_at):
    """'지금'을 FOREVER로 표현해 부등호 하나로 처리하려는 (틀린) 시도."""
    return [f for f in facts if f["tx_from"] <= tx_at < f["tx_to"]]


print("tx_at=FOREVER →", query_naive(facts, FOREVER))
# 출력: tx_at=FOREVER → []
#   과거 기록은 tx_to=3/10이라 당연히 탈락하고,
#   살아 있는 기록마저 FOREVER < FOREVER 가 거짓이라 탈락 → 결과가 텅 빈다.

# %% [markdown]
# ## 2. 왜 그런가 — 경계값 비교를 직접 확인
#
# 반열린 구간 $[tx\_from,\ tx\_to)$ 은 오른쪽 끝점을 **포함하지 않는다**.
# `tx_at`이 정확히 그 끝점(FOREVER)에 놓이면 구간 밖이다.

# %%
print("FOREVER <  FOREVER :", FOREVER < FOREVER)
print("FOREVER <= FOREVER :", FOREVER <= FOREVER)
open_rec = facts[1]
print("tx_from <= FOREVER :", open_rec["tx_from"] <= FOREVER)   # 왼쪽 조건은 참인데
print("FOREVER <  tx_to   :", FOREVER < open_rec["tx_to"])      # 오른쪽 조건이 거짓
# 출력: FOREVER <  FOREVER : False
# 출력: FOREVER <= FOREVER : True
# 출력: tx_from <= FOREVER : True
# 출력: FOREVER <  tx_to   : False

# %% [markdown]
# ## 3. 고치기 — "지금"은 값이 아니라 `None` 센티널로
#
# 저자의 해법: `tx_at=None`이면 부등호를 아예 타지 않고
# **아직 안 닫힌 기록**(`tx_to == FOREVER`)만 동등 비교로 고른다.
# `tx_at`에 실제 날짜가 오면 그때만 반열린 구간 비교를 쓴다.

# %%
def query_fixed(facts, tx_at=None):
    out = []
    for f in facts:
        if tx_at is None:
            if f["tx_to"] != FOREVER:      # 이미 정정·갱신된 기록은 뺀다
                continue
        elif not (f["tx_from"] <= tx_at < f["tx_to"]):
            continue
        out.append(f)
    return out


print("tx_at=None(지금)      →", [f["value"] for f in query_fixed(facts)])
print("tx_at=2024-03-05(과거) →", [f["value"] for f in query_fixed(facts, date(2024, 3, 5))])
print("tx_at=2024-03-20      →", [f["value"] for f in query_fixed(facts, date(2024, 3, 20))])
# 출력: tx_at=None(지금)      → ['박과장']
# 출력: tx_at=2024-03-05(과거) → ['김대리']
# 출력: tx_at=2024-03-20      → ['박과장']
#   '지금'은 열린 기록만, 과거 시점은 그 시점에 알고 있던 기록이 잡힌다.

# %% [markdown]
# ## 4. 시각화 — `tx_at=FOREVER`는 정확히 "포함 안 되는 끝점" 위에 선다
#
# 반열린 구간 $[tx\_from,\ FOREVER)$ 을 수직선으로 그리면,
# `tx_at=FOREVER`는 열린 끝점(○) 바로 위에 놓여 구간 밖으로 판정된다.

# %%
import plotly.graph_objects as go

# 개념도라서 축은 일부러 스키마틱한 숫자 축을 쓴다 (9999년을 날짜축에 그리면 다 뭉개짐)
X = {"2024-03-01": 0, "2024-03-10": 2, "…": 4, "FOREVER": 6}

fig = go.Figure()

rows = [
    ("김대리 (닫힌 기록)", X["2024-03-01"], X["2024-03-10"], "#8a8a8a"),
    ("박과장 (열린 기록)", X["2024-03-10"], X["FOREVER"], "#2b7de9"),
]
for i, (name, x0, x1, color) in enumerate(rows):
    y = 1 - i
    fig.add_trace(go.Scatter(x=[x0, x1], y=[y, y], mode="lines",
                             line=dict(color=color, width=10), name=name))
    fig.add_trace(go.Scatter(x=[x0], y=[y], mode="markers", showlegend=False,
                             marker=dict(color=color, size=14, symbol="circle")))
    # 반열린 구간의 오른쪽 끝: 포함 안 됨 → 속 빈 원
    fig.add_trace(go.Scatter(x=[x1], y=[y], mode="markers", showlegend=False,
                             marker=dict(color="white", size=14, symbol="circle",
                                         line=dict(color=color, width=3))))

# tx_at = FOREVER 조회 지점: 열린 끝점과 정확히 같은 자리
fig.add_trace(go.Scatter(x=[X["FOREVER"]], y=[0.5], mode="markers+text",
                         marker=dict(color="#d1342f", size=16, symbol="x"),
                         text=["tx_at = FOREVER"], textposition="top center",
                         textfont=dict(color="#d1342f"), name="조회 시점"))
fig.add_vline(x=X["FOREVER"], line=dict(color="#d1342f", dash="dot", width=1))

fig.add_annotation(x=X["FOREVER"], y=-0.55, showarrow=False, font=dict(size=12),
                   text="○ = tx_to (미포함 끝점) → FOREVER < FOREVER 는 거짓, 구간 밖")

fig.update_xaxes(tickvals=list(X.values()), ticktext=list(X.keys()),
                 title="기록 시간(tx) — 스키마틱", range=[-0.5, 7.2])
fig.update_yaxes(tickvals=[1, 0], ticktext=["김대리", "박과장"], range=[-0.9, 1.9])
fig.update_layout(title="반열린 구간 [tx_from, tx_to) 와 tx_at=FOREVER 의 위치",
                  width=820, height=380, template="plotly_white",
                  legend=dict(orientation="h", y=1.12))

_show(fig)
import os
fig.write_image(os.path.join(os.path.dirname(os.path.abspath(__file__))
                             if "__file__" in globals() else ".", "expy.png"), scale=2)
# 출력: (같은 폴더에 expy.png 저장)

# %% [markdown]
# ## 정리
#
# - FOREVER는 **저장용 센티널**(열린 구간의 표시)이지, **조회용 시점 값**이 아니다.
# - 반열린 구간 $tx\_from \le tx\_at < tx\_to$ 에 `tx_at=FOREVER`를 넣으면
#   열린 기록에서 $FOREVER < FOREVER$ 가 거짓 → 아무것도 안 걸린다.
# - "지금 아는 대로"는 `tx_at=None`으로 받아서 `tx_to == FOREVER` 동등 비교로 처리한다.
