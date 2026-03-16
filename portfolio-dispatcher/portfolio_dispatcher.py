"""Portfolio-specific routing layer for the 3-project build sequence.

Sits alongside the shared dispatcher.py without modifying it.
Enforces buildx pipelines (full or lite) with custom model assignments
and escalation paths per the portfolio routing contract.

Routing contract
-----------------
Planning & Architecture  → anthropic/claude-opus-4-6  (full buildx only)
Judge / Architecture     → anthropic/claude-opus-4-6  (full buildx only)
Implementation           → openai-codex/gpt-5.4
Research & long context  → opencode-go/kimi-k2.5  (escalate → opus)
Boilerplate / low-risk   → openai-codex/gpt-5.3-codex-spark (escalate → sonnet)
Testing / adversarial    → opencode-go/glm-5      (escalate → sonnet)
Code review (lite)       → anthropic/claude-sonnet-4-6

Tradeoff protocol
-----------------
Proposals  → anthropic/claude-opus-4-6 + openai-codex/gpt-5.3-codex
Judge      → openai-codex/gpt-5.4
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Iterable


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MODEL_ID_PATTERN = re.compile(r"^[a-z0-9-]+/[a-z0-9.-]+$")
CACHE_RETENTION_VALUES = frozenset({"long", "short"})

_LEGACY_FLAGS = ("--use-claude", "--force-opus", "--no-opus", "--force-claude")

_TRADEOFF_PATTERNS = (
    re.compile(r"\bevaluate\s+tradeoffs?\b", re.IGNORECASE),
    re.compile(
        r"\bcompare\s+(?:approaches?|options?|designs?|architectures?)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bchoose\s+(?:between|among)\b", re.IGNORECASE),
    re.compile(
        r"\bwhich\s+(?:approach|option|design|architecture)\s+(?:is\s+)?better\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bjudge\s+(?:these|the)\s+(?:designs?|architectures?)\b",
        re.IGNORECASE,
    ),
    # --- expanded natural-language triggers ---
    re.compile(
        r"\bwhat\s+(?:architecture|design|approach|option)\s+is\s+better\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bwhich\s+is\s+better\s+for\b", re.IGNORECASE),
    re.compile(r"\bpros\s+and\s+cons\s+of\b", re.IGNORECASE),
    re.compile(r"\bshould\s+I\s+use\s+.+\s+or\s+", re.IGNORECASE),
    re.compile(
        r"\badvantages\s+and\s+disadvantages\b", re.IGNORECASE,
    ),
    re.compile(r"\btradeoffs?\s+(?:of|for|between)\b", re.IGNORECASE),
    re.compile(
        r"\b\w+\s+vs\.?\s+\w+\b", re.IGNORECASE,
    ),
    re.compile(
        r"\bweigh\s+(?:the\s+)?(?:options?|approaches?|designs?)\b",
        re.IGNORECASE,
    ),
)

# Scoped-work patterns that trigger the lighter buildx-lite pipeline
_SCOPED_WORK_PATTERNS = (
    re.compile(r"\b(?:fix|patch|bugfix|hotfix)\b", re.IGNORECASE),
    re.compile(r"\brefactor\b", re.IGNORECASE),
    re.compile(r"\b(?:tweak|adjust|rename)\b", re.IGNORECASE),
    re.compile(r"\badd\s+(?:a\s+)?tests?\b", re.IGNORECASE),
    re.compile(r"\bsmall\s+(?:change|fix|update)\b", re.IGNORECASE),
    re.compile(r"\bminor\s+(?:change|fix|update|tweak)\b", re.IGNORECASE),
    re.compile(r"\bquick\s+(?:fix|change|update|patch)\b", re.IGNORECASE),
    re.compile(r"\bupdate\s+(?:the\s+)?(?:test|doc|readme|config)\b", re.IGNORECASE),
    re.compile(r"\bcleanup\b", re.IGNORECASE),
    re.compile(r"\blint\s+fix", re.IGNORECASE),
)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class PortfolioRoutingError(ValueError):
    """Raised when a portfolio route cannot be constructed safely."""


# ---------------------------------------------------------------------------
# Model catalog (portfolio-specific)
# ---------------------------------------------------------------------------

class Models:
    """Single source of truth for every model used in this portfolio."""

    # Planning & Architecture (reserved for hard decisions)
    OPUS = "anthropic/claude-opus-4-6"

    # Implementation
    GPT54 = "openai-codex/gpt-5.4"

    # Boilerplate / low-risk
    SPARK = "openai-codex/gpt-5.3-codex-spark"

    # Tradeoff proposal partner
    CODEX53 = "openai-codex/gpt-5.3-codex"

    # Research & long context
    KIMI = "opencode-go/kimi-k2.5"

    # Testing / adversarial review
    GLM5 = "opencode-go/glm-5"

    # Mid-tier Anthropic (review, escalation target)
    SONNET = "anthropic/claude-sonnet-4-6"


# ---------------------------------------------------------------------------
# Escalation
# ---------------------------------------------------------------------------

class Complexity(Enum):
    """Complexity signal that drives escalation decisions."""
    STANDARD = auto()
    COMPLEX = auto()


# Escalation map: (base_model) → escalation_model
_ESCALATION_TARGETS = {
    Models.KIMI:  Models.GPT54,    # research → gpt-5.4
    Models.SPARK: Models.SONNET,   # boilerplate → sonnet
    Models.GLM5:  Models.SONNET,   # testing → sonnet
}


def _resolve_model(base: str, complexity: Complexity) -> str:
    """Return the escalated model when complexity is COMPLEX and an
    escalation path exists; otherwise return the base model."""
    if complexity is Complexity.COMPLEX and base in _ESCALATION_TARGETS:
        return _ESCALATION_TARGETS[base]
    return base


# ---------------------------------------------------------------------------
# Data structures (mirror the shared dispatcher shapes)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ModelRun:
    model: str
    cache_retention: str
    role: str


@dataclass(frozen=True)
class PipelineStep:
    name: str
    run: ModelRun
    purpose: str


@dataclass(frozen=True)
class RoutePlan:
    mode: str
    primary: ModelRun | None = None
    parallel: tuple[ModelRun, ...] = ()
    judge: ModelRun | None = None
    pipeline: tuple[PipelineStep, ...] = ()
    reason: str = ""


# ---------------------------------------------------------------------------
# Cache policy
# ---------------------------------------------------------------------------

def _cache_for_model(model: str) -> str:
    _validate_models((model,))
    if model.startswith("openai-codex/"):
        return "long"
    if model.startswith("opencode-go/"):
        return "short"
    if model.startswith("anthropic/"):
        return "short"
    raise PortfolioRoutingError(f"unsupported provider for cache policy: {model}")


def _run(model: str, *, role: str) -> ModelRun:
    retention = _cache_for_model(model)
    return ModelRun(model=model, cache_retention=retention, role=role)


def _step(
    name: str,
    model: str,
    purpose: str,
    complexity: Complexity = Complexity.STANDARD,
) -> PipelineStep:
    resolved = _resolve_model(model, complexity)
    return PipelineStep(name=name, run=_run(resolved, role=name), purpose=purpose)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _validate_models(models: Iterable[str]) -> None:
    invalid = [m for m in models if not MODEL_ID_PATTERN.match(m)]
    if invalid:
        raise PortfolioRoutingError(
            "invalid model id format: " + ", ".join(invalid)
        )


def _reject_legacy_flags(prompt: str) -> None:
    found = [f for f in _LEGACY_FLAGS if f in prompt]
    if found:
        raise PortfolioRoutingError(
            "unsupported flags in portfolio mode: " + ", ".join(found)
        )


def _is_tradeoff_request(prompt: str) -> bool:
    return any(p.search(prompt) for p in _TRADEOFF_PATTERNS)


def _is_scoped_work(prompt: str) -> bool:
    """Detect scoped implementation, bugfix, or refactor prompts
    that don't need the full 12-step buildx pipeline."""
    return any(p.search(prompt) for p in _SCOPED_WORK_PATTERNS)


