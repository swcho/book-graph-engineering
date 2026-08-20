# 필요 패키지: plotly, kaleido  (미설치 시 시각화/PNG 저장은 건너뛰고 나머지는 검증됨)
# %% [markdown]
# # 권한을 목록이 아니라 «경로»로 본다
#
# `ex1_permission_graph.py`의 핵심 아이디어를 작은 모델로 재현한다.
#
# - **도구**마다 필요한 권한과, 그 도구가 «만들어 내는 능력»이 있다.
# - 에이전트에게 **권한 집합** $G$를 준다.
# - 어떤 도구 $t$는 그 필요 권한 $\text{need}(t)$가 $\text{need}(t) \subseteq G$ 일 때만 쓸 수 있다.
# - 쓸 수 있는 도구들이 만들어 내는 **능력의 합집합**을 $C = \bigcup_{t \in \text{usable}} \text{cap}(t)$ 라 하자.
# - **치명 조합**은 능력 부분집합 $K$ 로 정의된다. $K \subseteq C$ 이면 그 위험 경로에 «도달»한다.
#
# 즉 위험은 도구 하나가 아니라 «권한 → 도구 → 능력 → 조합»으로 이어지는 경로에서 나온다.

# %%
# 도구: 이름 -> (필요 권한, 만들어 내는 능력)
TOOLS = {
    "read_file":  ({"fs.read"},  {"파일 내용"}),
    "write_file": ({"fs.write"}, {"파일 변경"}),
    "run_shell":  ({"exec"},     {"임의 실행"}),
    "http_get":   ({"net.out"},  {"외부 데이터"}),
    "http_post":  ({"net.out"},  {"외부 전송"}),
    "db_query":   ({"db.read"},  {"고객 데이터"}),
    "send_mail":  ({"mail.send"},{"외부 전송"}),
}

# ex1_permission_graph.py가 정의하는 치명 조합 «네 가지»
# (필요 능력 집합, 이름, 등급)
COMBOS = [
    ({"고객 데이터", "외부 전송"}, "고객 데이터 유출", "심각"),
    ({"파일 내용", "외부 전송"},   "소스 코드 유출", "심각"),
    ({"임의 실행", "외부 데이터"}, "원격 코드 실행", "치명"),
    ({"파일 변경", "임의 실행"},   "지속성 확보",   "치명"),
]

for need, name, level in COMBOS:
    print(f"[{level}] {name:<12} <= {sorted(need)}")
# 출력:
# [심각] 고객 데이터 유출  <= ['고객 데이터', '외부 전송']
# [심각] 소스 코드 유출   <= ['외부 전송', '파일 내용']
# [치명] 원격 코드 실행   <= ['외부 데이터', '임의 실행']
# [치명] 지속성 확보     <= ['임의 실행', '파일 변경']


# %% [markdown]
# ## 권한 집합에서 도달 가능한 위험 판정
#
# 세 함수로 «경로»를 따라간다.
# - `usable(G)`: $\text{need}(t) \subseteq G$ 인 도구
# - `capabilities(tools)`: 그 도구들의 능력 합집합
# - `reachable_risks(caps)`: $K \subseteq C$ 인 치명 조합

# %%
def usable(granted):
    return {t for t, (need, _) in TOOLS.items() if need <= granted}


def capabilities(tools):
    out = set()
    for t in tools:
        out |= TOOLS[t][1]
    return out


def reachable_risks(caps):
    return [(name, level) for need, name, level in COMBOS if need <= caps]


def analyze(granted, label):
    ok = usable(granted)
    caps = capabilities(ok)
    risks = reachable_risks(caps)
    print(f"[{label}] 권한 {sorted(granted)}")
    print(f"  쓸 수 있는 도구 {len(ok)}개: {sorted(ok)}")
    print(f"  생기는 능력: {sorted(caps)}")
    print(f"  도달 위험 {len(risks)}개: {[r[0] for r in risks] or '없음'}")
    return ok, caps, risks


# 에이전트에게 준 권한 — 목록으로는 «읽기 + 네트워크 + DB»라 무해해 보인다
GRANTED = {"fs.read", "net.out", "db.read"}
ok, caps, risks = analyze(GRANTED, "원래")
# 출력:
# [원래] 권한 ['db.read', 'fs.read', 'net.out']
#   쓸 수 있는 도구 4개: ['db_query', 'http_get', 'http_post', 'read_file']
#   생기는 능력: ['고객 데이터', '외부 데이터', '외부 전송', '파일 내용']
#   도달 위험 2개: ['고객 데이터 유출', '소스 코드 유출']


# %% [markdown]
# ## 권한 하나(`net.out`)를 빼면 위험 경로가 사라진다
#
# `net.out`은 «외부 전송»과 «외부 데이터»를 동시에 여는 «나가는 문»이다.
# 이 하나를 빼면 도구는 조금 줄지만 위험 경로는 전부 사라진다.

