# %% [markdown]
# # `build_matrix()` — 인접 행렬을 비트맵으로 압축해 담기
#
# 8장 `ex1_three_forms.py`의 `build_matrix()`는 인접 행렬을 **행마다 비트맵 한 줄**로 만들어
# 하나의 평평한 `bytearray`에 담는다.
#
# - 한 행의 크기: $\lceil n/8 \rceil$ 바이트 = 파이썬 정수 연산으로 `(n + 7) // 8`
# - 전체 크기: `row_bytes * n` 바이트 (`bytearray` 하나, 중첩 없음)
# - 원소 $(a, b)$의 자리: **바이트는 `b >> 3`, 비트는 `1 << (b & 7)`**
#
# $$\text{addr}(a,b) = a \cdot \texttt{row\_bytes} + \left\lfloor \frac{b}{8} \right\rfloor,
# \qquad \text{mask}(b) = 2^{\,b \bmod 8}$$
#
# 필요 패키지: plotly, kaleido (마지막 시각화 셀에서만 사용. 없으면 그 셀만 건너뛴다)

# %%
import sys


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


# 아주 작은 무향 그래프. 노드 0~9, 노드 9는 일부러 고립시킨다.
N = 10
EDGES = [(0, 1), (0, 2), (1, 3), (2, 3), (3, 8), (4, 5), (5, 6), (6, 7)]
print("노드 수 n =", N)
print("엣지     =", EDGES)
# 출력: 노드 수 n = 10
# 출력: 엣지     = [(0, 1), (0, 2), (1, 3), (2, 3), (3, 8), (4, 5), (5, 6), (6, 7)]

# %% [markdown]
# ## 1단계 — 왜 `(n + 7) // 8`인가
#
# 한 행에는 비트가 $n$개 필요하다. 그런데 메모리는 **바이트 단위**로만 살 수 있다.
# 그래서 8로 나눈 뒤 **올림**해야 한다.
#
# $$\texttt{(n + 7) // 8} \;=\; \left\lceil \frac{n}{8} \right\rceil$$
#
# `+7`은 「나머지가 1이라도 있으면 한 칸 더」를 정수 나눗셈만으로 표현하는 관용구다.
# 부동소수점(`math.ceil(n/8)`)을 쓰지 않아 큰 $n$에서도 오차가 없다.

# %%
import math

print(f"{'n':>4} {'(n+7)//8':>10} {'ceil(n/8)':>10} {'n//8':>6} {'낭비 비트':>9}")
for n in (1, 7, 8, 9, 15, 16, 17, 63, 64, 10_000):
    row_bytes = (n + 7) // 8
    print(f"{n:>4} {row_bytes:>10} {math.ceil(n / 8):>10} {n // 8:>6} {row_bytes * 8 - n:>9}")
# 출력:    n   (n+7)//8  ceil(n/8)   n//8     낭비 비트
# 출력:    1          1          1      0         7
# 출력:    7          1          1      0         1
# 출력:    8          1          1      1         0
# 출력:    9          2          2      1         7
# 출력:   15          2          2      1         1
# 출력:   16          2          2      2         0
# 출력:   17          3          3      2         7
# 출력:   63          8          8      7         1
# 출력:   64          8          8      8         0
# 출력: 10000       1250       1250   1250         0
# (n//8 은 내림이라 9→1, 15→1, 63→7 로 틀린다. 반드시 올림이어야 한다.)

