# 13장 예제 실행 가이드

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
