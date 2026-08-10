# %% [markdown]
# # 노드 3개 · 엣지 2개 → 트리플 12개
#
# 5장 `model.py`의 데이터를 그대로 손으로 옮겨 놓고, LPG 자료구조에서
# RDF 트리플 리스트를 **직접 만들어** 개수가 정말 12가 되는지 계산해 본다.
#
# 세는 규칙은 세 줄뿐이다.
#
# - 라벨 하나 → `rdf:type` 트리플 하나
# - 노드 속성 하나 → 리터럴 트리플 하나
# - 엣지 하나 → 트리플 하나 (엣지 **속성**은 이 셈에서 제외)
#
# 그래서 노드 하나가 만드는 트리플 수는 $|L_i| + |P_i|$ 이고, 전체는
#
# $$T = \sum_{i=1}^{n}\bigl(|L_i| + |P_i|\bigr) + |E|$$
#
# 이 예제에서는 $T = (1+2) + (1+2) + (2+2) + 2 = 12$.

# %%
# 필요 패키지: plotly (시각화), kaleido (expy.png 저장). 둘 다 없어도 계산 셀은 그대로 돌아간다.
from __future__ import annotations

import os


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()

# %% [markdown]
# ## 1단계 — LPG 원본 데이터
#
# 노드도 엣지도 「속성 주머니」를 하나씩 갖는다. 이게 LPG가 세는 단위다.

# %%
LPG_NODES = {
    "n1": {"labels": ["Company"], "props": {"name": "가온테크", "grade": "A"}},
    "n2": {"labels": ["Contract"], "props": {"id": "C-2025-118", "amount": 5_000_000}},
    "n3": {"labels": ["Person", "Employee"], "props": {"name": "김하늘", "title": "부장"}},
}

LPG_EDGES = [
    {
        "from": "n1",
        "type": "SIGNED",
        "to": "n2",
        "props": {"at": "2025-06-02", "channel": "직접", "confidence": 0.98},
    },
    {
        "from": "n1",
        "type": "MANAGED_BY",
        "to": "n3",
        "props": {"since": "2023-04-01"},
    },
]

print(f"LPG: 노드 {len(LPG_NODES)}개, 엣지 {len(LPG_EDGES)}개")
print("노드 속성 총합:", sum(len(n["props"]) for n in LPG_NODES.values()))
print("라벨 총합:", sum(len(n["labels"]) for n in LPG_NODES.values()))
print("엣지 속성 총합:", sum(len(e["props"]) for e in LPG_EDGES))
# 출력: LPG: 노드 3개, 엣지 2개
# 출력: 노드 속성 총합: 6
# 출력: 라벨 총합: 4
# 출력: 엣지 속성 총합: 4

# %% [markdown]
# ## 2단계 — LPG → RDF 변환기
#
# 노드 id를 IRI로 바꾸고, 규칙 세 줄을 그대로 코드로 옮긴다.
# 트리플에 `kind` 태그(`type` / `literal` / `edge`)를 붙여 두면
# 나중에 항목별 개수를 그냥 세기만 하면 된다.

# %%
IRI = {"n1": "ex:Gaon", "n2": "ex:C2025118", "n3": "ex:Kim"}
PRED = {  # 속성 키 → 술어 이름
    "name": "ex:name",
    "grade": "ex:grade",
    "id": "ex:id",
    "amount": "ex:amount",
    "title": "ex:title",
}
EDGE_PRED = {"SIGNED": "ex:signed", "MANAGED_BY": "ex:managedBy"}


def literal(value):
    """파이썬 값을 RDF 리터럴 표기로."""
    if isinstance(value, bool):
        return f'"{str(value).lower()}"^^xsd:boolean'
    if isinstance(value, int):
        return f'"{value}"^^xsd:integer'
    if isinstance(value, float):
        return f'"{value}"^^xsd:decimal'
    return f'"{value}"'


def lpg_to_rdf(nodes, edges, include_edge_props=False):
    """LPG 딕셔너리 → (subject, predicate, object, kind) 리스트."""
    triples = []
    for nid, node in nodes.items():
        subj = IRI[nid]
        for label in node["labels"]:  # 라벨 → rdf:type
            triples.append((subj, "rdf:type", f"ex:{label}", "type"))
        for key, value in node["props"].items():  # 속성 → 리터럴 트리플
            triples.append((subj, PRED[key], literal(value), "literal"))
    for edge in edges:  # 엣지 → 트리플
        triples.append((IRI[edge["from"]], EDGE_PRED[edge["type"]], IRI[edge["to"]], "edge"))
        if include_edge_props:
            # 순진하게 붙이면 주어를 가리킬 방법이 없다. 3단계에서 제대로 본다.
            for key, value in edge["props"].items():
                triples.append((f'<<{IRI[edge["from"]]} {EDGE_PRED[edge["type"]]} {IRI[edge["to"]]}>>',
                                f"ex:{key}", literal(value), "edge-prop"))
    return triples


