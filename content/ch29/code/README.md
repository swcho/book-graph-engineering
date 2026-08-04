# 29장 — 하나의 백본

`5부 · 두 그래프가 만나는 곳` · [책 전체 목차](../../../README.md) · [출처 링크 모음](../../../SOURCES.md)

> 「보고서를 팀장님께 보냈습니다.」

5부의 마지막 장입니다. [27장](../../ch27/code/README.md)에서 그래프를 읽었고 [28장](../../ch28/code/README.md)에서 썼는데, 지금까지 둘을 *따로* 다뤘습니다. 이 장에서 합칩니다. 그리고 미리 말씀드리면, 완전히 합치는 건 안 됩니다. 왜 안 되는지, 그럼 어디까지 합치는지가 이 장의 절반이에요.

## 이 장의 절

| 절 | 제목 |
|---|---|
| 29.1 | 따로 두면 갈라진다 |
| 29.2 | 한 그래프에 지식과 실행을 같이 |
| 29.3 | 답에서 출처까지, 그리고 반대로 |
| 29.4 | 합치면 무엇이 나빠지나 |
| 29.5 | 아키텍처를 검사 가능한 형태로 |

## 한 장 요약

- 지식과 실행 상태를 따로 두면 갈라집니다. 그리고 에러 없이 갈라져요. 둘 다 자기 일을 제대로 하는데 결과가 틀립니다.
- 「매번 최신을 읽기」는 답이 아닙니다. 워크플로 안에서 값이 바뀌면 판단이 앞뒤가 안 맞아요. 상태에 담는 건 게으름이 아니라 의도적인 스냅숏입니다.
- 답은 「담아 두되 쓰기 직전에 확인하기」입니다. 그러려면 「읽은 시각」이 붙어 있어야 하고요.
- 한 그래프에 지식과 실행을 두면 *따로 뒀을 때 그릴 곳이 없던 엣지*가 생깁니다. 이 실행이 저 사실을 읽었다는 관계요. 그 엣지가 계보를 만들고, 계보가 두 방향으로 쓰입니다. 「왜 이 답이 나왔나」와 「이게 틀리면 뭐가 무너지나」.
- 다만 완전히 합치면 쓰기 부하가 열 배가 됩니다. 실행 상태 쓰기가 지식 쓰기보다 훨씬 많거든요. 그래서 절충합니다. 상태 본문은 빠른 저장소에, 그래프에는 링크만.
- 그리고 이건 타협이 아니라 옳은 설계인 것 같습니다. 지식과 실행은 수명이 다르니까요. 물을 것은 「무엇을 같은 그래프에 둘까」가 아니라 *「무엇을 엣지로 이어야 하나」*입니다.
- 참조 아키텍처는 그림이 아니라 검사 가능한 형태로 적으세요. 그림은 6개월이면 코드와 갈라집니다.
- 그리고 그 아키텍처를 처음부터 다 만들지 마세요. 아픈 것부터 만들되, *나중에 넣기 어려운 것*만 미리 넣으세요. `Reads` 엣지가 그렇습니다.

## 키워드와 1차 출처

| 키워드 | 상태 | 출처 |
|---|---|---|
| 참조 아키텍처 | [사실상 표준] | [reference architecture](https://learn.microsoft.com/en-us/azure/architecture/guide/) |
| 계보 추적 | [표준] | [data lineage](https://www.w3.org/TR/prov-o/#Derivation) |
| 읽은 시점 기록 | [사실상 표준] | [read timestamp](https://www.postgresql.org/docs/current/transaction-iso.html) |
| 다중 저장소 | [사실상 표준] | [polyglot persistence](https://martinfowler.com/bliki/PolyglotPersistence.html) |
| 경계 컨텍스트 | [사실상 표준] | [bounded context](https://martinfowler.com/bliki/BoundedContext.html) |
| 아키텍처 적합성 함수 | [사실상 표준] | [fitness function](https://www.thoughtworks.com/insights/articles/fitness-function-driven-development) |
| 쓰기 부하 분리 | [사실상 표준] | [write path separation](https://neo4j.com/docs/operations-manual/current/performance/) |

상태 표시는 **[표준]** 공식 명세, **[사실상 표준]** 명세는 없지만 업계가 널리 쓰는 것, **[실험]** 아직 자리를 잡는 중이라는 뜻입니다.

## 예제 실행

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

확인 시점 2026년 8월. Python 3.9 이상.

```bash
cd content/ch29/code
pip install kuzu

python3 ex1_two_stores.py        # 따로 두면 갈라진다
python3 ex2_one_backbone.py      # 한 그래프에 지식과 실행을 같이
python3 ex3_lineage.py           # 답에서 출처까지, 그리고 반대 방향
python3 ex4_split_cost.py        # 합치면 무엇이 나빠지나 (의존성 없음)
python3 ex5_reference_arch.py    # 아키텍처를 검사 가능한 형태로 (의존성 없음)
```

`ex4` 의 지연 값(그래프 쓰기 4.2ms, 키-값 0.35ms)은 21장에서 잰 값을
단순화한 것입니다. 여러분 환경에서는 직접 재서 넣으세요. 비율이 중요하지
절대값이 중요한 게 아닙니다.

`ex5` 는 일부러 규칙 위반을 하나 넣어 뒀습니다. CI 에 넣으면 여기서 실패합니다.

<!-- 실행 가이드 끝 -->

---

**다음 부에서 만나는 것:** 5부가 두 그래프를 합쳤습니다. 그런데 합쳐 놓고 보니 남은 문제들이 전부 같은 얼굴을 하고 있어요. 무엇이 언제 바뀌었나, 둘이 동시에 고치면 어떻게 되나, 구조를 바꿀 때 돌아가는 걸 어떻게 안 깨나. 6부는 그 백본을 «운영»하는 이야기입니다.

---

← [28장 에이전트가 스스로 그래프를 넓히다](../../ch28/code/README.md) · [전체 목차](../../../README.md) · [30장 무엇이 언제 바뀌었는지 아무도 모른다](../../ch30/code/README.md) →

이 장에서 틀린 곳을 찾으셨다면 [사실 오류로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml), 상태 라벨이 어긋났다면 [라벨 이의로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml) 적어 주세요.
