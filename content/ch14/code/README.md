# 14장 — 같은 사람이 노드 네 개로 앉아 있다

`3부 · 지식 그래프 엔지니어링 (트랙 1)` · [책 전체 목차](../../../README.md) · [출처 링크 모음](../../../SOURCES.md)

> 「가온테크」와 「가온테크(주)」를 자동으로 합치게 했습니다. 사업자번호도 주소도 대표자도 같았거든요.

이 장은 그 사흘에서 배운 것들입니다. 어떻게 후보를 찾고, 어떻게 점수를 매기고, 언제 사람에게 묻고, 그리고 틀렸을 때 어떻게 되돌릴지요. 마지막이 제일 중요합니다.

## 이 장의 절

| 절 | 제목 |
|---|---|
| 14.1 | 전부 비교할 수는 없다 |
| 14.2 | 점수를 매기고, 두 개의 임계를 둔다 |
| 14.3 | 되돌릴 수 있게 병합하라 |
| 14.4 | 임계를 어디에 둘 것인가 |
| 14.5 | 어느 값을 남길 것인가 |

## 한 장 요약

- 전부 비교할 수는 없어서 블로킹으로 후보를 좁힙니다. 성패는 재현율이에요. 후보에 못 들면 영영 못 만나니, 전략을 서너 개 돌리고 합집합을 쓰세요.
- 임계는 두 개 둡니다. 위는 자동, 아래는 무시, 사이는 사람에게. 자동화가 할 일은 다 맞히는 게 아니라 애매한 것을 골라내는 겁니다.
- 원본을 지우지 마세요. 대표 노드를 가리키게만 하면 되돌리기가 포인터 하나 고치는 일이 됩니다. 되돌릴 수 있으면 훨씬 공격적으로 자동화할 수 있고요.
- 점수 위에 「절대 안 되는」 거부권 규칙을 두세요. 사업자번호가 다르면 다른 법인입니다. 다른 게 아무리 같아도요.
- 생존 규칙은 필드마다 다르게 정합니다. 그리고 빈 값과 자리표시자는 절대 이기지 못하게 하세요. 한 줄인데 사고의 절반을 막습니다.

## 키워드와 1차 출처

| 키워드 | 상태 | 출처 |
|---|---|---|
| 엔티티 해상도 | [사실상 표준] | [entity resolution](https://www.vldb.org/pvldb/vol11/p1454-mudgal.pdf) |
| 블로킹 | [사실상 표준] | [blocking](https://dl.acm.org/doi/10.1145/3355491.3355496) |
| 확률적 레코드 연결 | [사실상 표준] | [Fellegi-Sunter model](https://www.tandfonline.com/doi/abs/10.1080/01621459.1969.10501049) |
| 동일성 선언 | [표준] | [owl:sameAs](https://www.w3.org/TR/owl2-syntax/#Individual_Equality) |
| 느슨한 동일성 | [표준] | [skos:closeMatch](https://www.w3.org/TR/skos-reference/#mapping) |
| 생존 규칙 | [실험] | [survivorship rules](https://www.iso.org/standard/35736.html) |
| 출처 추적 | [표준] | [PROV-O](https://www.w3.org/TR/prov-o/) |

상태 표시는 **[표준]** 공식 명세, **[사실상 표준]** 명세는 없지만 업계가 널리 쓰는 것, **[실험]** 아직 자리를 잡는 중이라는 뜻입니다.

## 예제 실행

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

확인 시점 2026년 8월. Python 3.9 이상. **의존성 없음.**

```bash
cd content/ch14/code
python3 ex1_blocking.py           # 전수 비교 대신 블로킹, 그리고 놓치는 것
python3 ex2_scoring.py            # 점수·임계·이행성, 그리고 사람 판정
python3 ex3_reversible_merge.py   # 되돌릴 수 있는 병합
python3 ex4_threshold_tuning.py   # 임계 하나가 바꾸는 것
python3 ex5_survivorship.py       # 어느 값을 남길 것인가
```

<!-- 실행 가이드 끝 -->

---

**다음 장에서 뒤집히는 것:** 지금까지는 데이터가 이미 있다고 가정했습니다. 다음 장은 문서에서 트리플을 뽑아내는 이야기예요. 1만 건에서 뽑았더니 절반이 거짓이었던 경험부터 시작합니다.

---

← [13장 검증하지 않은 그래프는 그냥 링크 뭉치다](../../ch13/code/README.md) · [전체 목차](../../../README.md) · [15장 문서 1만 건에서 트리플을 뽑았더니 절반이 거짓이었다](../../ch15/code/README.md) →

이 장에서 틀린 곳을 찾으셨다면 [사실 오류로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml), 상태 라벨이 어긋났다면 [라벨 이의로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml) 적어 주세요.