# %%
# n // 8 은 틀린다(내림). 큰 n 에서 float 은 정밀도가 무너진다.
big = 2**53 + 1
print("(n+7)//8  =", (big + 7) // 8)
print("ceil(n/8) =", math.ceil(big / 8), "  ← float 로 반올림되어 어긋난다")
print("일치?     =", (big + 7) // 8 == math.ceil(big / 8))
# 출력: (n+7)//8  = 1125899906842625
# 출력: ceil(n/8) = 1125899906842624   ← float 로 반올림되어 어긋난다
# 출력: 일치?     = False

# %% [markdown]
# ## 2단계 — 비트 주소 계산: `b >> 3` 과 `b & 7`
#
# 비트 번호 $b$를 (바이트 번호, 바이트 안의 비트 번호)로 쪼개는 일은 그냥 **8로 나눈 몫과 나머지**다.
# 8은 $2^3$이므로 나눗셈 대신 시프트/마스크로 쓴다.
#
# $$b \gg 3 = \left\lfloor \frac{b}{8} \right\rfloor, \qquad b \,\&\, 7 = b \bmod 8$$
#
# `7 = 0b111`이라 하위 3비트만 남기고, `>> 3`은 그 하위 3비트를 버린다.
# 두 연산이 $b$의 비트를 **겹치지 않게 정확히 나눠 갖는다**.

# %%
print(f"{'b':>3} {'2진수':>10} {'b>>3':>5} {'b&7':>4} {'divmod(b,8)':>13} {'1<<(b&7)':>9} {'마스크':>10}")
for b in (0, 1, 5, 7, 8, 9, 15, 16, 23, 42):
    print(
        f"{b:>3} {bin(b):>10} {b >> 3:>5} {b & 7:>4} {str(divmod(b, 8)):>13} "
        f"{1 << (b & 7):>9} {format(1 << (b & 7), '08b'):>10}"
    )
# 출력:   b        2진수  b>>3  b&7   divmod(b,8)  1<<(b&7)        마스크
# 출력:   0        0b0     0    0        (0, 0)         1   00000001
# 출력:   1        0b1     0    1        (0, 1)         2   00000010
# 출력:   5      0b101     0    5        (0, 5)        32   00100000
# 출력:   7      0b111     0    7        (0, 7)       128   10000000
# 출력:   8     0b1000     1    0        (1, 0)         1   00000001
# 출력:   9     0b1001     1    1        (1, 1)         2   00000010
# 출력:  15     0b1111     1    7        (1, 7)       128   10000000
# 출력:  16    0b10000     2    0        (2, 0)         1   00000001
# 출력:  23    0b10111     2    7        (2, 7)       128   10000000
# 출력:  42   0b101010     5    2        (5, 2)         4   00000100

# %%
# 항등식 확인: 모든 b 에 대해 (b>>3, b&7) == divmod(b, 8)
ok = all((b >> 3, b & 7) == divmod(b, 8) for b in range(100_000))
# 그리고 b = 8*(b>>3) + (b&7) 로 되돌릴 수 있다 (정보 손실 없음)
back = all(8 * (b >> 3) + (b & 7) == b for b in range(100_000))
print("(b>>3, b&7) == divmod(b, 8) :", ok)
print("8*(b>>3) + (b&7) == b       :", back)
# 출력: (b>>3, b&7) == divmod(b, 8) : True
# 출력: 8*(b>>3) + (b&7) == b       : True

# %% [markdown]
# ## 3단계 — set / test / clear
#
# 비트 하나를 다루는 세 가지 연산. 마스크 $m = 2^{b \bmod 8}$ 를 만들어 놓고,
#
# | 하는 일 | 연산 | 뜻 |
# |---|---|---|
# | **set** (엣지 추가) | `buf[i] \|= m` | 그 비트만 1로 |
# | **test** (엣지 확인) | `bool(buf[i] & m)` | 그 비트만 남기고 본다 |
# | **clear** (엣지 삭제) | `buf[i] &= ~m & 0xFF` | 그 비트만 0으로 |
#
# `|=`(OR)는 **멱등(idempotent)**이다. 같은 엣지를 두 번 넣어도 결과가 같다.
# 그래서 `build_matrix()`는 중복 엣지를 따로 걸러내지 않는다.

# %%
def bit_addr(a, b, row_bytes):
    """(행 a, 열 b) → (바이트 인덱스, 비트 마스크)"""
    return a * row_bytes + (b >> 3), 1 << (b & 7)


def bit_set(m, a, b, row_bytes):
    i, mask = bit_addr(a, b, row_bytes)
    m[i] |= mask


def bit_test(m, a, b, row_bytes):
    i, mask = bit_addr(a, b, row_bytes)
    return bool(m[i] & mask)


def bit_clear(m, a, b, row_bytes):
    i, mask = bit_addr(a, b, row_bytes)
    m[i] &= ~mask & 0xFF  # 파이썬 int 는 무한 비트라 0xFF 로 잘라 준다


ROW_BYTES = (N + 7) // 8
probe = bytearray(ROW_BYTES * N)
print("row_bytes =", ROW_BYTES, " 전체 =", len(probe), "바이트")
print("초기 (3,8)  :", bit_test(probe, 3, 8, ROW_BYTES))
bit_set(probe, 3, 8, ROW_BYTES)
print("set 후      :", bit_test(probe, 3, 8, ROW_BYTES))
bit_set(probe, 3, 8, ROW_BYTES)  # 두 번 넣어도 같다 (멱등)
print("두 번 set 후:", bit_test(probe, 3, 8, ROW_BYTES), " 행 3 바이트 =", list(probe[3 * ROW_BYTES : 4 * ROW_BYTES]))
bit_clear(probe, 3, 8, ROW_BYTES)
print("clear 후    :", bit_test(probe, 3, 8, ROW_BYTES), " 행 3 바이트 =", list(probe[3 * ROW_BYTES : 4 * ROW_BYTES]))
# 출력: row_bytes = 2  전체 = 20 바이트
# 출력: 초기 (3,8)  : False
# 출력: set 후      : True
# 출력: 두 번 set 후: True  행 3 바이트 = [0, 1]
# 출력: clear 후    : False  행 3 바이트 = [0, 0]

# %% [markdown]
# ## 4단계 — 원본 `build_matrix()` 그대로
#
# 무향 그래프이므로 **대칭 두 곳**을 함께 켠다. `(a,b)`와 `(b,a)`.

# %%
def build_matrix(edges, n):
    """인접 행렬. n×n 비트. 여기서는 bytearray 한 줄에 n비트씩."""
    row_bytes = (n + 7) // 8
    m = bytearray(row_bytes * n)
    for a, b in edges:
        m[a * row_bytes + (b >> 3)] |= 1 << (b & 7)
        m[b * row_bytes + (a >> 3)] |= 1 << (a & 7)
    return m


M = build_matrix(EDGES, N)
print("bytearray 길이 =", len(M), "( = row_bytes * n =", ROW_BYTES, "*", N, ")")
print("바이트 값      =", list(M))
print("hex            =", M.hex(" "))
# 출력: bytearray 길이 = 20 ( = row_bytes * n = 2 * 10 )
# 출력: 바이트 값      = [6, 0, 9, 0, 9, 0, 6, 1, 32, 0, 80, 0, 160, 0, 64, 0, 8, 0, 0, 0]
# 출력: hex            = 06 00 09 00 09 00 06 01 20 00 50 00 a0 00 40 00 08 00 00 00

# %%
# 행을 비트 문자열로 펼쳐 본다. 열 b 는 왼쪽부터 0,1,2,... 순서.
def row_bits(m, a, n, row_bytes):
    return "".join("1" if bit_test(m, a, b, row_bytes) else "." for b in range(n))


print("     열: 0123456789")
for a in range(N):
    print(f"행 {a}   : {row_bits(M, a, N, ROW_BYTES)}   바이트={list(M[a * ROW_BYTES : (a + 1) * ROW_BYTES])}")
# 출력:      열: 0123456789
# 출력: 행 0   : .11.......   바이트=[6, 0]
# 출력: 행 1   : 1..1......   바이트=[9, 0]
# 출력: 행 2   : 1..1......   바이트=[9, 0]
# 출력: 행 3   : .11.....1.   바이트=[6, 1]
# 출력: 행 4   : .....1....   바이트=[32, 0]
# 출력: 행 5   : ....1.1...   바이트=[80, 0]
# 출력: 행 6   : .....1.1..   바이트=[160, 0]
# 출력: 행 7   : ......1...   바이트=[64, 0]
# 출력: 행 8   : ...1......   바이트=[8, 0]
# 출력: 행 9   : ..........   바이트=[0, 0]

# %% [markdown]
# ### 함정 — 비트 순서는 사람이 읽는 순서와 반대다
#
# `1 << (b & 7)`은 열 $b$를 **하위 비트(LSB)부터** 채운다. 그래서 `format(byte, '08b')`로
# 찍으면(MSB 먼저) 열 순서가 뒤집혀 보인다. 행 0의 이웃이 열 1,2인데 바이트 값은 `6 = 0b00000110`이다.

# %%
b0 = M[0]
print("행 0 첫 바이트 =", b0, "=", format(b0, "08b"), "(MSB 먼저: 사람이 읽는 관습)")
print("열 순서(b=0..7):", "".join("1" if b0 >> b & 1 else "." for b in range(8)), "(LSB 먼저: 코드가 쓰는 순서)")
print("format 문자열  :", format(b0, "08b"), "→ 뒤집으면", format(b0, "08b")[::-1])
# 출력: 행 0 첫 바이트 = 6 = 00000110 (MSB 먼저: 사람이 읽는 관습)
# 출력: 열 순서(b=0..7): .11..... (LSB 먼저: 코드가 쓰는 순서)
# 출력: format 문자열  : 00000110 → 뒤집으면 01100000

# %%
# 대칭성 확인: 무향이므로 M[a][b] == M[b][a] 여야 한다.
sym = all(bit_test(M, a, b, ROW_BYTES) == bit_test(M, b, a, ROW_BYTES) for a in range(N) for b in range(N))
ones = sum(bin(byte).count("1") for byte in M)
print("대칭?          =", sym)
print("켜진 비트 수   =", ones, "( = 2E =", 2 * len(EDGES), ")")
print("낭비 비트 수   =", ROW_BYTES * 8 * N - N * N, "(패딩: 행마다", ROW_BYTES * 8 - N, "비트)")
# 출력: 대칭?          = True
# 출력: 켜진 비트 수   = 16 ( = 2E = 16 )
# 출력: 낭비 비트 수   = 60 (패딩: 행마다 6 비트)

# %% [markdown]
# ## 5단계 — 8배를 아끼지만 $n^2$은 못 벗어난다
#
# 비트맵은 「원소당 1바이트」 방식보다 (패딩을 빼면) **8배** 작다. 그런데 여전히 $\Theta(n^2)$다.
#
# $$\text{bits} = n \cdot \left\lceil \frac{n}{8} \right\rceil \text{ bytes} \approx \frac{n^2}{8},
# \qquad \text{CSR} = 4(n+1) + 8E$$
#
# 그리고 **엣지가 몇 개든 크기가 같다**. 이게 인접 행렬의 본질이다.

# %%
def bit_bytes(n):
    return ((n + 7) // 8) * n  # build_matrix 가 실제로 잡는 크기


def byte_bytes(n):
    return n * n  # 원소당 1바이트 (bytearray(n*n)) 또는 numpy bool


def csr_bytes(n, avg_deg=12):
    e = n * avg_deg // 2
    return 4 * (n + 1) + 4 * 2 * e  # 32비트 정수 배열 두 개


print(f"{'n':>9} {'비트 행렬':>14} {'바이트 행렬':>14} {'CSR(deg12)':>13} {'비트/CSR':>10}")
for n in (10, 100, 416, 1_000, 20_000, 1_000_000):
    b, y, c = bit_bytes(n), byte_bytes(n), csr_bytes(n)
    print(f"{n:>9,} {b:>14,} {y:>14,} {c:>13,} {b / c:>9.2f}x")
# 출력:         n          비트 행렬         바이트 행렬    CSR(deg12)     비트/CSR
# 출력:        10             20            100           524      0.04x
# 출력:       100          1,300         10,000         5,204      0.25x
# 출력:       416         21,632        173,056        21,636      1.00x
# 출력:     1,000        125,000      1,000,000        52,004      2.40x
# 출력:    20,000     50,000,000    400,000,000     1,040,004     48.08x
# 출력: 1,000,000 125,000,000,000 1,000,000,000,000    52,000,004   2403.85x

# %%
# 실제 bytearray 로 확인 (책의 N=20,000 과 같은 규모는 50MB 라서 여기선 2,000 으로)
n = 2_000
real = build_matrix([(0, 1), (5, 1999)], n)
print("sys.getsizeof(bytearray) =", f"{sys.getsizeof(real):,}", "바이트")
print("공식 ((n+7)//8)*n        =", f"{bit_bytes(n):,}", "바이트 (+ 객체 헤더)")
print("엣지 2개짜리인데 크기는  =", f"{bit_bytes(n) / 1024:.0f} KB — 엣지 수와 무관하다")
# 출력: sys.getsizeof(bytearray) = 500,057 바이트
# 출력: 공식 ((n+7)//8)*n        = 500,000 바이트 (+ 객체 헤더)
# 출력: 엣지 2개짜리인데 크기는  = 488 KB — 엣지 수와 무관하다

# %%
# 손익 분기점: 평균 차수 12 에서 비트 행렬이 CSR 보다 커지는 n
cross = next(n for n in range(1, 5_000) if bit_bytes(n) > csr_bytes(n))
print("평균 차수 12 기준 분기점 n ≈", cross)
print("→ 노드 수가", cross, "을 넘으면 비트 행렬이 CSR 보다 커진다. 8.1절의 «수천 개 이하»가 이 이야기.")
# 출력: 평균 차수 12 기준 분기점 n ≈ 417
# 출력: → 노드 수가 417 을 넘으면 비트 행렬이 CSR 보다 커진다. 8.1절의 «수천 개 이하»가 이 이야기.

# %% [markdown]
# ## 6단계 — 그림으로
#
# 왼쪽: 작은 그래프의 비트맵. 점선이 **바이트 경계**($\lceil n/8 \rceil = 2$ 바이트/행)이고
# 오른쪽 회색 띠가 패딩(낭비 비트)이다.
# 오른쪽: $n$이 커질 때의 메모리. 비트 행렬은 기울기 2(즉 $n^2$)라서 CSR(기울기 1)을 반드시 추월한다.

# %%
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    total_cols = ROW_BYTES * 8  # 패딩까지 포함한 실제 비트 폭
    grid = [[bit_test(M, a, b, ROW_BYTES) * 1 if b < N else -1 for b in range(total_cols)] for a in range(N)]
    text = [["1" if v == 1 else ("" if v == 0 else "·") for v in row] for row in grid]

    fig = make_subplots(
        rows=1,
        cols=2,
        column_widths=[0.46, 0.54],
        subplot_titles=(
            f"bytearray 배치 (n={N}, row_bytes=(n+7)//8={ROW_BYTES})",
            "메모리 규모 (평균 차수 12)",
        ),
    )

    fig.add_trace(
        go.Heatmap(
            z=grid,
            text=text,
            texttemplate="%{text}",
            colorscale=[[0.0, "#d9d9d9"], [0.5, "#f7f7f7"], [1.0, "#2b6cb0"]],
            zmin=-1,
            zmax=1,
            showscale=False,
            xgap=1,
            ygap=1,
            hovertemplate="행 a=%{y}, 열 b=%{x}<br>바이트 b>>3=%{customdata[0]}, 마스크 1<<(b&7)=%{customdata[1]}<extra></extra>",
            customdata=[[[b >> 3, 1 << (b & 7)] for b in range(total_cols)] for _ in range(N)],
        ),
        row=1,
        col=1,
    )
    for k in range(1, ROW_BYTES):
        fig.add_vline(x=k * 8 - 0.5, line=dict(color="#e53e3e", width=2, dash="dot"), row=1, col=1)
    fig.add_vline(x=N - 0.5, line=dict(color="#718096", width=2), row=1, col=1)

    ns = [2**k for k in range(3, 21)]
    for name, fn, color in (
        ("비트 행렬 ((n+7)//8 × n)", bit_bytes, "#2b6cb0"),
        ("바이트 행렬 (n × n)", byte_bytes, "#dd6b20"),
        ("CSR (4(n+1) + 8E)", csr_bytes, "#38a169"),
    ):
        fig.add_trace(
            go.Scatter(
                x=ns,
                y=[fn(n) for n in ns],
                mode="lines+markers",
                name=name,
                line=dict(color=color, width=2.5),
                marker=dict(size=5),
            ),
            row=1,
            col=2,
        )
    fig.add_vline(x=cross, line=dict(color="#718096", width=1.5, dash="dash"), row=1, col=2)
    fig.add_annotation(
        x=math.log10(cross), y=math.log10(csr_bytes(cross)), xref="x2", yref="y2",
        text=f"분기점 n≈{cross}", showarrow=True, arrowhead=2, ax=50, ay=-40,
    )

    fig.update_yaxes(autorange="reversed", title_text="행 a", dtick=1, row=1, col=1)
    fig.update_xaxes(title_text="열 b (점선 = 바이트 경계, 회색 = 패딩)", dtick=1, row=1, col=1)
    fig.update_xaxes(type="log", title_text="노드 수 n", row=1, col=2)
    fig.update_yaxes(type="log", title_text="바이트", row=1, col=2)
    fig.update_layout(
        title_text="build_matrix(): 행 = (n+7)//8 바이트 비트맵, 주소 = b>>3 / 1<<(b&7)",
        template="plotly_white",
        width=1280,
        height=560,
        legend=dict(orientation="h", y=-0.22, x=0.55),
    )

    _show(fig)
    fig.write_image("expy.png", scale=2)
    print("expy.png 저장 완료")
except ImportError as e:  # 필요 패키지: plotly, kaleido
    print("시각화 생략 (필요 패키지: plotly, kaleido):", e)
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# 1. 행 하나 = `(n + 7) // 8` 바이트 = $\lceil n/8 \rceil$. `+7`이 올림 관용구다.
# 2. 전체는 `bytearray(row_bytes * n)` **하나**. 2차원 리스트가 아니라 평평한 1차원이다.
# 3. 원소 $(a,b)$의 바이트는 `a * row_bytes + (b >> 3)`, 비트 마스크는 `1 << (b & 7)`.
# 4. `>> 3`과 `& 7`은 각각 8로 나눈 **몫**과 **나머지**다 ($8 = 2^3$).
# 5. set은 `|=`(멱등), test는 `& mask`, clear는 `&= ~mask & 0xFF`.
# 6. 8배를 아껴도 $\Theta(n^2)$는 그대로다. 평균 차수 12라면 노드 수 400여 개에서 이미 CSR에 진다.
