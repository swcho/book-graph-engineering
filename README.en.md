<p align="center">
  <img src="img/cover-front.png" alt="Graph Engineering - designing intelligence by connecting knowledge and agents" width="420">
</p>

<h1 align="center">Graph Engineering</h1>
<p align="center">
  From the bridges of Königsberg to the agent harness<br>
  Knowledge graphs and agent graphs, two tracks on one backbone<br>
  <br>
  <b>leaf meta (리프 메타)</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Published%20edition-Korean%20only-2f6f4e?style=for-the-badge" alt="Published edition: Korean only">
  &nbsp;
  <img src="https://img.shields.io/badge/English%20edition-under%20review-9a6b1f?style=for-the-badge" alt="English edition: under review">
</p>

<p align="center">
  <sub>
    <b>English</b> | <a href="README.md">한국어</a>
  </sub>
</p>

---

## Read this first - only a Korean edition exists

The book is published in Korean. 453 pages, one edition, and that is the only edition there is.

**An English edition is under review.** No decision, no date, and no download link on this page
until there is one. I would rather leave this blank than put up a link that turns out to be a
Korean PDF with an English button on it.

What is here in English right now, and usable today:

- **[SOURCES.en.md](SOURCES.en.md)** - every primary source in the book, 172 links across
  228 keywords, grouped by chapter, each labeled [Standard] / [De facto] / [Experimental].
  The source names and URLs were always in English. This page is a reading list on its own.
- **[`content_en/`](content_en)** - an English summary page for every one of the 35 chapters.
  Sections, the chapter in one page, sources, and how to run the examples.
- **Runnable examples** in [`content/`](content) - 170-odd Python files. Code is code.
  The comments and printed output are Korean; the structure is not.

Issues in English are welcome. The templates are written in Korean, but answer in English and
nothing breaks.

---

## License

**[Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)**.
Copy it, redistribute it, print it, use it in a class or an internal training deck. One condition:
credit the author (leaf meta) and the book title. If you modify it, say that it is modified so it
does not get confused with the original. Details in [`LICENSE`](LICENSE).

---

## Table of contents

35 chapters and 6 appendices, in 8 parts. After Parts 1 and 2 the book splits into
**Track 1 (knowledge graphs)** and **Track 2 (agent graphs)**, and rejoins them in Part 5.
If you are in a hurry, start at Part 2. If you only care about agents, jump to Part 4 -
it is written so that you will not get stuck.

Chapter titles link to that chapter's English summary page under
[`content_en/`](content_en). Each one carries a section list, the chapter in one page, the
keyword-to-source table, and how to run the examples. Use them to decide which chapters are
worth your time before you take on 453 pages of Korean.

### Part 1 - Roots: where the graph was all along

Early AI *was* a graph. Deep learning dissolved it into vectors. Now, in the era of LLM agents,
we are drawing graphs again. Sixty years and the last two, compressed.