RDF_TRIPLES = lpg_to_rdf(LPG_NODES, LPG_EDGES)

for i, (s, p, o, kind) in enumerate(RDF_TRIPLES, 1):
    print(f"{i:2d}. {s:14s} {p:14s} {o:24s} [{kind}]")
print(f"\n합계: {len(RDF_TRIPLES)} 트리플")
# 출력:  1. ex:Gaon       rdf:type       ex:Company               [type]
# 출력:  2. ex:Gaon       ex:name        "가온테크"                 [literal]
# 출력:  3. ex:Gaon       ex:grade       "A"                      [literal]
# 출력:  4. ex:C2025118   rdf:type       ex:Contract              [type]
# 출력:  5. ex:C2025118   ex:id          "C-2025-118"             [literal]
# 출력:  6. ex:C2025118   ex:amount      "5000000"^^xsd:integer   [literal]
# 출력:  7. ex:Kim        rdf:type       ex:Person                [type]
# 출력:  8. ex:Kim        rdf:type       ex:Employee              [type]
# 출력:  9. ex:Kim        ex:name        "김하늘"                   [literal]
# 출력: 10. ex:Kim        ex:title       "부장"                    [literal]
# 출력: 11. ex:Gaon       ex:signed      ex:C2025118              [edge]
# 출력: 12. ex:Gaon       ex:managedBy   ex:Kim                   [edge]
# 출력:
# 출력: 합계: 12 트리플

# %%
from collections import Counter  # noqa: E402

breakdown = Counter(kind for *_, kind in RDF_TRIPLES)
print("rdf:type   :", breakdown["type"], "  (Company 1 + Contract 1 + Person 1 + Employee 1)")
print("리터럴 속성 :", breakdown["literal"], "  (name/grade + id/amount + name/title)")
print("엣지       :", breakdown["edge"], "  (ex:signed, ex:managedBy)")
print("─" * 34)
print("합계       :", sum(breakdown.values()))
assert len(RDF_TRIPLES) == 12
assert (breakdown["type"], breakdown["literal"], breakdown["edge"]) == (4, 6, 2)
print("검증 통과: 4 + 6 + 2 = 12")
# 출력: rdf:type   : 4   (Company 1 + Contract 1 + Person 1 + Employee 1)
# 출력: 리터럴 속성 : 6   (name/grade + id/amount + name/title)
# 출력: 엣지       : 2   (ex:signed, ex:managedBy)
# 출력: ──────────────────────────────────
# 출력: 합계       : 12
# 출력: 검증 통과: 4 + 6 + 2 = 12

# %% [markdown]
# ## 3단계 — 공식으로 다시 확인
#
# 노드마다 $|L_i| + |P_i|$, 엣지마다 1.
#
# $$T = \underbrace{4}_{\text{라벨}} + \underbrace{6}_{\text{노드 속성}} + \underbrace{2}_{\text{엣지}} = 12$$

# %%
def predict_triples(nodes, edges):
    labels = sum(len(n["labels"]) for n in nodes.values())
    props = sum(len(n["props"]) for n in nodes.values())
    return labels + props + len(edges), labels, props, len(edges)


total, labels, props, n_edges = predict_triples(LPG_NODES, LPG_EDGES)
print(f"{labels} (라벨) + {props} (노드 속성) + {n_edges} (엣지) = {total}")
assert total == len(RDF_TRIPLES)
# 출력: 4 (라벨) + 6 (노드 속성) + 2 (엣지) = 12

# %% [markdown]
# ## 4단계 — 엣지 속성을 넣으면?
#
# LPG는 엣지 속성을 주머니에 그냥 넣어서 **엣지 수가 그대로 2개**다.
# RDF는 셋 중 하나를 골라야 하고, 방식마다 늘어나는 양이 다르다.
#
# 엣지 속성은 `SIGNED` 3개(at/channel/confidence) + `MANAGED_BY` 1개(since) = 4개.
#
# | 방식 | 규칙 | 늘어남 |
# |---|---|---|
# | 제외(기준) | 엣지 = 1 트리플 | — |
# | RDF-star | 원래 엣지 유지 + 속성마다 트리플 term 주어 1줄 | $+\sum_e |P_e|$ |
# | 구체화 | 엣지 트리플을 없애고 사건 노드로 승격 (`hasX` 1 + `rdf:type` 1 + `contract` 1 + 속성) | $-1 + 3 + |P_e|$ 씩 |
# | 이름 붙인 그래프 | 엣지 트리플을 named graph로 감싸고 그래프 이름에 속성 부착 | $+\sum_e |P_e|$, 대신 그래프 수 증가 |

