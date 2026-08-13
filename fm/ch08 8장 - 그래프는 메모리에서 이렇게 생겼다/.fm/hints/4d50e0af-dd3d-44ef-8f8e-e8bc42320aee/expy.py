# %% [markdown]
# # `skew=True` — 선호적 연결(preferential attachment)
#
# `graphgen.py`의 두 분기는 **뽑기 통이 다르다.**
#
# | 분기 | 이웃 고르기 | 통의 내용 |
# |---|---|---|
# | `skew=False` | `rnd.randrange(n)` | 0 ~ n-1 을 **똑같은 확률**로 |
# | `skew=True` | `rnd.choice(targets)` | 이미 등장한 노드가 **여러 번** 들어 있는 리스트 |
#
# `targets`에 같은 노드를 여러 번 넣어 두면, `random.choice`는 균등 추출인데도
# 결과는 **중복 횟수에 비례**한 추출이 된다.
#
# $$P(\text{노드 } v \text{ 선택}) = \frac{\text{mult}(v)}{|\texttt{targets}|}, \qquad
#   \text{mult}(v) = 1 + t(v)$$
#
# 여기서 $t(v)$는 $v$가 지금까지 타깃으로 **뽑힌 횟수**다. 뽑히면 차수가 오르고,
# 차수가 오르면 통에 한 장 더 들어가고, 그러면 더 뽑힌다. 이게 「부익부」다.
#
# 필요 패키지: plotly, kaleido (마지막 시각화 셀에서만 사용. 없으면 그 셀만 건너뛴다)

# %%
import math
import random
from collections import Counter


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


