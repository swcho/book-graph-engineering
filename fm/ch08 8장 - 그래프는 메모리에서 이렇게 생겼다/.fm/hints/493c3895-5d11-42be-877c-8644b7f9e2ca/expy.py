# %% [markdown]
# # `build_csr()`의 오프셋 배열 만들기
#
# 8장 예제 1·2의 `build_csr()`이 하는 일을 **아주 작은 그래프**로 손으로 따라간다.
#
# 핵심 한 줄: **오프셋은 차수의 누적합(prefix sum)이다.**
#
# $$\text{offset}[0] = 0, \qquad \text{offset}[i+1] = \text{offset}[i] + \deg[i]$$
#
# 순서는 항상 셋이다.
#
# 1. 차수 세기 (`deg`)
# 2. 누적합으로 경계 만들기 (`offset`)
# 3. 커서로 이웃 채우기 (`nbr`)

# %%
# 필요 패키지: plotly, kaleido (시각화 셀에서만 사용. 없으면 그 셀만 건너뛰면 된다)
from array import array


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


N = 6
EDGES = [(0, 1), (0, 2), (0, 3), (1, 2), (2, 4), (3, 4), (4, 5)]

print("노드", N, "개 / 엣지", len(EDGES), "개")
print("엣지:", EDGES)
# 출력:
# 노드 6 개 / 엣지 7 개
# 엣지: [(0, 1), (0, 2), (0, 3), (1, 2), (2, 4), (3, 4), (4, 5)]

# %% [markdown]
# ## 1단계 — 차수 세기
#
# 무향 그래프이므로 엣지 하나가 **양쪽 차수를 각각 1씩** 올린다.
# 그래서 차수의 합은 항상 $2E$가 된다(악수 보조정리).

# %%
deg = [0] * N
for a, b in EDGES:
    deg[a] += 1
    deg[b] += 1

print("deg      =", deg)
print("sum(deg) =", sum(deg), " 2E =", 2 * len(EDGES))
# 출력:
# deg      = [3, 2, 3, 2, 3, 1]
# sum(deg) = 14  2E = 14

# %% [markdown]
# ## 2단계 — 누적합으로 오프셋 만들기
#
# 이웃 배열 `nbr`을 한 줄로 쭉 이어 붙일 때, 노드 $i$의 구간이 어디서 시작하는지만 알면 된다.
# 노드 0부터 $i-1$까지의 이웃을 다 놓은 뒤가 곧 노드 $i$의 시작점이므로
#
# $$\text{offset}[i] = \sum_{k<i} \deg[k]$$
#
# 이것을 매번 다시 더하지 않고 한 번의 루프로 굴려서 얻는 게 누적합이다.
# 배열 길이가 $n+1$인 이유는 **마지막 노드의 끝 경계**가 필요하기 때문이다.
# 그리고 $\text{offset}[n] = 2E$ 는 곧 `nbr` 배열의 전체 길이다.

# %%
offset = array("i", [0] * (N + 1))
for i in range(N):
    offset[i + 1] = offset[i] + deg[i]
    print(f"  offset[{i+1}] = offset[{i}] + deg[{i}] = {offset[i]} + {deg[i]} = {offset[i+1]}")

print("offset    =", list(offset))
print("offset[n] =", offset[N], "= 2E =", 2 * len(EDGES), "→ nbr 배열의 길이")
# 출력:
#   offset[1] = offset[0] + deg[0] = 0 + 3 = 3
#   offset[2] = offset[1] + deg[1] = 3 + 2 = 5
#   offset[3] = offset[2] + deg[2] = 5 + 3 = 8
#   offset[4] = offset[3] + deg[3] = 8 + 2 = 10
#   offset[5] = offset[4] + deg[4] = 10 + 3 = 13
#   offset[6] = offset[5] + deg[5] = 13 + 1 = 14
# offset    = [0, 3, 5, 8, 10, 13, 14]
# offset[n] = 14 = 2E = 14 → nbr 배열의 길이

# %% [markdown]
# 오프셋이 만들어지면 **차수는 뺄셈으로 되살아난다**. 그래서 `deg` 배열은 버려도 된다.
#
# $$\deg[i] = \text{offset}[i+1] - \text{offset}[i]$$

# %%
print("뺄셈으로 복원한 차수 :", [offset[i + 1] - offset[i] for i in range(N)])
print("원래 차수            :", deg)
# 출력:
# 뺄셈으로 복원한 차수 : [3, 2, 3, 2, 3, 1]
# 원래 차수            : [3, 2, 3, 2, 3, 1]

