# 9장 예제 실행 가이드

확인 시점 2026년 8월. Python 3.9 이상. **의존성 없음.**

```bash
cd content/ch09/code
python3 ex1_bfs_explosion.py        # 홉이 늘 때 방문 노드가 몇 배가 되나
python3 ex2_bidirectional.py        # 양방향 탐색이 75배 줄이는 이유
python3 ex3_dijkstra_negative.py    # 음수 가중치가 조용히 답을 틀리게 만든다
python3 ex4_path_explosion.py       # 최단 경로 하나와 모든 경로는 다른 문제
python3 ex5_toposort.py             # 위상 정렬, 슈퍼스텝, 임계 경로
```

`ex1` 과 `ex2` 는 노드 20만 개를 만듭니다. 메모리 1GB 정도 씁니다.
