# %% [markdown]
# # `Guards.stalled()` — 정체 판정을 손으로 재현하기
#
# 필요 패키지: plotly, kaleido (없으면 표 출력까지만 실행됨)
#
# 20장 `code/guards.py`의 판정 규칙은 세 줄이 전부다.
#
# ```python
# n = self.stall_limit + 1
# if len(self.scores) < n:
#     return False
# window = self.scores[-n:]
# best_before = min(window[:-1])
# return window[-1] >= best_before
# ```
#
# 읽는 순서를 수식으로 두면 이렇다. 점수 열을 $s_1, \dots, s_t$,
# 창 크기를 $n = \text{stall\_limit} + 1$ 이라 할 때
#
# $$ \text{stalled}(t) \;=\; \Big[\, t \ge n \,\Big] \;\wedge\;
# \Big[\; s_t \;\ge\; \min\big(s_{t-n+1}, \dots, s_{t-1}\big) \;\Big] $$
#
# 세 가지를 짚어 둔다.
#
# 1. **점수는 낮을수록 좋다.** `min`을 쓰므로 위반 건수 같은 «줄어야 하는» 값이 전제다.
# 2. **창 크기는 `stall_limit + 1`.** 「몇 번 연속 안 나아졌나」를 재려면 비교 대상이
#    `stall_limit`개 있어야 하고, 거기에 마지막 한 개가 더 붙는다.
# 3. **경계는 `>=`.** 「같음」도 정체다. `>`로 두면 «나빠질 때»만 잡아서 늦다.

# %%
from typing import Optional


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


def stalled(scores, stall_limit: int = 2, strict: bool = False) -> bool:
    """guards.py 의 Guards.stalled() 를 그대로 옮긴 것.

    strict=True 면 경계를 `>` 로 바꿔 «악화만» 정체로 본다 (비교용).
    """
    n = stall_limit + 1
    if len(scores) < n:
        return False
    window = scores[-n:]
    best_before = min(window[:-1])
    return window[-1] > best_before if strict else window[-1] >= best_before


def first_stall_round(scores, stall_limit: int = 2, strict: bool = False) -> Optional[int]:
    """앞에서부터 한 회차씩 쌓으며 처음 정체 판정이 나는 회차."""
    for t in range(1, len(scores) + 1):
        if stalled(scores[:t], stall_limit, strict):
            return t
    return None


# 창이 어떻게 잘리는지 한 번 눈으로 확인
demo = [9, 6, 4, 4, 4, 3]
for t in range(1, len(demo) + 1):
    n = 2 + 1
    w = demo[:t][-n:] if t >= n else None
    print(f"t={t} scores={demo[:t]} window={w} stalled={stalled(demo[:t])}")
# 출력: t=1 scores=[9] window=None stalled=False
# 출력: t=2 scores=[9, 6] window=None stalled=False
# 출력: t=3 scores=[9, 6, 4] window=[9, 6, 4] stalled=False
# 출력: t=4 scores=[9, 6, 4, 4] window=[6, 4, 4] stalled=True
# 출력: t=5 scores=[9, 6, 4, 4, 4] window=[4, 4, 4] stalled=True
# 출력: t=6 scores=[9, 6, 4, 4, 4, 3] window=[4, 4, 3] stalled=False

# %% [markdown]
# 4회차를 보자. 창은 `[6, 4, 4]`, `best_before = min(6, 4) = 4`,
# 마지막 값도 4다. **`4 >= 4` 이므로 정체**. 이게 「같음도 정체로 본다」의 실체다.
#
# 6회차에서 다시 `False`가 되는 것도 중요하다. `stalled()`는 «최근 창»만 보는
# 슬라이딩 윈도우라 상태를 기억하지 않는다. 한 번 정체로 찍혔어도 다시 나아지면
# 판정이 풀린다. 실제 루프에서는 정체가 뜨는 즉시 종료하므로 6회차까지 가지 않는다.

# %%
# 네 가지 점수 시퀀스 (모두 «낮을수록 좋다»)
SEQS = {
    "계속 개선": [9, 7, 5, 4, 3, 2],
    "평탄":     [3, 3, 3, 3, 3, 3],
    "진동":     [8, 5, 6, 5, 6, 5],
    "악화":     [4, 5, 6, 7, 8, 9],
    "느린 개선": [9, 6, 4, 4, 4, 3],
}

print(f"{'시퀀스':<10} {'점수':<24} {'정체 회차(>=)':>13} {'정체 회차(>)':>13}")
print("-" * 64)
for name, s in SEQS.items():
    a = first_stall_round(s, 2, strict=False)
    b = first_stall_round(s, 2, strict=True)
    print(f"{name:<10} {str(s):<24} {str(a) if a else '안 걸림':>13} "
          f"{str(b) if b else '안 걸림':>13}")
# 출력: 시퀀스        점수                           정체 회차(>=)      정체 회차(>)
# 출력: ----------------------------------------------------------------
# 출력: 계속 개선      [9, 7, 5, 4, 3, 2]                안 걸림          안 걸림
# 출력: 평탄         [3, 3, 3, 3, 3, 3]                   3          안 걸림
# 출력: 진동         [8, 5, 6, 5, 6, 5]                   3             3
# 출력: 악화         [4, 5, 6, 7, 8, 9]                   3             3
# 출력: 느린 개선      [9, 6, 4, 4, 4, 3]                   4          안 걸림

