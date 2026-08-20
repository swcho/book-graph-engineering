# %% [markdown]
# # 마이그레이션 여섯 단계를 상태 기계로
#
# 32장 `ex5_migration_plan.py`의 아이디어를 확장한다.
#
# 마이그레이션 계획을 **문서**로 적으면 「지금 어디쯤인가」를 사람이 판단하게 되고,
# 사람은 「대충 된 것 같은데」로 다음 단계로 넘어간다.
# 계획을 **코드**로 적으면 조건을 못 채우면 넘어갈 수 없다.
#
# 여섯 단계와 각 단계를 *떠나기 위한* 관문 조건:
#
# | 단계 | 하는 일 | 떠나기 위한 관문 |
# |---|---|---|
# | `expand`     | 새 스키마를 더한다 (옛것 그대로) | 새 스키마 존재 |
# | `dual-write` | 쓰기를 양쪽에 한다 | 양쪽 쓰기 비율 = 100% |
# | `backfill`   | 옛 데이터를 새 스키마로 복사 | 백필 진행률 = 100% |
# | `dual-read`  | 읽기를 둘 다 하고 비교 | 불일치 건수 = 0 |
# | `cutover`    | 읽기를 새것으로, 옛것은 검증용 | 옛것 읽기 = 0 **그리고** 롤백 가능 |
# | `contract`   | 옛 스키마 삭제 | 조용한 일수 > 가장 긴 배치 주기 |
#
# 관문은 「단계에 들어가는」 조건이 아니라 「단계를 **떠나는**」 조건이다.
# 그래서 상태 기계의 진행은
#
# $$\text{진행 가능 단계 수} = \min\{\, i \;:\; \lnot G_i(s) \,\}$$
#
# 즉 관문 조건 $G_i$ 가 처음으로 거짓이 되는 지점에서 멈춘다.
# 뒤쪽 단계의 관문이 이미 참이어도 앞이 막히면 못 간다 (순서가 있는 상태 기계).

# %%
# 필요 패키지: plotly, kaleido  (pip install plotly kaleido)
# 실행: python3 expy.py  또는 VSCode 셀 단위 실행

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable

import plotly.graph_objects as go


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "."
print("plotly", go.__name__, "준비됨")
# 출력: plotly plotly.graph_objects 준비됨

# %% [markdown]
# ## 1. 관측 지표(State)와 관문(Gate)을 자료로 분리한다
#
# 사람의 낙관이 끼어들지 못하게, 판정에 쓰이는 값은 전부 **관측 지표**로만 받는다.
# - `양쪽_쓰기_비율` — 예제 2의 3단계에서 나온 값
# - `백필_진행률` — 쪼개서 돌린 백필의 체크포인트 진행률
# - `불일치_건수` — 예제 4의 「둘 다 읽고 비교」가 세어 준 값
# - `옛것_읽기_건수_최근` — 예제 1의 `Reads` 엣지 기반 카운트
# - `옛것_마지막_읽기_경과일` / `가장_긴_주기_일` — 예제 3의 분기 결산(92일)
# - `롤백_가능` — cutover 앞에만 붙는 추가 관문

# %%
@dataclass(frozen=True)
class Phase:
    name: str
    what: str


PHASES = [
    Phase("expand",     "새 스키마를 더한다. 옛것 그대로"),
    Phase("dual-write", "쓰기를 양쪽에 한다"),
    Phase("backfill",   "옛 데이터를 새 스키마로 복사"),
    Phase("dual-read",  "읽기를 둘 다 하고 비교"),
    Phase("cutover",    "읽기를 새것으로. 옛것은 검증용"),
    Phase("contract",   "옛 스키마 삭제"),
]

Check = tuple[str, Callable[[dict], bool]]

GATES: dict[str, list[Check]] = {
    "expand":     [("새 스키마가 있나", lambda s: bool(s["새_스키마_존재"]))],
    "dual-write": [("양쪽 쓰기가 100%인가", lambda s: s["양쪽_쓰기_비율"] >= 1.0)],
    "backfill":   [("백필이 끝났나", lambda s: s["백필_진행률"] >= 1.0)],
    "dual-read":  [("불일치가 0인가", lambda s: s["불일치_건수"] == 0)],
    "cutover":    [("옛것 읽기가 0인가", lambda s: s["옛것_읽기_건수_최근"] == 0),
                   ("롤백이 가능한가", lambda s: bool(s["롤백_가능"]))],
    "contract":   [("가장 긴 주기보다 오래 조용한가",
                    lambda s: s["옛것_마지막_읽기_경과일"] > s["가장_긴_주기_일"])],
}

