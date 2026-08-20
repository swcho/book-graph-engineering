# `ex1_lost_update.py`의 두 상태 타입은 어떻게 다른가?

`NoReducer`는 `logs: list`, `count: int`로 리듀서가 없고, `WithReducer`는
`Annotated[list, operator.add]`, `Annotated[int, operator.add]`로 리듀서를 붙였다.

## 시각화

![expy 시각화](expy.png)
