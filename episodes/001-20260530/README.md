# Lion Saturday Live — Episode 01: Reactive Agents & Knowledge Graphs That Reason

> Agents that **react to typed events** instead of being wired by hand, and a knowledge graph that **holds equations, proposes its own research agenda, and enforces who-can-do-what as policy** — built and debugged live.

|                |                                                                                                                                                            |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 📅 **Date**    | 2026-05-30                                                                                                                                                 |
| 🎙️ **Host**    | Ocean (Haiyang Li)                                                                                                                                         |
| 👤 **Guest**   | Andrew Eisenhawer                                                                                                                                          |
| ▶️ **Video**   | [Watch on YouTube](https://youtu.be/bpOEKSpBQ7g)                                                                                                           |
| ⏱️ **Runtime** | ~1h 50m                                                                                                                                                    |
| 🏷️ **Topics**  | multi-agent orchestration · reactive event bus · knowledge graphs · hypergraphs · hybrid retrieval · graph databases · Row-Level Security · policy-as-code |

**📖 Full notes & topic-by-topic walkthrough → [`SUMMARY.md`](./SUMMARY.md)**

Part 1 demos **lionagi's reactive capability bus** — agents emit typed signals inline as they work, and the session reacts in real time (orchestration by domain event, not by tool call), grown live into a recursive explorer→researcher→critic loop with a structural recursion bound. Part 2 is a deep exchange with Andrew on representing **equations and causality** in a knowledge graph using **khive** — from Structural Causal Models to "a note is a hyperedge" to the graph **proposing its own next build**, then a full architecture review of storage, retrieval, and governance.

---

## Techniques demonstrated

- **Reactive capability bus** — grant a branch a typed schema; it emits inline; the session observes and reacts. No dedicated tool call.
- **Structural recursion bounding** — cap fan-out via _what each branch is allowed to emit_ (a depth-1 DAG) + a global operation budget, not a counter.
- **Equations as a Structural Causal Model** — graph = causal DAG, equation = data on a node, solver = the math; three layers, never conflated.
- **Notes as hyperedges** — n-ary, higher-order relations via `annotates` (the factor-graph / incidence encoding), so the same entities carry different meanings.
- **Structural-hole discovery** — find "what to build next" from graph topology (Swanson's literature-based discovery on your own KG).
- **Event-sourced `propose`** — materialize a machine-found hypothesis as a reviewable change, not a direct mutation.
- **Trait-abstracted multi-backend storage** — dialect-keyed query compiler + a `GraphQuery` execution seam; vectors orthogonal to the graph store.
- **Row-Level Security** — move namespace/tenant isolation from application code into the database.
- **Deterministic cross-platform scoring** — fixed-point ranking, backed by a Lean formal proof.
- **Multi-embedding + RRF** — multiple embedding models per entity, keyed by model, fused by reciprocal rank fusion.
- **Policy-as-code authorization** — a pluggable gate evaluating Rego (Regorus / OPA) in-process, with `allow / deny / escalate`.

---

## Issues opened live

| Repo    | #                                                           | What                                                                    |
| ------- | ----------------------------------------------------------- | ----------------------------------------------------------------------- |
| lionagi | [#1214](https://github.com/ohdearquant/lionagi/issues/1214) | Observer handlers fire sequentially on the stream path (should fan out) |
| lionagi | [#1215](https://github.com/ohdearquant/lionagi/issues/1215) | Lion Studio frontend 404s (API base origin regression)                  |
| khive   | [#554](https://github.com/ohdearquant/khive/issues/554)     | **epic:** multi-backend storage — native graph DBs                      |
| khive   | [#555](https://github.com/ohdearquant/khive/issues/555)     | Dialect-keyed query compiler (Cypher / SurrealQL / Postgres SQL)        |
| khive   | [#556](https://github.com/ohdearquant/khive/issues/556)     | Abstract query execution off `SqlAccess` (`GraphQuery` trait)           |
| khive   | [#557](https://github.com/ohdearquant/khive/issues/557)     | Vectors + federated hybrid retrieval under multi-backend                |
| khive   | [#558](https://github.com/ohdearquant/khive/issues/558)     | Postgres backend (pgvector, dialect, pooling)                           |
| khive   | [#559](https://github.com/ohdearquant/khive/issues/559)     | Namespace isolation via Postgres Row-Level Security                     |
| khive   | [#560](https://github.com/ohdearquant/khive/issues/560)     | Sparse store O(corpus) scan → inverted postings index                   |

_Plus a staged khive `propose` (EAGLE-2 paper-node dedup) demonstrating the propose→review→apply lifecycle._

---

## Technologies & concepts mentioned

**Lion stack** · [lionagi](https://github.com/ohdearquant/lionagi) · [khive](https://github.com/ohdearquant/khive) · lattice (pure-Rust inference engine) · LN kernel (Lean-verified policy kernel)

**Tools / DBs** · [Regorus](https://github.com/microsoft/regorus) · [Open Policy Agent / Rego](https://www.openpolicyagent.org) · [Oxigraph](https://github.com/oxigraph/oxigraph) · FalkorDB · SurrealDB · Neo4j · Postgres · pgvector · Qdrant · Graphiti · SQLite

**Concepts** · Structural Causal Models (Pearl, do-calculus) · Literature-Based Discovery (Swanson ABC) · Reciprocal Rank Fusion (Cormack et al. 2009) · [EAGLE-2](https://arxiv.org/abs/2406.16858) · HNSW / Vamana · SPLADE (learned sparse) · MiniLM

---

## In this folder

| File                     | What it is                                      |
| ------------------------ | ----------------------------------------------- |
| `README.md`              | This page.                                      |
| `SUMMARY.md`             | Full topic-by-topic walkthrough of the episode. |
| `capability_bus_demo.py` | Runnable demo for the Part 1 capability bus.    |
| `youtube.md`             | Title, chapters & description for the upload.   |

_The video lives on [YouTube](https://youtu.be/bpOEKSpBQ7g); the raw transcript isn't published — `SUMMARY.md` is the canonical write-up._

---

**Lion** is an ecosystem for building AGI systems from composable, governed agents, by Ocean (Haiyang Li): own the whole stack — policy kernel → inference engine → orchestration → governance. 💬 Open a GitHub issue or join the Discord. **New episode every Saturday.**
