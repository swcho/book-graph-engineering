# %% [markdown]
# # 세 구성의 초당 부하 — 90ms / 937ms / 191ms
#
# 29장 예제 4(`ex4_split_cost.py`)의 계산을 단계별로 재현한다.
#
# 초당 부하 공식:
#
# $$\text{load} = w_{\text{graph}} \times 4.2\,\text{ms} + w_{\text{kv}} \times 0.35\,\text{ms}$$
#
# - 지식 쓰기 3/s, 실행 상태 쓰기 220/s (실행이 지식의 약 70배)
# - 그래프 DB 쓰기 4.2ms/건, 키-값 저장소 쓰기 0.35ms/건

# %%
# 필요 패키지: plotly, kaleido (시각화 셀에서만 사용)
def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# 워크로드 (건/초)
KG_WRITE_QPS = 3        # 지식 갱신
RUN_WRITE_QPS = 220     # 실행 상태 쓰기 — 슈퍼스텝마다 (21장)

# 저장소별 쓰기 지연 (ms/건)
GRAPH_WRITE_MS = 4.2
KV_WRITE_MS = 0.35

print(f"실행 쓰기 / 지식 쓰기 = {RUN_WRITE_QPS / KG_WRITE_QPS:.0f}배")
# 출력: 실행 쓰기 / 지식 쓰기 = 73배

# %% [markdown]
# ## 구성 1 — 따로 (그래프 DB + 상태 저장소)
#
# 지식 쓰기만 그래프로, 실행 쓰기 220건은 전부 키-값으로 간다.

# %%
sep_graph_w = KG_WRITE_QPS                    # 3/s
sep_kv_w = RUN_WRITE_QPS                      # 220/s
sep_load = sep_graph_w * GRAPH_WRITE_MS + sep_kv_w * KV_WRITE_MS
print(f"따로: {sep_graph_w}×{GRAPH_WRITE_MS} + {sep_kv_w}×{KV_WRITE_MS}"
      f" = {sep_load:.1f}ms → 약 {round(sep_load)}ms")
# 출력: 따로: 3×4.2 + 220×0.35 = 89.6ms → 약 90ms

# %% [markdown]
# ## 구성 2 — 합침 (한 그래프 DB)
#
# 쓰기 223건이 전부 그래프 DB로 몰린다.

# %%
mrg_graph_w = KG_WRITE_QPS + RUN_WRITE_QPS    # 223/s
mrg_load = mrg_graph_w * GRAPH_WRITE_MS
print(f"합침: {mrg_graph_w}×{GRAPH_WRITE_MS} = {mrg_load:.1f}ms → 약 {round(mrg_load)}ms")
print(f"초당 1,000ms 예산 대비 사용률: {mrg_load / 1000:.0%} → 거의 포화")
# 출력: 합침: 223×4.2 = 936.6ms → 약 937ms
# 출력: 초당 1,000ms 예산 대비 사용률: 94% → 거의 포화

# %% [markdown]
# ## 구성 3 — 절충 (본문은 키-값, 링크만 그래프에)
#
# 실행 쓰기의 12%(Run 노드 + Reads/Writes 링크 엣지)만 그래프에 남기고,
# 나머지 88%(상태 본문·체크포인트)는 SQLite·Postgres 같은 빠른 저장소로.

# %%
WRITE_AMP = 0.12
mid_graph_w = KG_WRITE_QPS + RUN_WRITE_QPS * WRITE_AMP        # 29.4/s
mid_kv_w = RUN_WRITE_QPS * (1 - WRITE_AMP)                    # 193.6/s
mid_load = mid_graph_w * GRAPH_WRITE_MS + mid_kv_w * KV_WRITE_MS
print(f"절충: {mid_graph_w:.1f}×{GRAPH_WRITE_MS} + {mid_kv_w:.1f}×{KV_WRITE_MS}"
      f" = {mid_load:.1f}ms → 약 {round(mid_load)}ms")
print(f"따로의 {mid_load / sep_load:.1f}배, 합침의 1/{mrg_load / mid_load:.1f}")
# 출력: 절충: 29.4×4.2 + 193.6×0.35 = 191.2ms → 약 191ms
# 출력: 따로의 2.1배, 합침의 1/4.9

# %% [markdown]
# ## 요약표
#
# | 구성 | 초당 부하 | 교차 질의 | 한 트랜잭션 |
# |---|---|---|---|
# | 따로 | 90ms | 불가 | 불가 |
# | 합침 | 937ms (포화 직전) | 가능 | 가능 |
# | 절충 | 191ms | 가능 | 포기 → 30·31장 |

# %%
configs = ["따로", "합침", "절충"]
loads = [sep_load, mrg_load, mid_load]
for name, load in zip(configs, loads):
    bar = "#" * round(load / 20)
    print(f"{name:<4}{load:>7.0f}ms |{bar}")
print(f"{'한계':<4}{1000:>7.0f}ms |" + "-" * 50)
# 출력: 따로     90ms |####
# 출력: 합침    937ms |###############################################
# 출력: 절충    191ms |##########
# 출력: 한계   1000ms |--------------------------------------------------

# %% [markdown]
# ## 시각화
#
# 세 구성의 초당 부하를 그래프/키-값 성분으로 쌓아 보고,
# 초당 1,000ms 한계선과 비교한다.

# %%
import os

import plotly.graph_objects as go

graph_parts = [sep_graph_w * GRAPH_WRITE_MS,
               mrg_graph_w * GRAPH_WRITE_MS,
               mid_graph_w * GRAPH_WRITE_MS]
kv_parts = [sep_kv_w * KV_WRITE_MS, 0.0, mid_kv_w * KV_WRITE_MS]

fig = go.Figure()
fig.add_bar(x=configs, y=graph_parts, name="그래프 DB 쓰기 (4.2ms/건)",
            marker_color="#4C6EF5",
            text=[f"{v:.0f}" for v in graph_parts], textposition="inside")
fig.add_bar(x=configs, y=kv_parts, name="키-값 쓰기 (0.35ms/건)",
            marker_color="#94A3B8",
            text=[f"{v:.0f}" if v else "" for v in kv_parts],
            textposition="inside")
fig.add_hline(y=1000, line_dash="dash", line_color="#E03131",
              annotation_text="초당 1,000ms 한계",
              annotation_position="top left")
for name, load in zip(configs, loads):
    fig.add_annotation(x=name, y=load, text=f"<b>{load:.0f}ms</b>",
                       showarrow=False, yshift=14)
fig.update_layout(barmode="stack",
                  title="세 구성의 초당 쓰기 부하 — 합침은 한계에 거의 포화",
                  yaxis_title="초당 부하 (ms)", xaxis_title="구성",
                  yaxis_range=[0, 1100], template="plotly_white",
                  width=760, height=480,
                  legend=dict(orientation="h", y=1.06, x=0))
_show(fig)

_here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else "."
fig.write_image(os.path.join(_here, "expy.png"), scale=2)
print("expy.png 저장 완료")
# 출력: expy.png 저장 완료
