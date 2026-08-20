# %% [markdown]
# # `ex1_two_stores.py`의 사고 — t0 → t1 → t2 → t3
#
# 29장 29.1절 「따로 두면 갈라진다」.
# 같은 사실(결제팀 팀장)이 **지식 그래프**와 **에이전트 상태** 두 곳에 있고,
# 한쪽만 바뀌면서 에러 없이 갈라지는 과정을 단계별로 재현한다.
#
# | 시각 | 사건 | 그래프 | 상태 |
# |---|---|---|---|
# | $t_0$ | 팀장을 읽어 상태에 담음 | 박민수 | 박민수 |
# | $t_1$ | 사흘간 승인 대기 | 박민수 | 박민수 |
# | $t_2$ | 지식 그래프만 갱신 | **이서연** | 박민수 |
# | $t_3$ | 재개, 옛 값으로 실행 | 이서연 | **박민수** ← 사고 |

# %%
# 필요 패키지: kuzu, plotly, kaleido
import shutil
import tempfile

import kuzu


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# %% [markdown]
# ## 등장인물 둘: 지식 그래프와 에이전트 상태
#
# - `AgentState`: 실행이 들고 다니는 스냅숏(19장). 「그때 읽은 값」을 보존하는 게 본분.
# - Kùzu 그래프: 「지금 값」을 반영하는 게 본분.

# %%
class AgentState:
    """에이전트 실행 상태 — 지금까지 알아낸 것을 들고 다닌다."""

    def __init__(self):
        self.facts = {}

    def remember(self, k, v):
        self.facts[k] = v

    def get(self, k):
        return self.facts.get(k)


def build_kg(path):
    db = kuzu.Database(path)
    c = kuzu.Connection(db)
    c.execute("CREATE NODE TABLE N(name STRING, PRIMARY KEY(name))")
    c.execute("CREATE REL TABLE R(FROM N TO N, kind STRING)")
    for n in ("박민수", "이서연", "결제팀"):
        c.execute("CREATE (:N {name:$n})", {"n": n})
    c.execute("MATCH (a:N {name:'박민수'}),(b:N {name:'결제팀'}) "
              "CREATE (a)-[:R {kind:'이끔'}]->(b)")
    return c


def kg_leader(c):
    r = c.execute("MATCH (p:N)-[:R {kind:'이끔'}]->(:N {name:'결제팀'}) "
                  "RETURN p.name")
    return r.get_next()[0] if r.has_next() else None


tmp = tempfile.mkdtemp()
kg = build_kg(tmp + "/db")
st = AgentState()
timeline = []  # (시각, 그래프 값, 상태 값) 기록 — 시각화용

# %% [markdown]
# ## [t0] 지식 그래프에서 팀장을 읽어 상태에 담는다
#
# 이 시점엔 두 저장소가 일치한다. 상태에 담는 건 게으름이 아니라 **의도적 스냅숏**이다.

# %%
st.remember("팀장", kg_leader(kg))
timeline.append(("t0\n읽어서 담음", kg_leader(kg), st.get("팀장")))
print(f"[t0] 그래프: {kg_leader(kg)} / 상태: {st.get('팀장')}")
# 출력: [t0] 그래프: 박민수 / 상태: 박민수

# %% [markdown]
# ## [t1] 사람 승인을 기다린다 — 사흘
#
# 상태는 체크포인트에 저장돼 사흘 뒤에도 그대로 살아 있다(21장).
# 이 「오래 멈춰 있는 시간」이 사고의 창이다. 아무것도 안 바뀌었지만, 바뀔 수 있는 시간이 흐른다.

# %%
timeline.append(("t1\n승인 대기(사흘)", kg_leader(kg), st.get("팀장")))
print(f"[t1] 그래프: {kg_leader(kg)} / 상태: {st.get('팀장')}  (아직 일치)")
# 출력: [t1] 그래프: 박민수 / 상태: 박민수  (아직 일치)

# %% [markdown]
# ## [t2] 다른 경로로 팀장이 바뀐다 — 지식 그래프만 갱신
#
# 인사 이동. 그래프를 고친 쪽은 잠들어 있는 실행의 존재를 모르고,
# 잠든 상태는 바깥 변화를 알 길이 없다. **에러는 나지 않는다.**

# %%
kg.execute("MATCH (a:N {name:'박민수'})-[e:R {kind:'이끔'}]->"
           "(:N {name:'결제팀'}) DELETE e")
