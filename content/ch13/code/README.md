# 13장 — 검증하지 않은 그래프는 그냥 링크 뭉치다

`3부 — 지식 그래프 엔지니어링 (트랙 1)` | [책 전체 목차](../../../README.md) | [출처 링크 모음](../../../SOURCES.md)

> 적재를 막았더니 데이터가 안 들어왔습니다.

다음 날 저는 검증을 껐습니다. 그리고 3개월 뒤에 다시 켤 때까지, 데이터는 다시 썩었습니다. 이 장은 그 사이에서 균형을 잡는 이야기입니다. 무엇을 막고 무엇을 통과시킬지, 그리고 검증으로 못 잡는 것들을 어떻게 잡을지요.

## 이 장의 절

| 절 | 제목 |
|---|---|
| 13.1 | 추론기와 검증기는 다른 물건이다 |
| 13.2 | 전부 막으면 아무것도 안 들어온다 |
| 13.3 | SHACL로 못 잡는 것들 |
| 13.4 | 모양은 맞는데 뜻이 달라졌다 |
| 13.5 | 품질을 한 숫자로 만들지 마라 |

## 한 장 요약

- 추론기와 검증기는 다른 물건입니다. OWL은 없으면 있다고 결론 내고, SHACL은 없으면 위반이라고 적습니다. 품질 검사에 추론기를 쓰면 3주를 날립니다.
- 전부 막으면 데이터가 안 들어오고, 그러면 사람들이 검증을 우회합니다. 우회 경로가 주 경로가 되는 게 최악이에요. 심각도를 셋으로 나누고, 차단 기준은 「되돌릴 수 없는가」 하나로 정하세요.
- SHACL로 못 잡는 게 많습니다. 슈퍼 노드, 사이클, 중복 의심, 다중 소속. 이건 세어 봐야 보이고, 자동으로 고치면 안 됩니다. 목록만 뽑아 사람이 보게 하세요.
- 형태 검사를 다 통과하면서 답이 달라지는 변경이 있습니다. 역량 질의를 회귀 테스트에 넣어야 잡힙니다. 골든 데이터셋은 30~50건이면 충분하고, 크기보다 경계 사례가 중요해요.
- 품질을 한 숫자로 합치지 마세요. 데이터가 늘면 비율은 좋아지고 절대 개수는 나빠집니다. 둘 다 적어야 속지 않습니다.

## 키워드와 1차 출처

| 키워드 | 상태 | 출처 |
|---|---|---|
| SHACL 형태 제약 | [표준] | [Shapes Constraint Language](https://www.w3.org/TR/shacl/) |
| 제약 위반 심각도 | [표준] | [sh:severity](https://www.w3.org/TR/shacl/#severity) |
| SHACL 고급 기능 | [표준] | [SHACL Advanced Features](https://www.w3.org/TR/shacl-af/) |
| OWL 2 프로필 | [표준] | [OWL 2 Profiles](https://www.w3.org/TR/owl2-profiles/) |
| 데이터 품질 차원 | [표준] | [ISO/IEC 25012](https://www.iso.org/standard/35736.html) |
| 그래프 스멜 | [실험] | [graph smell](https://www.w3.org/TR/shacl/) |
| 역량 질의 회귀 테스트 | [실험] | [competency question regression](https://protege.stanford.edu/publications/ontology_development/ontology101.pdf) |

상태 표시는 **[표준]** 공식 명세, **[사실상 표준]** 명세는 없지만 업계가 널리 쓰는 것, **[실험]** 아직 자리를 잡는 중이라는 뜻입니다.

## 예제 실행

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

확인 시점 2026년 8월. Python 3.9 이상.

```bash
cd content/ch13/code
pip install pyshacl owlrl "rdflib>=7,<8"
python3 ex1_shacl_severity.py     # 심각도 세 단계
python3 ex2_infer_vs_validate.py  # 추론기와 검증기는 다른 물건
python3 ex3_graph_smells.py       # 의존성 없음
python3 ex4_regression.py         # 의존성 없음
python3 ex5_quality_metrics.py    # 의존성 없음
```

| 파일 | 보여 주는 것 |
|---|---|
| `shapes.ttl` / `data.ttl` | SHACL 형태와 일부러 어긴 데이터 |
| `ex1` | `sh:severity` 로 차단/경고/기록을 나눈다 |
| `ex2` | 같은 규칙을 OWL로 쓰면 «없으면 있다고 결론»낸다 |
| `ex3` | SHACL로 못 잡는 다섯 가지 그래프 스멜 |
| `ex4` | 형태 검사는 통과하는데 질의 답이 달라지는 변경 |
| `ex5` | 품질 점수 하나로 합치면 안 되는 이유 |

<!-- 실행 가이드 끝 -->

---

**다음 장에서 뒤집히는 것:** 이 장에서 「중복 의심」을 스멜로만 다뤘습니다. 다음 장이 그 본편이에요. 같은 사람이 노드 네 개로 앉아 있는 상황을 어떻게 푸는지, 그리고 왜 자동 병합이 위험한지 제대로 봅니다.

---

이전 [12장 온톨로지를 3주 만에 갈아엎은 이야기](../../ch12/code/README.md) | [전체 목차](../../../README.md) | 다음 [14장 같은 사람이 노드 네 개로 앉아 있다](../../ch14/code/README.md)

이 장에서 틀린 곳을 찾으셨다면 [사실 오류로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml), 상태 라벨이 어긋났다면 [라벨 이의로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml) 적어 주세요.
