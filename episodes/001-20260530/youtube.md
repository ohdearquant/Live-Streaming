# YouTube metadata — Episode 01

## Title (primary)

**Reactive AI Agents & Knowledge Graphs That Reason — Lion Saturday Live #1 (w/ Andrew Eisenhawer)**

### Alternates

- Building AGI Infrastructure Live: Event-Driven Agents + Knowledge Graphs That Propose Their Own Research
- Agents That React, Graphs That Reason — Live AGI Engineering (Lion Saturday #1)
- A Knowledge Graph That Tells You What to Build Next — Lion Saturday Live #1
- Reactive Capability Bus + Knowledge Graphs for Equations & Causality — Lion Saturday #1

---

## Description

Live from Lion Saturday — Ocean (Haiyang Li) builds and debugs AGI infrastructure on stream, this week with guest Andrew Eisenhawer.

Two halves, one bet. First, **lionagi's reactive capability bus**: instead of wiring agents together by hand, you grant a branch a typed schema it can _emit inline_ as it works, and the session reacts to those signals in real time — orchestration by domain event, not by tool call. We build it live, grow it to a recursive explorer→researcher→critic loop, and solve the "what stops infinite recursion?" problem structurally.

Then **khive**, a knowledge-graph runtime for AI agents, takes on Andrew's hard question: how do you represent **equations and causality** — F = ma — in a knowledge graph? The answer runs from Structural Causal Models, to "a note is a hyperedge," to a live demo of the graph **proposing its own research agenda** by finding structural holes in its own topology — to a full architecture review of multi-backend storage, Postgres Row-Level Security, and policy-as-code governance.

Real engineering, real bugs, real issues filed on stream.

⏱️ Chapters
0:00 Intro — Lion Saturday Live
4:43 Reactive capability bus — the live demo
28:20 Recursive capabilities: Finding → Hypothesis → Correction
30:35 lionagi's next chapter: preset personas + cognitive modes
38:00 The "Show / Play / Actor" orchestration model
43:00 Bounding recursion via capability grants + budget
49:00 Packs — rules on the agent roster & governance boundaries
52:00 The app layer — a FastAPI-shaped session.observe()
55:46 Andrew's question: equations & causality in a knowledge graph
58:40 Introducing khive (knowledge-hive)
1:01:30 F = ma → Structural Causal Model
1:06:00 Dimensional analysis as a hypergraph
1:10:56 A note is a hyperedge
1:15:17 Querying the graph for what to build next
1:21:25 propose + version control → "build more plugins"
1:22:32 Deterministic scoring + a Lean formal proof
1:24:00 Multi-backend storage & the SPARQL→SQL question
1:31:00 …and the vectors?
1:39:14 Postgres + Row-Level Security
1:41:00 Sparse store + multi-embedding setup
1:44:01 Regorus / OPA — authorization as policy

🔗 Links
lionagi → https://github.com/ohdearquant/lionagi
khive → https://github.com/ohdearquant/khive
Episode notes, transcript & deep-dives → (repo link)
Discord → (invite link)

📌 Lion is an ecosystem for building AGI systems from composable, governed agents — policy kernel → inference engine → orchestration → governance, owned top to bottom. New episode every Saturday.

#AI #AGI #KnowledgeGraph #MultiAgent #LLM #RustLang #AIEngineering #OpenSource #RAG #AgentOrchestration