# graphgen.make 를 그대로 옮겨 온다. 시드는 원본과 동일하게 고정.
def make(n=50_000, avg_deg=12, skew=False, seed=20260801):
    """skew=True 면 차수가 한쪽으로 쏠린 그래프를 만든다(선호적 연결)."""
    rnd = random.Random(seed)
    edges = set()
    if not skew:
        for a in range(n):
            for _ in range(avg_deg // 2):
                b = rnd.randrange(n)          # ← 균등 추출
                if a != b:
                    edges.add((min(a, b), max(a, b)))
        return sorted(edges)
    # 선호적 연결: 이미 차수가 높은 노드에 더 붙는다
    targets = [0, 1, 2]
    for a in range(3, n):
        for _ in range(avg_deg // 2):
            b = rnd.choice(targets)           # ← 통에서 한 장 뽑기 = 차수 비례
            if a != b:
                edges.add((min(a, b), max(a, b)))
                targets.append(b)             # ← 뽑힌 놈을 한 장 더 넣는다
        targets.append(a)                     # ← 새 노드도 통에 등록(딱 한 장)
    return sorted(edges)


def degrees(edges, n):
    d = [0] * n
    for a, b in edges:
        d[a] += 1
        d[b] += 1
    return d


print("준비 완료. m = avg_deg // 2 =", 12 // 2, "(새 노드가 던지는 주사위 수)")
# 출력: 준비 완료. m = avg_deg // 2 = 6 (새 노드가 던지는 주사위 수)

# %% [markdown]
# ## 1단계 — 통 속을 직접 들여다본다
#
# 아주 작은 그래프(`n=12`)로 `targets`가 어떻게 자라는지 한 줄씩 찍어 본다.
# 통의 길이는 노드마다 최대 $m+1 = 7$장씩 늘어난다.

# %%
def make_traced(n, avg_deg=12, seed=20260801, snap_upto=0):
    """make(skew=True) 와 완전히 같은 난수 소비 순서. targets 를 그대로 돌려준다.

    snap_upto: 앞쪽 몇 개 노드까지 targets 스냅샷을 남길지. 스냅샷은 리스트 복사라
    비싸니 기본값은 0(안 남김)."""
    rnd = random.Random(seed)
    edges, targets, log = set(), [0, 1, 2], []
    for a in range(3, n):
        picked = []
        for _ in range(avg_deg // 2):
            b = rnd.choice(targets)
            if a != b:
                edges.add((min(a, b), max(a, b)))
                targets.append(b)
                picked.append(b)
            else:
                picked.append(None)           # 자기 자신 → 버린다
        targets.append(a)
        if a < 3 + snap_upto:
            log.append((a, picked, list(targets)))
    return sorted(edges), targets, log


_, _, log = make_traced(12, snap_upto=6)
for a, picked, snap in log:
    got = ",".join("self" if p is None else str(p) for p in picked)
    print(f"a={a:>2} 뽑은 것=[{got:<13}]  len={len(snap):>3}  targets={snap}")
# 출력: a= 3 뽑은 것=[2,2,2,2,1,1  ]  len= 10  targets=[0, 1, 2, 2, 2, 2, 2, 1, 1, 3]
# 출력: a= 4 뽑은 것=[2,2,2,2,0,3  ]  len= 17  targets=[..., 2, 2, 2, 2, 0, 3, 4]
# 출력: a= 5 뽑은 것=[2,2,2,0,2,2  ]  len= 24
# 출력: a= 6 뽑은 것=[5,2,2,3,2,2  ]  len= 31
# 출력: a= 7 뽑은 것=[1,3,1,2,0,0  ]  len= 38
# 출력: a= 8 뽑은 것=[2,0,2,2,0,2  ]  len= 45
# 출력: → 노드 2가 초반에 운 좋게 몇 번 뽑히자, 통이 2로 뒤덮이고 계속 2만 뽑힌다.
# 출력:   len 이 매번 +7 (= m+1) 씩 자란다.

# %% [markdown]
# ## 2단계 — 중복 횟수가 곧 차수다
#
# 통 안에서 노드 $v$가 몇 장인지 세 보면, 그 값이 $v$의 차수를 거의 그대로 따라간다.
#
# $$\text{mult}(v) = \underbrace{1}_{\texttt{targets.append(a)}} + \underbrace{t(v)}_{\text{타깃으로 뽑힌 횟수}}$$
#
# 허브에서는 $t(v)$가 압도적이라 $\text{mult}(v) \approx \deg(v)$가 되고,
# 따라서 `rnd.choice(targets)`는 **차수 비례 샘플링**이 된다.
#
# $$\Pi(v) \;\propto\; 1 + t(v) \;\approx\; \deg(v)$$

# %%
N_SMALL = 5_000
edges_s, targets_s, _ = make_traced(N_SMALL)
deg_s = degrees(edges_s, N_SMALL)
mult = Counter(targets_s)

print(f"n={N_SMALL:,}  |targets|={len(targets_s):,}  = {len(targets_s) / N_SMALL:.2f}·n  (예측 m+1=7)")
print()
print(f"{'노드':>6} {'차수':>8} {'통 안 장수':>10} {'장수/차수':>10}")
for v in sorted(range(N_SMALL), key=lambda i: -deg_s[i])[:6]:
    print(f"{v:>6} {deg_s[v]:>8,} {mult[v]:>10,} {mult[v] / deg_s[v]:>10.2f}")
print(f"{'...':>6}")
leaf = min(range(N_SMALL), key=lambda i: deg_s[i] * 1000 + i)
print(f"{leaf:>6} {deg_s[leaf]:>8,} {mult[leaf]:>10,} {mult[leaf] / deg_s[leaf]:>10.2f}   ← 한 번도 안 뽑힌 노드")
# 출력: n=5,000  |targets|=34,982  = 7.00·n  (예측 m+1=7)
# 출력:     노드       차수     통 안 장수      장수/차수
# 출력:      2    3,705      6,148       1.66
# 출력:      0    2,444      3,240       1.33
# 출력:      1    1,013      1,112       1.10
# 출력:      5      920      1,006       1.09
# 출력:      3      818        888       1.09
# 출력:      6      591        620       1.05
# 출력:    151        3          1       0.33   ← 한 번도 안 뽑힌 노드
# 출력: → 허브는 장수 ≈ 차수 (1을 살짝 넘는 이유는 중복 엣지도 append 되기 때문).
# 출력:   안 뽑힌 노드는 영원히 1장 — 통에서 사실상 보이지 않는다.

# %% [markdown]
# ## 3단계 — 균등 vs 선호적 연결, 같은 평균 다른 세상
#
# 8장 `ex3_degree_skew.py`가 재는 값이다. **평균 차수는 거의 같은데** 최대 차수와
# 차수 제곱합이 자릿수로 갈린다. 2홉 탐색 비용이 바로 이 제곱합에 비례한다.
#
# $$\text{2홉 비용} \;\propto\; \sum_v \deg(v)^2$$

# %%
N = 50_000
stats = {}
for label, skew in (("고른 분포", False), ("쏠린 분포", True)):
    e = make(n=N, avg_deg=12, skew=skew)
    d = degrees(e, N)
    stats[label] = {
        "deg": d,
        "edges": len(e),
        "avg": sum(d) / N,
        "max": max(d),
        "sum_d2": sum(x * x for x in d),
        "top10": sum(sorted(d, reverse=True)[:10]),
    }

print(f"{'그래프':<10} {'엣지':>10} {'평균차수':>9} {'최대차수':>10} {'상위10합':>10} {'Σd²':>16}")
print("-" * 70)
for label, s in stats.items():
    print(f"{label:<10} {s['edges']:>10,} {s['avg']:>9.2f} {s['max']:>10,} "
          f"{s['top10']:>10,} {s['sum_d2']:>16,}")

r = stats["쏠린 분포"]["sum_d2"] / stats["고른 분포"]["sum_d2"]
rm = stats["쏠린 분포"]["max"] / stats["고른 분포"]["max"]
print(f"\nΣd² 배수 {r:,.0f}배,  최대 차수 배수 {rm:,.0f}배")
print(f"쏠린 쪽 1위 노드 차수 {stats['쏠린 분포']['max']:,} "
      f"= 전체 노드의 {stats['쏠린 분포']['max'] / N * 100:.0f}%와 연결")
# 출력: 그래프          엣지     평균차수    최대차수   상위10합              Σd²
# 출력: 고른 분포    299,958    12.00        25       241        7,494,946
# 출력: 쏠린 분포    280,374    11.21    30,267    86,040    1,520,876,110
# 출력:
# 출력: Σd² 배수 203배,  최대 차수 배수 1,211배
# 출력: 쏠린 쪽 1위 노드 차수 30,267 = 전체 노드의 61%와 연결

# %% [markdown]
# ## 4단계 — 멱법칙 지수를 재 본다
#
# 선호적 연결의 결과는 **멱법칙(power law)** 꼬리다.
#
# $$P(k) \sim k^{-\gamma}$$
#
# 교과서 Barabási–Albert 모형은 $\gamma = 3$이다. 힐(Hill) 추정으로 재 보면
# `graphgen`의 꼬리는 그보다 **더 두껍다**($\gamma \approx 2.2$).
#
# 이유는 `targets.append(a)`의 **위치**다. 원조 BA는 새 엣지마다 **양 끝**을 통에
# 넣어서 통이 $2mN$장으로 자란다. `graphgen`은 새 노드를 루프 **바깥에서 한 번만**
# 넣으니 통이 $(m+1)N$장으로만 자란다. 통이 천천히 자라면 기존 허브의 지분이
# 덜 희석되고, 그만큼 부익부가 더 세진다.
#
# 평균장(mean-field) 계산으로 보면, $w \propto N^{\beta}$이고
#
# $$\beta = \frac{m}{|\texttt{targets}|/N} = \frac{m}{m+1} = \frac{6}{7} \approx 0.86,
#   \qquad \gamma = 1 + \frac{1}{\beta} = 1 + \frac{7}{6} \approx 2.17$$
#
# 원조 BA는 $\beta = m/(2m) = 1/2$라서 $\gamma = 3$이다.

# %%
def hill_gamma(deg, kmin):
    """멱법칙 지수의 최대우도 추정(이산 보정판)."""
    tail = [x for x in deg if x >= kmin]
    g = 1 + len(tail) / sum(math.log(x / (kmin - 0.5)) for x in tail)
    return g, len(tail)


for kmin in (20, 50, 100):
    g, nt = hill_gamma(stats["쏠린 분포"]["deg"], kmin)
    print(f"쏠린 분포  kmin={kmin:>3}  꼬리 노드 {nt:>5,}개  γ̂ = {g:.2f}")

# 원조 BA 방식으로 장부만 바꿔 본다: 엣지마다 양 끝을 통에 넣는다.
def make_textbook_ba(n, m=6, seed=20260801):
    rnd = random.Random(seed)
    edges, targets = set(), [0, 1, 2]
    for a in range(3, n):
        for _ in range(m):
            b = rnd.choice(targets)
            if a != b:
                edges.add((min(a, b), max(a, b)))
                targets.append(b)
                targets.append(a)             # ← 여기! 새 노드도 엣지마다 등록
    return sorted(edges), targets


e_ba, t_ba = make_textbook_ba(N)
d_ba = degrees(e_ba, N)
g_ba, _ = hill_gamma(d_ba, 50)
_, t_gg, _ = make_traced(N)                       # graphgen 쪽 통의 실제 길이
print()
print(f"{'장부 방식':<22} {'|targets|':>12} {'/n':>6} {'최대차수':>10} {'Σd²':>16} {'γ̂(kmin=50)':>12}")
print("-" * 84)
print(f"{'graphgen (바깥 1회)':<22} {len(t_gg):>12,} {len(t_gg) / N:>6.2f} "
      f"{stats['쏠린 분포']['max']:>10,} {stats['쏠린 분포']['sum_d2']:>16,} "
      f"{hill_gamma(stats['쏠린 분포']['deg'], 50)[0]:>12.2f}")
print(f"{'원조 BA (엣지마다)':<22} {len(t_ba):>12,} {len(t_ba) / N:>6.2f} {max(d_ba):>10,} "
      f"{sum(x * x for x in d_ba):>16,} {g_ba:>12.2f}")
# 출력: 쏠린 분포  kmin= 20  꼬리 노드 2,214개  γ̂ = 2.32
# 출력: 쏠린 분포  kmin= 50  꼬리 노드   628개  γ̂ = 2.19
# 출력: 쏠린 분포  kmin=100  꼬리 노드   266개  γ̂ = 2.11
# 출력:   → kmin 을 올릴수록 예측값 2.17 로 수렴한다.
# 출력:
# 출력: 장부 방식              |targets|    /n   최대차수              Σd²  γ̂(kmin=50)
# 출력: graphgen (바깥 1회)      349,982  7.00     30,267    1,520,876,110      2.19
# 출력: 원조 BA (엣지마다)       599,943 12.00      1,694       25,625,976      2.95
# 출력:   → append 한 줄의 위치만 옮기면 γ̂ 2.19 → 2.95(≈3), 최대 차수 30,267 → 1,694,
# 출력:     Σd² 는 59배 줄어든다. 통이 자라는 속도가 꼬리 두께를 정한다.

# %% [markdown]
# ## 5단계 — log-log 로 보면 직선이다
#
# 멱법칙은 양쪽 축에 로그를 씌우면 **직선**이 된다.
#
# $$\log P(k) = -\gamma \log k + \text{const}$$
#
# 여기서는 꼬리를 볼 때 잡음이 적은 **여누적분포(CCDF)** $P(K \ge k)$를 그린다.
# CCDF의 기울기는 $-(\gamma - 1)$이다.

# %%
def ccdf(deg):
    """P(K >= k). (k, 확률) 쌍을 반환."""
    cnt = Counter(deg)
    ks = sorted(cnt)
    total = len(deg)
    out, acc = [], 0
    for k in reversed(ks):
        acc += cnt[k]
        out.append((k, acc / total))
    return out[::-1]


for label in ("고른 분포", "쏠린 분포"):
    pts = ccdf(stats[label]["deg"])
    hi = [(k, p) for k, p in pts if k >= 50]
    print(f"{label}: 서로 다른 차수 값 {len(pts):>4}가지, "
          f"차수 50 이상 구간 {len(hi):>4}가지, "
          f"P(K≥50) = {next((p for k, p in pts if k >= 50), 0.0):.2e}, "
          f"최대 {max(stats[label]['deg']):>6,}")
# 출력: 고른 분포: 서로 다른 차수 값   20가지, 차수 50 이상 구간    0가지, P(K≥50) = 0.00e+00, 최대     25
# 출력: 쏠린 분포: 서로 다른 차수 값  279가지, 차수 50 이상 구간  231가지, P(K≥50) = 1.26e-02, 최대 30,267
# 출력: → 고른 분포는 차수 50 이상이 아예 없다. 꼬리가 없으니 log-log 에서 직선도 없다.

# %%
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    PALETTE = ["#4C78A8", "#F58518", "#54A24B", "#E45756", "#B279A2"]

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "차수 분포 CCDF (log-log) — 쏠린 쪽만 직선 꼬리",
            "상위 20개 노드의 차수 (log y)",
            "Σd² = 2홉 비용 (log x)",
            "targets 안 장수 vs 차수 (log-log)",
        ),
        vertical_spacing=0.14, horizontal_spacing=0.11,
    )

    # (1,1) CCDF log-log
    for i, label in enumerate(("고른 분포", "쏠린 분포")):
        pts = ccdf(stats[label]["deg"])
        fig.add_trace(
            go.Scatter(
                x=[k for k, _ in pts], y=[p for _, p in pts],
                mode="lines+markers", name=label,
                line=dict(color=PALETTE[i], width=2), marker=dict(size=4),
            ),
            row=1, col=1,
        )
    # 기울기 -(γ-1) 기준선
    g_fit, _ = hill_gamma(stats["쏠린 분포"]["deg"], 50)
    xs = [50, 20_000]
    p50 = next(p for k, p in ccdf(stats["쏠린 분포"]["deg"]) if k >= 50)
    fig.add_trace(
        go.Scatter(
            x=xs, y=[p50 * (x / 50) ** (-(g_fit - 1)) for x in xs],
            mode="lines", name=f"기울기 −(γ−1), γ̂={g_fit:.2f}",
            line=dict(color=PALETTE[3], width=2, dash="dash"),
        ),
        row=1, col=1,
    )

    # (1,2) 상위 20 차수
    for i, label in enumerate(("고른 분포", "쏠린 분포")):
        top = sorted(stats[label]["deg"], reverse=True)[:20]
        fig.add_trace(
            go.Bar(
                x=list(range(1, 21)), y=top, name=label,
                marker_color=PALETTE[i], showlegend=False,
            ),
            row=1, col=2,
        )

    # (2,1) Σd² 비교
    labels = ["고른 분포", "쏠린 분포", "원조 BA 장부"]
    vals = [stats["고른 분포"]["sum_d2"], stats["쏠린 분포"]["sum_d2"], sum(x * x for x in d_ba)]
    base = vals[0]
    fig.add_trace(
        go.Bar(
            x=vals, y=labels, orientation="h",
            marker_color=[PALETTE[0], PALETTE[1], PALETTE[2]],
            text=[f"{v:,} ({v / base:.0f}x)" for v in vals],
            textposition="auto", showlegend=False,
        ),
        row=2, col=1,
    )

    # (2,2) 장수 vs 차수
    pts = [(deg_s[v], mult[v]) for v in range(N_SMALL) if deg_s[v] > 0]
    fig.add_trace(
        go.Scatter(
            x=[d for d, _ in pts], y=[m for _, m in pts],
            mode="markers", name="노드", showlegend=False,
            marker=dict(color=PALETTE[4], size=4, opacity=0.45),
        ),
        row=2, col=2,
    )
    lim = [1, max(deg_s) * 1.3]
    fig.add_trace(
        go.Scatter(
            x=lim, y=lim, mode="lines", name="장수 = 차수 (기준선)",
            line=dict(color="#8C8C8C", width=2, dash="dot"),
        ),
        row=2, col=2,
    )

    fig.update_xaxes(type="log", title_text="차수 k", row=1, col=1)
    fig.update_yaxes(type="log", title_text="P(K ≥ k)", row=1, col=1)
    fig.update_xaxes(title_text="순위", row=1, col=2)
    fig.update_yaxes(type="log", title_text="차수", row=1, col=2)
    fig.update_xaxes(type="log", title_text="Σd²", row=2, col=1)
    fig.update_xaxes(type="log", title_text="차수 deg(v)", row=2, col=2)
    fig.update_yaxes(type="log", title_text="targets 안 장수", row=2, col=2)
    fig.update_layout(
        title=f"skew=True 는 선호적 연결 — n={N:,}, avg_deg=12, seed=20260801",
        template="plotly_white",
        width=1100, height=820,
        legend=dict(orientation="h", y=-0.08, x=0.5, xanchor="center"),
        margin=dict(l=100, r=40, t=100, b=90),
    )

    _show(fig)
    fig.write_image("expy.png", scale=2)
    print("expy.png 저장 완료")
except ImportError as exc:
    print("plotly/kaleido 없음 — 시각화 셀 건너뜀:", exc)
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# | 질문 | 답 |
# |---|---|
# | `skew=True`의 방식 | 선호적 연결(preferential attachment) |
# | 구현 트릭 | `targets` 리스트에 이미 등장한 노드를 **반복 추가** |
# | 왜 차수 비례가 되나 | `random.choice`는 균등인데, **중복 장수**가 확률의 가중치 역할을 한다 |
# | 수식 | $\Pi(v) \propto 1 + t(v) \approx \deg(v)$ |
# | 결과 분포 | 멱법칙 $P(k) \sim k^{-\gamma}$, 측정 $\hat\gamma \approx 2.2$ |
# | 교과서 BA와 차이 | `targets.append(a)`가 루프 **바깥**이라 통이 $(m+1)N$장 → 꼬리가 더 두껍다 |
# | 8장에서의 의미 | 평균 차수는 같은데 $\sum d^2$가 **203배** → 슈퍼 노드, 2홉 폭발 |
#
# 그리고 부수 효과 두 개. `if a != b`로 자기 루프를 버리고 `set`으로 중복 엣지를
# 접기 때문에, 쏠린 쪽은 목표 평균 차수 12를 채우지 못하고 **11.21**에서 멈춘다.
# 허브를 두 번 뽑는 일이 잦아질수록 버려지는 뽑기가 늘기 때문이다.
