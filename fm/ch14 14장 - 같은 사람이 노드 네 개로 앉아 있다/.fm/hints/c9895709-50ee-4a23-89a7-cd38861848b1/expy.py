# %% [markdown]
# # 오병합 하나 = 검토 180건
#
# 저자가 적어 둔 숫자는 두 줄뿐이다.
#
# - 사람 한 건 검토: 약 **40초**, 인건비로 환산해 **400원**
# - 오병합 하나 수습: 평균 **2시간** (원인 파악 + 되돌리기 + 영향 받은 질의 확인)
#
# 여기서 「오병합 하나가 검토 180건과 맞먹는다」가 나온다. 이 노트는
#
# 1. 180이 어떻게 나오는지 시간·금액 두 경로로 재현하고,
# 2. 그 비율 $\rho = c_{FP}/c_{review}$ 가 **최적 임계**를 어떻게 결정하는지 보고,
# 3. 되돌리기가 싸질 때(2시간 → 5분 → 30초) 임계가 어떻게 내려가는지 확인한다.
#
# 필요 패키지: plotly, kaleido (없으면 표 출력까지는 그대로 동작)

# %%
import random

# %% [markdown]
# ## 1. 180의 재현 — 시간 경로
#
# $$\rho = \frac{c_{FP}}{c_{review}} = \frac{2\ \text{시간}}{40\ \text{초}} = \frac{7200}{40} = 180$$

# %%
REVIEW_SEC = 40  # 검토 한 건에 드는 시간
REVIEW_KRW = 400  # 검토 한 건의 인건비 환산
FP_SEC = 2 * 3600  # 오병합 하나 수습 시간 = 2시간

rho_time = FP_SEC / REVIEW_SEC
print(f"오병합 수습 {FP_SEC}초 / 검토 {REVIEW_SEC}초 = {rho_time:.1f}건")
# 출력: 오병합 수습 7200초 / 검토 40초 = 180.0건

# %% [markdown]
# ## 2. 같은 180을 금액 경로로
#
# 40초 = 400원이면 시급은 $400 \times (3600/40) = 36{,}000$원. 2시간이면 72,000원이고,
# 72,000 / 400 = 180. 두 경로가 같은 수에 도달한다 — 애초에 같은 환산율을 쓰기 때문이다.

# %%
wage_per_hour = REVIEW_KRW * (3600 / REVIEW_SEC)
fp_krw = wage_per_hour * (FP_SEC / 3600)
rho_money = fp_krw / REVIEW_KRW

print(f"환산 시급        : {wage_per_hour:,.0f}원/시간")
print(f"오병합 하나 금액 : {fp_krw:,.0f}원")
print(f"금액 기준 rho    : {rho_money:.1f}건")
print(f"두 경로 일치?    : {abs(rho_time - rho_money) < 1e-9}")
# 출력: 환산 시급        : 36,000원/시간
# 출력: 오병합 하나 금액 : 72,000원
# 출력: 금액 기준 rho    : 180.0건
# 출력: 두 경로 일치?    : True

# %% [markdown]
# 즉 「180건」은 정밀한 측정값이 아니라 **한 번의 실수와 한 번의 검토를 같은 단위로 바꾸는 환율**이다.
# 이 환율 하나가 임계를 정한다.

# %% [markdown]
# ## 3. 점수 분포 — asset의 예제 4와 같은 모양
#
# 같은 쌍 400개는 높은 쪽(평균 0.86), 다른 쌍 9,600개는 낮은 쪽(평균 0.42)에 몰리되
# 겹치는 구간이 있다. 겹침이 없으면 임계 고민 자체가 없다.

# %%
random.seed(20260801)
SAME = [min(1.0, max(0.0, random.gauss(0.86, 0.11))) for _ in range(400)]
DIFF = [min(1.0, max(0.0, random.gauss(0.42, 0.15))) for _ in range(9_600)]

LOW = 0.55  # 검토 하한은 고정. 이 아래는 그냥 무시(= 놓침 비용이 t와 무관해진다)


def evaluate(high, low=LOW):
    """high 이상은 자동 병합, [low, high)는 사람 검토, low 미만은 무시."""
    tp = sum(1 for s in SAME if s >= high)
    fp = sum(1 for s in DIFF if s >= high)  # 오병합
    fn = sum(1 for s in SAME if s < low)  # 놓침 (low 고정이므로 상수)
    review = sum(1 for s in SAME + DIFF if low <= s < high)
    prec = tp / (tp + fp) if tp + fp else 0.0
    return prec, tp / len(SAME), fp, fn, review


print(f"{'자동임계':>8} {'정밀도':>7} {'재현율':>7} {'오병합':>7} {'놓침':>6} {'사람검토':>8}")
for h in (0.95, 0.90, 0.85, 0.75, 0.65, 0.55):
    p, r, fp, fn, rv = evaluate(h)
    print(f"{h:>8.2f} {p:>7.3f} {r:>7.3f} {fp:>7,} {fn:>6,} {rv:>8,}")
