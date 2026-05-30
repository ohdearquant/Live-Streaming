# Copyright (c) 2023-2026, HaiyangLi <quantocean.li at gmail dot com>
# SPDX-License-Identifier: Apache-2.0

"""Reactive capability bus — live demo.

A claude_code/sonnet *explorer* reads part of the codebase and, *as it goes*,
emits typed capabilities inline in its normal text (```json blocks): a
``Finding`` it has verified, a ``Hypothesis`` it still needs to test, or a
``Correction`` retracting an earlier claim. We don't wait for the run to finish:
session observers fire the instant each signal streams in, so we react in real
time — log it, score it, or spawn a deeper investigation.

Each confirmed Finding fans out to two more branches on the *same* session:
a *researcher* that cross-checks it against the literature (emitting
``Hypothesis``), and a *critic* that challenges it (emitting ``Correction`` when
it disagrees). Those signals ride the bus back into terminal observers that
maintain a shared knowledge base — the branch→session loop closed across
branches.

Non-recursion invariant: only the ``Finding`` observers spawn sub-branches, and
those sub-branches are granted *non-``Finding``* capabilities (researcher →
``hypothesis``, critic → ``correction``). The ``Hypothesis``/``Correction``
observers only do bookkeeping and spawn nothing. No capability path leads back
to ``Finding``, so the reaction graph is a depth-1 DAG and cannot cycle — the
one and only source of Findings is the single top-level ``explorer.run()``.

Contrast with before: either we sat idle while the model ran, or we had to give
it a dedicated tool to call. Now any text response can carry typed signals and
the agentic loop keeps going uninterrupted.

Run::

    uv run python examples/capability_bus_demo.py
"""

from __future__ import annotations

import asyncio
from typing import Literal

from pydantic import BaseModel, Field

import lionagi as li
from lionagi.ln.types import Operable, Spec
from lionagi.session import Session


class Finding(BaseModel):
    """A single, concrete observation the agent emits *while* reading code.

    This is the typed capability raised onto the reactive bus: every field is a
    signal a downstream observer can branch on, so each ``Finding`` is scoped to
    stand alone — a handler should be able to act on it without re-reading the
    source. Emit one the moment you understand something, not in a batch at the
    end.
    """

    claim: str = Field(
        description=(
            "One specific, verifiable fact about the code, stated as an "
            "assertion (not a question or a TODO). Scope it to a single "
            "behavior — e.g. 'emit() stores the event in the Flow before "
            "dispatching to handlers', not 'the observer does a lot of things'."
        ),
    )
    category: Literal["mechanism", "contract", "edge_case", "risk"] = Field(
        default="mechanism",
        description=(
            "What kind of claim this is: 'mechanism' (how it works), "
            "'contract' (an invariant callers rely on), 'edge_case' (a boundary "
            "or failure behavior), or 'risk' (a smell or latent bug)."
        ),
    )
    file: str = Field(
        default="",
        description=(
            "Where the claim was observed, as 'path:symbol' or 'path:line' when "
            "known (e.g. 'lionagi/session/observer.py:emit'). Leave empty only "
            "when the claim genuinely spans files."
        ),
    )
    evidence: str = Field(
        default="",
        description=(
            "The concrete detail backing the claim — a short quoted line, a "
            "signature, or a control-flow note. A follow-up investigation "
            "reasons over this, so prefer specifics over paraphrase."
        ),
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description=(
            "Calibrated certainty in the claim, 0-1. Use <0.6 when it is "
            "inferred or unverified, >=0.8 only when the cited evidence is "
            "conclusive. Downstream handlers gate expensive work on this value."
        ),
    )


