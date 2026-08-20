# %% [markdown]
# # 중단점 앞에 부작용을 두면 안 되는 이유
#
# **질문** — 중단점 앞에 부작용을 두면 안 되는 이유는 무엇인가?
#
# **답** — 재개하면 그 노드를 **처음부터** 다시 돌기 때문이다.
# 노드 안에서 `interrupt` 앞의 코드는 두 번 실행된다.
#
# 핵심은 21장의 「슈퍼스텝 경계」와 같다.
# 체크포인트는 **노드 경계**에 찍힌다. 노드 중간에는 안 찍힌다.
#
# - `interrupt()`는 노드 *중간*에서 멈춘다.
# - 그런데 저장된 마지막 체크포인트는 그 노드가 **시작되기 직전**의 상태다.
# - 그래서 재개(`Command(resume=...)`)하면 노드 함수를 처음부터 다시 호출한다.
# - `interrupt` 앞의 줄은 재실행되고, `interrupt`는 이번엔 멈추는 대신
#   사람이 준 값을 *돌려주며* 통과한다.
#
# 실행 횟수를 식으로 쓰면, 그 노드가 $k$ 번 중단됐다 재개될 때
#
# $$\text{앞의 코드 실행 횟수} = k + 1, \qquad \text{뒤의 코드 실행 횟수} = 1$$
#
# 읽기만 하는 코드는 $k+1$ 번 돌아도 괜찮다.
# 밖으로 나가는 것(메일, 결제, API 호출)은 전부 `interrupt` **뒤**로 민다.

# %%
# 필요 패키지: plotly, kaleido (그래프 저장용)
# langgraph 는 있으면 실제 검증에 쓰고, 없으면 아래 미니 런타임만으로 전부 재현된다.


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# %% [markdown]
# ## 1. 미니 인터럽트 런타임 20줄
#
# LangGraph 없이도 의미론은 그대로 재현된다. 필요한 건 세 가지뿐이다.
#
# 1. `interrupt()`는 **줄 값이 없으면** 예외를 던져 노드를 통째로 중단시킨다.
# 2. 재개할 때 주는 답은 노드 안의 **호출 순서(index)** 로 재생(replay)된다.
# 3. 재개는 노드 함수를 **처음부터** 다시 호출한다.

# %%
class GraphInterrupt(Exception):
    """노드 중간에서 정상적으로 멈춘다. 예외지만 「오류」가 아니다."""

    def __init__(self, payload):
        self.payload = payload


class Runner:
    """노드 하나짜리 그래프. 체크포인트는 노드 경계에만 찍힌다."""

    def __init__(self, node):
        self.node = node
        self.answers = []  # 사람이 준 답들. 노드 안 호출 순서대로 재생된다.
        self.calls = 0  # 노드 함수가 실제로 호출된 횟수

    def _interrupt(self, payload):
        i = self._idx
        self._idx += 1
        if i < len(self.answers):  # 이미 답이 있다 → 멈추지 않고 그 값을 돌려준다
            return self.answers[i]
        raise GraphInterrupt(payload)  # 답이 없다 → 여기서 중단

    def invoke(self, state, resume=None):
        if resume is not None:
            self.answers.append(resume)
        self._idx = 0  # 노드를 「처음부터」 다시 도니 인덱스도 0부터
        self.calls += 1
        try:
            return {"status": "done", "value": self.node(state, self._interrupt)}
        except GraphInterrupt as e:
            return {"status": "interrupted", "ask": e.payload}


print("미니 런타임 준비 완료")
# 출력: 미니 런타임 준비 완료

# %% [markdown]
# ## 2. 부작용이 `interrupt` **앞**에 있을 때 (나쁨)
#
# 담당자에게 「검토 요청」 메일을 보내고 나서 사람에게 묻는 노드다.
# 자연스러워 보이지만, 재개하면 메일 발송 줄이 다시 실행된다.

# %%
보낸메일 = []


def 나쁜노드(state, interrupt):
    보낸메일.append(state["주문"])  # ← 부작용이 interrupt 앞
    print(f"    → 담당자에게 검토 요청 메일 발송 (누적 {len(보낸메일)}회)")
    답 = interrupt("승인하시겠습니까?")
    return 답


