# Lion Saturday Live — Episode 01 · Full Summary

_2026-05-30 · Ocean (Haiyang Li) with Andrew Eisenhawer_

Two halves of one bet. **Part 1** demos a feature recently landed in **lionagi** — the
_reactive capability bus_: agents emit typed signals inline as they work, and the session
reacts to those signals in real time. **Part 2** is a long, live exchange with Andrew about
representing equations and causality in a knowledge graph, which turns into a tour of
**khive**'s design — hypergraphs, self-proposing research frontiers, multi-backend storage,
Row-Level Security, and policy-as-code.

The unifying thesis Ocean keeps returning to: **own the whole stack** — policy kernel →
inference engine → orchestration → governance — and put the controls on the _agent-tooling_
side.

---

## Chapters

| Time      | Chapter                                                                           |
| --------- | --------------------------------------------------------------------------------- |
| `0:00`    | Intro — Lion Saturday Live                                                        |
| `4:43`    | **Part 1:** Reactive capability bus — the live demo (`grant` → `observe` → react) |
| `28:20`   | Recursive capabilities: `Finding` → `Hypothesis` → `Correction`                   |
| `30:35`   | lionagi's next chapter: 40 preset personas, 10–12 cognitive modes                 |
| `38:00`   | The "Show / Play / Actor" orchestration model                                     |
| `43:00`   | Bounding recursion: capability grants as the structural bound + budget            |
| `49:00`   | Packs — asserting rules onto the agent roster; governance boundaries              |
| `52:00`   | The app layer — a FastAPI-shaped `session.observe(...)`                           |
| `55:46`   | **Part 2:** Andrew's question — equations & causality in a knowledge graph        |
| `58:40`   | Introducing khive (knowledge-hive)                                                |
| `1:01:30` | F = ma → Structural Causal Model: structure vs. properties                        |
| `1:04:00` | Closed taxonomy, packs, a task as a specialized note                              |
| `1:06:00` | Andrew's framing: dimensional analysis as a hypergraph                            |
| `1:10:56` | **A note is a hyperedge** — `annotates` targets entities, notes, edges            |
| `1:15:17` | Querying the curated graph for _what to build next_                               |
| `1:21:25` | `propose` + version control → "build more plugins"                                |
| `1:22:32` | Deterministic scoring + a Lean formal proof; KG-as-GitHub                         |
| `1:24:00` | Multi-backend storage; the SPARQL→SQL question                                    |
| `1:31:00` | …and the vectors?                                                                 |
| `1:39:14` | Postgres + Row-Level Security                                                     |
| `1:41:00` | Sparse store + multi-embedding-engine setup                                       |
| `1:44:01` | Regorus / OPA — authorization as policy; owning the whole stack                   |

---

# Part 1 — lionagi: the reactive capability bus

### From message-oriented to event-oriented orchestration

Most agent frameworks orchestrate by _messages and tool calls_: you wire up who talks to
whom and give the model tools to invoke when it wants something to happen. You end up
managing the plumbing — the hand-offs, the escalation logic, the control flow.

The capability bus inverts that. You **grant a branch a capability** — a typed schema it is
allowed to emit — and the model emits instances of it _inline in its normal text_, as it
works, in a fenced ```json block. The session parses every assistant message, lifts those
emissions onto a bus, and dispatches them to whatever observers you've registered.

> _"We're not using a sub-agent as a tool… we're merely asking the explorer to emit a
> finding. The finding-to-research logic is the observer, and that's independent of the
> explorer. From the explorer's perspective, it just finds something — it doesn't know what
> the system is going to do with it next. And that is precisely the point."_ — Ocean

So you stop orchestrating _how agents talk to each other_ and start orchestrating _what
happens when a domain event occurs_. It's the difference between hand-writing an expert
system's escalation flow and letting domain events route themselves reactively.

### The demo, built live

The skeleton is tiny:

```python
session = Session()
branch  = session.default_branch
branch.chat_model = li.iModel(provider="claude_code", model="sonnet")

# 1) Grant the capability — sets the runtime grant AND injects an instruction
#    block so the model knows it may emit Finding inline.
branch.grant_capabilities(Operable((Spec(Finding, name="finding"),), name="Caps"))