class Hypothesis(BaseModel):
    """A testable conjecture the agent holds but has *not* yet confirmed.

    The counterpart to ``Finding``: where a Finding asserts something seen,
    a Hypothesis names a belief that still needs evidence — and, crucially,
    states how to settle it, so a reader knows the next concrete step.
    """

    claim: str = Field(
        description=(
            "The conjecture, phrased so it could be proven true or false — "
            "e.g. 'handlers run sequentially, so a slow one blocks the stream', "
            "not 'the dispatch might be slow'."
        ),
    )
    reasoning: str = Field(
        description=(
            "Why you suspect this, citing what you have read so far. Make the "
            "inference explicit rather than asserting a hunch."
        ),
    )
    test: str = Field(
        default="",
        description=(
            "The concrete check that would confirm or refute the claim — a file "
            "or function to read, an experiment to run, or an output to observe."
        ),
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Calibrated prior that the hypothesis is correct, 0-1.",
    )


class Correction(BaseModel):
    """A retraction of an earlier ``Finding`` the agent now believes is wrong.

    Emitting this keeps the bus self-correcting: rather than silently dropping a
    bad claim, the agent publishes the disagreement *and* the replacement, so an
    observer can supersede the original on the record.
    """

    claim: str = Field(
        description=(
            "The earlier claim now believed wrong, quoted closely enough that a "
            "reader can match it to the original Finding."
        ),
    )
    reason: str = Field(
        description=("Why it is wrong, citing the specific code or evidence that contradicts it."),
    )
    corrected: str = Field(
        default="",
        description=(
            "The accurate statement that should replace the retracted claim. A "
            "correction without the fix is incomplete."
        ),
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Calibrated certainty that the correction is right, 0-1.",
    )


class ResearchReport(BaseModel):
    """The result of digging deeper into a high-confidence ``Finding``.

    Produced by a follow-up agent that cross-checks the claim against external
    literature, so the verdict and its confidence — not just the prose — are
    what a caller acts on.
    """

    summary: str = Field(
        description=(
            "A concise synthesis (2-4 sentences) of what the deeper "
            "investigation established, written to stand on its own without the "
            "original claim in front of the reader."
        ),
    )
    verdict: Literal["supports", "refutes", "mixed", "inconclusive"] = Field(
        default="inconclusive",
        description=(
            "Whether the gathered research 'supports' the finding, 'refutes' "
            "it, is 'mixed', or is 'inconclusive' (no decisive evidence found)."
        ),
    )
    related_papers: list[str] = Field(
        default_factory=list,
        description=(
            "Academic papers or authoritative sources consulted, each a citable "
            "reference (title — author/venue/year, or a URL). Empty if none "
            "were relevant."
        ),
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Calibrated certainty in the verdict above, 0-1.",
    )


# Named Specs: the Spec name is the key the model uses in its ```json block,
# e.g. {"finding": {...}}. Defined once and reused across every branch's grant.
finding = Spec(Finding, name="finding")
hypothesis = Spec(Hypothesis, name="hypothesis")
correction = Spec(Correction, name="correction")


# Global hard cap on the operations we launch reactively. The fan-out (one
# researcher + one critic per confident Finding) grows with what the explorer
# emits; this bounds the total spend regardless. The single explorer.run() that
# seeds everything is the driver, not a launched op, so it is not counted.
MAX_OPERATIONS = 10


class OperationBudget:
    """Async-safe global allowance for reactively launched operations.

    ``take()`` claims one unit and returns True, or returns False once the
    budget is spent — callers skip their launch and log instead. The lock keeps
    the count exact even if observer dispatch runs handlers concurrently.
    """

    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.launched = 0
        self._lock = asyncio.Lock()

    async def take(self) -> bool:
        async with self._lock:
            if self.launched >= self.limit:
                return False
            self.launched += 1
            return True