# %%
GRANTED_CUT = GRANTED - {"net.out"}
ok2, caps2, risks2 = analyze(GRANTED_CUT, "net.out 제거")
# 출력:
# [net.out 제거] 권한 ['db.read', 'fs.read']
#   쓸 수 있는 도구 2개: ['db_query', 'read_file']
#   생기는 능력: ['고객 데이터', '파일 내용']
#   도달 위험 0개: 없음

print(f"\n도구: {len(ok)}개 -> {len(ok2)}개 (권한 1개 제거)")
print(f"위험 경로: {len(risks)}개 -> {len(risks2)}개")
# 출력:
# 도구: 4개 -> 2개 (권한 1개 제거)
# 위험 경로: 2개 -> 0개


# %% [markdown]
# ## 네 가지 치명 조합을 모두 켜 보려면 어떤 권한이 필요한가
#
# 네 조합 모두에 도달하려면 «나가는 문» 세 개 — `net.out`(외부 전송/데이터),
# `exec`(임의 실행), `fs.write`(파일 변경) — 가 함께 있어야 한다.

# %%
FULL = {"fs.read", "fs.write", "exec", "net.out", "db.read"}
_, _, risks_full = analyze(FULL, "위험 최대")
assert len(risks_full) == 4, "네 조합 모두 도달해야 한다"
print("\n네 가지 치명 조합이 모두 도달 가능 -> 최소 권한 원칙 위반")
# 출력:
# [위험 최대] 권한 ['db.read', 'exec', 'fs.read', 'fs.write', 'net.out']
#   쓸 수 있는 도구 6개: ['db_query', 'http_get', 'http_post', 'read_file', 'run_shell', 'write_file']
#   생기는 능력: ['고객 데이터', '외부 데이터', '외부 전송', '임의 실행', '파일 내용', '파일 변경']
#   도달 위험 4개: ['고객 데이터 유출', '소스 코드 유출', '원격 코드 실행', '지속성 확보']
#
# 네 가지 치명 조합이 모두 도달 가능 -> 최소 권한 원칙 위반


# %% [markdown]
# ## 시각화: 권한 → 도구 → 능력 → 치명 조합 그래프
#
# «위험 최대» 권한에서의 도달 경로를 계층 그래프로 그린다.
# 각 치명 조합(빨강)이 두 능력에서 이어지는 것을 눈으로 확인한다.

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

    granted = FULL
    ok_f = usable(granted)
    caps_f = capabilities(ok_f)

    # 4개 계층 좌표
    perms = sorted(granted)
    tools = sorted(ok_f)
    capsl = sorted(caps_f)
    combos = [c[1] for c in COMBOS]

    def col_pos(items, x):
        n = len(items)
        return {it: (x, (n - 1) / 2 - i) for i, it in enumerate(items)}

    P = col_pos(perms, 0)
    T = col_pos(tools, 1)
    Cp = col_pos(capsl, 2)
    Cb = col_pos(combos, 3)

    edge_x, edge_y = [], []

    def add_edge(a, b):
        edge_x.extend([a[0], b[0], None])
        edge_y.extend([a[1], b[1], None])

    # 권한 -> 도구
    for t in tools:
        need = TOOLS[t][0]
        for p in need:
            if p in P:
                add_edge(P[p], T[t])
    # 도구 -> 능력
    for t in tools:
        for cap in TOOLS[t][1]:
            if cap in Cp:
                add_edge(T[t], Cp[cap])
    # 능력 -> 치명 조합
    for need, name, _ in COMBOS:
        for cap in need:
            if cap in Cp:
                add_edge(Cp[cap], Cb[name])

    def scatter(pos, color, name):
        return go.Scatter(
            x=[v[0] for v in pos.values()],
            y=[v[1] for v in pos.values()],
            mode="markers+text",
            text=list(pos.keys()),
            textposition="middle right",
            marker=dict(size=18, color=color),
            name=name,
        )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(color="rgba(120,120,120,0.4)", width=1),
        hoverinfo="none", showlegend=False,
    ))
    fig.add_trace(scatter(P, "#4C78A8", "권한"))
    fig.add_trace(scatter(T, "#72B7B2", "도구"))
    fig.add_trace(scatter(Cp, "#F58518", "능력"))
    fig.add_trace(scatter(Cb, "#E45756", "치명 조합"))
    fig.update_layout(
        title="권한 → 도구 → 능력 → 치명 조합 (위험 최대 권한)",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                   tickvals=[0, 1, 2, 3], range=[-0.3, 4]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        width=1000, height=640, template="plotly_white",
    )
    _show(fig)

    import os
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
    try:
        fig.write_image(out)
        print(f"PNG 저장: {out}")
    except Exception as e:  # kaleido 미설치 등
        print(f"PNG 저장 건너뜀: {e}")
except ImportError:
    print("plotly 미설치 — 시각화 건너뜀 (모델 검증은 완료)")
# 출력:
# PNG 저장: /.../expy.png
