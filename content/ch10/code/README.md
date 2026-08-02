# 10장 예제 실행 가이드

확인 시점 2026년 8월. Python 3.9 이상. **의존성 없음.**

```bash
cd content/ch10/code
python3 ex1_centralities.py       # 네 가지 중심성, 1등이 서로 다르다
python3 ex2_pagerank.py           # 싱크 노드가 점수를 삼킨다
python3 ex3_betweenness_cost.py   # 매개 중심성의 비용과 근사
python3 ex4_communities.py        # 라벨 전파 vs 모듈러리티
python3 ex5_resolution.py         # 해상도 한계
```

`ex3` 은 노드 1,600개까지 전수 계산을 하므로 10초쯤 걸립니다.
