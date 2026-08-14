# %% [markdown]
# # 전부 이중 시간으로 저장하면 저장량이 얼마나 되는가
#
# 16장 16.5절(`ex5_storage_cost.py`)의 모델을 단계별로 재현한다.
#
# - **전부 이중 시간**으로 저장하면 현재값만 저장할 때의 **139배**까지 커진다.
# - 「이 값 때문에 나중에 누가 항의할 수 있나」로 **골라 붙이면 약 12배**로 떨어진다.

# %%
# 필요 패키지: plotly, kaleido  (시각화 셀에만 필요. 계산 셀은 의존성 없음)
def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# %% [markdown]
# ## 1. 저장량 모델
#
# 책의 모델은 세 단계다. 엔티티 수 $N$, 필드 수 $F$, 연 변경 횟수 $c$, 경과 연수 $y$일 때
# 한 필드의 버전 수는
#
# $$V = 1 + c \cdot y$$
#
# | 저장 방식 | 행 수 |
# |---|---|
# | 현재값만 | $N \cdot F$ |
# | 유효 시간 | $N \cdot F \cdot V$ |
# | 이중 시간 | $N \cdot F \cdot V \cdot (1 + 0.15)$ |
#
# 이중 시간의 $\times 1.15$는 **정정 비율 15%** — 변경 여섯 번에 한 번쯤 정정이 일어나
# 기록이 하나 더 생긴다는 실측 가정이다.

# %%
N_ENTITY = 100_000
FIELDS = 8
BYTES_PER_FACT = 120  # 값 + 두 시간 축 + 색인. 엔진마다 다르다.
CORRECTIONS = 0.15    # 실측: 변경 여섯 번에 한 번쯤 정정


def rows(entities, fields, changes_per_year, years, model):
    """model: current / valid / bitemporal"""
    if model == "current":
        return entities * fields
    versions = 1 + changes_per_year * years
    if model == "valid":
        return int(entities * fields * versions)
    # 이중 시간 — 정정이 일어나면 기록이 하나 더 생긴다
    return int(entities * fields * versions * (1 + CORRECTIONS))


# 감 잡기: 연 12회 변경, 10년이면 버전 수는?
print("버전 수 V = 1 + 12 × 10 =", 1 + 12 * 10)
print("이중 시간 배수 = 121 × 1.15 =", 121 * 1.15)
# 출력: 버전 수 V = 1 + 12 × 10 = 121
# 출력: 이중 시간 배수 = 121 × 1.15 = 139.14999999999998

# %% [markdown]
# 여기서 이미 답이 보인다. **139배 = 121개 버전 × 1.15(정정분)**.
#
# ## 2. 책의 표 재현 — 어디서 139배가 나오나

# %%
print(f"엔티티 {N_ENTITY:,}개, 필드 {FIELDS}개 기준\n")
print(f"{'연 변경 횟수':>10} {'경과 연수':>8} "
      f"{'현재값만':>14} {'유효 시간':>14} {'이중 시간':>14} {'배수':>7}")
print("-" * 74)
for cpy, yrs in ((0.5, 3), (2, 3), (2, 10), (12, 3), (12, 10)):
    a = rows(N_ENTITY, FIELDS, cpy, yrs, "current")
    b = rows(N_ENTITY, FIELDS, cpy, yrs, "valid")
    c = rows(N_ENTITY, FIELDS, cpy, yrs, "bitemporal")
    print(f"{cpy:>10} {yrs:>8} {a:>14,} {b:>14,} {c:>14,} {c/a:>6.1f}x")
# 출력: 엔티티 100,000개, 필드 8개 기준
# 출력:
# 출력:     연 변경 횟수     경과 연수       현재값만      유효 시간      이중 시간     배수
# 출력: --------------------------------------------------------------------------
# 출력:        0.5        3        800,000      2,000,000      2,300,000    2.9x
# 출력:          2        3        800,000      5,600,000      6,439,999    8.0x
# 출력:          2       10        800,000     16,800,000     19,320,000   24.1x
# 출력:         12        3        800,000     29,600,000     34,040,000   42.5x
# 출력:         12       10        800,000     96,800,000    111,319,999  139.1x
# (6,439,999·111,319,999는 float 1.15 곱셈 후 int() 절사 때문 — 배수 계산에는 영향 없다)

# %% [markdown]
# 마지막 줄이 문제의 그 숫자다. **자주 바뀌는 필드(연 12회)를 10년** 끌고 가면
# 이중 시간 저장은 현재값만 저장할 때의 **139배**가 된다.
#
# ## 3. 골라 붙이면 — 12배로 떨어진다
#
# 기준은 「**이 값 때문에 나중에 누가 항의할 수 있나**」.
#
# - 항의가 올 수 있는 필드(등급·담당·계약금액·상태) → **이중 시간**.
#   이런 필드는 대개 느리게 변한다(연 2회 수준).
# - 로그성 값(최근접속일·조회수·메모·태그) → **현재값만**.
#   하필 자주 바뀌는(연 12회) 필드가 바로 이쪽이라, 여기가 저장량 폭발의 주범이었다.

# %%
YEARS = 10
contentious = 4   # 항의 가능 필드: 등급, 담당, 계약금액, 상태 — 연 2회 변경
log_like = FIELDS - contentious  # 로그성 필드: 현재값만

