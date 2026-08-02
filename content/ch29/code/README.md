# 29장 예제 실행 가이드

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
