# 6장 예제 실행 가이드

확인 시점 2026년 8월. Python 3.9 이상. **의존성 없음.**

```bash
cd content/ch06/code
python3 ex1_rag_limits.py        # 조각 검색으로 전역 질문 시도 → 실패
python3 ex2_graphrag_lite.py     # 색인 시점에 접어 두기 → 성공
python3 ex3_message_passing.py   # GNN 한 층이 하는 일
python3 ex4_link_prediction.py   # 이웃만 세도 되는 예측, 임베딩이 필요해지는 지점
```

| 파일 | 보여 주는 것 |
|---|---|
| `corpus.py` | 장애 회고 12건과 거기서 뽑은 트리플 |
| `ex1_rag_limits.py` | 「전부 몇 건인가」는 top-k 로 못 센다 |
| `ex2_graphrag_lite.py` | 라벨 전파로 커뮤니티를 찾고 요약을 접어 둔다 |
| `ex3_message_passing.py` | 층을 돌 때마다 구조가 값에 녹아든다 |
| `ex4_link_prediction.py` | 되짚을 수 있는 예측과 없는 예측의 갈림길 |

`ex2` 의 요약문은 규칙으로 만듭니다. 진짜 GraphRAG 는 모델이 씁니다.
여기서 보여 주려는 건 요약 품질이 아니라 **언제 접느냐**입니다.