# %% [markdown]
# ## 3단계 — 커서로 이웃 채우기
#
# 각 노드의 구간 시작점을 **복사**해서 쓰기 커서로 쓴다. 쓸 때마다 커서를 한 칸 밀면
# 엣지 목록을 딱 한 번만 훑고도 이웃이 제자리에 들어간다.
#
# `cursor = list(offset[:n])`에서 **복사가 핵심**이다. `offset`을 직접 밀면 경계가 망가진다(아래 4단계).

# %%
cursor = list(offset[:N])
nbr = array("i", [0] * offset[N])

print("초기 커서:", cursor)
for a, b in EDGES:
    nbr[cursor[a]] = b
    cursor[a] += 1
    nbr[cursor[b]] = a
    cursor[b] += 1
    print(f"  엣지 ({a},{b}) 처리 후 커서 {cursor}  nbr {list(nbr)}")
# 출력:
# 초기 커서: [0, 3, 5, 8, 10, 13]
#   엣지 (0,1) 처리 후 커서 [1, 4, 5, 8, 10, 13]  nbr [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
#   엣지 (0,2) 처리 후 커서 [2, 4, 6, 8, 10, 13]  nbr [1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
#   엣지 (0,3) 처리 후 커서 [3, 4, 6, 9, 10, 13]  nbr [1, 2, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
#   엣지 (1,2) 처리 후 커서 [3, 5, 7, 9, 10, 13]  nbr [1, 2, 3, 0, 2, 0, 1, 0, 0, 0, 0, 0, 0, 0]
#   엣지 (2,4) 처리 후 커서 [3, 5, 8, 9, 11, 13]  nbr [1, 2, 3, 0, 2, 0, 1, 4, 0, 0, 2, 0, 0, 0]
#   엣지 (3,4) 처리 후 커서 [3, 5, 8, 10, 12, 13]  nbr [1, 2, 3, 0, 2, 0, 1, 4, 0, 4, 2, 3, 0, 0]
#   엣지 (4,5) 처리 후 커서 [3, 5, 8, 10, 13, 14]  nbr [1, 2, 3, 0, 2, 0, 1, 4, 0, 4, 2, 3, 5, 4]

# %%
print("최종 커서 :", cursor, "  (offset[1:]과 같아야 한다)")
print("offset[1:]:", list(offset[1:]))
print()
print("nbr =", list(nbr))
print()
for u in range(N):
    print(f"  이웃({u}) = nbr[{offset[u]}:{offset[u+1]}] = {list(nbr[offset[u]:offset[u+1]])}")
# 출력:
# 최종 커서 : [3, 5, 8, 10, 13, 14]   (offset[1:]과 같아야 한다)
# offset[1:]: [3, 5, 8, 10, 13, 14]
#
# nbr = [1, 2, 3, 0, 2, 0, 1, 4, 0, 4, 2, 3, 5, 4]
#
#   이웃(0) = nbr[0:3] = [1, 2, 3]
#   이웃(1) = nbr[3:5] = [0, 2]
#   이웃(2) = nbr[5:8] = [0, 1, 4]
#   이웃(3) = nbr[8:10] = [0, 4]
#   이웃(4) = nbr[10:13] = [2, 3, 5]
#   이웃(5) = nbr[13:14] = [4]

# %% [markdown]
# ## 4단계 — 흔한 실수: `offset`을 커서로 쓰기
#
# 복사하지 않고 `offset` 자체를 밀면 채우기가 끝난 뒤 `offset[i]`에는
# 원래 시작점이 아니라 **끝 경계**가 들어 있다. 즉 `offset`이 한 칸 왼쪽으로 밀린 배열이 되고,
# 이후 모든 이웃 조회가 엉뚱한 구간을 읽는다.

# %%
bad = array("i", list(offset))  # 복사 없이 이걸 커서로 쓴다고 가정
bad_nbr = array("i", [0] * offset[N])
for a, b in EDGES:
    bad_nbr[bad[a]] = b
    bad[a] += 1
    bad_nbr[bad[b]] = a
    bad[b] += 1

print("망가진 offset :", list(bad))
print("정상 offset   :", list(offset))
print("→ 망가진 쪽으로 읽은 이웃(0) =", list(bad_nbr[bad[0] : bad[1]]), "  (정답은 [1, 2, 3])")
# 출력:
# 망가진 offset : [3, 5, 8, 10, 13, 14, 14]
# 정상 offset   : [0, 3, 5, 8, 10, 13, 14]
# → 망가진 쪽으로 읽은 이웃(0) = [0, 2]   (정답은 [1, 2, 3])

# %% [markdown]
# ## 정리: 한 함수로 묶은 `build_csr()`
#
# 8장 예제와 같은 형태다. 세 단계가 그대로 보인다.

