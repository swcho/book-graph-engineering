# 15장 예제 실행 가이드

확인 시점 2026년 8월. Python 3.9 이상. **의존성 없음.**

```bash
cd content/ch15/code
python3 ex1_measure.py       # 정밀도·재현율을 먼저 잰다
python3 ex2_grounding.py     # 근거 검사로 지어내기 거르기
python3 ex3_normalize.py     # 어휘 정규화와 보류함
python3 ex4_confidence.py    # 자기 보고 vs 여러 번 돌려 표 세기
python3 ex5_incremental.py   # 문서가 바뀌면 무엇을 지울까
```

`extractor.py` 는 API 키 없이 돌리려고 만든 **가짜 추출기**입니다.
진짜 모델이 흔히 보이는 실패 네 가지(지어내기·어휘 벗어나기·추측을 사실로·누락)를
그대로 흉내 냅니다.