# 출력:     자동임계     정밀도     재현율     오병합    놓침     사람검토
# 출력:     0.95   0.963   0.195       3      0    2,207
# 출력:     0.90   0.911   0.357      14      0    2,131
# 출력:     0.85   0.898   0.527      24      0    2,053
# 출력:     0.75   0.701   0.797     136      0    1,833
# 출력:     0.65   0.379   0.975     638      0    1,260
# 출력:     0.55   0.175   1.000   1,888      0        0
#
# 놓침이 0인 이유: 같은 쌍의 점수가 모두 0.55 이상이라 검토 하한 아래로 떨어지지 않는다.

# %% [markdown]
# ## 4. 총비용 — 검토 건수 단위로 환산
#
# 검토 한 건을 1로 두면 총비용은
#
# $$C(t) = \rho \cdot FP(t) + 1 \cdot Review(t) + \mu \cdot FN$$
#
# $FN$은 검토 하한 $t_{low}=0.55$를 고정했으므로 $t$와 무관한 상수다. 따라서 argmin에는
# 영향이 없고, 아래에서는 생략한다. 남는 건 **오병합 $\times \rho$** 대 **검토 건수**의 저울질뿐이다.

# %%
GRID = [round(0.55 + 0.005 * i, 3) for i in range(91)]  # 0.55 ~ 1.00
CACHE = {t: evaluate(t) for t in GRID}


def total_cost(t, rho):
    _, _, fp, _, review = CACHE[t]
    return rho * fp + review


def optimum(rho):
    best = min(GRID, key=lambda t: (total_cost(t, rho), -t))
    _, _, fp, _, review = CACHE[best]
    return best, total_cost(best, rho), fp, review


print(f"{'rho':>7} {'최적임계':>8} {'총비용(검토건)':>13} {'오병합':>7} {'검토':>7}")
for rho in (1, 3, 10, 30, 180, 1000):
    t, c, fp, rv = optimum(rho)
    print(f"{rho:>7} {t:>8.3f} {c:>13,.0f} {fp:>7,} {rv:>7,}")
# 출력:     rho     최적임계   총비용(검토건)     오병합      검토
# 출력:       1    0.570         1,888   1,554     334
# 출력:       3    0.830         2,118      33   2,019
# 출력:      10    0.955         2,230       2   2,210
# 출력:      30    0.980         2,239       0   2,239
# 출력:     180    0.980         2,239       0   2,239
# 출력:    1000    0.980         2,239       0   2,239

# %% [markdown]
# 읽는 법:
#
# - $\rho = 1$ — 오병합이 검토 한 건만큼도 안 아프다. 그러면 사람을 거의 부르지 말고
#   자동으로 밀어버리는 게 최적이다(임계 0.57, 오병합 1,554건을 그냥 감수).
# - $\rho = 3$ — 임계 0.83. 오병합이 33건으로 줄고 그 대가로 2,019건을 사람이 본다.
# - $\rho = 10$ — 임계 0.955. 오병합 2건.
# - $\rho = 30$ 이상 — **포화**. 임계가 0.98에서 멈추고 $\rho$를 180으로, 1000으로 올려도
#   답이 바뀌지 않는다. 오병합이 이미 0이라 더 올릴 이유가 없기 때문이다.
#
# 그래서 저자의 180은 「임계를 정확히 몇으로 하라」가 아니라 **「어느 쪽 극단에 서라」**를
# 말해 주는 숫자다. 두 자릿수만 넘으면 결론은 하나 — 「임계를 높게 잡는다. 사람이 많이
# 보더라도.」 비용비를 정밀하게 추정하지 않아도 자릿수만 맞으면 의사결정이 같아진다는 뜻이고,
# 이게 이런 봉투 뒷면 계산이 실무에서 쓸모 있는 이유다.
#
# 단, 대가는 정직하게 보자. $\rho = 180$ 의 답은 「사실상 자동화를 포기하고 2,239건을 다
# 사람이 본다」다. 사람 시간 24.9시간(2239 × 40초)을 써서 오병합 24건(0.85 임계 기준,
# 48시간어치)을 막는 거래다. 되돌리기가 비싸면 자동화 여지 자체가 좁아진다.

# %% [markdown]
# ## 5. 되돌리기가 싸지면 계산이 뒤집힌다
#
# asset의 마지막 줄: 「unmerge 가 대입 한 번이면 오병합 값이 2시간에서 5분이 된다.」
# $\rho$는 수습 시간을 검토 40초로 나눈 값이므로 그대로 따라 내려간다.

# %%
print(f"{'수습시간':>10} {'rho':>8} {'최적임계':>8} {'오병합':>7} {'검토':>7}")
for label, sec in (("2시간", 7200), ("5분", 300), ("30초", 30)):
    rho = sec / REVIEW_SEC
    t, _, fp, rv = optimum(rho)
    print(f"{label:>10} {rho:>8.2f} {t:>8.3f} {fp:>7,} {rv:>7,}")
# 출력:      수습시간      rho     최적임계     오병합      검토
# 출력:        2시간   180.00    0.980       0   2,239
# 출력:          5분     7.50    0.870      18   2,082
# 출력:         30초     0.75    0.550   1,888       0