bad = Runner(나쁜노드)
print("[1회차 invoke]")
r1 = bad.invoke({"주문": "A-1024"})
print(f"    상태: {r1['status']} / 물음: {r1['ask']}")
print("    ...사람이 사흘 뒤에 답한다...")
print("[재개 invoke]")
r2 = bad.invoke({"주문": "A-1024"}, resume="승인")
print(f"    상태: {r2['status']} / 결과: {r2['value']}")
print(f"\n노드 호출 {bad.calls}회, 메일 발송 {len(보낸메일)}회 → {보낸메일}")
# 출력:
# [1회차 invoke]
#     → 담당자에게 검토 요청 메일 발송 (누적 1회)
#     상태: interrupted / 물음: 승인하시겠습니까?
#     ...사람이 사흘 뒤에 답한다...
# [재개 invoke]
#     → 담당자에게 검토 요청 메일 발송 (누적 2회)
#     상태: done / 결과: 승인
#
# 노드 호출 2회, 메일 발송 2회 → ['A-1024', 'A-1024']

# %% [markdown]
# 담당자는 검토 요청 메일을 **두 번** 받았다.
# 그것도 두 번째는 자기가 **승인을 하고 난 뒤에**.
#
# 메일이면 짜증으로 끝나지만, 이 자리에 결제·환불 API가 있었다면
# 돈이 두 번 나간다. 22장의 보상 트랜잭션이 필요해지는 사고가 바로 이 모양이다.

# %% [markdown]
# ## 3. 부작용을 `interrupt` **뒤**로 밀면 (좋음)

# %%
기록된결과 = []


def 좋은노드(state, interrupt):
    답 = interrupt("승인하시겠습니까?")  # ← 먼저 멈춘다
    기록된결과.append((state["주문"], 답))  # ← 부작용은 뒤
    print(f"    → 결과 기록 (누적 {len(기록된결과)}회)")
    return 답


good = Runner(좋은노드)
print("[1회차 invoke]")
g1 = good.invoke({"주문": "A-1031"})
print(f"    상태: {g1['status']}")
print("    ...사람이 답한다...")
print("[재개 invoke]")
g2 = good.invoke({"주문": "A-1031"}, resume="거절")
print(f"    상태: {g2['status']} / 결과: {g2['value']}")
print(f"\n노드 호출 {good.calls}회, 결과 기록 {len(기록된결과)}회 → {기록된결과}")
# 출력:
# [1회차 invoke]
#     상태: interrupted
#     ...사람이 답한다...
# [재개 invoke]
#     → 결과 기록 (누적 1회)
#     상태: done / 결과: 거절
#
# 노드 호출 2회, 결과 기록 1회 → [('A-1031', '거절')]

# %% [markdown]
# 노드 함수는 똑같이 **2번** 호출됐다. 그건 못 막는다.
# 막을 수 있는 건 「부작용이 그 2번에 같이 끌려 들어가느냐」다.
#
# > 규칙은 하나다. **`interrupt` 앞에는 부작용을 두지 않는다.**
# > 읽기만 하는 코드는 괜찮다. 밖으로 나가는 것은 전부 뒤로 민다.

# %% [markdown]
# ## 4. 부작용이 꼭 앞에 있어야 한다면 — 노드를 쪼갠다
#
# 「검토 요청 메일을 보내고 나서 물어야 한다」는 요구는 정당하다.
# 그럴 땐 순서를 바꾸는 게 아니라 **경계를 하나 더 만든다**.
#
# ```
# [부작용 노드: 메일 발송] --경계(체크포인트)--> [interrupt 노드: 묻기]
# ```
#
# 앞 노드가 끝나는 순간 체크포인트가 찍히므로, 재개는 뒤 노드만 다시 돈다.

# %%
class TwoNodeRunner:
    """부작용 노드 → interrupt 노드. 사이에 체크포인트 경계가 있다."""

    def __init__(self, effect_node, ask_node):
        self.effect_node, self.ask_node = effect_node, ask_node
        self.done_upto = 0  # 경계 체크포인트: 몇 번째 노드까지 끝났나
        self.answers = []
        self.calls = {"effect": 0, "ask": 0}

    def _interrupt(self, payload):
        i = self._idx
        self._idx += 1
        if i < len(self.answers):
            return self.answers[i]
        raise GraphInterrupt(payload)

    def invoke(self, state, resume=None):
        if resume is not None:
            self.answers.append(resume)
        if self.done_upto < 1:  # 이미 끝난 노드는 다시 안 돈다
            self.calls["effect"] += 1
            self.effect_node(state)
            self.done_upto = 1  # ← 여기서 체크포인트가 찍힌다
        self._idx = 0
        self.calls["ask"] += 1
        try:
            return {"status": "done", "value": self.ask_node(state, self._interrupt)}
        except GraphInterrupt as e:
            return {"status": "interrupted", "ask": e.payload}


