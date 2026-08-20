# %% [markdown]
# # 층별 타임아웃의 함정 — 아무도 잘못하지 않았는데 전체가 실패한다
#
# `ex2_timeout_budget.py`가 보여주는 문제를 재현한다.
#
# 4단계 파이프라인(검색 → 요약 → 초안 → 검토)이 있고,
# 사용자에게 약속한 전체 응답 시간(바깥 타임아웃)은 **15초**다.
# 그런데 각 단계에는 **각자 10초**의 타임아웃을 걸어 두었다.
#
# 핵심 모순은 한 줄의 부등식이다:
#
# $$\sum_{i} T_i^{\text{step}} = 4 \times 10 = 40 \;>\; T^{\text{outer}} = 15$$
#
# 각 층의 타임아웃 합이 바깥 타임아웃보다 크면 그 설정은 «거짓말»이다.
# 아무도 지킬 수 없는 약속이기 때문이다.

# %%
# 필요 패키지: plotly, kaleido (시각화 셀에서만 사용. 시뮬레이션 자체는 표준 라이브러리만 필요)

#        이름     실제 걸리는 시간   쓸모 있으려면 최소한 필요한 시간
STEPS = [("검색", 4.0, 1.0), ("요약", 3.0, 1.0), ("초안", 9.0, 3.0), ("검토", 2.0, 2.0)]
OUTER_TIMEOUT = 15.0     # 사용자에게 약속한 응답 시간
PER_STEP_TIMEOUT = 10.0  # 각 단계에 건 타임아웃

total_step_timeout = len(STEPS) * PER_STEP_TIMEOUT
print(f"바깥 타임아웃: {OUTER_TIMEOUT:.0f}초, 층별 타임아웃 합: {total_step_timeout:.0f}초")
print(f"층별 합({total_step_timeout:.0f}) > 바깥({OUTER_TIMEOUT:.0f}) → 지킬 수 없는 약속")
# 출력: 바깥 타임아웃: 15초, 층별 타임아웃 합: 40초
# 출력: 층별 합(40) > 바깥(15) → 지킬 수 없는 약속

# %% [markdown]
# ## 방식 1 — 층마다 따로 건 타임아웃 (naive)
#
# 각 단계는 자기 타임아웃(10초)만 본다. 전체 예산은 아무도 보지 않는다.
#
# - 검색 4초 (10초 이내, 통과)
# - 요약 3초 (10초 이내, 통과)
# - 초안 9초 (10초 이내, 통과) — 그런데 누적 $4+3+9=16 > 15$
# - 검토는 시작조차 못 한다

# %%
def run_naive():
    """각 층이 자기 타임아웃만 본다."""
    spent, log = 0.0, []
    for name, need, _min in STEPS:
        took = min(need, PER_STEP_TIMEOUT)
        spent += took
        cut = took < need
        log.append((name, need, PER_STEP_TIMEOUT, took,
                    "단계 타임아웃" if cut else "완료"))
        if spent >= OUTER_TIMEOUT:
            log.append(("(바깥)", 0, OUTER_TIMEOUT, spent, "전체 타임아웃 — 여기서 끊긴다"))
            break
    return spent, log


def show(title, spent, log):
    print(f"\n[{title}]")
    print(f"  {'단계':<8}{'필요':>6}{'허용':>8}{'실제':>8}  결과")
    for name, need, allow, took, res in log:
        need_s = f"{need:.1f}" if need else "-"
        print(f"  {name:<8}{need_s:>6}{allow:>8}{took:>8.1f}  {res}")
    print(f"  총 {spent:.1f}초 / 약속 {OUTER_TIMEOUT:.1f}초")


naive_spent, naive_log = run_naive()
show("층마다 따로 건 타임아웃", naive_spent, naive_log)
# 출력:
# [층마다 따로 건 타임아웃]
#   단계        필요      허용      실제  결과
#   검색       4.0    10.0     4.0  완료
#   요약       3.0    10.0     3.0  완료
#   초안       9.0    10.0     9.0  완료
#   (바깥)       -    15.0    16.0  전체 타임아웃 — 여기서 끊긴다
#   총 16.0초 / 약속 15.0초

# %% [markdown]
# **여기가 문제의 핵심이다.**
#
# 검색·요약·초안 모두 자기 타임아웃 10초를 지켰다. 어느 단계도 «잘못»하지 않았다.
# 그런데 초안이 9초를 다 쓰고 나면 누적 16초 — 약속한 15초를 넘어 바깥이 먼저 끊긴다.
# **검토 단계에는 도달조차 못 하고, 전체 요청은 실패한다.**
#
# 지역적으로 모두 정상인데 전역적으로 실패하는 전형적인 구성 오류다.

# %% [markdown]
# ## 방식 2 — 남은 예산을 나눠 쓰기 (budget)
#
# 단계마다 «최소 필요분» $m_i$를 미리 선언해 둔다: 검색 1, 요약 1, 초안 3, 검토 2초.
# $i$번째 단계가 쓸 수 있는 시간은 뒤 단계들의 최소분을 떼어 놓은 나머지다:
#
# $$\text{allow}_i = \max\!\Big(0,\; \text{remaining} - \sum_{j>i} m_j\Big)$$
#
# 초안은 $15 - (4+3) - 2 = 6$초만 허용받고 잘리지만, 검토는 필요한 2초를 온전히 받는다.