async def main() -> None:
    session = Session()

    # Global ceiling: at most MAX_OPERATIONS researcher/critic launches total,
    # shared across every observer firing this run.
    budget = OperationBudget(MAX_OPERATIONS)

    # The explorer reads the code and emits typed signals inline as it goes.
    # It holds all three capabilities — it is the only branch allowed to raise
    # a Finding, which is what keeps the reactive fan-out below bounded.
    explorer = session.default_branch
    explorer.chat_model = li.iModel(provider="claude_code", model="sonnet")
    explorer.grant_capabilities(Operable((finding, hypothesis, correction), name="Caps"))

    # A researcher digs into a confirmed finding and returns a structured
    # ResearchReport. It may raise hypotheses of its own — but NOT findings,
    # so its emissions can't re-trigger dig_deeper.
    def create_researcher_branch():
        researcher = session.new_branch(
            system=(
                "You dig deeper into findings about the codebase, looking up "
                "related academic papers to support or argue against them."
            ),
            chat_model=li.iModel(provider="claude_code", model="sonnet"),
        )
        researcher.grant_capabilities(Operable((hypothesis,), name="Caps"))
        return researcher

    # A critic challenges a finding and, when it disagrees, emits a Correction
    # that supersedes it. The correction flows back onto the same session bus
    # into note_correction — branch → session observer, the loop closed across
    # branches. Granted only `correction`, so it cannot spawn more findings.
    def create_critic_branch():
        critic = session.new_branch(
            system=(
                "You are a critical reviewer who pressure-tests claims about "
                "the codebase. When a claim is wrong or imprecise you emit a "
                "correction stating the accurate version; when it holds up you "
                "say so and emit nothing."
            ),
            chat_model=li.iModel(provider="claude_code", model="sonnet"),
        )
        critic.grant_capabilities(Operable((correction,), name="Caps"))
        return critic

    # -- Shared knowledge base the observers maintain in real time -----------
    # The single source of truth the reactive handlers read and mutate, keyed
    # by a normalized claim. Findings populate it; Corrections supersede entries
    # in place (the bus self-correcting); Hypotheses are logged as open
    # questions. Inspect it at the end to see the settled result.
    kb: dict[str, dict] = {}

    def kb_key(claim: str) -> str:
        return " ".join(claim.lower().split())[:80]

    def kb_match(claim: str) -> str | None:
        """Best-effort match of a claim back to an existing KB entry.

        The critic won't quote a Finding verbatim, so fall back to loose
        containment either direction. Robust to dispatch ordering — a
        Correction that arrives before its Finding is just recorded standalone.
        """
        key = kb_key(claim)
        if key in kb:
            return key
        for existing in kb:
            if existing in key or key in existing:
                return existing
        return None

    # -- Observers: independent reactors, one or more per capability type -----
    #
    # Non-recursion invariant (see module docstring): only the Finding
    # observers below spawn sub-branches, and those sub-branches are granted
    # non-Finding capabilities. The Hypothesis/Correction observers only mutate
    # `kb` and spawn nothing, so no reaction can loop back to a new Finding.

    # Two observers subscribe to Finding; both react to every Finding the
    # explorer emits. dig_deeper researches it; challenge attacks it.
    @session.observe(Finding)
    async def dig_deeper(finding: Finding, _session: Session) -> None:
        print(f"\n  ⚡ FINDING [{finding.category}] (conf={finding.confidence}): {finding.claim}")
        if finding.file:
            print(f"     ↳ {finding.file}")
        if finding.confidence < 0.6:
            print("     → low confidence; recorded unverified, skipping research")
            kb[kb_key(finding.claim)] = {
                "claim": finding.claim,
                "status": "unverified",
                "verdict": "—",
            }
            return

        if not await budget.take():
            print("     → operation budget exhausted; skipping research")
            return

        researcher = create_researcher_branch()
        report = await researcher.operate(
            instruct={
                "instruction": (
                    "Dig deeper into this finding. Cross-check it against "
                    "related academic papers that support or argue against its "
                    "validity, then return a concise summary and an explicit "
                    "verdict."
                ),
                "context": {"finding": finding.model_dump_json()},
            },
            response_format=ResearchReport,
        )
        print(
            f"     → research verdict={report.verdict} (conf={report.confidence}): {report.summary}"
        )
        if report.related_papers:
            print(f"       related papers: {report.related_papers}")
        kb[kb_key(finding.claim)] = {
            "claim": finding.claim,
            "status": "researched",
            "verdict": report.verdict,
        }

    @session.observe(Finding)
    async def challenge(finding: Finding, _session: Session) -> None:
        # Only worth challenging claims the explorer is confident about.
        if finding.confidence < 0.6:
            return
        if not await budget.take():
            print("     → operation budget exhausted; skipping critique")
            return
        critic = create_critic_branch()
        # The critic's Correction (if any) is emitted inline and rides the bus
        # back to note_correction; we don't need its return value here.
        await critic.operate(
            instruct={
                "instruction": (
                    "Challenge this finding. If it is wrong or imprecise, emit "
                    "a `correction` signal that quotes the claim, says why it "
                    "is wrong, and gives the corrected statement. If the "
                    "finding holds up, emit nothing."
                ),
                "context": {"finding": finding.model_dump_json()},
            },
        )

    @session.observe(Hypothesis)
    async def note_hypothesis(hyp: Hypothesis, _session: Session) -> None:
        # Terminal: log the open question into the KB. Never re-emitted as a
        # Finding, so this closes the branch of the reaction graph.
        print(f"\n  ❓ HYPOTHESIS (conf={hyp.confidence}): {hyp.claim}")
        if hyp.test:
            print(f"     → test: {hyp.test}")
        kb[kb_key(hyp.claim)] = {
            "claim": hyp.claim,
            "status": "open_question",
            "verdict": "untested",
        }

    @session.observe(Correction)
    async def note_correction(corr: Correction, _session: Session) -> None:
        # Terminal: supersede the matching finding in place — this is the bus
        # self-correcting its own knowledge base — else record it standalone.
        print(f"\n  ✏️  CORRECTION (conf={corr.confidence}): {corr.claim}")
        print(f"     → reason: {corr.reason}")
        if corr.corrected:
            print(f"     → corrected: {corr.corrected}")
        target = kb_match(corr.claim)
        if target is not None:
            kb[target].update(
                status="superseded",
                verdict="refuted by critic",
                corrected=corr.corrected,
            )
            print(f"     → superseded KB entry: {kb[target]['claim'][:60]}")
        else:
            kb[kb_key(corr.claim)] = {
                "claim": corr.claim,
                "status": "correction",
                "verdict": "standalone",
                "corrected": corr.corrected,
            }
            print("     → no matching finding; recorded standalone")

    # -- Drive the explorer; signals fire live as it reads --------------------
    prompt = (
        "Read lionagi/session/signal.py and lionagi/session/observer.py. "
        "As you go, emit typed signals inline as ```json blocks the instant you "
        "have something to say — then keep reading. You have three "
        "capabilities:\n"
        '  • finding   — a fact you have verified, e.g. {"finding": {"claim": '
        '"...", "category": "mechanism", "file": "observer.py:emit", '
        '"evidence": "...", "confidence": 0.8}}\n'
        '  • hypothesis — a belief you still need to test, e.g. {"hypothesis": '
        '{"claim": "...", "reasoning": "...", "test": "...", "confidence": '
        "0.4}}\n"
        '  • correction — retract an earlier claim, e.g. {"correction": '
        '{"claim": "...", "reason": "...", "corrected": "..."}}\n'
        "Emit 3-5 findings (plus any hypotheses/corrections that come up), then "
        "give a one-line summary."
    )

    print("=== streaming claude_code/sonnet (signals fire live) ===")
    async for _msg in explorer.run(prompt):
        pass  # signals fire via the observers above; nothing to do per message

    print("\n=== done ===")
    obs = session.observer
    print(
        f"bus recorded {len(obs.by_type(Finding))} findings, "
        f"{len(obs.by_type(Hypothesis))} hypotheses, "
        f"{len(obs.by_type(Correction))} corrections"
    )
    print(f"launched {budget.launched}/{budget.limit} operations")
    print(f"\nknowledge base — {len(kb)} entries after self-correction:")
    for rec in kb.values():
        print(f"  • [{rec['status']:>12}] {rec['claim'][:64]}")


if __name__ == "__main__":
    asyncio.run(main())