# %% [markdown]
# 되돌리기를 싸게 만드는 엔지니어링(asset 예제 3의 `unmerge`)은 곧 **$\rho$를 깎는 작업**이다.
# $\rho$가 180 → 7.5 → 0.75로 떨어지면 최적 임계도 0.98 → 0.87 → 0.55로 내려가고,
# 사람 검토 부담이 2,239건 → 2,082건 → 0건으로 사라진다.
# 임계값을 소수점까지 튜닝하는 것보다 되돌리기를 싸게 만드는 쪽이 대체로 남는 장사다.

# %%
def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    RHOS = [1, 10, 180, 1000]
    COLORS = {1: "#4C78A8", 10: "#54A24B", 180: "#E45756", 1000: "#B279A2"}

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=(
            "rho 별 총비용 곡선 (검토 건수 단위, 최소=1.0 정규화)",
            "최적 임계 궤적 — rho 가 오르면 임계도 오른다",
        ),
    )

    seen = set()
    for rho in RHOS:
        ys = [total_cost(t, rho) for t in GRID]
        m = min(ys)
        t_opt, _, _, _ = optimum(rho)
        label = f"rho={rho}" + (" (임계 동일)" if t_opt in seen else "")
        fig.add_trace(
            go.Scatter(
                x=GRID,
                y=[y / m for y in ys],
                name=label,
                line=dict(color=COLORS[rho], width=2, dash="dot" if t_opt in seen else "solid"),
                hovertemplate="임계 %{x:.3f}<br>상대비용 %{y:.2f}<extra></extra>",
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=[t_opt],
                y=[1.0],
                mode="markers+text",
                marker=dict(color=COLORS[rho], size=11, symbol="diamond"),
                # 최적 임계가 겹치는 rho 는 라벨을 생략(0.980 중복)
                text=[""] if t_opt in seen else [f"{t_opt:.3f}"],
                textposition="top left" if rho == 10 else "top center",
                showlegend=False,
                hoverinfo="skip",
            ),
            row=1,
            col=1,
        )
        seen.add(t_opt)

    # 오른쪽: rho 를 촘촘히 훑어 최적 임계 궤적
    sweep = [0.5 * 1.25**i for i in range(40)]
    fig.add_trace(
        go.Scatter(
            x=sweep,
            y=[optimum(r)[0] for r in sweep],
            mode="lines",
            line=dict(color="#555", width=2, shape="hv"),
            showlegend=False,
            hovertemplate="rho %{x:.1f} → 임계 %{y:.3f}<extra></extra>",
        ),
        row=1,
        col=2,
    )
    for label, sec, color, pos in (
        ("30초 (rho 0.75)", 30, "#B279A2", "middle right"),
        ("5분 (rho 7.5)", 300, "#54A24B", "middle right"),
        ("2시간 (rho 180) — 저자의 숫자", 7200, "#E45756", "bottom center"),
    ):
        r = sec / REVIEW_SEC
        fig.add_trace(
            go.Scatter(
                x=[r],
                y=[optimum(r)[0]],
                mode="markers+text",
                marker=dict(color=color, size=13, symbol="star"),
                text=[label],
                textposition=pos,
                showlegend=False,
                hoverinfo="skip",
            ),
            row=1,
            col=2,
        )

    fig.update_xaxes(title_text="자동 병합 임계", row=1, col=1)
    fig.update_yaxes(
        title_text="총비용 / 최소 총비용 (로그)",
        type="log",
        range=[-0.03, 2.3],  # 1배 ~ 200배
        row=1,
        col=1,
    )
    fig.update_xaxes(title_text="rho = 오병합 수습 / 검토 한 건 (로그)", type="log", row=1, col=2)
    fig.update_yaxes(title_text="최적 자동 병합 임계", range=[0.5, 1.02], row=1, col=2)
    fig.update_layout(
        title_text="오병합 하나 = 검토 180건 — 비용비 rho 가 임계를 정한다",
        template="plotly_white",
        width=1180,
        height=520,
        legend=dict(orientation="h", y=-0.18),
    )

    _show(fig)
    fig.write_image("expy.png", scale=2)
    print("expy.png 저장 완료")
except Exception as exc:  # noqa: BLE001
    print(f"시각화 생략: {exc}")
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# - 검토 한 건 40초·400원, 오병합 수습 2시간 → $7200/40 = 180$. 금액으로도 $72{,}000/400 = 180$.
# - 180은 「오병합 하나를 막기 위해 검토 179건까지는 써도 이득」이라는 뜻의 환율이다.
# - 이 환율이 임계를 정한다: $\rho$ 1 → 0.57, 3 → 0.83, 10 → 0.955, 30 이상 → 0.98(포화).
# - 되돌리기가 싸지면($\rho$ 180 → 7.5 → 0.75) 최적 임계도 0.98 → 0.87 → 0.55로 내려가고
#   사람 검토 부담(2,239 → 2,082 → 0건)이 사라진다.