# %%
def count_rdf_star(nodes, edges):
    """원래 엣지 트리플은 그대로 두고, 속성마다 << >> 주어 트리플 1개."""
    base, *_ = predict_triples(nodes, edges)
    return base + sum(len(e["props"]) for e in edges)


def count_reified(nodes, edges):
    """엣지를 사건 노드로 승격. 엣지 트리플 1개가 3 + |props| 개로 바뀐다."""
    base, *_ = predict_triples(nodes, edges)
    delta = 0
    for e in edges:
        if e["props"]:
            delta += -1 + 3 + len(e["props"])  # 엣지 트리플 제거, hasX/type/target + 속성
    return base + delta


def count_named_graph(nodes, edges):
    """엣지 트리플을 이름 붙인 그래프로 감싸고, 그래프 이름에 속성을 단다."""
    base, *_ = predict_triples(nodes, edges)
    stmts = base + sum(len(e["props"]) for e in edges)
    graphs = 1 + sum(1 for e in edges if e["props"])  # default + 엣지별 1개
    return stmts, graphs


base_total, *_ = predict_triples(LPG_NODES, LPG_EDGES)
star = count_rdf_star(LPG_NODES, LPG_EDGES)
reified = count_reified(LPG_NODES, LPG_EDGES)
ng_stmts, ng_graphs = count_named_graph(LPG_NODES, LPG_EDGES)

RESULTS = [
    ("LPG (노드+엣지)", len(LPG_NODES) + len(LPG_EDGES)),
    ("RDF 엣지속성 제외", base_total),
    ("RDF-star", star),
    ("이름 붙인 그래프", ng_stmts),
    ("구체화(reification)", reified),
]
for name, cnt in RESULTS:
    print(f"{name:20s} {cnt:3d}")
print(f"\n이름 붙인 그래프의 그래프 수: {ng_graphs}개 (default + 엣지 2개)")
assert (base_total, star, reified, ng_stmts) == (12, 16, 20, 16)
# 출력: LPG (노드+엣지)            5
# 출력: RDF 엣지속성 제외           12
# 출력: RDF-star              16
# 출력: 이름 붙인 그래프             16
# 출력: 구체화(reification)      20
# 출력:
# 출력: 이름 붙인 그래프의 그래프 수: 3개 (default + 엣지 2개)

# %% [markdown]
# 구체화만 유일하게 **원래 `ex:signed` 엣지가 사라진다**. 그래서 트리플이 20개로
# 가장 많이 늘고, 기존 질의도 깨진다. RDF-star는 원래 엣지를 남기므로 16개에서 멈춘다.

# %%
# 구체화 결과를 실제로 만들어서 20개인지 확인 (model.py 의 RDF_REIFIED 와 같은 모양)
EVENT = {"SIGNED": ("ex:hasSigning", "ex:Signing", "ex:Signing1", "ex:contract"),
         "MANAGED_BY": ("ex:hasManagement", "ex:Management", "ex:Mgmt1", "ex:person")}


def build_reified(nodes, edges):
    triples = [t for t in lpg_to_rdf(nodes, edges) if t[3] != "edge"]
    for e in edges:
        if not e["props"]:
            triples.append((IRI[e["from"]], EDGE_PRED[e["type"]], IRI[e["to"]], "edge"))
            continue
        has, cls, inst, target = EVENT[e["type"]]
        triples.append((IRI[e["from"]], has, inst, "reified"))
        triples.append((inst, "rdf:type", cls, "reified"))
        triples.append((inst, target, IRI[e["to"]], "reified"))
        for k, v in e["props"].items():
            triples.append((inst, f"ex:{k}", literal(v), "reified"))
    return triples


REIFIED = build_reified(LPG_NODES, LPG_EDGES)
print(f"구체화 트리플 수: {len(REIFIED)} (예측 {reified})")
for s, p, o, kind in REIFIED:
    if kind == "reified":
        print(f"   {s:16s} {p:16s} {o}")