# %%
def run_budget():
    """남은 예산을 보고 각 층의 타임아웃을 그때그때 정한다."""
    remaining, log = OUTER_TIMEOUT, []
    for i, (name, need, _min) in enumerate(STEPS):
        # 뒤에 남은 단계들의 «최소 필요분»을 먼저 떼어 놓는다
        reserved = sum(m for _, _, m in STEPS[i + 1:])
        allow = max(0.0, remaining - reserved)
        took = min(need, allow)
        remaining -= took
        cut = took < need
        log.append((name, need, round(allow, 1), took,
                    "잘림 — 부분 결과 반환" if cut else "완료"))
    return OUTER_TIMEOUT - remaining, log


budget_spent, budget_log = run_budget()
show("남은 예산을 나눠 쓰기", budget_spent, budget_log)
# 출력:
# [남은 예산을 나눠 쓰기]
#   단계        필요      허용      실제  결과
#   검색       4.0     9.0     4.0  완료
#   요약       3.0     6.0     3.0  완료
#   초안       9.0     6.0     6.0  잘림 — 부분 결과 반환
#   검토       2.0     2.0     2.0  완료
#   총 15.0초 / 약속 15.0초

# %% [markdown]
# ## 비교 정리
#
# | | 층별 타임아웃 | 예산 배분 |
# |---|---|---|
# | 초안 | 9초 전부 씀 (자기 한도 10초 이내) | 6초에서 잘림, 부분 결과 |
# | 검토 | **도달 못 함** | 필요한 2초 온전히 확보 |
# | 전체 | 15초 초과 → 실패 | 15초 정확히 지킴 |
#
# 「완성 안 된 초안을 검토한 결과」와 「초안만 있고 검토 못 한 결과」 중
# 어느 쪽이 나은지는 도메인이 정한다. 중요한 건 예산 방식에서는 **고를 수 있게** 된다는 점이다.

# %%
# 시각화 — 시간축 간트 스타일로 두 방식을 나란히 비교
import plotly.graph_objects as go


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


COLORS = {"완료": "#4C78A8", "잘림": "#F2A93B", "실패": "#D6564C"}

fig = go.Figure()


def add_bars(row_label, log, y):
    t = 0.0
    for name, need, _allow, took, res in log:
        if name == "(바깥)":
            continue
        color = COLORS["완료"] if "완료" in res else COLORS["잘림"]
        fig.add_trace(go.Bar(
            x=[took], y=[y], base=[t], orientation="h",
            marker=dict(color=color, line=dict(color="white", width=1)),
            text=f"{name} {took:.0f}s", textposition="inside",
            insidetextanchor="middle", showlegend=False,
        ))
        t += took
    return t


add_bars("naive", naive_log, "층별 타임아웃")
# naive에서 도달 못 한 '검토'를 실패 표시로 추가
fig.add_trace(go.Bar(
    x=[2.0], y=["층별 타임아웃"], base=[16.0], orientation="h",
    marker=dict(color=COLORS["실패"], line=dict(color="white", width=1), opacity=0.55),
    text="검토 도달 못 함", textposition="inside", insidetextanchor="middle",
    showlegend=False,
))
add_bars("budget", budget_log, "예산 배분")

fig.add_vline(x=OUTER_TIMEOUT, line_dash="dash", line_color="#D6564C",
              annotation_text="바깥 타임아웃 15초", annotation_position="top")

fig.update_layout(
    barmode="stack",
    title="층별 타임아웃 vs 예산 배분 — 같은 15초 약속, 다른 결말",
    xaxis_title="경과 시간 (초)",
    yaxis=dict(categoryorder="array", categoryarray=["예산 배분", "층별 타임아웃"]),
    height=320, width=860,
    margin=dict(l=110, r=30, t=70, b=50),
    plot_bgcolor="#F7F7F5",
)

_show(fig)

import os
_here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "."
fig.write_image(os.path.join(_here, "expy.png"), scale=2)
print("expy.png 저장 완료")
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 결론
#
# `ex2_timeout_budget.py`의 층별 타임아웃 방식의 문제:
#
# 1. **각 단계는 모두 자기 타임아웃(10초)을 지켰다** — 검색 4초, 요약 3초, 초안 9초. 지역적으로는 전부 정상.
# 2. 그러나 **초안이 9초를 다 쓰면 누적 16초로 바깥 약속 15초를 넘고, 검토 단계에는 도달하지 못한다.**
# 3. 즉 **아무 단계도 잘못하지 않았는데 전체가 실패한다.** 층별 타임아웃 합(40초) > 바깥 타임아웃(15초)인 설정은 아무도 지킬 수 없는 «거짓말»이다.
# 4. 해법은 남은 예산에서 뒤 단계들의 최소 필요분을 떼어 놓고 각 층의 허용 시간을 그때그때 정하는 **예산 배분** 방식이다.
