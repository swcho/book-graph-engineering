# %% [markdown]
# # ex5 — 체인과 그래프가 갈리는 지점
#
# 18장 `ex5_when_to_switch.py`의 비용 모델을 그대로 재현해 본다.
#
# 조건이 $n$개인 체인은 분기 경로가 $2^n$개 생긴다. 사람이 실제로 테스트하는 건
# 여덟 가지쯤이므로, 미검증 경로는 $\max(0,\; 2^n - 8)$개.
#
# **체인의 예상 손실** (일 단위):
#
# $$L_{\text{체인}}(n) = \max(0,\; 2^n - 8) \times p \times c$$
#
# - $p = 0.08$ : 미검증 경로가 실제로 터질 확률
# - $c = 0.5$일 : 버그 하나가 만드는 비용의 기댓값
#
# **그래프의 총비용**: 노드 수는 선형($2n+3$)으로 늘고, 개념 학습 비용이 처음 한 번 붙는다.
#
# $$C_{\text{그래프}}(n) = 2.0 + (2n + 3) \times 0.05$$
#
# 지수 대 선형의 싸움이므로 교차점은 반드시 생긴다. 어디서 생기는지 보자.

# %%
# 필요 패키지: plotly, kaleido (표 계산 자체는 표준 라이브러리만으로 동작)
import os


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


HERE = os.path.dirname(os.path.abspath(__file__))

# 책의 ex5와 동일한 전제
LEARN_COST_DAYS = 2.0   # 상태 그래프 개념·도구를 익히는 데 드는 시간
BUG_COST_DAYS = 0.5     # 미검증 경로 하나가 언젠가 만드는 비용의 기댓값
BUG_RATE = 0.08         # 미검증 경로가 실제로 터질 확률
TESTED_PATHS = 8        # 사람이 실제로 테스트하는 경로 수


def chain_loss(n, bug_cost=BUG_COST_DAYS):
    paths = 2 ** n
    untested = max(0, paths - TESTED_PATHS)
    return untested * BUG_RATE * bug_cost


def graph_cost(n, learn_cost=LEARN_COST_DAYS):
    nodes = n * 2 + 3
    return learn_cost + nodes * 0.05

# %% [markdown]
# ## 1. 책의 표 재현 — 조건 수 $n$을 1부터 8까지 스윕

# %%
print(f"{'조건 수':>4} {'체인 경로':>8} {'미검증':>6} {'체인 손실(일)':>10} {'그래프 비용(일)':>11} {'유리한 쪽':>6}")
print("-" * 62)
for n in range(1, 9):
    paths = 2 ** n
    untested = max(0, paths - TESTED_PATHS)
    cl, gc = chain_loss(n), graph_cost(n)
    better = "체인" if cl < gc else "그래프"
    print(f"{n:>6} {paths:>11,} {untested:>8,} {cl:>13.2f} {gc:>16.2f} {better:>8}")

# 출력:
# 조건 수    체인 경로    미검증   체인 손실(일)   그래프 비용(일)  유리한 쪽
# --------------------------------------------------------------
#      1           2        0          0.00             2.25       체인
#      2           4        0          0.00             2.35       체인
#      3           8        0          0.00             2.45       체인
#      4          16        8          0.32             2.55       체인
#      5          32       24          0.96             2.65       체인
#      6          64       56          2.24             2.75       체인
#      7         128      120          4.80             2.85      그래프
#      8         256      248          9.92             2.95      그래프

# %% [markdown]
# **갈리는 지점은 조건 6~7개 사이.**
#
# - $n=6$: 체인 손실 $56 \times 0.08 \times 0.5 = 2.24$일 < 그래프 $2.75$일 → 아직 체인이 싸다
# - $n=7$: 체인 손실 $120 \times 0.08 \times 0.5 = 4.80$일 > 그래프 $2.85$일 → 그래프가 낫다
#
# 그 전에는 체인이 이긴다. 개념이 적고 코드가 짧으니까(학습 비용 2일이 안 붙는다).
# 미검증 경로가 $2^n$으로 불어나면서 지수가 선형을 따라잡는 순간이 전환점이다.

# %% [markdown]
# ## 2. 전제를 바꾸면 전환점이 움직인다
#
# 세 전제 중 특히 **버그 하나의 비용 $c$** 가 크면 전환점이 확 앞으로 온다.
# 결제·삭제처럼 되돌리기 힘든 일이면 조건 두세 개에서도 그래프가 낫다.

