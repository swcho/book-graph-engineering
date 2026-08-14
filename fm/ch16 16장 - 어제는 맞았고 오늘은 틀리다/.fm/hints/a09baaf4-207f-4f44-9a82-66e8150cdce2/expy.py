# %% [markdown]
# # `assert_fact()`의 겹침 처리 — 논리적 갱신 재현
#
# 이중 시간 저장소에서 사실 하나는 시간 축 두 개를 갖는다.
#
# - **유효 시간**: $[\text{valid\_from},\ \text{valid\_to})$ — 현실에서 참인 기간
# - **기록 시간**: $[\text{tx\_from},\ \text{tx\_to})$ — 시스템이 그렇게 알고 있던 기간
#
# 새 사실의 시작이 기존 사실의 유효 기간 안쪽에 떨어지면
# ($\text{vf}_{old} < \text{vf}_{new} < \text{vt}_{old}$),
# `assert_fact()`는 UPDATE 대신 세 동작으로 **논리적 갱신**을 만든다.
#
# 1. `_retire(f, tx_at)` — 기존 기록의 `tx_to`를 닫는다 (물리 삭제 없음)
# 2. 같은 값을 잘린 유효 기간 $[\text{vf}_{old}, \text{vf}_{new})$로 재기록
# 3. 새 사실을 추가

# %%
# 필요 패키지: plotly, kaleido (시각화 셀에서만 사용. 저장소 로직은 의존성 없음)
from datetime import date

FOREVER = date(9999, 12, 31)


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# %% [markdown]
# ## 1. BiTemporalStore 미니 구현
#
# 책의 `bitemporal.py`에서 쓰기 경로만 그대로 가져온 축소판.

# %%
class BiTemporalStore:
    def __init__(self):
        self.facts = []  # dict: s, p, value, valid_from/to, tx_from/to

    def assert_fact(self, s, p, v, valid_from, tx_at, valid_to=FOREVER):
        """새 사실을 기록한다. 같은 (s, p)의 겹치는 기간은 유효 시간을 잘라 준다."""
        for f in self.facts:
            if (f["s"], f["p"]) != (s, p) or f["tx_to"] != FOREVER:
                continue  # 다른 사실이거나 이미 닫힌 기록은 건너뜀
            if f["valid_from"] < valid_from < f["valid_to"]:
                # 기존 사실의 유효 기간을 잘라 «논리적 갱신»을 만든다
                self._retire(f, tx_at)                      # (1) tx로 닫고
                self._append(s, p, f["value"],
                             f["valid_from"], valid_from, tx_at)  # (2) 잘라서 재기록
        self._append(s, p, v, valid_from, valid_to, tx_at)         # (3) 새 사실 추가

    def _append(self, s, p, v, vf, vt, tx):
        self.facts.append({"s": s, "p": p, "value": v,
                           "valid_from": vf, "valid_to": vt,
                           "tx_from": tx, "tx_to": FOREVER})

    def _retire(self, f, tx_at):
        f["tx_to"] = tx_at  # 물리 삭제가 아니라 기록 시간만 닫는다

    def query(self, s, p, valid_at, tx_at=None):
        out = []
        for f in self.facts:
            if (f["s"], f["p"]) != (s, p):
                continue
            if not (f["valid_from"] <= valid_at < f["valid_to"]):
                continue
            if tx_at is None:
                if f["tx_to"] != FOREVER:  # 이미 닫힌(갱신된) 기록은 뺀다
                    continue
            elif not (f["tx_from"] <= tx_at < f["tx_to"]):
                continue
            out.append(f)
        return out


def fmt(d):
    return "—" if d == FOREVER else d.isoformat()


def dump(st, title):
    print(f"\n{title}")
    print(f"    {'값':<8} {'유효':<24} {'기록'}")
    for f in st.facts:
        print(f"    {f['value']:<8} [{fmt(f['valid_from'])} ~ {fmt(f['valid_to']):<10}]"
              f"  [{fmt(f['tx_from'])} ~ {fmt(f['tx_to'])}]")


