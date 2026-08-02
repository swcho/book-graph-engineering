# 23장 예제 실행 가이드

확인 시점 2026년 8월. Python 3.9 이상.

```bash
cd content/ch23/code
pip install "langgraph>=1.0,<2.0"

python3 ex1_interrupt.py     # 멈추고, 답 받고, 이어 가기
python3 ex2_node_reruns.py   # interrupt 앞의 부작용이 두 번 실행된다
python3 ex3_gate_policy.py   # 승인 문턱을 용량으로 정하기 (의존성 없음)
python3 ex4_no_answer.py     # 사람이 답을 안 할 때 (의존성 없음)
python3 ex5_audit.py         # 승인 감사 기록 (의존성 없음)
```

`ex1`, `ex2` 는 메모리 체크포인터를 씁니다. 운영에서는 21장에서 본 대로
디스크에 저장하는 체크포인터를 써야 사람이 사흘 뒤에 답해도 이어집니다.