보낸메일2 = []


def 메일노드(state):
    보낸메일2.append(state["주문"])
    print(f"    → [메일노드] 검토 요청 발송 (누적 {len(보낸메일2)}회)")


def 묻기노드(state, interrupt):
    return interrupt("승인하시겠습니까?")


split = TwoNodeRunner(메일노드, 묻기노드)
print("[1회차 invoke]")
s1 = split.invoke({"주문": "A-1050"})
print(f"    상태: {s1['status']}")
print("    ...사람이 답한다...")
print("[재개 invoke]")
s2 = split.invoke({"주문": "A-1050"}, resume="승인")
print(f"    상태: {s2['status']} / 결과: {s2['value']}")
print(f"\n노드 호출 {split.calls}, 메일 발송 {len(보낸메일2)}회")
# 출력:
# [1회차 invoke]
#     → [메일노드] 검토 요청 발송 (누적 1회)
#     상태: interrupted
#     ...사람이 답한다...
# [재개 invoke]
#     상태: done / 결과: 승인
#
# 노드 호출 {'effect': 1, 'ask': 2}, 메일 발송 1회

# %% [markdown]
# `ask` 노드는 2번 돌았지만 `effect` 노드는 1번만 돌았다.
# 경계가 사이에 생겼기 때문이다. 이게 「노드를 둘로 쪼개라」의 정확한 의미다.

# %% [markdown]
# ## 5. 중단이 여러 번이면 증폭된다
#
# 실무에서 중단은 한 번으로 안 끝난다.
# 「금액 확인 → 사유 확인 → 최종 승인」처럼 한 노드 안에서 여러 번 물을 수도 있고,
# 23.4절의 등급 올리기로 담당자를 바꿔 가며 다시 물을 수도 있다.
#
# 중단이 $k$ 번이면 앞의 부작용은 $k+1$ 번 실행된다. 선형으로 늘어난다.

# %%
def 부작용횟수(k, 위치):
    """중단 k번일 때 부작용 실행 횟수를 미니 런타임으로 실측한다."""
    cnt = {"n": 0}

    def node(state, interrupt):
        if 위치 == "앞":
            cnt["n"] += 1
        for i in range(k):
            interrupt(f"질문 {i + 1}")
        if 위치 == "뒤":
            cnt["n"] += 1
        return "done"

    r = Runner(node)
    out = r.invoke({})
    while out["status"] == "interrupted":
        out = r.invoke({}, resume="승인")
    return cnt["n"]


ks = list(range(1, 7))
앞 = [부작용횟수(k, "앞") for k in ks]
뒤 = [부작용횟수(k, "뒤") for k in ks]
for k, a, b in zip(ks, 앞, 뒤):
    print(f"  중단 {k}회 → 앞에 두면 {a}회 실행, 뒤에 두면 {b}회 실행")
# 출력:
#   중단 1회 → 앞에 두면 2회 실행, 뒤에 두면 1회 실행
#   중단 2회 → 앞에 두면 3회 실행, 뒤에 두면 1회 실행
#   중단 3회 → 앞에 두면 4회 실행, 뒤에 두면 1회 실행
#   중단 4회 → 앞에 두면 5회 실행, 뒤에 두면 1회 실행
#   중단 5회 → 앞에 두면 6회 실행, 뒤에 두면 1회 실행
#   중단 6회 → 앞에 두면 7회 실행, 뒤에 두면 1회 실행

# %%
import os

import plotly.graph_objects as go

fig = go.Figure()
fig.add_bar(x=ks, y=앞, name="부작용이 interrupt 앞 (k+1회)", marker_color="#d1495b",
            text=[f"{v}회" for v in 앞], textposition="outside")
fig.add_bar(x=ks, y=뒤, name="부작용이 interrupt 뒤 (1회)", marker_color="#2a9d8f",
            text=[f"{v}회" for v in 뒤], textposition="outside")