print(f"단계 {len(PHASES)}개, 관문 조건 {sum(len(v) for v in GATES.values())}개")
# 출력: 단계 6개, 관문 조건 7개

# %% [markdown]
# ## 2. 상태 기계 — 관문이 처음 거짓인 곳에서 멈춘다

# %%
def evaluate(state: dict) -> list[dict]:
    """각 단계의 관문을 평가한다. 앞이 막히면 뒤는 '도달 못함'."""
    rows, reached = [], True
    for ph in PHASES:
        results = [(label, fn(state)) for label, fn in GATES[ph.name]]
        passed = all(v for _l, v in results)
        rows.append({
            "phase": ph.name,
            "what": ph.what,
            "checks": results,
            "passed": passed,
            "reached": reached,
        })
        if not passed:
            reached = False   # 이 단계를 못 떠나므로 이후 단계는 도달 불가
    return rows


def blocked_at(rows: list[dict]) -> str | None:
    for r in rows:
        if not r["passed"]:
            return r["phase"]
    return None


def report(title: str, state: dict) -> list[dict]:
    rows = evaluate(state)
    print(f"== {title} ==")
    print(f"{'단계':<12}{'관문':<30}{'통과':<6}{'도달'}")
    print("-" * 60)
    for r in rows:
        gate = " / ".join(l for l, _v in r["checks"])
        print(f"{r['phase']:<12}{gate:<30}"
              f"{'○' if r['passed'] else '✗':<6}"
              f"{'예' if r['reached'] else '아니오'}")
    b = blocked_at(rows)
    if b is None:
        print("\n막힌 곳 없음 → contract 까지 진행 가능 (옛 스키마 삭제 승인)\n")
    else:
        print(f"\n막혀 있는 곳: {b}")
        for l, v in [(l, fn(state)) for l, fn in GATES[b]]:
            if not v:
                print(f"  → {l} : 아니오")
        print()
    return rows


# %% [markdown]
# ## 3. 시나리오 A — 불일치 3건이 남아 `dual-read`에서 막힌다
#
# `expand` / `dual-write` / `backfill` 관문은 전부 통과했다.
# 그런데 「둘 다 읽고 비교」가 불일치 3건을 세고 있다.
# 불일치가 0이 아니면 **수축하지 않는다** — 상태 기계는 여기서 멈춘다.
#
# 흥미로운 건, `cutover`의 「옛것 읽기 0 / 롤백 가능」이 이미 참이라는 점이다.
# 그래도 못 간다. 관문에는 순서가 있다.

# %%
STATE_A = {
    "새_스키마_존재": True,
    "양쪽_쓰기_비율": 1.00,
    "백필_진행률": 1.00,
    "불일치_건수": 3,            # ← 여기서 막힌다
    "옛것_읽기_건수_최근": 0,
    "가장_긴_주기_일": 92,
    "옛것_마지막_읽기_경과일": 52,   # 92일을 아직 안 넘겼다
    "롤백_가능": True,
}

rows_a = report("시나리오 A — 불일치 3건", STATE_A)
# 출력: == 시나리오 A — 불일치 3건 ==
# 출력: 단계          관문                            통과    도달
# 출력: ------------------------------------------------------------
# 출력: expand      새 스키마가 있나                       ○     예
# 출력: dual-write  양쪽 쓰기가 100%인가                   ○     예
# 출력: backfill    백필이 끝났나                         ○     예
# 출력: dual-read   불일치가 0인가                        ✗     예
# 출력: cutover     옛것 읽기가 0인가 / 롤백이 가능한가         ○     아니오
# 출력: contract    가장 긴 주기보다 오래 조용한가              ✗     아니오
# 출력:
# 출력: 막혀 있는 곳: dual-read
# 출력:   → 불일치가 0인가 : 아니오

# %% [markdown]
# ## 4. 시나리오 B — 불일치를 고치고 한 주기 더 기다린 뒤
#
# 불일치 3건을 그 키만 따로 고쳐 0으로 만들고,
# `contract` 관문을 위해 가장 긴 주기(분기 결산 92일)보다 **오래** 조용해질 때까지 기다린다.
# 52일이 아니라 100일. 그러면 여섯 단계가 전부 열린다.
#
# 「최근 30일」 기준으로는 52일에도 지워도 된다고 나오지만, 그건 40일 뒤에
# 깨어날 분기 결산을 놓친 판정이다. 기준은 시간이 아니라 $\max(\text{주기})$ 다.