kg.execute("MATCH (a:N {name:'이서연'}),(b:N {name:'결제팀'}) "
           "CREATE (a)-[:R {kind:'이끔'}]->(b)")
timeline.append(("t2\n그래프만 갱신", kg_leader(kg), st.get("팀장")))
print(f"[t2] 그래프: {kg_leader(kg)} / 상태: {st.get('팀장')}  ← 갈라졌다")
# 출력: [t2] 그래프: 이서연 / 상태: 박민수  ← 갈라졌다

# %% [markdown]
# ## [t3] 승인이 나서 재개 — 상태의 옛 값으로 실행
#
# 보고서를 «박민수»에게 보냈는데 지금 팀장은 «이서연».
# 둘 다 자기 일을 제대로 했는데 결과가 틀렸다.

# %%
timeline.append(("t3\n옛 값으로 실행", kg_leader(kg), st.get("팀장")))
print(f"[t3] → 보고서를 «{st.get('팀장')}» 에게 보냈다.")
print(f"     → 그런데 지금 팀장은 «{kg_leader(kg)}» 다.")
# 출력: [t3] → 보고서를 «박민수» 에게 보냈다.
#      → 그런데 지금 팀장은 «이서연» 다.

# %% [markdown]
# ## 선택지 2의 미리보기 — 「읽은 시각」을 담고 쓰기 직전에 재확인
#
# 사고를 막는 실무 절충: 스냅숏에 읽은 시각을 붙여 두고,
# 쓰기 직전에 같은 질의를 다시 던져 달라졌으면 멈춘다(ex2의 `Reads`+`as_of` 엣지와 같은 발상).

# %%
snapshot = {"값": st.get("팀장"), "읽은시각": "t0"}
now = kg_leader(kg)
if snapshot["값"] != now:
    print(f"멈춤 — {snapshot['읽은시각']}에 읽은 «{snapshot['값']}» 이 "
          f"지금은 «{now}». 다시 확인 필요.")
else:
    print("진행해도 된다.")
# 출력: 멈춤 — t0에 읽은 «박민수» 이 지금은 «이서연». 다시 확인 필요.

# %% [markdown]
# ## 시각화 — 두 저장소가 갈라지는 순간

# %%
import plotly.graph_objects as go

x = [t for t, _, _ in timeline]
kg_vals = [g for _, g, _ in timeline]
st_vals = [s for _, _, s in timeline]
ymap = {"박민수": 0, "이서연": 1}

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=x, y=[ymap[v] for v in kg_vals], mode="lines+markers+text",
    name="지식 그래프 (지금 값)", text=kg_vals, textposition="top center",
    line=dict(color="#4363d8", width=3), marker=dict(size=12)))
fig.add_trace(go.Scatter(
    x=x, y=[ymap[v] - 0.04 for v in st_vals], mode="lines+markers+text",
    name="에이전트 상태 (그때 읽은 값)", text=st_vals,
    textposition="bottom center",
    line=dict(color="#e6194b", width=3, dash="dash"), marker=dict(size=12)))
fig.add_vrect(x0=1.5, x1=3.2, fillcolor="#e6194b", opacity=0.08, line_width=0,
              annotation_text="갈라진 구간", annotation_position="top left")
fig.update_layout(
    title="ex1_two_stores.py — 두 저장소가 에러 없이 갈라진다",
    yaxis=dict(tickvals=[0, 1], ticktext=["박민수", "이서연"],
               title="결제팀 팀장", range=[-0.4, 1.4]),
    xaxis=dict(title="시각"), width=820, height=420,
    legend=dict(orientation="h", y=1.12))
_show(fig)

import os
fig.write_image(os.path.join(os.path.dirname(os.path.abspath(__file__))
                             if "__file__" in dir() else ".", "expy.png"),
                scale=2)
print("expy.png 저장 완료")
# 출력: expy.png 저장 완료

# %%
shutil.rmtree(tmp, ignore_errors=True)

# %% [markdown]
# ## 정리
#
# - **t0** 읽어서 상태에 담음(스냅숏) → **t1** 사흘 승인 대기 → **t2** 지식 그래프만 갱신(갈라짐) → **t3** 재개해 옛 값으로 실행(사고).
# - 상태는 「그때 값」, 그래프는 「지금 값」— 둘 다 옳은데 결과가 틀렸다. 같은 사실이 두 곳에 있는 한 언제나 갈라질 수 있다.
# - 대책: ② 읽은 시각을 담고 쓰기 직전 재확인(절충), ③ 한 백본에 두고 링크만 그래프에(29장의 주제).