fig.update_layout(
    title="중단 횟수 k에 따른 부작용 실행 횟수 — 노드는 재개 때마다 처음부터 다시 돈다",
    xaxis_title="한 노드 안에서 중단된 횟수 k",
    yaxis_title="부작용(메일·결제 API) 실행 횟수",
    barmode="group",
    template="plotly_white",
    legend=dict(orientation="h", y=1.08, x=0),
    height=460,
)
fig.update_yaxes(range=[0, max(앞) + 1.2])

_here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
png = os.path.join(_here, "expy.png")
try:
    fig.write_image(png, width=980, height=460, scale=2)
    print(f"저장: {png}")
except Exception as e:  # kaleido 미설치 등
    print(f"png 저장 실패: {e}")
_show(fig)
# 출력: 저장: .../expy.png

# %% [markdown]
# ## 6. 실제 LangGraph 로 확인
#
# 위 미니 런타임이 지어낸 규칙이 아니라는 걸 확인한다.
# `langgraph` 가 설치돼 있으면 실제 그래프로 같은 결과가 나온다.
# 책의 `ex2_node_reruns.py` 와 같은 구조다.

# %%
try:
    from typing import TypedDict

    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.graph import END, START, StateGraph
    from langgraph.types import Command, interrupt as lg_interrupt

    호출수 = {"메일": 0, "조회": 0}

    class S(TypedDict):
        주문: str
        승인: str

    def lg_나쁜노드(s):
        호출수["메일"] += 1
        print(f"    → 검토 요청 메일 발송 (누적 {호출수['메일']}회)")
        return {"승인": lg_interrupt("승인하시겠습니까?")}

    def lg_좋은노드(s):
        답 = lg_interrupt("승인하시겠습니까?")
        호출수["조회"] += 1
        print(f"    → 결과 기록 (누적 {호출수['조회']}회)")
        return {"승인": 답}

    def build(node):
        g = StateGraph(S)
        g.add_node("검토", node)
        g.add_edge(START, "검토")
        g.add_edge("검토", END)
        return g.compile(checkpointer=InMemorySaver())

    for label, node, tid in (
        ("부작용이 interrupt 앞", lg_나쁜노드, "t1"),
        ("부작용이 interrupt 뒤", lg_좋은노드, "t2"),
    ):
        print(f"\n[{label}]")
        app = build(node)
        cfg = {"configurable": {"thread_id": tid}}
        app.invoke({"주문": "A-1024", "승인": ""}, cfg)
        print("    ...사람이 답한다...")
        app.invoke(Command(resume="승인"), cfg)

    print(f"\nLangGraph 실측 → 메일 발송 {호출수['메일']}회, 결과 기록 {호출수['조회']}회")
    assert 호출수["메일"] == 2 and 호출수["조회"] == 1
    print("미니 런타임과 결과가 같다. 규칙 확인.")
except ImportError:
    print('langgraph 미설치 — pip install "langgraph>=1.0,<2.0" 후 다시 실행하면 실측된다.')
# 출력:
# [부작용이 interrupt 앞]
#     → 검토 요청 메일 발송 (누적 1회)
#     ...사람이 답한다...
#     → 검토 요청 메일 발송 (누적 2회)
#
# [부작용이 interrupt 뒤]
#     ...사람이 답한다...
#     → 결과 기록 (누적 1회)
#
# LangGraph 실측 → 메일 발송 2회, 결과 기록 1회
# 미니 런타임과 결과가 같다. 규칙 확인.

# %% [markdown]
# ## 정리
#
# | | 노드 함수 호출 | 부작용 실행 |
# |---|---|---|
# | 부작용이 `interrupt` 앞 | 2회 | **2회** (중단 $k$회면 $k+1$회) |
# | 부작용이 `interrupt` 뒤 | 2회 | 1회 |
# | 노드 분리 (부작용 → interrupt) | effect 1회 / ask 2회 | 1회 |
#
# - 재실행 자체는 막을 수 없다. 체크포인트가 노드 경계에만 찍히기 때문이다.
# - 막을 수 있는 건 **무엇이 재실행에 끌려 들어가느냐**다.
# - 읽기 전용 코드는 `interrupt` 앞에 둬도 된다.
# - 밖으로 나가는 것(메일·결제·발송)은 전부 뒤로 밀거나, 노드를 쪼개 경계를 만든다.
