# %% [markdown]
# # 슈퍼 노드 판정 — 「전체 평균 차수의 5배 초과」
#
# `ex3_graph_smells.py`의 `smell_supernode()`가 하는 일을 단계별로 재현한다.
#
# 1. 차수 분포 계산 (`degrees`)
# 2. 평균 차수 $\bar{d}$
# 3. 5배 임계 $5\bar{d}$
# 4. 슈퍼 노드 판정 $\deg(v) > 5\bar{d}$
# 5. 평균이 슈퍼 노드에게 끌려가는 문제 → 중앙값·백분위수 대안
#
# 필요 패키지: plotly (시각화), kaleido (PNG 저장). 판정 로직 자체는 표준 라이브러리만 쓴다.
#   pip install plotly kaleido

# %%
from collections import Counter

import plotly.graph_objects as go


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# %% [markdown]
# ## 0. 예제 그래프 — `ex3_graph_smells.py`와 동일
#
# 부품 40개, 카테고리 3개(`미분류`/`체결`/`전자`), 공급사 2개, 고아 1개.
# 핵심은 **40개 부품 중 30개가 `hub`(= '미분류')에 붙어 있다**는 점이다.

# %%
NODES = {f"n{i}": {"label": "Part"} for i in range(1, 41)}
NODES.update(
    {
        "hub": {"label": "Category", "name": "미분류"},  # ← fallback 카테고리
        "cat1": {"label": "Category", "name": "체결"},
        "cat2": {"label": "Category", "name": "전자"},
        "orph": {"label": "Part", "name": "고아 부품"},
        "dupA": {"label": "Supplier", "name": "가온테크"},
        "dupB": {"label": "Supplier", "name": "가온테크(주)"},
    }
)

EDGES = []
for i in range(1, 31):
    EDGES.append((f"n{i}", "IN_CATEGORY", "hub"))  # 슈퍼 노드
for i in range(31, 36):
    EDGES.append((f"n{i}", "IN_CATEGORY", "cat1"))
for i in range(36, 41):
    EDGES.append((f"n{i}", "IN_CATEGORY", "cat2"))
EDGES += [
    ("n1", "SUPPLIED_BY", "dupA"),
    ("n2", "SUPPLIED_BY", "dupB"),  # 중복 엔티티
    ("n3", "REPLACES", "n4"),
    ("n4", "REPLACES", "n5"),
    ("n5", "REPLACES", "n3"),  # 사이클
    ("n6", "IN_CATEGORY", "cat1"),
    ("n6", "IN_CATEGORY", "cat2"),  # 다중 소속
]

print(f"노드 {len(NODES)}개, 엣지 {len(EDGES)}개")
# 출력: 노드 46개, 엣지 47개

# %% [markdown]
# ## 1. 차수 분포 — 엣지 양끝을 모두 센다
#
# 방향을 구분하지 않는 **무방향 총 차수**다. 엣지 하나가 두 번 세어지므로
#
# $$\sum_{v} \deg(v) = 2\,|E|$$

# %%
def degrees(edges):
    d = Counter()
    for a, _, b in edges:
        d[a] += 1
        d[b] += 1
    return d


d = degrees(EDGES)

print(f"차수가 잡힌 노드 수 = {len(d)}   (전체 {len(NODES)}개 중)")
print(f"차수 총합 = {sum(d.values())}  == 2 * |E| = {2 * len(EDGES)}")
print(f"상위 6개 = {d.most_common(6)}")
print(f"'orph' 가 Counter 에 있는가? {'orph' in d}")
# 출력: 차수가 잡힌 노드 수 = 45   (전체 46개 중)
# 출력: 차수 총합 = 94  == 2 * |E| = 94
# 출력: 상위 6개 = [('hub', 30), ('cat1', 6), ('cat2', 6), ('n3', 3), ('n4', 3), ('n5', 3)]
# 출력: 'orph' 가 Counter 에 있는가? False

# %% [markdown]
# 고아 노드 `orph`는 `Counter`에 키 자체가 없다.
# 그래서 다음 단계의 평균은 **`len(NODES)`가 아니라 `len(d)`로 나눈다**.
# 분모가 46이 아니라 45라는 뜻이다.

