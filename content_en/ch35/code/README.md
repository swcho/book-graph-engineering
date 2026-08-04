# Chapter 35 — Five Claims Most Likely to Be Wrong in Three Years

`Part 8 — What Comes Next` | **English** | [한국어](../../../content/ch35/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> I decided one thing before I started writing this book: *in the last chapter, point at the places where I am wrong.*

And that is how it went. The list in this chapter was not assembled at the end, it *accumulated as I wrote*.

## Sections

| # | Title |
|---|---|
| 35.1 | Putting a claim in falsifiable form |
| 35.2 | 1. Model calls take 90% |
| 35.3 | 2. Injection cannot be stopped at the prompt layer |
| 35.4 | 3. Automatic expansion needs gates |
| 35.5 | 4. Knowledge and execution belong apart |
| 35.6 | 5. This term sticks |
| 35.7 | Where have the standards got to |
| 35.8 | What you should measure again |
| 35.9 | What this book could not answer |

## The chapter in one page

- On the five core claims of this book, my average confidence is 46%.
- The one I expect to break first is "model calls take more than 90% of response time." Models are getting faster. The one I expect to last longest is "automatic expansion needs gates," because one of the gates has nothing to do with accuracy.
- Something you cannot write a falsification condition for is an opinion, not a claim. Every sentence in this book that slid into that category was cut.
- Track 1 and Track 2 are about twenty years apart in maturity. All five [Standard] labels are Track 1 and all four [Experimental] ones are Track 2. That is why Parts 3 and 4 read differently.
- Names last a few years, problems last decades, solutions last centuries. This book's title hangs on the first layer, and I hope what is inside it belongs to the second and third.
- Use the numbers in this book for order of magnitude and direction only. Re-measuring in your environment takes a day. If you only pick one, pick the dominant segment from Chapter 33.
- And while writing this book I issued 19 corrections. About half were things I had believed for a long time. I left those corrections in rather than deleting them.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| falsifiability | [De facto] | [plato.stanford.edu/entries/popper](https://plato.stanford.edu/entries/popper/) |
| ISO/IEC 39075 | [Standard] | [iso.org/standard/76120.html](https://www.iso.org/standard/76120.html) |
| SPARQL 1.2 | [Standard] | [w3.org/TR/sparql12-query](https://www.w3.org/TR/sparql12-query/) |
| MCP | [De facto] | [modelcontextprotocol.io/specification/2025-06-18](https://modelcontextprotocol.io/specification/2025-06-18) |
| agent interoperability | [Experimental] | [a2a-protocol.org](https://a2a-protocol.org/) |
| world model | [Experimental] | [openreview.net/forum?id=BZ5a1r-kVsf](https://openreview.net/forum?id=BZ5a1r-kVsf) |
| self-refining ontology | [Experimental] | [arxiv.org/abs/2404.13501](https://arxiv.org/abs/2404.13501) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch35/code/`](../../../content/ch35/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

Checked August 2026. Python 3.9+. No external dependencies.

```bash
cd content/ch35/code
python3 ex1_five_claims.py       # the five claims most likely to be wrong
python3 ex2_standard_watch.py    # where the standards have got to
python3 ex3_what_survives.py     # the lifespan of names, problems, and solutions
python3 ex4_selfcheck.py         # the list to re-measure in your system
python3 ex5_next_questions.py    # what this book could not answer
```

The examples in this chapter are closer to *tables* than to code. Opening the files and editing
them is more useful than running them.

The `confidence` values in `ex1` in particular are the author's judgment, and yours may differ.
Change the numbers and write down how much you believe each claim.

<!-- 실행 가이드 끝 -->

---

**Last thing:** go measure. If your numbers come out different, yours are right. A value measured in your environment beats any sentence in this book.

---

Previous: [Ch 34 What It Means to Erase Personal Data from a Graph](../../ch34/code/README.md) | [Contents](../../../README.en.md)

Found something wrong in this chapter? [File a factual error](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml) or [object to a status label](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml). English is fine.
