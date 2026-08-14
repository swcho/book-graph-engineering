# %% [markdown]
# # `is_hedged()` — 창(window) 탐색으로 «단정하지 않는» 표현 찾기
#
# 15장의 근거 검사 3종 중 마지막 검사. LLM이 «~로 알려져 있으나»라는
# 추측 문장을 확정 사실처럼 트리플로 바꿔 놓은 경우를 잡는다.
#
# 핵심 아이디어: **근거 문장(quote) 자체가 아니라, 원문에서 그 문장의
# «주변»을 본다.** 헤지 표현은 quote 바깥(앞뒤)에 붙어 있을 수 있기 때문이다.
#
# 동작 순서:
# 1. 원문에서 `quote[:8]` — 근거 문장의 **앞 8글자** — 의 위치 $i$ 를 찾는다
#    (`text.find`). 8글자면 한국어 문장을 특정하기에 충분하고, LLM이 quote
#    끝부분을 조금 다르게 잘라도 앞머리는 대개 보존되기 때문.
# 2. 위치를 찾았으면 창을 자른다:
#
#    $$\text{window} = \text{text}\big[\max(0,\; i-20) \;:\; i + |\text{quote}| + 40\big]$$
#
#    즉 quote 앞으로 20자, 뒤로 40자를 더 본다.
# 3. 못 찾았으면($i < 0$) 문서 **전체**를 창으로 쓴다 (보수적 fallback).
# 4. 창 안에 헤지 단어(`알려져`, `추정`, `가능성`, ...)가 하나라도 있으면 True.

# %%
HEDGE = ["알려져", "추정", "듯", "로 보인다", "가능성", "일 수 있"]

# 원문(15장 DOCS 축약판)
TEXT = {
    "d01": "가온테크는 2025년 6월 2일 나루소프트와 유지보수 계약을 체결했다. "
           "계약번호는 C-2025-118이며, 담당자는 김하늘 부장이다.",
    "d05": "마루상사는 다올물산의 자회사로 알려져 있으나, 공시된 바는 없다.",
}


def is_hedged(doc_id, quote):
    """원문에서 그 문장 주변에 «단정하지 않는» 표현이 있는가."""
    text = TEXT.get(doc_id, "")
    i = text.find(quote[:8])                                   # ① 앞 8글자로 위치 특정
    window = text[max(0, i - 20): i + len(quote) + 40] if i >= 0 else text  # ② 창 자르기
    return any(h in window for h in HEDGE)                     # ③ 헤지 단어 검사


print(is_hedged("d05", "마루상사는 다올물산의 자회사"))  # 헤지가 quote 뒤에 있음
print(is_hedged("d01", "가온테크는 2025년 6월 2일"))      # 단정 문장
# 출력:
# True
# False

# %% [markdown]
# ## 1단계씩 뜯어보기 — d05 예제
#
# quote 자체에는 헤지 단어가 없다. 그런데도 True가 나오는 이유를 추적한다.

# %%
def trace(doc_id, quote, front=20, back=40):
    text = TEXT.get(doc_id, "")
    key = quote[:8]
    i = text.find(key)
    if i >= 0:
        lo, hi = max(0, i - front), i + len(quote) + back
        window = text[lo:hi]
    else:
        lo, hi, window = 0, len(text), text
    hits = [h for h in HEDGE if h in window]
    print(f"quote[:8]      = {key!r}")
    print(f"find 위치 i    = {i}")
    print(f"창 범위        = [{lo}:{hi}]  (앞 {front}자 + quote {len(quote)}자 + 뒤 {back}자)")
    print(f"창 내용        = {window!r}")
    print(f"quote 안 헤지  = {[h for h in HEDGE if h in quote]}")
    print(f"창 안 헤지     = {hits}  →  is_hedged = {bool(hits)}")


trace("d05", "마루상사는 다올물산의 자회사")
# 출력:
# quote[:8]      = '마루상사는 다올'
# find 위치 i    = 0
# 창 범위        = [0:55]  (앞 20자 + quote 15자 + 뒤 40자)
# 창 내용        = '마루상사는 다올물산의 자회사로 알려져 있으나, 공시된 바는 없다.'
# quote 안 헤지  = []
# 창 안 헤지     = ['알려져']  →  is_hedged = True

# %% [markdown]
# quote(«마루상사는 다올물산의 자회사»)에는 헤지가 없지만, 창이 quote 끝에서
# **뒤로 40자**를 더 덮기 때문에 바로 다음에 오는 «알려져»가 잡힌다.
# LLM이 근거 문장을 헤지 직전에서 잘라 내도 못 빠져나간다는 뜻이다.

# %% [markdown]
# ## 2. 성공/실패 케이스 모음
#
# 창 방식의 특성을 드러내는 인공 문서로 4가지 경우를 본다.
# - 헤지가 quote **앞** 20자 안 → 잡힘
# - 헤지가 quote **뒤** 40자 안 → 잡힘
# - 헤지가 창 **밖** (멀리) → 놓침 (한계)
# - quote 앞 8글자가 원문에 **없음** → 문서 전체를 창으로 → 잡힘 (보수적)