| Ch | Title | What it covers |
|---|---|---|
| 1 | [Sixty Years of AI, Read as a Graph](content_en/ch01/code/README.md) | Symbols to vectors and back to graphs. Landing on harness engineering |
| 2 | [From Harness Engineering to Graph Engineering](content_en/ch02/code/README.md) | Agents, skills, orchestrators translated into nodes, subgraphs, executors |
| 3 | [Why Seven Bridges Couldn't Be Crossed, and Why Tables Won](content_en/ch03/code/README.md) | Euler's proof; what the relational model won with and what it gave up |
| 4 | [Why the Semantic Web Looked Like a Failure](content_en/ch04/code/README.md) | The ambition of RDF and OWL, the stall, and what survived |
| 5 | [Things, Not Strings](content_en/ch05/code/README.md) | Google's knowledge graph announcement and the rise of property graphs |
| 6 | [It Took Ten Years to Get Back What We Dissolved into Vectors](content_en/ch06/code/README.md) | Graph embeddings and GNNs; RAG's ceiling and the turn to GraphRAG |

### Part 2 - The basic grammar of graphs

Nodes, edges, properties, traversal, centrality, query languages. Whichever track you take,
you walk over this ground first.

| Ch | Title | What it covers |
|---|---|---|
| 7 | [One Node Drawn Wrong Cost Me Three Weeks](content_en/ch07/code/README.md) | Nodes, edges, properties, labels; direction and weight; schema and constraints |
| 8 | [What a Graph Actually Looks Like in Memory](content_en/ch08/code/README.md) | Adjacency lists and CSR; how storage layout decides performance |
| 9 | [Counting Degrees of Separation Killed the Server](content_en/ch09/code/README.md) | BFS and DFS, shortest paths, the cost that explodes as hops grow |
| 10 | [Which Node Actually Matters](content_en/ch10/code/README.md) | Centrality measures and community detection, and the question each one answers |
| 11 | [One Question, Three Languages](content_en/ch11/code/README.md) | Cypher vs SPARQL vs Gremlin, plus ISO GQL and SQL/PGQ |

### Part 3 - Knowledge graph engineering (Track 1)

What the model **knows**. Ontology design, triple extraction, time, hybrid retrieval.

| Ch | Title | What it covers |
|---|---|---|
| 12 | [How I Tore Down an Ontology in Three Weeks](content_en/ch12/code/README.md) | Deriving vocabulary from queries; when to freeze the schema |
| 13 | [An Unvalidated Graph Is Just a Pile of Links](content_en/ch13/code/README.md) | SHACL constraints, OWL inference, where to put validation |
| 14 | [The Same Person, Sitting There as Four Nodes](content_en/ch14/code/README.md) | Entity resolution and merging, and how to undo a merge |
| 15 | [I Pulled Triples from 10,000 Documents and Half Were False](content_en/ch15/code/README.md) | Managing precision and recall when extracting from unstructured text |
| 16 | [True Yesterday, Wrong Today](content_en/ch16/code/README.md) | Valid time and transaction time, provenance and trust (PROV-O) |
| 17 | [Questions Vectors Alone Can't Answer](content_en/ch17/code/README.md) | Hybrid retrieval; GraphRAG vs LightRAG vs HippoRAG |

### Part 4 - Agent graph engineering (Track 2)

What the model **does**. This field is still finding its footing, so the text marks in plain
sentences where verified fact ends and my estimate begins.

| Ch | Title | What it covers |
|---|---|---|
| 18 | [Where Does a Chain Break](content_en/ch18/code/README.md) | The limits of a linear chain, and why we draw graphs instead |
| 19 | [State Graphs, Reducers, and Supersteps](content_en/ch19/code/README.md) | Merge rules for state, superstep scheduling |
| 20 | [How to End a Loop That Won't End](content_en/ch20/code/README.md) | Branching and cycles, termination conditions, stopping node explosion |
| 21 | [The Process Dies, the Work Must Not](content_en/ch21/code/README.md) | Checkpointing and durable execution |
| 22 | [How to Pay Back What You Can't Undo](content_en/ch22/code/README.md) | Retries and timeouts, compensating transactions |
| 23 | [Where the Human Steps In](content_en/ch23/code/README.md) | Human-in-the-loop interrupts and resumption |
| 24 | [Your Context Is Full](content_en/ch24/code/README.md) | Compaction, summarization, offloading, memory tiers, subagent isolation |
| 25 | [Six Topologies, and the Sockets You Plug Tools Into](content_en/ch25/code/README.md) | The multi-agent topology catalog; tool calls and MCP |
| 26 | [What Will You Forbid](content_en/ch26/code/README.md) | Guardrails and permission boundaries; observability, tracing, evaluation |

### Part 5 - Where the two graphs meet

The junction. This is the climax of the book.

| Ch | Title | What it covers |
|---|---|---|
| 27 | [The Cheapest Way to Give an Agent Memory](content_en/ch27/code/README.md) | Using a knowledge graph as an agent's long-term memory |
| 28 | [When the Agent Grows the Graph by Itself](content_en/ch28/code/README.md) | The self-expansion loop, and what it costs you |
| 29 | [One Backbone](content_en/ch29/code/README.md) | A reference architecture that joins both tracks |

### Part 6 - The backbone: state management engine

The heart of the book. All of it in working code and diagrams.

| Ch | Title | What it covers |
|---|---|---|
| 30 | [Nobody Knows What Changed, or When](content_en/ch30/code/README.md) | Event sourcing, idempotency, exactly-once execution |
| 31 | [Two Agents Edited the Same Node at Once](content_en/ch31/code/README.md) | Optimistic locking, conflict resolution, the saga pattern |
| 32 | [The Day You Change the Schema](content_en/ch32/code/README.md) | Expand-and-contract migration, dual reads, versioning |

### Part 7 - Operations

| Ch | Title | What it covers |
|---|---|---|
| 33 | [Read the Query Plan and You See the Bill](content_en/ch33/code/README.md) | Performance tuning, what indexes actually buy, the cost model |
| 34 | [What It Means to Erase Personal Data from a Graph](content_en/ch34/code/README.md) | Right to erasure, re-identification risk, how far a cascade should go |

### Part 8 - What comes next

| Ch | Title | What it covers |
|---|---|---|
| 35 | [Five Claims Most Likely to Be Wrong in Three Years](content_en/ch35/code/README.md) | The author names five of his own claims and attaches a falsification condition to each |

### Appendices

Glossary (Korean to English), full source list, Cypher/SPARQL/GQL cheat sheet, engine comparison,
example run guide, exercise answer index

---

## Sources

**[📎 SOURCES.en.md - every primary source in the book](SOURCES.en.md)**

172 links across 228 keywords, grouped by chapter, with a separate table of the sources cited by
more than one chapter. If you read nothing else here, read that page.

Every keyword in the book carries one of three labels: **[Standard]** (an official specification
exists), **[De facto]** (no specification, but the industry uses it widely), **[Experimental]**
(still finding its footing). Counts: 62 / 142 / 24. That distribution is itself an argument -
[Standard] clusters in the knowledge-graph half, [Experimental] in the agent half, and the gap
between them is about twenty years.

Think a label is wrong? [Say so](../../issues/new?template=03-status-label.yml).

There is also a [further-reading page](LINKS.md) collecting 106 papers, textbooks, courses,
engines, datasets and vendor platforms that are *not* cited in the book, each tagged with the chapter it goes
with. That page is Korean-only, but the entries are links and English titles, so it reads fine
either way.

---

## Editions

| Edition | Status |
|---|---|
| Korean | Published. 453 pages, one edition |
| English | **Under review.** No decision and no date |

There is deliberately no download link on this page. The only file that exists is the Korean
PDF, and putting it behind an English button would misrepresent what you are getting. If you
read Korean, the [Korean page](README.md) has the download, the checksum, and the release notes.

If the English edition happens, it will be announced here and shipped as a separate release
asset with `en` in the filename, next to the Korean one. Until then this line stays as it is.

### What "under review" actually means

I am not being coy. The body text runs to about 250,000 Korean characters, roughly 115,000
English words, and all 140 diagram sources have Korean baked into them. For one person that is
months of work, not a scheduling question, so it stays an open decision. What you see here -
this page, the [sources](SOURCES.en.md), the [chapter summaries](content_en) - is the part that
was worth doing either way.

Watching this repository is the way to hear about it. There is nothing else to sign up for.

---

## Example code

The runnable examples from the book, one directory per chapter.

```
content/                  # the code itself. One copy, not one per language
├─ ch01/code/             # README.md here is Korean
├─ ch02/code/
│  ...
└─ ch35/code/

content_en/               # English chapter pages. No code, by design
├─ ch01/code/README.md
│  ...
└─ ch35/code/README.md
```

The code is not duplicated per language. Translating 170 files of comments would guarantee the
two copies drift apart, and a drifted example is worse than a Korean one. So `content_en/`
mirrors the path shape and points back at the single copy under `content/`.

Most of them run on Python 3.11+ with nothing installed. Where an example needs a database or an
external API, that chapter's `code/README.md` lists the versions, the install command, and the
sample data. Those READMEs are in Korean, but the command blocks are not, and each file's purpose
is one `pip install` line away from obvious.

Chapters that need more than the standard library use `langgraph`, `kuzu`, `rdflib`, `pyshacl`,
or `mcp`. No API key is required anywhere - the examples that would otherwise call a model use a
deliberately built fake that reproduces two failure modes real models have.

---

## Corrections and refutations

This is not a book you can trust because it is correct. It is a book you can trust **because it
gets fixed when it turns out to be wrong**. [Issues](../../issues) is where that happens.

There is not a single "report an error" line inside the book itself. A contact address printed on
a page dies in a few years, and after that it is just a gesture toward being correctable. So the
repository is open instead.

### Three ways in

| What | When | Open |
|---|---|---|
| **Factual error** | Something in the text is not true. Page, quote, evidence | [File it](../../issues/new?template=01-fact-error.yml) |
| **Refutation** | You have evidence that one of the five claims in Chapter 35 is wrong | [File it](../../issues/new?template=02-refutation.yml) |
| **Status label objection** | A [Standard] / [De facto] / [Experimental] label is misapplied | [File it](../../issues/new?template=03-status-label.yml) |
| **Suggest a link** | You found something for the [further-reading page](LINKS.md), or a link there is dead | [File it](../../issues/new?template=04-link-suggestion.yml) |

The forms are in Korean. Write your answers in English - nothing about that is a problem. If none
of the four fit, open a blank issue. The templates exist to help you write, not to keep you out.

### The refutations are already on the table

In Chapter 35 the author names five of the book's own claims and writes down, for each one,
**what would have to be true for the claim to be wrong**. Average confidence: 46%. Below half.

| Claim | Confidence | If this is true, I am wrong |
|---|---|---|
| 1. Model calls take more than 90% of response time (Ch 33) | 35% | Model latency for the same work drops 10× and the share falls below 60% |
| 2. Prompt injection cannot be stopped at the prompt layer (Ch 26) | 55% | A model ships that separates instructions from data structurally |
| 3. A self-expanded graph is unusable without gates (Ch 28) | 70% | Extraction accuracy reaches 99.9% and three of the four gates become unnecessary |
| 4. Knowledge graph and agent state belong in separate stores (Ch 29) | 50% | Graph DB write performance reaches key-value store levels |
| 5. The term "agent graph engineering" sticks (preface) | 20% | Three years from now, nobody uses the phrase |

A sentence you cannot write a falsification condition for is an opinion, not a claim. Every
sentence in this book that slid into that category was cut. This table is that rule applied to
the author.

### Before you file

- Check whether the latest edition already fixed it. The edition number is printed in the book
  and is in the filename, if you have the PDF.
- Cite primary sources: official specifications, vendor documentation, RFCs, papers, official
  repositories. The book was written to that standard and gets corrected to the same one.
- "Here is what I measured in my environment" is the strongest evidence this book accepts. Use the
  numbers in the book for order of magnitude and direction only, and measure your own.

---

## About the book

The goal was not a textbook. It was **the book you read alone at night and then open your laptop**.
Every section moves in four beats: where you got stuck, why you got stuck, the smallest thing that
gets you through, and when that thing betrays you.

So the failures run longer than the successes. In every chapter, at least three times, the author
doubts a claim, checks it, and - when it turns out wrong - corrects what he said earlier. Those
reversals were not smoothed out afterward. The trust in this book comes from **the habit of
correcting**, not from being right.

Every chapter ends with a box called "what I still don't know": two or three things the author is
not confident about, written down as they are.

---

<sub><b>English</b> | <a href="README.md">한국어</a> - the Korean page is the original and is
updated first.</sub>