bi = rows(N_ENTITY, contentious, 2, YEARS, "bitemporal")
cur = rows(N_ENTITY, log_like, 0, YEARS, "current")
base = rows(N_ENTITY, FIELDS, 0, YEARS, "current")

print(f"이중 시간(항의 가능 {contentious}개 필드, 연 2회, {YEARS}년): {bi:>12,}행")
print(f"현재값만(로그성 {log_like}개 필드):              {cur:>12,}행")
print(f"합계 {bi + cur:,}행 → 현재값만 대비 {(bi + cur) / base:.1f}배")
# 출력: 이중 시간(항의 가능 4개 필드, 연 2회, 10년):    9,660,000행
# 출력: 현재값만(로그성 4개 필드):                   400,000행
# 출력: 합계 10,060,000행 → 현재값만 대비 12.6배

# %% [markdown]
# **139배 → 약 12배.** 같은 10년인데, 이중 시간을 붙일 필드를 고르는 것만으로
# 한 자릿수 배수까지 내려온다. 책의 대처법 세 가지 중 1번(필드별로 정한다)이 이것이고,
# 나머지는 2번(오래된 이력을 접는다), 3번(이력을 별도 저장소로 뺀다)이다.
#
# ## 4. 바이트로 감 잡기 (사실 하나 120바이트 가정)

# %%
for label, r in (("전부 이중 시간 (연 12회, 10년)",
                  rows(N_ENTITY, FIELDS, 12, YEARS, "bitemporal")),
                 ("선별 적용 (항의 가능 4개 필드만)", bi + cur)):
    print(f"    {label}: {r * BYTES_PER_FACT / 1e9:.1f} GB")
# 출력:     전부 이중 시간 (연 12회, 10년): 13.4 GB
# 출력:     선별 적용 (항의 가능 4개 필드만): 1.2 GB

# %% [markdown]
# ## 5. 시각화 — 배수가 연수에 따라 벌어지는 모양
#
# 두 정책의 배수를 같은 축에 놓으면, 「전부 붙이기」의 기울기가 왜 위험한지 한눈에 보인다.
# 그리고 과거는 소급해서 만들 수 없으니, 이 선택은 **필요해지기 전에** 해야 한다.

# %%
try:
    import plotly.graph_objects as go

    years = list(range(0, YEARS + 1))
    all_bi = [(1 + 12 * y) * (1 + CORRECTIONS) for y in years]
    selective = [(contentious * (1 + 2 * y) * (1 + CORRECTIONS) + log_like) / FIELDS
                 for y in years]

    BLUE, ORANGE = "#2a78d6", "#eb6834"  # 검증된 카테고리 팔레트 1·2번
    INK, MUTED, GRID, SURFACE = "#1a1a19", "#5f5e58", "#e8e7e2", "#fcfcfb"

    fig = go.Figure()
    fig.add_scatter(x=years, y=all_bi, mode="lines+markers",
                    name="전부 이중 시간 (8개 필드, 연 12회 변경)",
                    line=dict(color=BLUE, width=2),
                    marker=dict(size=8, color=BLUE))
    fig.add_scatter(x=years, y=selective, mode="lines+markers",
                    name="선별 적용 (항의 가능 4개 필드만, 연 2회)",
                    line=dict(color=ORANGE, width=2),
                    marker=dict(size=8, color=ORANGE))
    fig.add_annotation(x=YEARS, y=all_bi[-1], text="<b>139배</b>",
                       font=dict(color=INK), xanchor="right", yanchor="bottom",
                       showarrow=False, yshift=6)
    fig.add_annotation(x=YEARS, y=selective[-1], text="<b>12.6배</b>",
                       font=dict(color=INK), xanchor="right", yanchor="bottom",
                       showarrow=False, yshift=6)
    fig.update_layout(
        title="이중 시간 저장량 — 전부 붙이기 vs 골라 붙이기 (현재값만 = 1배)",
        xaxis_title="경과 연수", yaxis_title="현재값만 대비 배수",
        font=dict(family="Apple SD Gothic Neo, AppleGothic, sans-serif",
                  color=INK, size=13),
        paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    font=dict(color=MUTED)),
        margin=dict(l=70, r=30, t=90, b=60), width=880, height=520,
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False, dtick=1)
    fig.update_yaxes(gridcolor=GRID, zeroline=False)

    _show(fig)
    import pathlib
    fig.write_image(str(pathlib.Path(__file__).resolve().parent / "expy.png"),
                    scale=2)  # kaleido 필요
    print("expy.png 저장 완료")
except ImportError as e:
    print("시각화 생략 (필요 패키지 없음):", e)
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# - 전부 이중 시간이면 $121 \times 1.15 \approx$ **139배** (연 12회 변경 × 10년 기준).
# - 「누가 항의할 수 있나」로 골라 붙이면 **약 12배** — 항의 가능한 필드는 느리게 변하고,
#   자주 바뀌는 로그성 필드는 현재값만으로 충분하기 때문이다.
# - 이력은 소급해서 만들 수 없다. 지우기 전엔 법정 보관 기간(계약 5년, 회계 10년)도 확인할 것.
