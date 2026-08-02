# 1장 예제 실행 가이드

확인 시점 2026년 8월. Python 3.9 이상.

```bash
cd content/ch01/code

# 예제 1, 2 — 의존성 없음
python3 ex1_vector_only.py
python3 ex2_graph_grounded.py

# 예제 3 — LangGraph 필요 (API 키는 필요 없다)
pip install "langgraph>=1.0,<2.0"
python3 ex3_agent_loop.py
```

| 파일 | 무엇을 보여 주나 | 기대 결과 |
|---|---|---|
| `notes.py` | 같은 사실을 문장 8줄과 트리플 7개로 두 번 적은 샘플 데이터 | — |
| `ex1_vector_only.py` | 벡터 검색만으로 2홉 질문에 답하려는 시도 | 오답. 라온에너지가 딸려 나온다 |
| `ex2_graph_grounded.py` | 같은 질문을 그래프 경로로 | 정답. 근거 경로가 함께 출력된다 |
| `ex3_agent_loop.py` | 종료 조건과 체크포인트가 있는 상태 그래프 루프 | 정답. 재시도 1회 뒤 종료, 체크포인트 8개 |

`ex1`이 틀리는 건 임베딩 모델이 작아서가 아니다. 관계를 저장하지 않았기 때문이다.
모델을 바꿔도 결과는 같다. 직접 바꿔 보고 확인하기를 권한다.
