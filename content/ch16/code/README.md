# 16장 — 어제는 맞았고 오늘은 틀리다

`3부 — 지식 그래프 엔지니어링 (트랙 1)` | [책 전체 목차](../../../README.md) | [출처 링크 모음](../../../SOURCES.md)

> 감사팀에서 6월 30일 자 계약 현황 보고서를 다시 뽑아 달라고 했습니다.

저는 답을 못 했습니다. 우리 시스템에는 「지금 아는 것」만 있었고, 「6월 30일에 알고 있던 것」은 어디에도 없었으니까요. 이 장은 그 두 가지를 다 담는 방법입니다.

## 이 장의 절

| 절 | 제목 |
|---|---|
| 16.1 | 시간 축이 하나가 아니다 |
| 16.2 | 만료와 정정은 다르다 |
| 16.3 | 날짜를 문자열로 두면 조용히 틀린다 |
| 16.4 | 시간이 붙으면 관계가 사건이 된다 |
| 16.5 | 그래서 얼마나 커지나 |

## 한 장 요약

- 시간 축은 둘입니다. 유효 시간은 현실에서 참인 기간이고, 기록 시간은 우리가 그렇게 알고 있던 기간이에요. 「3월에 담당이 누구였나」와 「3월에 우리는 누구로 알았나」는 다른 질문입니다.
- 만료와 정정은 다릅니다. 만료는 그때는 맞았고, 정정은 그때도 틀렸어요. 섞으면 과거 보고서가 소급해서 바뀝니다. 입력 화면에서 물어보세요.
- 날짜를 문자열로 비교하면 조용히 틀립니다. 예외가 안 나고 그냥 반대로 정렬돼요. 적재 시점에 파싱하고, 파싱 실패는 차단 등급으로 올리세요.
- 시간을 붙이면 관계가 사건이 됩니다. 시간을 붙일 관계는 처음부터 사건 노드로 만드는 게 나중에 승격하는 것보다 쌉니다.
- 전부 이중 시간으로 하면 139배가 됩니다. 「이 값 때문에 나중에 누가 항의할 수 있나」로 골라 붙이면 12배로 떨어져요. 그리고 과거는 소급해서 만들 수 없으니, 필요해지기 전에 정해야 합니다.

## 키워드와 1차 출처

| 키워드 | 상태 | 출처 |
|---|---|---|
| 이중 시간 | [사실상 표준] | [bitemporal](https://www.iso.org/standard/76583.html) |
| 유효 시간 | [표준] | [valid time](https://www.iso.org/standard/76583.html) |
| 기록 시간 | [표준] | [transaction time](https://www.iso.org/standard/76583.html) |
| 시간 인식 그래프 | [실험] | [Graphiti / Zep](https://github.com/getzep/graphiti) |
| 시각 표현 표준 | [표준] | [ISO 8601](https://www.iso.org/iso-8601-date-and-time-format.html) |
| RDF 시간 온톨로지 | [표준] | [OWL-Time](https://www.w3.org/TR/owl-time/) |
| 느리게 변하는 차원 | [사실상 표준] | [slowly changing dimension](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/) |

상태 표시는 **[표준]** 공식 명세, **[사실상 표준]** 명세는 없지만 업계가 널리 쓰는 것, **[실험]** 아직 자리를 잡는 중이라는 뜻입니다.

## 예제 실행

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

확인 시점 2026년 8월. Python 3.9 이상.

```bash
cd content/ch16/code
python3 ex1_two_axes.py       # 의존성 없음
python3 ex2_correction.py     # 의존성 없음
python3 ex3_string_dates.py   # 의존성 없음
pip install kuzu "rdflib>=7,<8"
python3 ex4_temporal_query.py # Cypher / SPARQL 시점 질의
python3 ex5_storage_cost.py   # 의존성 없음
```

| 파일 | 보여 주는 것 |
|---|---|
| `bitemporal.py` | 이중 시간 저장소 100줄 |
| `ex1` | 같은 저장소에 네 가지 시점 질문 |
| `ex2` | 만료와 정정을 섞으면 과거 재현이 깨진다 |
| `ex3` | 날짜를 문자열로 비교하면 6건 중 5건이 틀린다 |
| `ex4` | LPG는 엣지 속성으로, RDF는 사건 노드로 |
| `ex5` | 이중 시간의 저장 비용과 자르는 기준 |

<!-- 실행 가이드 끝 -->

---

**다음 장에서 뒤집히는 것:** 3부의 마지막입니다. 지금까지 그래프를 짓고 지켰다면, 다음 장은 그걸로 답을 만드는 이야기예요. 벡터만으로 안 되는 질문에 그래프를 어떻게 붙일지, 그리고 그 조합이 언제 손해인지 봅니다.

---

이전 [15장 문서 1만 건에서 트리플을 뽑았더니 절반이 거짓이었다](../../ch15/code/README.md) | [전체 목차](../../../README.md) | 다음 [17장 벡터만으로 답이 안 나오는 질문들](../../ch17/code/README.md)

이 장에서 틀린 곳을 찾으셨다면 [사실 오류로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml), 상태 라벨이 어긋났다면 [라벨 이의로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml) 적어 주세요.