assert len(REIFIED) == reified
# 출력: 구체화 트리플 수: 20 (예측 20)
# 출력:    ex:Gaon          ex:hasSigning    ex:Signing1
# 출력:    ex:Signing1      rdf:type         ex:Signing
# 출력:    ex:Signing1      ex:contract      ex:C2025118
# 출력:    ex:Signing1      ex:at            "2025-06-02"
# 출력:    ex:Signing1      ex:channel       "직접"
# 출력:    ex:Signing1      ex:confidence    "0.98"^^xsd:decimal
# 출력:    ex:Gaon          ex:hasManagement ex:Mgmt1
# 출력:    ex:Mgmt1         rdf:type         ex:Management
# 출력:    ex:Mgmt1         ex:person        ex:Kim
# 출력:    ex:Mgmt1         ex:since         "2023-04-01"

# %% [markdown]
# ## 5단계 — 규모가 커지면
#
# 노드 하나가 라벨 $\ell$ 개, 속성 $p$ 개를 갖고 노드당 엣지가 $d$ 개라면
#
# $$T(n) = n\,(\ell + p + d)$$
#
# 이 예제의 평균값은 $\ell \approx 1.33$, $p = 2$, $d \approx 0.67$ 이라 노드 1개당 트리플 4개.
# LPG 카운트는 노드당 $1 + d$ 개다. **비율이 상수**라서, 「12개」는 데이터가 커진다는 뜻이 아니라
# 자를 바꿔 잰다는 뜻일 뿐이다.

# %%
AVG_PER_NODE = 12 / 3  # 트리플/노드
AVG_LPG_PER_NODE = 5 / 3  # (노드+엣지)/노드
for n in (3, 30, 300, 3000):
    print(f"노드 {n:5d}개 → RDF 트리플 {int(n * AVG_PER_NODE):6d}, LPG 요소 {int(n * AVG_LPG_PER_NODE):5d}")
# 출력: 노드     3개 → RDF 트리플     12, LPG 요소     5
# 출력: 노드    30개 → RDF 트리플    120, LPG 요소    50
# 출력: 노드   300개 → RDF 트리플   1200, LPG 요소   500
# 출력: 노드  3000개 → RDF 트리플  12000, LPG 요소  5000

# %% [markdown]
# ## 6단계 — 시각화
#
# 왼쪽: 12개의 구성(4 + 6 + 2). 오른쪽: 엣지 속성 처리 방식별 트리플 수.

# %%
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("12개 트리플의 구성", "엣지 속성 처리 방식별 트리플 수"),
        specs=[[{"type": "bar"}, {"type": "bar"}]],
    )

    parts = [("rdf:type (라벨)", 4), ("리터럴 속성", 6), ("엣지", 2)]
    fig.add_trace(
        go.Bar(
            x=[p[0] for p in parts],
            y=[p[1] for p in parts],
            text=[p[1] for p in parts],
            textposition="outside",
            marker_color=["#4C78A8", "#F58518", "#54A24B"],
            name="구성",
            showlegend=False,
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Bar(
            x=[r[0] for r in RESULTS],
            y=[r[1] for r in RESULTS],
            text=[r[1] for r in RESULTS],
            textposition="outside",
            marker_color=["#B279A2", "#4C78A8", "#54A24B", "#EECA3B", "#E45756"],
            name="방식",
            showlegend=False,
        ),
        row=1,
        col=2,
    )

    fig.update_yaxes(title_text="트리플 수", range=[0, 8], row=1, col=1)
    fig.update_yaxes(title_text="트리플 수", range=[0, 24], row=1, col=2)
    fig.update_layout(
        title_text="노드 3개 · 엣지 2개 = 트리플 12개 (엣지 속성 제외)",
        template="plotly_white",
        height=460,
        width=1000,
        font=dict(size=13),
    )

    _show(fig)
    png = os.path.join(HERE, "expy.png")
    fig.write_image(png, scale=2)  # kaleido 필요
    print("저장:", png)
except ImportError as exc:  # plotly/kaleido 없을 때도 위 계산 셀은 유효
    print("시각화 건너뜀:", exc)
# 출력: 저장: .../expy.png

# %% [markdown]
# ## 정리
#
# - **12개 = rdf:type 4 + 리터럴 속성 6 + 엣지 2** (엣지 속성 제외)
# - 라벨이 2개인 `ex:Kim`(`Person`, `Employee`)이 `rdf:type`을 2줄 만든다 — 4개가 되는 이유
# - LPG는 5개(노드 3 + 엣지 2), RDF는 12개. **같은 사실, 다른 자**
# - 엣지 속성 4개를 넣으면 RDF-star 16, 이름 붙인 그래프 16(+그래프 2개), 구체화 20
# - 진짜 차이는 개수가 아니라 「속성 하나를 손가락으로 가리킬 수 있는가」다.
#   RDF는 트리플 하나를 가리킬 수 있고, LPG는 속성이 주머니 안이라 손잡이가 없다.