# ---------------------------------------------------------------------------
# Step-complexity hints
# ---------------------------------------------------------------------------

@dataclass
class StepComplexityHints:
    """Per-step complexity overrides.

    Any step name listed here with COMPLEX will trigger escalation
    for models that have an escalation path defined.
    """
    overrides: dict[str, Complexity] = field(default_factory=dict)

    def get(self, step_name: str) -> Complexity:
        return self.overrides.get(step_name, Complexity.STANDARD)


# ---------------------------------------------------------------------------
# Portfolio Router
# ---------------------------------------------------------------------------

class PortfolioRouter:
    """Buildx router for the 3-project portfolio sequence.

    Prompts are classified into three routes:
    - **tradeoff** — parallel proposals + judge (architecture decisions)
    - **buildx** — full 12-step pipeline (greenfield features, major work)
    - **buildx-lite** — lean 7-step pipeline (bugfixes, refactors, scoped changes)

    Call ``route()`` for every prompt.  The caller never needs to
    decide which codepath to take.
    """

    def __init__(
        self,
        hints: StepComplexityHints | None = None,
        *,
        force_full: bool = False,
    ) -> None:
        self._hints = hints or StepComplexityHints()
        self._force_full = force_full

    # -- public entry point -------------------------------------------------

    def route(self, prompt: str) -> RoutePlan:
        if not prompt or not prompt.strip():
            raise PortfolioRoutingError("prompt must not be empty")

        _reject_legacy_flags(prompt)

        # Tradeoff requests get a dedicated protocol.
        if _is_tradeoff_request(prompt):
            return self._tradeoff_route()

        # Scoped work gets the lite pipeline (unless force_full).
        if not self._force_full and _is_scoped_work(prompt):
            return self._buildx_lite_pipeline()

        # Everything else goes through the full buildx pipeline.
        return self._buildx_pipeline()

    # -- tradeoff -----------------------------------------------------------

    def _tradeoff_route(self) -> RoutePlan:
        parallel = (
            _run(Models.CODEX53, role="proposal"),
            _run(Models.GLM5, role="proposal"),
        )
        return RoutePlan(
            mode="tradeoff",
            parallel=parallel,
            judge=_run(Models.GPT54, role="judge"),
            reason=(
                "portfolio tradeoff: gpt-5.3-codex + glm-5 proposals, "
                "judged by gpt-5.4"
            ),
        )

    # -- buildx pipeline (full 12-step) ------------------------------------

    def _buildx_pipeline(self) -> RoutePlan:
        h = self._hints.get  # shorthand

        steps = (
            # 1-2: parallel planning — opus leads, gpt-5.4 challenges
            _step(
                "parallel-plan-a", Models.KIMI,
                "produce architecture and implementation outline",
            ),
            _step(
                "parallel-plan-b", Models.GPT54,
                "challenge assumptions with an alternate plan",
            ),

            # 3: judge — opus decides architecture
            _step(
                "judge-plan", Models.OPUS,
                "choose architecture; emit blueprint, risks, and review checklist",
            ),

            # 4: boilerplate — spark, escalate to sonnet if complex
            _step(
                "boilerplate", Models.SPARK,
                "scaffold files and repetitive structure",
                complexity=h("boilerplate"),
            ),

            # 5: implement — gpt-5.4
            _step(
                "implement", Models.GPT54,
                "build main functionality",
            ),

            # 6: test — glm-5, escalate to sonnet if complex
            _step(
                "test", Models.GLM5,
                "validate correctness and edge cases",
                complexity=h("test"),
            ),

            # 7: simplify — gpt-5.4 (implementation-grade code review)
            _step(
                "simplify", Models.GPT54,
                "remove unnecessary complexity and duplication",
            ),

            # 8: retest — glm-5, escalate to sonnet if complex
            _step(
                "retest", Models.GLM5,
                "verify simplified result preserves behavior",
                complexity=h("retest"),
            ),

            # 9: first review — sonnet (code-level review)
            _step(
                "review-resolve-a", Models.SONNET,
                "perform first PR-style review and fix pass",
            ),

            # 10: test after first review — glm-5
            _step(
                "test-a", Models.GLM5,
                "test after first review resolution",
                complexity=h("test-a"),
            ),

            # 11: second wide-context review — kimi, escalate to gpt-5.4
            _step(
                "review-resolve-b", Models.KIMI,
                "perform second wide-context review and fix pass",
                complexity=h("review-resolve-b"),
            ),

            # 12: final test — glm-5, escalate to sonnet if complex
            _step(
                "final-test", Models.GLM5,
                "run final correctness check",
                complexity=h("final-test"),
            ),
        )

        return RoutePlan(
            mode="buildx",
            pipeline=steps,
            reason="portfolio buildx pipeline with custom routing and escalation paths",
        )

    # -- buildx-lite pipeline (7-step, no Opus) ----------------------------

    def _buildx_lite_pipeline(self) -> RoutePlan:
        h = self._hints.get

        steps = (
            # 1: plan — gpt-5.4 (no dual-plan needed for scoped work)
            _step(
                "plan", Models.GPT54,
                "plan scoped change and identify affected files",
            ),

            # 2: implement — gpt-5.4
            _step(
                "implement", Models.GPT54,
                "implement the change",
            ),

            # 3: test — glm-5
            _step(
                "test", Models.GLM5,
                "validate correctness",
                complexity=h("test"),
            ),

            # 4: simplify — gpt-5.4
            _step(
                "simplify", Models.GPT54,
                "remove unnecessary complexity",
            ),

            # 5: retest — glm-5
            _step(
                "retest", Models.GLM5,
                "verify simplified result",
                complexity=h("retest"),
            ),

            # 6: review — sonnet (no Opus for scoped work)
            _step(
                "review", Models.SONNET,
                "code review and fix pass",
            ),

            # 7: final-test — glm-5
            _step(
                "final-test", Models.GLM5,
                "final correctness check",
                complexity=h("final-test"),
            ),
        )

        return RoutePlan(
            mode="buildx-lite",
            pipeline=steps,
            reason="portfolio buildx-lite pipeline for scoped work (no Opus)",
        )


# ---------------------------------------------------------------------------
# Convenience constructors
# ---------------------------------------------------------------------------

def default_router() -> PortfolioRouter:
    """Router with no complexity overrides (all steps at STANDARD)."""
    return PortfolioRouter()


def full_router(**step_overrides: Complexity) -> PortfolioRouter:
    """Router that always uses the full 12-step pipeline,
    even for scoped work. Accepts per-step complexity overrides."""
    return PortfolioRouter(
        hints=StepComplexityHints(overrides=step_overrides),
        force_full=True,
    )


def escalated_router(**step_overrides: Complexity) -> PortfolioRouter:
    """Router with explicit complexity flags per step name.

    Example::

        router = escalated_router(
            test=Complexity.COMPLEX,
            boilerplate=Complexity.COMPLEX,
        )
    """
    return PortfolioRouter(hints=StepComplexityHints(overrides=step_overrides))