# %% [markdown]
# ## 2. 평균 차수와 3. 5배 임계
#
# $$\bar{d} = \frac{\sum_{u \in V_E} \deg(u)}{|V_E|} = \frac{2|E|}{|V_E|},
# \qquad \text{threshold} = 5\,\bar{d}$$

# %%
avg = sum(d.values()) / len(d)
FACTOR = 5
threshold = avg * FACTOR

print(f"평균 차수  avg = {sum(d.values())} / {len(d)} = {avg:.4f}")
print(f"임계값     5 * avg = {threshold:.4f}")
# 출력: 평균 차수  avg = 94 / 45 = 2.0889
# 출력: 임계값     5 * avg = 10.4444

# %% [markdown]
# ## 4. 슈퍼 노드 판정
#
# $$\text{supernode}(v) \iff \deg(v) > 5\,\bar{d}$$
#
# `>=`가 아니라 `>` 이므로 **정확히 5배는 걸리지 않는다**.

# %%
def smell_supernode(nodes, edges, factor=5):
    d = degrees(edges)
    if not d:
        return []
    avg = sum(d.values()) / len(d)
    return [(v, n) for v, n in d.most_common() if n > avg * factor]


sn = smell_supernode(NODES, EDGES)
print(f"[슈퍼 노드] 평균 차수의 5배 초과 — {len(sn)}건")
for v, n in sn:
    print(f"    {v} ({NODES[v].get('name', '')}) 차수 {n}  = 평균의 {n / avg:.1f}배")
# 출력: [슈퍼 노드] 평균 차수의 5배 초과 — 1건
# 출력:     hub (미분류) 차수 30  = 평균의 14.4배

# %%
# 2등과의 격차 확인 — 왜 판정이 깔끔하게 떨어지는가
for v, n in d.most_common(3):
    mark = "★ 슈퍼 노드" if n > threshold else "  (통과)"
    print(f"  {v:5s} {NODES[v].get('name', ''):6s} 차수 {n:3d}  평균의 {n / avg:5.1f}배  {mark}")
# 출력:   hub   미분류    차수  30  평균의  14.4배  ★ 슈퍼 노드
# 출력:   cat1  체결      차수   6  평균의   2.9배    (통과)
# 출력:   cat2  전자      차수   6  평균의   2.9배    (통과)

# %% [markdown]
# `체결`·`전자`도 평균의 2.9배지만 임계선 10.44에는 못 미친다.
# fallback 카테고리 `미분류`만 혼자 14.4배로 튀어 나온다.
# **개별 엣지는 전부 스키마상 합법**이라 SHACL로는 못 잡고, 세어 봐야 보인다.

# %% [markdown]
# ## 5. 시각화 — 차수 분포와 임계선

# %%
counts = sorted(d.values())
dist = Counter(counts)

fig = go.Figure()
fig.add_trace(
    go.Histogram(
        x=counts,
        xbins=dict(start=-0.5, end=31.5, size=1),
        name="노드 수",
        marker=dict(color="#4C78A8", line=dict(color="white", width=0.5)),
        hovertemplate="차수 %{x}<br>노드 %{y}개<extra></extra>",
    )
)
fig.add_vline(
    x=avg,
    line=dict(color="#54A24B", width=2, dash="dot"),
    annotation_text=f"평균 {avg:.2f}",
    annotation_position="top right",
)
fig.add_vline(
    x=threshold,
    line=dict(color="#E45756", width=2, dash="dash"),
    annotation_text=f"임계 5×평균 = {threshold:.2f}",
    annotation_position="top right",
)
fig.add_annotation(
    x=30,
    y=1,
    ax=-30,
    ay=-70,
    text="hub «미분류»<br>차수 30 (노드 1개)",
    showarrow=True,
    arrowhead=2,
    font=dict(color="#E45756", size=12),
)
fig.update_layout(
    title="차수 분포와 슈퍼 노드 임계선 (평균의 5배 초과)",
    xaxis_title="차수 (degree)",
    yaxis_title="노드 수",
    xaxis=dict(range=[-1.5, 33], dtick=5),
    yaxis=dict(range=[0, 42], dtick=5),
    bargap=0.05,
    template="plotly_white",
    width=900,
    height=440,
    showlegend=False,
)
_show(fig)

