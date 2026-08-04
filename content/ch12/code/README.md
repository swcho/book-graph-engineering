# 12장 — 온톨로지를 3주 만에 갈아엎은 이야기

`3부 — 지식 그래프 엔지니어링 (트랙 1)` | **한국어** | [English](../../../content_en/ch12/code/README.md) | [책 전체 목차](../../../README.md) | [출처 링크 모음](../../../SOURCES.md)

> [4장](../../ch04/code/README.md)에서 6개월짜리 온톨로지가 아무에게도 안 쓰인 이야기를 했습니다. 이 장은 그걸 어떻게 고쳤는지에 대한 겁니다.

그 다섯 문장에서 낱말을 뽑았더니 열 개쯤 나왔습니다. 214개가 아니라요. 나머지 204개는 정확한 분류였지만, 우리가 답하려는 질문에 필요가 없었습니다. 이 장은 그 방법에 대한 겁니다. 위에서 아래로 짓지 말고 질의에서 거꾸로 뽑는 법, 그리고 스키마를 언제 못 박고 언제 풀어 둘지요.

## 이 장의 절

| 절 | 제목 |
|---|---|
| 12.1 | 질의에서 거꾸로 뽑는다 |
| 12.2 | 쪼갤 것인가 속성으로 둘 것인가 |
| 12.3 | 스키마를 언제 못 박을 것인가 |
| 12.4 | 남의 어휘를 가져다 쓸까 |
| 12.5 | 문서 말고 데이터에게 물어보라 |

## 한 장 요약

- 온톨로지는 도메인의 진리가 아니라 지금 우리 질의가 필요로 하는 최소 어휘입니다. 위에서 아래로 지으면 끝나는 조건이 없고, 질의에서 거꾸로 뽑으면 「질의가 돌면 끝」이 됩니다.
- 분류를 나누는 근거는 「다른 물건인가」가 아니라 「다른 속성을 갖는가」입니다. 종류가 많거나 자주 늘면 클래스가 아니라 속성으로 두세요.
- 스키마 없이 시작해도 되는 건 혼자일 때와 버릴 데이터일 때뿐입니다. 그리고 문서만 있고 검사가 없는 게 제일 위험해요. 지키고 있다고 착각하게 됩니다.
- 공개 어휘는 적합도를 숫자로 매겨 판단합니다. 억지로 맞춰 쓰면 예외 조항이 쌓입니다. 우리 것으로 만들고 사상만 걸어 두세요.
- 문서는 거짓말을 하고 데이터는 안 합니다. 드리프트 감사를 배치로 돌리세요. 30줄이면 됩니다.

## 키워드와 1차 출처

| 키워드 | 상태 | 출처 |
|---|---|---|
| SHACL 형태 제약 | [표준] | [Shapes Constraint Language](https://www.w3.org/TR/shacl/) |
| OWL 2 프로필 | [표준] | [OWL 2 Profiles](https://www.w3.org/TR/owl2-profiles/) |
| RDF 스키마 | [표준] | [RDF Schema 1.1](https://www.w3.org/TR/rdf11-schema/) |
| 공용 어휘 | [사실상 표준] | [schema.org](https://schema.org/docs/schemas.html) |
| 개념 체계 어휘 | [표준] | [SKOS](https://www.w3.org/TR/skos-reference/) |
| 역량 질문 | [사실상 표준] | [competency question](https://protege.stanford.edu/publications/ontology_development/ontology101.pdf) |
| 그래프 스키마 선언 | [표준] | [ISO/IEC 39075:2024 GQL](https://www.iso.org/standard/76120.html) |

상태 표시는 **[표준]** 공식 명세, **[사실상 표준]** 명세는 없지만 업계가 널리 쓰는 것, **[실험]** 아직 자리를 잡는 중이라는 뜻입니다.

## 예제 실행

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

확인 시점 2026년 8월. Python 3.9 이상.

```bash
cd content/ch12/code
python3 ex1_vocab_from_questions.py   # 의존성 없음
pip install kuzu "rdflib>=7,<8" pyshacl
python3 ex2_deep_vs_flat.py           # 깊은 분류 vs 얕은 분류
python3 ex3_when_schema.py            # 스키마를 언제 못 박을 것인가
python3 ex4_reuse_or_build.py         # 의존성 없음
python3 ex5_schema_drift.py           # 의존성 없음
```

<!-- 실행 가이드 끝 -->

---

**다음 장에서 뒤집히는 것:** 이 장에서 검증을 두 번 언급했는데, 다음 장이 그 이야기입니다. 검증하지 않은 그래프는 링크 뭉치일 뿐이고, 검증을 추론기로 하려다 3주를 날린 이야기를 제대로 풀어 봅니다.

---

이전 [11장 같은 질문, 세 가지 언어](../../ch11/code/README.md) | [전체 목차](../../../README.md) | 다음 [13장 검증하지 않은 그래프는 그냥 링크 뭉치다](../../ch13/code/README.md)

이 장에서 틀린 곳을 찾으셨다면 [사실 오류로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml), 상태 라벨이 어긋났다면 [라벨 이의로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml) 적어 주세요.
