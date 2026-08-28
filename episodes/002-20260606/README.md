# Lion Saturday Live — Episode 02: Why Your AI Agent Forgets Everything

> Most AI agents start every conversation from zero. Here's how to give them real memory — and why what you remember matters more than how you store it.

|                 |                          |
| --------------- | ------------------------ |
| Date     | 2026-06-06               |
| Host     | Ocean (Haiyang Li)       |
| Guest(s) | _open Q&A_               |
| Video    | [Watch on YouTube](TBD)  |
| Runtime  | ~45 min                  |
| Topics   | agent-memory · recall · episodic-vs-semantic · decay · brain-profiles |

## Episode Notes (presenter reference)

### Opening hook (2 min)

"Every time you start a new Claude session, it doesn't know who you are. You explain the same
context, the same preferences, the same project structure — every single time. Your AI has
amnesia. Today I'm going to show you how I fixed that, and what I learned about what's actually
worth remembering."

- Show: start a bare Claude Code session, it knows nothing
- Show: start a Leo session, it loads identity + recalls context from weeks ago
- "That difference is memory. Let's build it."

---

### Part 1: The three kinds of agent memory (8 min)

**Frame**: human memory isn't one thing. Neither is agent memory.

| Type | What it stores | Decays? | Example |
|------|---------------|---------|---------|
| **Episodic** | What happened — events, sessions, decisions | Yes (fast) | "Last Tuesday we debugged the auth middleware" |
| **Semantic** | What's true — facts, patterns, preferences | Slow | "Ocean prefers short responses, no emojis" |
| **Procedural** | How to behave — corrections, learned behaviors | No | "Never use Opus 4.7 — it fabricates evidence" |

**Key insight**: most "AI memory" products just do semantic (RAG over past conversations).
That's the least interesting kind. The corrections (procedural) are where the real value compounds.

**Show**: the memory directory structure
```
~/.claude/projects/.../memory/
├── MEMORY.md          # index (loaded every session)
├── user_*.md          # who Ocean is
├── feedback_*.md      # corrections — the gold
├── project_*.md       # what's happening
└── reference_*.md     # where to find things
```

**Talk through**: why feedback memories are the most valuable — each one prevents a class of
future mistakes. Show a real example: `feedback_read_profile_before_forms.md` — the 4.8
incident where the model applied to 30 jobs with hallucinated contact info. That correction
now prevents it from ever happening again.

---

### Part 2: What to remember (and what not to) (8 min)

**Frame**: "The hard part isn't storing memories. It's deciding what's worth storing."

**What TO save**:
- Corrections ("don't do X because Y happened")
- User preferences that aren't obvious from code
- Project context that isn't in git history
- Relationship context (who is this person, what's the history)

**What NOT to save**:
- Code patterns (read the code — it's the source of truth)
- Git history (git log exists)
- Architecture decisions (they're in ADRs/commits)
- Anything that rots faster than you'll re-read it

**The rot problem**: a memory that says "auth is in src/auth.rs" is correct today and wrong
next month. Code-referencing memories are a trap — they feel useful but become landmines.

**Show**: the actual exclusion list from the memory system instructions

**Key quote**: "A memory that names a specific function or file is a claim that it existed
*when the memory was written*. It may have been renamed, removed, or never merged."

---

### Part 3: Recall — when and how to retrieve (8 min)

**Frame**: memory without recall is a write-only database.

**Trigger-based recall** (not "search everything every time"):
- Session start → load recent context
- Person mentioned → recall relationship history  
- Topic revisited → recall last decision
- Major decision → recall similar past outcomes

**Show**: the recall trigger table from KHIVE.md
**Show**: a live `memory.recall(query="...")` call — what comes back, how it's ranked

**Salience + decay**: not all memories are equal
- Salience: how important was this when stored (0-1)
- Decay: how fast does it lose relevance
- Corrections (high salience, no decay) vs session notes (medium salience, fast decay)

**The anti-pattern**: "I have context loaded" when you haven't actually recalled anything.
The model THINKS it knows because the memory file names are in context. But file names ≠
content. You have to actually read them.

---

### Part 4: Live demo — memory in action (12 min)

**Show the full loop**:

1. Start a fresh Leo session (`/leo-start`)
2. Watch identity load via hook (not manual Read)
3. Watch memory recall for recent session context
4. Do a real task — something that requires remembering a prior decision
5. Show what happens when memory catches a mistake before it happens
6. Store a new memory from this session

**Narrate**: "This isn't magic. It's a file system, a recall function, and a set of rules
about when to use them. The magic is in the rules — knowing when to remember and when to
look at the actual code instead."

---

### Part 5: Where this goes — self-adaptive memory (5 min)

**Tease the next evolution**:

- Current: explicit memory (I tell it what to remember)
- Next: brain profiles — Bayesian priors that update from feedback
- The model learns your preferences implicitly, not just from corrections
- Drift detection: when the brain's model of you diverges from reality
- "Small models steering big models" — the brain as a lightweight routing layer

"That's a whole episode on its own. For now — the system I showed you today is running in
production, it's been running for months, and it genuinely makes the AI better at its job
over time. The corrections compound. That's the whole point."

---

### Closing (2 min)

- Recap: three types of memory, what to save vs not, trigger-based recall, the rot problem
- "The takeaway: don't try to remember everything. Remember corrections. They compound."
- Point to GitHub repos (lionagi, khive) if people want to dig in
- Next episode tease: "small models steering big models"

---

## Technical setup

- Screen share: terminal (Claude Code) + VS Code for file browsing
- Have ready:
  - Fresh CC session (no memory) for before/after
  - Leo session for live demo
  - Memory directory open in VS Code
  - A task that triggers recall (something from a prior session)

## Talking points if Q&A comes up

- "Isn't this just RAG?" — No. RAG retrieves documents. This retrieves corrections and
  behavioral rules. The memory shapes how the agent BEHAVES, not what it KNOWS.
- "Why not use a vector database?" — You could. But for personal agent memory, flat files
  with good naming beat a vector DB. You want to READ your memories, not just embed them.
- "How much memory is too much?" — MEMORY.md index has a 200-line cap. If you're past that,
  you're storing too much. Prune ruthlessly.
- "Does this work with other models?" — The memory system is model-agnostic. The recall
  quality depends on the model, but the architecture works with anything.