print(f"차수별 노드 수: {dict(sorted(dist.items()))}")
# 출력: 차수별 노드 수: {1: 36, 2: 2, 3: 4, 6: 2, 30: 1}

# %%
# 정적 이미지 저장 (kaleido 필요). HTML 로는 저장하지 않는다.
import os

_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
fig.write_image(_png, scale=2)
print(f"saved: {_png}")
# 출력: saved: .../expy.png

# %% [markdown]
# 왼쪽에 차수 1짜리 노드 36개가 몰려 있고(초록 점선 = 평균 2.09가 거의 그 안에 있다),
# 오른쪽 끝 차수 30 자리에 `hub` 하나가 외따로 떨어져 있다.
# 빨간 파선(임계 10.44)과 데이터 사이가 텅 비어 있다 —
# 전형적인 **두꺼운 꼬리(heavy-tail)** 분포이고, 그래서 판정이 애매하지 않게 떨어진다.

# %% [markdown]
# ## 6. 평균의 함정 — 잡으려는 대상이 임계선을 끌어올린다
#
# `avg`는 **슈퍼 노드 자신의 차수를 포함해서** 계산된다.
# 즉 슈퍼 노드가 클수록 임계선도 같이 올라가 자기 자신을 숨긴다(self-masking).

# %%
without_hub = Counter({k: v for k, v in d.items() if k != "hub"})
avg_wo = sum(without_hub.values()) / len(without_hub)

print(f"hub 포함 평균 = {avg:.4f}   → 임계 {avg * 5:.4f}")
print(f"hub 제외 평균 = {avg_wo:.4f}   → 임계 {avg_wo * 5:.4f}")
print(f"hub 가 총 차수의 {30 / sum(d.values()) * 100:.1f}% 를 혼자 차지한다")
# 출력: hub 포함 평균 = 2.0889   → 임계 10.4444
# 출력: hub 제외 평균 = 1.4545   → 임계 7.2727
# 출력: hub 가 총 차수의 31.9% 를 혼자 차지한다

# %%
# 극단 사례 — 별(star) 그래프에서는 평균 기준이 아예 무력해진다.
#   중심 노드 1개 + 잎 k 개. 차수 총합 = 2k, 노드 수 = k+1.
#   avg = 2k/(k+1) → k 가 커지면 2 에 수렴, 중심 차수 k 는 무한히 커진다.
#   → 잎이 아주 많으면 잡히지만, 작은 별 여러 개가 섞이면 평균이 올라가 안 잡힌다.
for k in (4, 5, 9, 10):
    star = Counter({"c": k})
    star.update({f"l{i}": 1 for i in range(k)})
    a = sum(star.values()) / len(star)
    print(f"  잎 {k:2d}개: avg={a:.3f}, 임계={a * 5:.3f}, 중심차수={k} → {'검출' if k > a * 5 else '미검출'}")
# 출력:   잎  4개: avg=1.600, 임계=8.000, 중심차수=4 → 미검출
# 출력:   잎  5개: avg=1.667, 임계=8.333, 중심차수=5 → 미검출
# 출력:   잎  9개: avg=1.800, 임계=9.000, 중심차수=9 → 미검출
# 출력:   잎 10개: avg=1.818, 임계=9.091, 중심차수=10 → 검출

# %% [markdown]
# ## 7. 대안 기준 — 중앙값·백분위수·MAD
#
# 차수 분포는 멱법칙에 가까운 두꺼운 꼬리라 평균이 애초에 대표값으로 부적절하다.
# 이상치에 둔감한(robust) 기준을 쓰면 자기 마스킹을 피할 수 있다.
#
# - 중앙값 기준: $\deg(v) > 5 \cdot \mathrm{median}$
# - 백분위수 기준: $\deg(v) > P_{99}$
# - MAD 기준: $\deg(v) > \mathrm{median} + k \cdot \mathrm{MAD}$, &nbsp; $\mathrm{MAD} = \mathrm{median}(|x_i - \mathrm{median}|)$