# 2) React the instant a Finding streams in.
@session.observe(Finding)
async def dig_deeper(finding: Finding, _session: Session) -> None:
    ...

# 3) Drive the run; signals fire live as the model reads and writes.
async for _ in branch.run(prompt):
    pass
```

`Finding` is just a Pydantic model — `claim`, `file`, `confidence`. (Andrew asked early
whether `Finding` was bespoke; it's a plain base model — _granting_ it as a capability is
what lets the branch emit it.) Live, the explorer read `signal.py` and `observer.py` and, as
it read, emitted structured findings inside its text. The session observed every one
straight out of that inline emission — no tool call, no waiting for the run to finish.

The first reaction, `dig_deeper`, spawns a **researcher** sub-branch that cross-checks each
confident finding against the literature and returns a structured `ResearchReport`.
Crucially, that reaction lives on the _session_, not in the explorer — the explorer never
asked for a researcher. A nice consequence: because the reaction is just a callback,
**`dig_deeper` can be any workflow** — a plain LLM call, a Codex process, even an existing
LangGraph agent. The bus doesn't care.

### Many capabilities, and the recursion question

The demo then grew three capabilities across three roles:

| Branch                 | May emit     | Reacts by                                        |
| ---------------------- | ------------ | ------------------------------------------------ |
| **explorer** (default) | `Finding`    | — (it's the seed)                                |
| **researcher**         | `Hypothesis` | digging deeper → `ResearchReport`                |
| **critic**             | `Correction` | challenging a finding, superseding it when wrong |

This is where it "gets really dynamic, very fast" — and where the obvious risk lives. If a
reaction to a signal can emit a signal that triggers another reaction, what stops it from
looping forever? Ocean's instruction on the stream was blunt: _"help me do logic so we don't
have endless recursion."_

The answer is **structural, not a counter**: bound recursion through the capability grants.
Only the **explorer** is granted `Finding`; sub-branches get _non-`Finding`_ capabilities
(researcher → `Hypothesis`, critic → `Correction`), and those observers do **terminal** work
— update a shared knowledge base, spawn nothing. Since no capability path leads back to
`Finding`, the reaction graph is a **depth-1 DAG**, and every fan-out terminates. The bound
is enforced by what each branch is _allowed to say_ — far more robust than detecting a cycle
after the fact. On top of that, a **global operation budget** (10 in the demo) caps total
reactively-launched operations; each spawn calls `await budget.take()` first.

Two live moments worth keeping. Ocean had accidentally granted the critic `Hypothesis` while
its prompt said _emit corrections_ — an incoherence we caught and fixed so grant and
instruction agreed. And Andrew's sharp meta-question: _"that critic operation — did you
build it, or did Opus build it when you told it to finish?"_ The honest answer is both:
Ocean defined the capability scope and tapped out the first lines; the assistant filled in
the rest under that scope. **The capability boundaries are the human-authored part; the
wiring within them is delegable.**

### Two bugs caught live — the case for observability

Reacting to typed events mid-run is its own debugging tool: you can _see_ the system do the
wrong thing in real time. Two issues surfaced and went straight to GitHub.

1. **Observer handlers fire sequentially on the stream path** (lionagi #1214). Findings were
   researched one-by-one instead of fanning out. Andrew diagnosed it precisely on the call:
   the `await` blocks, so the next finding isn't dispatched until the current handler
   returns — observer dispatch isn't concurrent. The fix is to dispatch handlers as
   concurrent tasks and gather at run completion.
2. **Lion Studio frontend 404s** (lionagi #1215). The monitoring UI failed to load — traced
   to the frontend resolving its API base to the wrong origin (a regressed hot-fix),
   compounded by a stale route build.

Both are the ordinary tax of live demos, but they make the point: the bus gives you a
real-time window into a multi-agent run — exactly when you want one.

### Where this is heading

The capability bus is the substrate for lionagi's next chapter — moving agent definition
from _pre-configured before runtime_ to _composed at runtime from the situation_:

- **~40 preset personas** and **~10–12 cognitive modes** (constraint-solving, associative,
  empathetic, evidence-driven, fast, …). These compose: `fast` + `analyst` → a fast analyst;
  `evidence-driven` + `entrepreneur` → a fact-driven entrepreneur. Rather than hand-build an
  expert system and its escalation flow, you let the orchestrator assemble the roster from
  context.
- **Packs** — an abstraction that asserts rules onto the agent roster. The default pack
  bounds the orchestrator: it can't change caller requirements, can't make architecture
  decisions, can't merge artifacts without authorization, and must _escalate_ on scope creep
  or conflicting agent outputs. A coding pack and a research pack carry different rules;
  role hand-offs are on the roadmap.
- **An app layer** with FastAPI-shaped ergonomics — the piece Ocean sees as the missing
  usability link:

  ```python
  session = Session()

  @session.observe(Finding)
  async def research(finding, _session):
      ...  # literally anything

  # when any branch in the session emits a Finding, this just runs.
  ```

- **Governance as a first-class concern.** lionagi's gate primitive is _allow / deny /
  **escalate**_ (Andrew: "escalate certainly should be a primitive"), with policy expressible
  in a Rego-style engine running in-process.

> _Ocean also runs orchestration as a "Show" — a DAG of "Plays," each a dynamically-generated
> sub-DAG whose nodes can be a Codex process, a Claude Code run, or a plain LLM call. Issues
> filed on stream get cleared by firing an overnight Show that lists everything as PRs in
> strict merge sequence for morning review._

---

# Part 2 — khive: knowledge graphs that reason

### What khive is

khive (knowledge-_hive_) is a **knowledge-graph runtime for AI agents** — typed entities, a
closed edge ontology, hybrid retrieval (dense vectors + BM25 + learned-sparse, fused), and
GQL/SPARQL queries, all in a single Rust binary speaking MCP. It's _opinionated_: 8 entity
kinds, 15 edge relations, 5 note kinds — all closed sets. If your data doesn't fit, you
remodel; you don't extend the schema. That constraint is the point — it's what keeps a graph
coherent over months instead of decaying into tag soup (Ocean: _"you can have 100 very
similar edges… and then the graph is kind of useless"_).

The recurring theme: **the closed core never moves; everything interesting is built on top**
— through packs, trait-abstracted backends, notes-as-edges, policy-as-data.

### Q1 — Can a graph represent equations, and reason _causally_ with them?

The honest answer starts with a distinction everyone gets wrong: **a knowledge graph
represents _what relates to what_ (topology and causal direction); it does not represent the
_semantics of the equation_ (the algebra, the solving).** Trying to make the graph "do the
math" is the classic failure mode. Split it into three layers:

| Layer                   | Holds                                               | Where it lives                                        |
| ----------------------- | --------------------------------------------------- | ----------------------------------------------------- |
| Causal / relational DAG | which quantities influence which, in what direction | entities + edges                                      |
| Structural equation     | `F = m·a`, units, dimensions                        | a property on the law node (a SymPy-parseable string) |
| Solver                  | "given F and m, find a"                             | an external CAS, reading that property                |

This is exactly a **Structural Causal Model** (Pearl): a DAG _plus_ structural equations.
`Force`, `Mass`, `Acceleration`, and `Newton's Second Law` are concept entities; the
quantities carry units/dimensions as properties; the law carries the equation string; edges
encode the causal reading. You **traverse** to discover _what governs what_, then hand the
equation to a solver for the numbers. (Live, khive's own knowledge corpus surfaced the
Pearl/SCM and causal-graph-reasoning atoms to ground this.)