# %%
def crossover(bug_cost, learn_cost=LEARN_COST_DAYS):
    """그래프가 처음으로 유리해지는 조건 수 n."""
    for n in range(1, 20):
        if chain_loss(n, bug_cost) >= graph_cost(n, learn_cost):
            return n
    return None


for c in (0.5, 1.0, 2.0, 5.0):
    print(f"버그 비용 {c:>4.1f}일 → 조건 {crossover(c)}개부터 그래프가 유리")
print(f"팀이 그래프를 이미 알 때(학습 0일, 버그 0.5일) → 조건 {crossover(0.5, 0.0)}개부터")

# 출력:
# 버그 비용  0.5일 → 조건 7개부터 그래프가 유리
# 버그 비용  1.0일 → 조건 6개부터 그래프가 유리
# 버그 비용  2.0일 → 조건 5개부터 그래프가 유리
# 버그 비용  5.0일 → 조건 4개부터 그래프가 유리
# 팀이 그래프를 이미 알 때(학습 0일, 버그 0.5일) → 조건 5개부터

# %% [markdown]
# 반대 방향도 성립한다. «틀려도 사람이 다시 누르면 그만»인 일(버그 비용이 작은 일)이면
# 조건 여덟 개까지도 체인으로 버틸 만하다.

# %% [markdown]
# ## 3. 시각화 — 지수(체인) 대 선형(그래프)의 교차

# %%
import plotly.graph_objects as go

ns = list(range(1, 9))
chain_base = [chain_loss(n) for n in ns]            # 버그 0.5일 (책 기본값)
chain_heavy = [chain_loss(n, 2.0) for n in ns]      # 버그 2.0일 (되돌리기 어려운 일)
graph_line = [graph_cost(n) for n in ns]

BLUE, ORANGE = "#2a78d6", "#eb6834"

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=ns, y=chain_base, name="체인 예상 손실 (버그 0.5일)",
    mode="lines+markers", line=dict(color=BLUE, width=2), marker=dict(size=8)))
fig.add_trace(go.Scatter(
    x=ns, y=chain_heavy, name="체인 예상 손실 (버그 2.0일)",
    mode="lines+markers", line=dict(color=BLUE, width=2, dash="dash"),
    marker=dict(size=8, symbol="diamond")))
fig.add_trace(go.Scatter(
    x=ns, y=graph_line, name="그래프 총비용 (학습 2일 + 노드)",
    mode="lines+markers", line=dict(color=ORANGE, width=2), marker=dict(size=8)))

# 전환점 표시
fig.add_annotation(x=7, y=chain_loss(7), text="기본값: 6~7개 사이에서 역전",
                   showarrow=True, arrowhead=2, ax=-90, ay=-25,
                   font=dict(color=BLUE, size=12))
fig.add_annotation(x=5, y=chain_loss(5, 2.0), text="버그 비용 4배 → 전환점이 5개로",
                   showarrow=True, arrowhead=2, ax=-100, ay=-40,
                   font=dict(color=BLUE, size=12))

fig.update_layout(
    title="ex5 — 언제 체인에서 그래프로 갈아탈까",
    xaxis_title="조건 수 n", yaxis_title="예상 비용 (일)",
    template="plotly_white", width=880, height=520,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    font=dict(size=13),
)
fig.update_xaxes(dtick=1, showgrid=False)
fig.update_yaxes(gridcolor="#e8e8e8")

fig.write_image(os.path.join(HERE, "expy.png"), scale=2)
_show(fig)
print("expy.png 저장 완료")

# 출력:
# expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# - 책의 기본 전제(학습 2일, 터질 확률 8%, 버그 0.5일)에서 **체인과 그래프는 조건 6~7개
#   사이에서 갈린다**. 그 전에는 개념이 적고 코드가 짧은 체인이 싸다.
# - 원리는 단순하다: 체인의 미검증 경로는 $2^n$으로(지수), 그래프 비용은 $2n$으로(선형)
#   늘어나므로 교차점은 반드시 온다.
# - 전제는 여러분 값으로 바꿔야 한다. 버그 비용이 크면(결제·삭제) 전환점이 조건 4~5개로
#   당겨지고, 팀이 그래프를 이미 알면(학습 0일) 더 일찍 온다.