# %%
import statistics

vals = sorted(d.values())
med = statistics.median(vals)
mad = statistics.median([abs(x - med) for x in vals])


def percentile(xs, p):
    xs = sorted(xs)
    i = min(int(round((p / 100) * (len(xs) - 1))), len(xs) - 1)
    return xs[i]


criteria = {
    "평균 × 5 (예제 방식)": avg * 5,
    "중앙값 × 5": med * 5,
    "P95": percentile(vals, 95),
    "P99": percentile(vals, 99),
    "중앙값 + 5×MAD": med + 5 * mad,
    "절대 임계 (>20)": 20,
}

print(f"median={med}, MAD={mad}\n")
print(f"{'기준':<22} {'임계값':>9}   검출 노드")
for name, thr in criteria.items():
    hits = [(v, n) for v, n in d.most_common() if n > thr]
    label = ", ".join(f"{v}({n})" for v, n in hits) or "없음"
    print(f"{name:<22} {thr:>9.2f}   {label}")
# 출력: median=1, MAD=0
# 출력:
# 출력: 기준                        임계값   검출 노드
# 출력: 평균 × 5 (예제 방식)          10.44   hub(30)
# 출력: 중앙값 × 5                     5.00   hub(30), cat1(6), cat2(6)
# 출력: P95                            6.00   hub(30)
# 출력: P99                           30.00   없음
# 출력: 중앙값 + 5×MAD                 1.00   hub(30), cat1(6), cat2(6), n3(3), n4(3), n5(3), n6(3), n1(2), n2(2)
# 출력: 절대 임계 (>20)                20.00   hub(30)

# %% [markdown]
# 읽는 법:
#
# - **평균 × 5** — 이 데이터에서는 잘 맞는다. 1등과 2등이 5배 벌어져 있어서 운이 좋았다.
# - **중앙값 × 5** — 중앙값이 1이라 임계가 5로 낮아진다. `체결`·`전자`까지 딸려 온다. 민감도가 높다.
# - **P99** — 상위 1%가 노드 45개 기준 0.45개라 인덱스 반올림으로 `hub` 자신이 임계값이 되어 버린다.
#   `>` 비교라 아무것도 안 잡힌다. **작은 그래프에서 백분위수는 위험하다.**
# - **MAD** — 차수 1짜리 노드가 과반이라 MAD가 0이 된다. 임계가 median 그대로여서 대량 오검출.
# - **절대 임계** — 시스템 한계(예: 인접 리스트 페이지 크기)에 맞춰 정하면 그래프가 커져도 안 흔들린다.
#
# 결론: **은탄환은 없다.** 자기 그래프의 차수 분포를 실제로 그려 보고,
# 관계 타입별로 나눠서(`IN_CATEGORY` 차수와 `SUPPLIED_BY` 차수를 섞지 말고) 임계를 정해야 한다.
# 예제가 평균을 쓴 이유는 정교해서가 아니라, "전체를 세어 봐야 나오는 **상대값**이라
# SHACL 로는 못 잡는다"는 사실을 가장 짧게 보여 주기 때문이다.

# %% [markdown]
# ## 8. 정리
#
# | 단계 | 코드 | 예제 값 |
# |---|---|---|
# | 차수 계산 | `d[a] += 1; d[b] += 1` | 총합 94 (= 2×47) |
# | 평균 | `sum(d.values()) / len(d)` | 94 / **45** ≈ 2.0889 |
# | 임계 | `avg * factor`, `factor=5` | ≈ 10.4444 |
# | 판정 | `n > avg * factor` | `hub`('미분류') 차수 30 — **1건** |
#
# fallback 카테고리('미분류')는 "나머지 전부"를 받기 때문에 구조적으로 슈퍼 노드가 된다.
# 그런데 개별 엣지는 전부 합법이라 형태 검사는 통과한다.
# 그래서 검증은 두 겹 — **1층 SHACL(참/거짓이 분명한 형태 제약)**,
# **2층 스멜(세어 보고 이상하면 사람이 본다)**. 2층은 자동으로 고치지 않는다.