### Q2 — "But an equation means different things in different contexts — hypergraphs?"

This was Andrew's deepest point. He'd been circling a hypergraph framing himself: in
dimensional analysis, **units are nodes** and **conversions** (meters ↔ kilograms via
density) are relationships, so an equation is "embodied in how nodes and edges connect," not
stored in any one node — multiple relationships co-defined over a _set_ of nodes. That's a
hypergraph, and binary edges can't express it.

khive's answer: **a note is a hyperedge.** The textbook way to represent a hypergraph in a
binary-edge store is the _incidence (bipartite) encoding_ — promote each hyperedge to a node
and connect it to its members. That's a **factor graph**, and khive has the primitives:

| Hypergraph concept     | khive primitive                          |
| ---------------------- | ---------------------------------------- |
| vertex                 | entity                                   |
| hyperedge              | **note**                                 |
| incidence (membership) | the **`annotates`** edge (note → member) |

The key rule: `annotates` is the only cross-substrate relation — its source must be a note,
and its target can be an entity, **another note, or an edge**. So one note binds
`{Force, Mass, Acceleration}` — that note _is_ the hyperedge. Because a note can annotate
other notes, you get a **higher-order hypergraph** a plain set-of-vertices model can't
express. And the same entities can be incident to _multiple_ notes — Newtonian reading,
control-systems reading, a measurement record — each a distinct, content-bearing,
role-labeled hyperedge. **The semantics live in the notes, not smeared across overloaded
edge types.** (Andrew didn't claim a full "aha" on stream — he took it away to replicate —
but the note-as-hyperedge mapping is the answer khive offers.)