# %% [markdown]
# ## 2. 겹침 없는 첫 기록
#
# 3월 1일부터 김하늘이 담당. 우리는 4월 10일에 알았다.
# 겹치는 기존 기록이 없으니 행 하나만 생긴다.

# %%
D = date
st = BiTemporalStore()
st.assert_fact("가온테크", "담당", "김하늘", valid_from=D(2026, 3, 1), tx_at=D(2026, 4, 10))
dump(st, "assert_fact #1 후 — 행 1개")
# 출력:
# assert_fact #1 후 — 행 1개
#     값       유효                       기록
#     김하늘      [2026-03-01 ~ —         ]  [2026-04-10 ~ —]

# %% [markdown]
# ## 3. 겹치는 두 번째 기록 — 논리적 갱신 발생
#
# 6월 1일부터 박서준으로 교체(6월 3일에 알게 됨).
# 새 시작 6/1이 김하늘 기록의 유효 기간 $[3/1, \infty)$ 안쪽이므로 겹침 처리가 발동한다.
#
# 행이 1개 → 3개가 되는 것이 핵심이다:
# **닫힌 원본 + 잘린 원본 + 새 사실**. 어떤 행도 지워지지 않았다.

# %%
st.assert_fact("가온테크", "담당", "박서준", valid_from=D(2026, 6, 1), tx_at=D(2026, 6, 3))
dump(st, "assert_fact #2 후 — 행 3개 (retire + 잘린 재기록 + 새 사실)")
# 출력:
# assert_fact #2 후 — 행 3개 (retire + 잘린 재기록 + 새 사실)
#     값       유효                       기록
#     김하늘      [2026-03-01 ~ —         ]  [2026-04-10 ~ 2026-06-03]
#     김하늘      [2026-03-01 ~ 2026-06-01]  [2026-06-03 ~ —]
#     박서준      [2026-06-01 ~ —         ]  [2026-06-03 ~ —]

# %% [markdown]
# 행별 해석:
#
# | 행 | 의미 |
# |---|---|
# | 김하늘 `[3/1, —)` tx `[4/10, 6/3)` | `_retire`로 닫힌 원본. «6/3 전까지 우리가 알던 모습» |
# | 김하늘 `[3/1, 6/1)` tx `[6/3, —)` | 잘린 유효 기간으로 재기록. «김하늘은 6/1 전까지만 담당이었다» |
# | 박서준 `[6/1, —)` tx `[6/3, —)` | 새 사실 |

# %% [markdown]
# ## 4. 왜 이렇게 하나 — 네 가지 시점 질문
#
# 닫힌 원본이 남아 있어서 «그때 우리가 알던 대로»를 재현할 수 있다.

# %%
cases = [
    ("7/1 담당 (지금 아는 대로)",              D(2026, 7, 1), None),
    ("6/2에 우리는 7월 담당을 누구로 알았나",   D(2026, 7, 1), D(2026, 6, 2)),
    ("3/15 담당 (지금 아는 대로)",             D(2026, 3, 15), None),
    ("3/15에 우리는 누구로 알고 있었나",        D(2026, 3, 15), D(2026, 3, 15)),
]
for label, va, ta in cases:
    rows = st.query("가온테크", "담당", valid_at=va, tx_at=ta)
    ans = ", ".join(r["value"] for r in rows) or "모름"
    print(f"{label:<32} → {ans}")
# 출력:
# 7/1 담당 (지금 아는 대로)                → 박서준
# 6/2에 우리는 7월 담당을 누구로 알았나        → 김하늘
# 3/15 담당 (지금 아는 대로)               → 김하늘
# 3/15에 우리는 누구로 알고 있었나           → 모름

# %% [markdown]
# 두 번째 줄이 겹침 처리의 존재 이유다. `_retire`가 행을 지웠다면
# «6/2 시점의 지식»(김하늘이 계속 담당)을 재현할 수 없다.
# 네 번째 줄은 tx 축의 효과 — 3/15에는 아직 아무것도 기록되지 않았다.