# %%
def build_csr(edges, n):
    deg = [0] * n                                   # 1) 차수 세기
    for a, b in edges:
        deg[a] += 1
        deg[b] += 1
    offset = array("i", [0] * (n + 1))              # 2) 누적합
    for i in range(n):
        offset[i + 1] = offset[i] + deg[i]
    cursor = list(offset[:n])                       # 3) 커서 복사 후 채우기
    nbr = array("i", [0] * offset[n])
    for a, b in edges:
        nbr[cursor[a]] = b
        cursor[a] += 1
        nbr[cursor[b]] = a
        cursor[b] += 1
    return offset, nbr


off2, nbr2 = build_csr(EDGES, N)
print("offset 일치:", list(off2) == list(offset))
print("nbr    일치:", list(nbr2) == list(nbr))
# 출력:
# offset 일치: True
# nbr    일치: True

# %% [markdown]
# ## 시각화
#
# 위: 차수 막대와 그 위를 계단으로 지나가는 누적합(= 오프셋).
# 아래: `nbr` 배열 14칸이 오프셋 경계로 노드별 구간으로 잘려 있는 모습.

# %%
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    palette = ["#4C78A8", "#F58518", "#54A24B", "#E45756", "#72B7B2", "#B279A2"]

    fig = make_subplots(
        rows=2,
        cols=1,
        row_heights=[0.45, 0.55],
        vertical_spacing=0.16,
        subplot_titles=(
            "1~2단계: 차수(막대)와 누적합 offset(계단)",
            "3단계: nbr 배열이 offset 경계로 잘린 모습",
        ),
    )

    # 위: 차수 막대 + 누적합 계단
    fig.add_trace(
        go.Bar(
            x=list(range(N)),
            y=deg,
            marker_color=palette,
            opacity=0.55,
            text=[f"deg={d}" for d in deg],
            textposition="auto",
            name="deg[i] (차수)",
            showlegend=True,
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=list(range(N + 1)),
            y=list(offset),
            mode="lines+markers+text",
            line_shape="hv",
            line=dict(color="#333", width=2),
            marker=dict(size=8, color="#333"),
            text=[str(v) for v in offset],
            textposition="top center",
            textfont=dict(size=12, color="#333"),
            name="offset[i] (차수의 누적합)",
        ),
        row=1,
        col=1,
    )

    # 아래: nbr 배열 셀. x = 배열 인덱스, 소유 노드별 색
    owner = []
    for u in range(N):
        owner += [u] * (offset[u + 1] - offset[u])
    fig.add_trace(
        go.Bar(
            x=list(range(len(nbr))),
            y=[1] * len(nbr),
            marker=dict(color=[palette[o] for o in owner], line=dict(color="white", width=1)),
            text=[str(v) for v in nbr],
            textposition="inside",
            hovertext=[f"nbr[{i}]={nbr[i]}  소유 노드 {owner[i]}" for i in range(len(nbr))],
            hoverinfo="text",
            showlegend=False,
        ),
        row=2,
        col=1,
    )
    for u in range(N):
        mid = (offset[u] + offset[u + 1] - 1) / 2
        fig.add_annotation(
            x=mid,
            y=1.18,
            text=f"노드 {u}<br>[{offset[u]}:{offset[u+1]})",
            showarrow=False,
            font=dict(size=10, color=palette[u]),
            row=2,
            col=1,
        )
    for b in list(offset)[1:-1]:
        fig.add_vline(x=b - 0.5, line=dict(color="#888", width=1, dash="dot"), row=2, col=1)

    fig.update_xaxes(title_text="노드 번호 i", dtick=1, row=1, col=1)
    fig.update_yaxes(title_text="개수 / 누적합", range=[0, 17.5], row=1, col=1)
    fig.update_xaxes(title_text="nbr 배열 인덱스", dtick=1, row=2, col=1)
    fig.update_yaxes(showticklabels=False, range=[0, 1.6], row=2, col=1)
    fig.update_layout(
        title="offset = 차수의 누적합, nbr = 그 경계로 잘린 이웃 배열",
        height=680,
        width=900,
        bargap=0.08,
        template="plotly_white",
        margin=dict(t=110, b=90),
        font=dict(family="Apple SD Gothic Neo, Noto Sans KR, sans-serif", size=12),
        legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center"),
    )

    _show(fig)

    import pathlib

    out = pathlib.Path(__file__).resolve().parent / "expy.png" if "__file__" in dir() else pathlib.Path("expy.png")
    fig.write_image(str(out), scale=2)
    print("저장:", out)
except ImportError as e:
    print("plotly/kaleido 없음 — 시각화 생략:", e)
# 출력:
# 저장: .../expy.png
