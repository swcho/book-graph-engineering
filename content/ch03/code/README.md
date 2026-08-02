# 3장 예제 실행 가이드

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
| `graphdata.py` | 사람 200명·친구 관계 1,163개. 시드 고정이라 매번 같은 그래프 |
| `ex1_euler.py` | 1736년 계산을 20줄로. 다리를 하나 더 놓으면 답이 바뀐다 |
| `ex2_sql_vs_graph.py` | 4홉에서 조인이 순회보다 78배 느려지는 지점 |
| `ex3_recursive_cte.py` | 재귀 CTE 와 순회의 결과가 «달라지는» 이유 |
| `ex4_why_tables_won.py` | 선언적 질의 · 제약 · 트랜잭션 |

측정값은 기계마다 다릅니다. 배수만 보세요.