# %% [markdown]
# ## 5. 시각화 — 겹침 처리 전후의 유효 기간 막대
#
# 위: 갱신 전(행 1개). 아래: 갱신 후(행 3개).
# 회색 빗금 = `_retire`로 닫힌 기록(과거 지식 전용), 초록 = 지금 아는 대로 살아 있는 기록.

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

X_END = D(2026, 10, 1)  # FOREVER 는 화살표 느낌으로 10월까지 그린다


def bars(fig, facts, row):
    for i, f in enumerate(facts):
        alive = f["tx_to"] == FOREVER
        vt = min(f["valid_to"], X_END)
        y = len(facts) - i
        label = (f"{f['value']}  유효 [{fmt(f['valid_from'])} ~ {fmt(f['valid_to'])}]"
                 f"  기록 [{fmt(f['tx_from'])} ~ {fmt(f['tx_to'])}]")
        fig.add_trace(go.Scatter(
            x=[f["valid_from"], vt], y=[y, y],
            mode="lines",
            line=dict(width=22, color="#2e7d32" if alive else "#9e9e9e"),
            opacity=1.0 if alive else 0.55,
            name=label, showlegend=False, hovertext=label,
        ), row=row, col=1)
        fig.add_annotation(
            x=f["valid_from"], y=y, xanchor="left", yanchor="middle",
            text=(f"<b>{f['value']}</b> " + ("(살아 있음)" if alive else f"(tx {fmt(f['tx_to'])}에 닫힘)")),
            showarrow=False, font=dict(size=12, color="white"), row=row, col=1)


fig = make_subplots(
    rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.18,
    subplot_titles=("갱신 전 — assert_fact(김하늘, 3/1) 직후",
                    "갱신 후 — assert_fact(박서준, 6/1) : retire + 잘린 재기록 + 새 사실"))

st_before = BiTemporalStore()
st_before.assert_fact("가온테크", "담당", "김하늘", valid_from=D(2026, 3, 1), tx_at=D(2026, 4, 10))
bars(fig, st_before.facts, row=1)
bars(fig, st.facts, row=2)

for r in (1, 2):
    fig.add_vline(x=D(2026, 6, 1), line_dash="dash", line_color="#c62828", row=r, col=1)
fig.add_annotation(x=D(2026, 6, 1), y=3.55, text="새 valid_from = 6/1", showarrow=False,
                   xanchor="left", xshift=8,
                   font=dict(color="#c62828", size=12), row=2, col=1)

fig.update_yaxes(visible=False, range=[0.3, 1.7], row=1, col=1)
fig.update_yaxes(visible=False, range=[0.3, 3.7], row=2, col=1)
fig.update_xaxes(title_text="유효 시간 →", row=2, col=1)
fig.update_layout(
    title="assert_fact() 겹침 처리 — 행 1개가 3개로 바뀌는 논리적 갱신",
    width=900, height=520, plot_bgcolor="#fafafa", margin=dict(l=40, r=40, t=90, b=50))

_show(fig)

import os
_here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else "."
fig.write_image(os.path.join(_here, "expy.png"), scale=2)
print("expy.png 저장 완료")
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# - `assert_fact()`는 같은 $(s, p)$의 살아 있는 기록(`tx_to == FOREVER`) 중
#   새 `valid_from`이 유효 기간 안쪽에 떨어지는 것을 찾아,
#   **`_retire`로 기록 시간을 닫고**, **잘린 유효 기간 $[\text{vf}_{old}, \text{vf}_{new})$으로 재기록**한 뒤 새 사실을 추가한다.
# - 삭제·덮어쓰기가 없으므로 «그때 우리가 알던 대로»(tx 축 질의)가 항상 재현된다.
# - 이것은 만료(그때는 맞았다) 처리다. 정정(그때도 틀렸다)은 `correct()`가 맡으며,
#   잘린 재기록 없이 닫기만 한다 — 그 값은 참이었던 기간이 없기 때문이다.