# %%
STATE_B = dict(STATE_A, 불일치_건수=0, 옛것_마지막_읽기_경과일=100)
rows_b = report("시나리오 B — 고친 뒤", STATE_B)
# 출력: == 시나리오 B — 고친 뒤 ==
# 출력: 단계          관문                            통과    도달
# 출력: ------------------------------------------------------------
# 출력: expand      새 스키마가 있나                       ○     예
# 출력: dual-write  양쪽 쓰기가 100%인가                   ○     예
# 출력: backfill    백필이 끝났나                         ○     예
# 출력: dual-read   불일치가 0인가                        ○     예
# 출력: cutover     옛것 읽기가 0인가 / 롤백이 가능한가         ○     예
# 출력: contract    가장 긴 주기보다 오래 조용한가              ○     예
# 출력:
# 출력: 막힌 곳 없음 → contract 까지 진행 가능 (옛 스키마 삭제 승인)

# %% [markdown]
# ## 5. 관문 하나만 흔들어 본다 — 롤백 불가라면?
#
# `cutover`는 되돌리기 제일 어려운 단계라, 그 앞에서 「되돌릴 수 있나」를 묻는다.
# 다른 지표가 완벽해도 롤백이 안 되면 cutover를 떠날 수 없다.

# %%
STATE_C = dict(STATE_B, 롤백_가능=False)
rows_c = report("시나리오 C — 롤백 불가", STATE_C)
# 출력: == 시나리오 C — 롤백 불가 ==
# 출력: 단계          관문                            통과    도달
# 출력: ------------------------------------------------------------
# 출력: expand      새 스키마가 있나                       ○     예
# 출력: dual-write  양쪽 쓰기가 100%인가                   ○     예
# 출력: backfill    백필이 끝났나                         ○     예
# 출력: dual-read   불일치가 0인가                        ○     예
# 출력: cutover     옛것 읽기가 0인가 / 롤백이 가능한가         ✗     예
# 출력: contract    가장 긴 주기보다 오래 조용한가              ○     아니오
# 출력:
# 출력: 막혀 있는 곳: cutover
# 출력:   → 롤백이 가능한가 : 아니오

# %% [markdown]
# ## 6. 시각화 — 관문 통과 상태
#
# 세 시나리오를 나란히 놓는다. 각 칸의 색은
# **통과**(초록) / **막힘**(빨강) / **도달 못함**(회색) 세 가지다.
# 앞이 빨강이면 뒤는 통과 여부와 무관하게 회색이 된다 — 그게 상태 기계의 핵심이다.

# %%
SCEN = [("A · 불일치 3건", rows_a), ("B · 고친 뒤", rows_b), ("C · 롤백 불가", rows_c)]
PHASE_NAMES = [p.name for p in PHASES]

# 0 = 도달 못함, 1 = 막힘, 2 = 통과
def cell(r):
    if not r["reached"]:
        return 0
    return 2 if r["passed"] else 1


Z = [[cell(r) for r in rows] for _t, rows in SCEN]
TEXT = [["○ 통과" if v == 2 else ("✗ 막힘" if v == 1 else "· 미도달") for v in row]
        for row in Z]

fig = go.Figure(go.Heatmap(
    z=Z, x=PHASE_NAMES, y=[t for t, _r in SCEN],
    text=TEXT, texttemplate="%{text}",
    colorscale=[[0.0, "#d9dce1"], [0.33, "#d9dce1"],
                [0.34, "#e8736a"], [0.66, "#e8736a"],
                [0.67, "#4fa96b"], [1.0, "#4fa96b"]],
    zmin=0, zmax=2, showscale=False, xgap=3, ygap=3,
    hovertemplate="%{y} · %{x}<br>%{text}<extra></extra>",
))
fig.update_layout(
    title="확장-수축 여섯 단계: 각 단계를 떠나기 위한 관문 통과 상태",
    xaxis=dict(title="단계 (왼쪽 → 오른쪽 진행)", side="top"),
    yaxis=dict(title="", autorange="reversed"),
    width=980, height=340, margin=dict(l=120, r=40, t=110, b=60),
    template="plotly_white",
)
_show(fig)

out = os.path.join(HERE, "expy.png")
fig.write_image(out, scale=2)
print("저장:", out)
# 출력: 저장: .../expy.png

# %% [markdown]
# ## 정리
#
# - 관문은 「들어가는 조건」이 아니라 **「떠나는 조건」**이다.
# - `expand` → 새 스키마 존재 / `dual-write` → 양쪽 쓰기 100% /
#   `backfill` → 진행률 100% / `dual-read` → 불일치 0 /
#   `cutover` → 옛것 읽기 0 **그리고** 롤백 가능 / `contract` → 가장 긴 주기보다 오래 조용
# - 뒤 단계의 관문이 참이어도 앞이 막히면 못 간다. 그래서 상태 기계다.
# - 이 파일을 CI에 넣으면 마이그레이션이 사람의 낙관을 안 탄다.
