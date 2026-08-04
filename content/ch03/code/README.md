# 3장 — 다리 일곱 개를 건널 수 없었던 이유, 그리고 표가 이긴 이유

`1부 — 뿌리: 그래프는 어디에 있었나` | [책 전체 목차](../../../README.md) | [출처 링크 모음](../../../SOURCES.md)

> 새벽 2시에 알림을 받았습니다. 데이터베이스 CPU가 100%에 붙어서 안 떨어진다고요.

이 장은 두 가지를 봅니다. 그래프가 어쩌다 발명됐는지, 그리고 왜 40년 동안 표에 밀렸는지. 두 번째가 더 중요합니다. 표가 이긴 이유를 모르면 그래프로 옮기고도 같은 실수를 반복하거든요.

## 이 장의 절

| 절 | 제목 |
|---|---|
| 3.1 | 땅의 모양을 버리자 답이 나왔다 |
| 3.2 | 그런데 왜 40년 동안 표가 이겼나 |
| 3.3 | 표가 놓친 것 — 깊이가 비용을 정한다 |
| 3.4 | 재귀 CTE — 되긴 되는데 |
| 3.5 | 표준은 양쪽에서 만났다 |

## 한 장 요약

- 오일러는 지도를 버려서 답을 얻었습니다. 남은 건 차수뿐이었고, 홀수 차수가 0개나 2개일 때만 모든 다리를 한 번씩 건널 수 있습니다.
- 표가 40년 이긴 이유는 셋입니다. 선언적 질의, 제약, 트랜잭션. 그래프 엔진을 고를 때 이 셋부터 확인하세요.
- 표가 놓친 건 저장이 아니라 따라가기입니다. 조인은 겹칠 때마다 중간 결과가 곱해지고, 순회는 방문한 만큼만 읽습니다. 측정해 보면 4홉에서 78배 차이가 났습니다.
- 재귀 CTE는 되긴 되는데, 방문 표시를 둘 자리가 없어서 「정확히 k다리」를 틀리게 셉니다. 고칠 수는 있고, 고치면 20줄이 됩니다.

## 키워드와 1차 출처

| 키워드 | 상태 | 출처 |
|---|---|---|
| 쾨니히스베르크 다리 문제 | [표준] | [Seven Bridges of Königsberg](https://scholarlycommons.pacific.edu/euler-works/53/) |
| 차수 | [표준] | [degree](https://scholarlycommons.pacific.edu/euler-works/53/) |
| 관계형 모델 | [표준] | [relational model](https://dl.acm.org/doi/10.1145/362384.362685) |
| 재귀 공통 테이블 식 | [표준] | [recursive CTE](https://www.sqlite.org/lang_with.html) |
| 트랜잭션 | [표준] | [transaction, ACID](https://www.sqlite.org/transactional.html) |
| 속성 그래프 질의 SQL/PGQ | [표준] | [ISO/IEC 9075-16:2023](https://www.iso.org/standard/79473.html) |
| 그래프 질의 언어 GQL | [표준] | [ISO/IEC 39075:2024](https://www.iso.org/standard/76120.html) |

상태 표시는 **[표준]** 공식 명세, **[사실상 표준]** 명세는 없지만 업계가 널리 쓰는 것, **[실험]** 아직 자리를 잡는 중이라는 뜻입니다.

## 예제 실행

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

확인 시점 2026년 8월. Python 3.9 이상. **의존성 없음** (`sqlite3`는 표준 라이브러리).

```bash
cd content/ch03/code
python3 graphdata.py          # 샘플 그래프 통계
python3 ex1_euler.py          # 오일러 판정
python3 ex2_sql_vs_graph.py   # 홉이 늘 때의 비용
python3 ex3_recursive_cte.py  # 재귀 CTE 의 한계
python3 ex4_why_tables_won.py # 표가 이긴 이유
```

| 파일 | 보여 주는 것 |
|---|---|
| `graphdata.py` | 사람 200명, 친구 관계 1,163개. 시드 고정이라 매번 같은 그래프 |
| `ex1_euler.py` | 1736년 계산을 20줄로. 다리를 하나 더 놓으면 답이 바뀐다 |
| `ex2_sql_vs_graph.py` | 4홉에서 조인이 순회보다 78배 느려지는 지점 |
| `ex3_recursive_cte.py` | 재귀 CTE 와 순회의 결과가 «달라지는» 이유 |
| `ex4_why_tables_won.py` | 선언적 질의, 제약, 트랜잭션 |

측정값은 기계마다 다릅니다. 배수만 보세요.

<!-- 실행 가이드 끝 -->

---

**다음 장에서 뒤집히는 것:** 이 장은 "관계를 저장하자"까지 왔습니다. 다음 장은 그 생각을 웹 전체로 밀어붙였던 시도, 시맨틱 웹을 봅니다. 야심은 옳았는데 20년 동안 조롱받았어요. 왜 그랬는지, 그리고 지금 왜 다시 꺼내 쓰는지를 봅니다.

---

이전 [2장 하네스 엔지니어링에서 그래프 엔지니어링으로](../../ch02/code/README.md) | [전체 목차](../../../README.md) | 다음 [4장 시맨틱 웹은 왜 실패한 것처럼 보였나](../../ch04/code/README.md)

이 장에서 틀린 곳을 찾으셨다면 [사실 오류로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml), 상태 라벨이 어긋났다면 [라벨 이의로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml) 적어 주세요.