# %% [markdown]
# 「같음도 정체」의 효과가 «평탄»과 «느린 개선»에서 갈린다.
#
# - **평탄** `[3,3,3,...]` — `>=`는 3회차에 잡는다. `>`는 **영원히 못 잡는다.**
#   같은 점수를 무한히 반복하는 루프가 상한까지 예산을 다 태우게 된다.
#   본문 주석 «나빠지는 것만 잡으면 늦다»가 가리키는 게 정확히 이 경우다.
# - **느린 개선** `[9,6,4,4,4,3]` — `>=`는 4회차에 끊는다. 6회차까지 갔으면 3으로
#   내려갔을 텐데 못 본다. 즉 「같음도 정체」는 **공짜가 아니다.**
#   정체를 일찍 잡는 대신, 잠깐 멈췄다가 다시 내려가는 루프를 놓친다.
#   그 균형을 조절하는 손잡이가 `stall_limit`이다.

# %%
# stall_limit 를 바꾸면 판정 시점이 어떻게 밀리나
print(f"{'시퀀스':<10} " + " ".join(f"{'L=' + str(L):>7}" for L in (1, 2, 3, 4)))
print("-" * 44)
sweep = {}
for name, s in SEQS.items():
    row = [first_stall_round(s, L) for L in (1, 2, 3, 4)]
    sweep[name] = row
    print(f"{name:<10} " + " ".join(f"{str(r) if r else '—':>7}" for r in row))
# 출력: 시퀀스            L=1     L=2     L=3     L=4
# 출력: --------------------------------------------
# 출력: 계속 개선            —       —       —       —
# 출력: 평탄               2       3       4       5
# 출력: 진동               3       3       4       5
# 출력: 악화               2       3       4       5
# 출력: 느린 개선            4       4       4       5

# %% [markdown]
# 창 크기가 $n = L + 1$ 이므로 «평탄»·«악화»처럼 첫 회차부터 안 나아지는 열은
# 정확히 $L+1$ 회차에서 걸린다. 판정에 필요한 최소 표본이 그만큼이기 때문이다.
#
# $$ \text{첫 정체 회차} \;\ge\; \text{stall\_limit} + 1 $$
#
# 즉 `stall_limit`은 「몇 번을 봐줄 것인가」이고, 그만큼 회차·비용이 더 든다.

# %%
# 시각화 — (1) 시퀀스별 점수 궤적과 정체 지점, (2) >= 와 > 의 대비
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    rounds = list(range(1, 7))
    colors = {"계속 개선": "#2E86AB", "평탄": "#E4572E", "진동": "#8A4FFF",
              "악화": "#B23A48", "느린 개선": "#17A398"}

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("점수 궤적과 정체 판정 지점 (stall_limit=2)",
                        "경계 조건: '같음도 정체(>=)' vs '악화만(>)'"),
    )

    for name, s in SEQS.items():
        fig.add_trace(go.Scatter(x=rounds, y=s, mode="lines+markers", name=name,
                                 line=dict(color=colors[name], width=2)),
                      row=1, col=1)
        at = first_stall_round(s, 2)
        if at:
            fig.add_trace(go.Scatter(x=[at], y=[s[at - 1]], mode="markers",
                                     marker=dict(symbol="x", size=16, line=dict(width=3),
                                                 color=colors[name]),
                                     showlegend=False,
                                     hovertext=f"{name}: {at}회차 정체"),
                          row=1, col=1)

    names = list(SEQS)
    ge = [first_stall_round(SEQS[n], 2, False) or 7 for n in names]
    gt = [first_stall_round(SEQS[n], 2, True) or 7 for n in names]
    fig.add_trace(go.Bar(x=names, y=ge, name=">= (본문 구현)",
                         marker_color="#E4572E",
                         text=[str(v) if v < 7 else "안 걸림" for v in ge],
                         textfont=dict(size=11), cliponaxis=False,
                         textposition="outside"), row=1, col=2)
    fig.add_trace(go.Bar(x=names, y=gt, name="> (악화만)",
                         marker_color="#9AA0A6",
                         text=[str(v) if v < 7 else "안 걸림" for v in gt],
                         textfont=dict(size=11), cliponaxis=False,
                         textposition="outside"), row=1, col=2)

    fig.update_xaxes(title_text="회차", row=1, col=1)
    fig.update_yaxes(title_text="점수 (낮을수록 좋다)", row=1, col=1)
    fig.update_yaxes(title_text="정체 판정 회차 (7=안 걸림)", range=[0, 8.5], row=1, col=2)
    fig.update_layout(height=460, width=1100, barmode="group",
                      title_text="Guards.stalled() — 창 크기 stall_limit+1, 경계 >=",
                      legend=dict(orientation="h", y=-0.18))

    _show(fig)
    fig.write_image("expy.png", scale=2)
    print("expy.png 저장 완료")
except ImportError as e:
    print(f"시각화 건너뜀: {e}")
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# - 창 크기는 `stall_limit + 1`. 점수가 그보다 적으면 무조건 `False` (판정 보류).
# - 비교 대상은 창의 **마지막을 뺀 나머지의 최솟값** — 전체 이력의 최선이 아니라
#   «최근 창 안에서의 최선»이다. 그래서 오래전 최고 기록은 판정에 영향을 주지 않는다.
# - 경계가 `>=`라서 **같아도 정체**. 평탄한 루프를 잡아내는 대신, 잠시 멈췄다가
#   다시 좋아지는 루프는 놓칠 수 있다. `stall_limit`으로 그 관용도를 조절한다.
# - `min`을 쓰므로 **낮을수록 좋은 점수** 전제. 높을수록 좋은 척도를 쓰려면
#   `max` + `<=`로 뒤집어야 한다 (`ex2_stall_detection.py`의 `stalled_at`이 그 일반형).