### Q3 — Can the graph tell you _what to build next_?

Yes — and this is where a curated graph stops being passive storage. The trick is
**structural holes**: two mature, well-connected concepts that _aren't_ connected are a
latent hypothesis (Swanson's literature-based discovery, run on your own graph).

Live, against ~2,400 entities / ~7,400 edges / ~11,500 notes, we swept the inference
cluster: `Speculative Decoding` **enables** `FlatKVCache` (single-sequence, **linear**
rollback) and **contains** `EAGLE-2` (dynamic **draft trees**) — but `EAGLE-2` and
`FlatKVCache` share _no_ edge. Read against the node semantics, the absence _is_ the finding:
FlatKVCache can't fork, so it can't support EAGLE-2-style tree speculation → **build a
forkable / tree-structured KV cache**. We then closed the loop: filed the open question as a
first-class queryable object incident on the three concepts that revealed it. **The graph's
topology becomes a rankable, persistent, compounding research agenda.**

### Q4 — "Sounds like you need more plugins."

Exactly right — and the correct mechanism for materializing a finding isn't to mutate the
graph directly (which the demo did, by hand, as a teachable shortcut) but khive's **`propose`**
verb: an event-sourced change-proposal lifecycle, so a machine-surfaced hypothesis is
_reviewed_ before it lands. None of Q1–Q3 touched the closed core — equations → notes +
properties; discovery → existing query verbs; materializing → `propose`. The value is in
**packs** that compose primitives into domain capabilities: a _discovery_ pack (rank holes,
auto-propose), a _physics/quantity_ pack (laws-as-hyperedges + a solver bridge — _zero new
edge relations_, which is why it's a pack not a schema change), a _causal_ pack (SCM
intervene/counterfactual). Ocean likes plugins precisely because they're version-trapped and
low-config for humans.

### Q5 — Multi-backend storage: native graph DBs, and the SPARQL→SQL question

khive compiles GQL/SPARQL to **SQLite SQL** today. The code-verified path:

```
query → parse (GQL|SPARQL) → backend-agnostic AST → compile → SQL → execute → rows
```

The AST is already backend-neutral, and CRUD/neighbors/traverse already route through
abstract storage traits — so they'd work on a native graph DB the moment it implements the
traits. Only the **`query` path is SQLite-bound**, in two spots: (1) the compiler is singular
and SQLite-flavored → make it a **dialect-keyed strategy** (Cypher for Neo4j/FalkorDB,
SurrealQL for SurrealDB); (2) execution is hardwired to SQL and returns SQL rows → move it
behind a **`GraphQuery` trait with a backend-neutral row type** so the runtime stops knowing
SQL exists. Then each DB is a new crate implementing the traits + its compiler. (Candidates
discussed: Neo4j, FalkorDB, SurrealDB, Oxigraph.)

### Q6 — …and the vectors?

Sharp follow-up — vectors physically sit in the SQLite file today. But in the code,
**`VectorStore` is a _separate_ trait from `GraphStore`**, with its own capability model, and
retrieval talks to it keyed by the same entity UUID. So vectors are **orthogonal to the graph
backend by design** — and khive is already migrating them onto in-process Rust ANN
(HNSW/Vamana) that's storage-neutral. The genuinely hard part isn't _storage_, it's the
**hybrid query**: one file makes "vector-similar ∧ graph-reachable ∧ keyword-match" a single
fused query; split the stores and it becomes a **federated query** where rank-fusion still
works (it's neutral, UUID-keyed) but cross-store _pre-filter pushdown_ breaks and you now own
UUID consistency across stores. That tradeoff — pushdown vs. over-fetch — is the real
decision, not the file layout.

### Q7 — Postgres + Row-Level Security

Postgres is the _cheapest_ backend to add (it's SQL — reuses the compiler with a dialect
fork: `$1` placeholders, `tsvector`, **pgvector**, `jsonb`) and the _most valuable_, because
of **RLS**. khive enforces namespace isolation in _application code_ today — every ID op must
call a namespace check, and one forgotten check is a cross-namespace leak. RLS makes
isolation a **database invariant** (`USING (namespace = current_setting('khive.namespace'))`)
— you cannot forget a check the database enforces. It's also the substrate for multi-tenancy:
tenant = namespace = RLS-isolated row set. (Andrew uses Supabase precisely for RLS-bound auth,
and PGVector — slow once, now fast enough at the 10⁴–10⁵-vector scale.)

### Q8 — Sparse store + multi-embedding-engine setup

**Multi-embedding:** embedders register behind a provider trait keyed by a unique name; the
same entity carries vectors from _multiple_ models at once (live: a small/fast MiniLM + a
multilingual paraphrase model), each in its own keyed space — because different models produce
_incomparable geometries_, so keying by model keeps them disjoint. Candidates fuse via RRF.
Adopting a new embedder is additive (add a field, backfill, retire the old). **Sparse:** khive
treats learned-sparse (SPLADE-style) as a first-class third modality with a clean CSR vector
type and rank-fusion — but the current impl is an honest O(corpus) brute-force scan where it
should be an inverted postings index. The interface is right; the index is a placeholder, and
it's tracked. (That "we know where the bodies are" discipline runs through the whole system.)

### Q9 — Regorus: authorization as policy, not code

khive's authorization is a pluggable **gate** consulted before every verb dispatch — a clean
policy-enforcement / policy-decision split. The reference backend, `khive-gate-rego`, uses
**Regorus** — Microsoft's pure-Rust interpreter for **Rego** (Open Policy Agent). A policy
sees the request as JSON (`actor`, `namespace`, `verb`, `args`) and returns allow/deny with
optional **obligations** (audit, rate-limit). Why: authz becomes _config, not a recompile_,
in one auditable place; it's in-process pure Rust (no external OPA server, fits the
single-binary ethos); and it's pluggable + opt-in (the local OSS build uses a permissive gate
and doesn't even compile Regorus). With Postgres RLS this gives **defense in depth across
three layers** — the gate decides _can this actor invoke this verb_, RLS decides _which rows
the namespace sees_, the runtime check is the portable floor. lionagi extends OPA's allow/deny
with an **escalate** primitive.

> A deeper thread Ocean surfaced: scoring in khive is **deterministic and cross-platform** —
> the same ranking reproduces on any platform — backed by a **Lean formal proof that
> compiles**. The longer game is a Lean-verified policy kernel (the _LN kernel_, ~26k lines)
> asserting end-to-end invariants like strict tenant isolation. And the vision for khive
> itself: **GitHub for knowledge bases** — a diff format, `propose`/review, and `supersedes`
> (keep the record, mark it stale) so the graph is versioned like a codebase, feeding a
> `brain` pack that learns retrieval quality from an event-feedback loop.

---

## The through-line

Every answer came back to the same design taste:

1. **A small, frozen, opinionated core** — coherence by constraint.
2. **Clean trait seams** so backends, vector stores, embedders, and policy engines are
   _orthogonal, pluggable, and opt-in_ — the local OSS user pays nothing for what the
   enterprise deployment turns on.
3. **Data vs. view discipline** — history is preserved (`supersedes`, not delete); what's
   _shown_ is a query decision.
4. **Notes as hyperedges** — n-ary, higher-order, semantic structure without bloating the
   relation set.
5. **Reactivity over wiring** — orchestrate domain events, not message plumbing.
6. **Governance and determinism as first-class** — policy-as-code, RLS, formally-proven
   invariants.
7. **Intellectual honesty about maturity** — the gaps are found, measured, and tracked, not
   hidden.

Own the whole stack — policy kernel → inference engine → orchestration → governance — and a
knowledge graph that holds equations _and_ causality, proposes its own frontier, runs on the
engine you choose, and enforces who-can-do-what as reviewable policy. That's the bet.