# %%
TEXT["t_front"] = "업계에서는 추정만 무성하다. 한빛제약이 해외 공장을 짓는다. 세부 계획은 미정이다."
TEXT["t_back"]  = "한빛제약이 해외 공장을 짓는다. 다만 완공 시점은 지연될 가능성이 있다."
TEXT["t_far"]   = ("한빛제약이 해외 공장을 짓는다. " + "무관한 재무 지표 설명이 길게 이어진다. " * 2
                   + "이는 어디까지나 추정이다.")

quote = "한빛제약이 해외 공장을 짓는다"
cases = [
    ("t_front", quote,        "헤지 '추정'이 quote 앞 10자 지점"),
    ("t_back",  quote,        "헤지 '가능성'이 quote 뒤 16자 지점"),
    ("t_far",   quote,        "헤지 '추정'이 quote 뒤 57자 지점 → 창(뒤 40자) 밖"),
    ("t_front", "존재하지 않는 근거문장", "find 실패(i<0) → 문서 전체 검사"),
]
for did, q, desc in cases:
    print(f"{str(is_hedged(did, q)):<5}  {desc}")
# 출력:
# True   헤지 '추정'이 quote 앞 10자 지점
# True   헤지 '가능성'이 quote 뒤 16자 지점
# False  헤지 '추정'이 quote 뒤 57자 지점 → 창(뒤 40자) 밖
# True   find 실패(i<0) → 문서 전체 검사

# %% [markdown]
# 세 번째 케이스가 이 방식의 **한계**다: 헤지가 창(뒤 40자) 밖에 있으면 놓친다.
# 네 번째는 반대로 **보수적 설계**다: quote 위치를 못 찾으면 문서 전체를 뒤져서
# 라도 헤지를 찾는다 — 놓치는 쪽(추측을 사실로 확정)이 더 위험하기 때문.

# %% [markdown]
# ## 3. 창 크기가 결과를 가른다
#
# 뒤쪽 여유(back margin)를 0~80자로 바꿔 가며, 헤지까지의 거리가 다른
# 세 문서에서 탐지 여부가 어떻게 변하는지 본다.

# %%
def is_hedged_sized(doc_id, quote, front, back):
    text = TEXT.get(doc_id, "")
    i = text.find(quote[:8])
    window = text[max(0, i - front): i + len(quote) + back] if i >= 0 else text
    return any(h in window for h in HEDGE)


docs = [("d05", "헤지가 quote 뒤 +2자"),
        ("t_back", "헤지가 quote 뒤 +16자"),
        ("t_far", "헤지가 quote 뒤 +57자")]
backs = [0, 10, 20, 30, 40, 60, 80]

print(f"{'뒤 여유(back)':>12} | " + " | ".join(f"{d:^22}" for _, d in docs))
print("-" * 92)
for b in backs:
    row = " | ".join(f"{str(is_hedged_sized(did, quote if did != 'd05' else '마루상사는 다올물산의 자회사', 20, b)):^22}"
                     for did, _ in docs)
    mark = " ← 기본값" if b == 40 else ""
    print(f"{b:>12} | {row}{mark}")
# 출력:
#  뒤 여유(back) |    헤지가 quote 뒤 +2자    |   헤지가 quote 뒤 +16자    |   헤지가 quote 뒤 +57자
# --------------------------------------------------------------------------------------------
#            0 |         False          |         False          |         False
#           10 |          True          |         False          |         False
#           20 |          True          |          True          |         False
#           30 |          True          |          True          |         False
#           40 |          True          |          True          |         False           ← 기본값
#           60 |          True          |          True          |          True
#           80 |          True          |          True          |          True
#
# (t_back의 '가능성'은 quote 끝에서 16자 뒤라 back=20(16+단어길이 3≤20)부터 잡히고,
#  t_far의 '추정'은 57자 뒤라 back=60에서야 잡힌다. back=40 기본값은 t_far를 놓친다)

# %% [markdown]
# 창이 좁으면(back=0) quote 바깥의 헤지를 전부 놓치고, 창이 넓으면 멀리 있는
# **무관한 문장의 헤지까지** 끌어와 멀쩡한 트리플을 버리게 된다(정밀도↔재현율
# 트레이드오프의 축소판). 기본값 «앞 20 / 뒤 40»은 "같은 문장 또는 바로 이어지는
# 절 안의 헤지"를 노린 절충이다.
#
# ## 정리
#
# - **위치 특정**: `text.find(quote[:8])` — 근거 문장의 앞 8글자를 앵커로 쓴다.
# - **창 구성**: `text[max(0, i-20) : i+len(quote)+40]` — 앞 20자 + quote + 뒤 40자.
# - **fallback**: 앵커를 못 찾으면 문서 전체가 창 (보수적).
# - **판정**: 창 안에 `알려져/추정/듯/로 보인다/가능성/일 수 있` 중 하나라도 있으면 헤지.
# - 모델 호출 없는 순수 문자열 검사라 밀리초 단위, 결정적(항상 같은 결과).
