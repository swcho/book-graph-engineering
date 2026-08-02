# 26장 예제 실행 가이드

확인 시점 2026년 8월. Python 3.9 이상. 외부 의존성 없음.

```bash
cd content/ch26/code
python3 ex1_permission_graph.py   # 권한을 목록이 아니라 도달 경로로
python3 ex2_deny_vs_allow.py      # 금지 목록은 왜 반드시 새는가
python3 ex3_injection.py          # 문서 안에 섞인 명령
python3 ex4_blast_radius.py       # 하나가 뚫렸을 때 어디까지
python3 ex5_audit_trail.py        # 차단 로그가 정책을 고친다
```

`ex3` 은 모델을 부르지 않습니다. 실제 인젝션 성공률을 재려면 모델이 필요한데,
그 실험은 공격 문자열을 책에 싣게 되므로 여기서는 «구조»만 보여 줍니다.
