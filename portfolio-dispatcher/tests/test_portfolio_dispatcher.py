"""Tests for portfolio_dispatcher.py

Covers:
- buildx full pipeline structure and model assignments
- buildx-lite pipeline for scoped work
- tradeoff protocol routing (including expanded natural-language triggers)
- escalation paths for all escalatable steps
- cache retention correctness
- legacy flag rejection
- empty prompt rejection
- Opus containment (Opus only in full-buildx planning/tradeoff, never in lite)
- force_full override
- policy-fit: scoped prompts → lite, greenfield prompts → full
"""

import pytest

from portfolio_dispatcher import (
    Complexity,
    Models,
    PortfolioRouter,
    PortfolioRoutingError,
    StepComplexityHints,
    default_router,
    escalated_router,
    full_router,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def router():
    return default_router()


# ---------------------------------------------------------------------------
# Buildx full pipeline structure
# ---------------------------------------------------------------------------

class TestBuildxPipeline:

    def test_mode_is_buildx(self, router):
        plan = router.route("implement the auth module for the finance project")
        assert plan.mode == "buildx"

    def test_pipeline_has_12_steps(self, router):
        plan = router.route("build the complete data ingestion pipeline")
        assert len(plan.pipeline) == 12

    def test_step_names_match_buildx_spec(self, router):
        plan = router.route("build the complete data ingestion pipeline")
        names = [s.name for s in plan.pipeline]
        assert names == [
            "parallel-plan-a",
            "parallel-plan-b",
            "judge-plan",
            "boilerplate",
            "implement",
            "test",
            "simplify",
            "retest",
            "review-resolve-a",
            "test-a",
            "review-resolve-b",
            "final-test",
        ]

    def test_no_primary_or_judge_on_buildx(self, router):
        plan = router.route("build the complete data ingestion pipeline")
        assert plan.primary is None
        assert plan.judge is None


# ---------------------------------------------------------------------------
# Model assignments at STANDARD complexity (full pipeline)
# ---------------------------------------------------------------------------

class TestStandardModelAssignments:

    def _model_map(self, router):
        plan = router.route("scaffold the entire project from scratch")
        return {s.name: s.run.model for s in plan.pipeline}

    def test_planning_uses_correct_models(self, router):
        m = self._model_map(router)
        assert m["parallel-plan-a"] == Models.KIMI
        assert m["judge-plan"] == Models.OPUS

    def test_alternate_plan_uses_gpt54(self, router):
        m = self._model_map(router)
        assert m["parallel-plan-b"] == Models.GPT54

    def test_implementation_uses_gpt54(self, router):
        m = self._model_map(router)
        assert m["implement"] == Models.GPT54

    def test_simplify_uses_gpt54(self, router):
        m = self._model_map(router)
        assert m["simplify"] == Models.GPT54

    def test_boilerplate_uses_spark(self, router):
        m = self._model_map(router)
        assert m["boilerplate"] == Models.SPARK

    def test_testing_steps_use_glm5(self, router):
        m = self._model_map(router)
        for step in ("test", "retest", "test-a", "final-test"):
            assert m[step] == Models.GLM5, f"{step} should use glm-5"

    def test_review_resolve_a_uses_sonnet(self, router):
        """First review step now uses Sonnet (not Opus) to reduce Opus usage."""
        m = self._model_map(router)
        assert m["review-resolve-a"] == Models.SONNET

    def test_review_resolve_b_uses_kimi(self, router):
        m = self._model_map(router)
        assert m["review-resolve-b"] == Models.KIMI


# ---------------------------------------------------------------------------
# Buildx-lite pipeline (scoped work)
# ---------------------------------------------------------------------------

class TestBuildxLite:

    def test_mode_is_buildx_lite(self, router):
        plan = router.route("fix the broken test in auth module")
        assert plan.mode == "buildx-lite"

    def test_lite_pipeline_has_7_steps(self, router):
        plan = router.route("refactor the data loader")
        assert len(plan.pipeline) == 7

    def test_lite_step_names(self, router):
        plan = router.route("fix the broken import")
        names = [s.name for s in plan.pipeline]
        assert names == [
            "plan",
            "implement",
            "test",
            "simplify",
            "retest",
            "review",
            "final-test",
        ]

    def test_lite_has_no_opus(self, router):
        """Scoped work should never invoke Opus."""
        plan = router.route("quick fix for the config parser")
        for step in plan.pipeline:
            assert step.run.model != Models.OPUS, (
                f"Opus found in lite step {step.name}"
            )

    def test_lite_review_uses_sonnet(self, router):
        plan = router.route("refactor the validation logic")
        review = next(s for s in plan.pipeline if s.name == "review")
        assert review.run.model == Models.SONNET

    def test_lite_plan_uses_gpt54(self, router):
        plan = router.route("fix the broken test")
        plan_step = next(s for s in plan.pipeline if s.name == "plan")
        assert plan_step.run.model == Models.GPT54


class TestScopedWorkTriggers:
    """Verify scoped-work patterns route to buildx-lite."""

    SCOPED_PROMPTS = [
        "fix the broken test in auth module",
        "patch the null pointer in data loader",
        "bugfix: handle empty response from API",
        "hotfix for the login crash",
        "refactor the data loader to use async",
        "tweak the error message formatting",
        "adjust the retry backoff timing",
        "rename the user_data variable to patient_data",
        "add a test for the edge case in parser",
        "add tests for the new validation rules",
        "small change to the config defaults",
        "minor fix for the date parsing",
        "minor update to the README",
        "quick fix for the import error",
        "quick patch for the null check",
        "update the test fixtures",
        "update the config to use new API endpoint",
        "update the readme with new instructions",
        "cleanup the unused imports",
        "lint fix for the healthcare module",
    ]

    @pytest.mark.parametrize("prompt", SCOPED_PROMPTS)
    def test_scoped_prompt_routes_to_lite(self, prompt):
        router = default_router()
        plan = router.route(prompt)
        assert plan.mode == "buildx-lite", (
            f"expected buildx-lite for: {prompt!r}, got {plan.mode}"
        )


class TestGreenfieldPrompts:
    """Verify greenfield / major prompts still route to full buildx."""

    FULL_PROMPTS = [
        "build the complete data ingestion pipeline",
        "scaffold the entire project from scratch",
        "design and implement the authentication system",
        "create the ML prediction service end to end",
        "implement the full dashboard with charts and filters",
        "set up the CI/CD pipeline and deployment config",
    ]

    @pytest.mark.parametrize("prompt", FULL_PROMPTS)
    def test_greenfield_prompt_routes_to_full(self, prompt):
        router = default_router()
        plan = router.route(prompt)
        assert plan.mode == "buildx", (
            f"expected buildx for: {prompt!r}, got {plan.mode}"
        )


# ---------------------------------------------------------------------------
# force_full override
# ---------------------------------------------------------------------------

class TestForceFullRouter:

    def test_force_full_overrides_scoped_detection(self):
        r = full_router()
        plan = r.route("fix the broken test")
        assert plan.mode == "buildx"
        assert len(plan.pipeline) == 12

    def test_force_full_with_escalation(self):
        r = full_router(test=Complexity.COMPLEX)
        plan = r.route("refactor the loader")
        assert plan.mode == "buildx"
        m = {s.name: s.run.model for s in plan.pipeline}
        assert m["test"] == Models.SONNET


# ---------------------------------------------------------------------------
# Escalation paths
# ---------------------------------------------------------------------------

class TestEscalation:

    def test_boilerplate_escalates_to_sonnet(self):
        r = escalated_router(boilerplate=Complexity.COMPLEX)
        plan = r.route("build the scaffold from scratch")
        m = {s.name: s.run.model for s in plan.pipeline}
        assert m["boilerplate"] == Models.SONNET

    def test_test_escalates_to_sonnet(self):
        r = escalated_router(test=Complexity.COMPLEX)
        plan = r.route("build the entire system")
        m = {s.name: s.run.model for s in plan.pipeline}
        assert m["test"] == Models.SONNET

    def test_retest_escalates_to_sonnet(self):
        r = escalated_router(retest=Complexity.COMPLEX)
        plan = r.route("build the entire module")
        m = {s.name: s.run.model for s in plan.pipeline}
        assert m["retest"] == Models.SONNET

    def test_test_a_escalates_to_sonnet(self):
        r = escalated_router(**{"test-a": Complexity.COMPLEX})
        plan = r.route("build the whole thing")
        m = {s.name: s.run.model for s in plan.pipeline}
        assert m["test-a"] == Models.SONNET

    def test_final_test_escalates_to_sonnet(self):
        r = escalated_router(**{"final-test": Complexity.COMPLEX})
        plan = r.route("build the whole thing")
        m = {s.name: s.run.model for s in plan.pipeline}
        assert m["final-test"] == Models.SONNET

    def test_review_resolve_b_escalates_to_gpt54(self):
        r = escalated_router(**{"review-resolve-b": Complexity.COMPLEX})
        plan = r.route("build the whole thing")
        m = {s.name: s.run.model for s in plan.pipeline}
        assert m["review-resolve-b"] == Models.GPT54

    def test_non_escalatable_steps_unchanged(self):
        """Steps without escalation paths stay on their base model
        even when marked COMPLEX."""
        r = escalated_router(implement=Complexity.COMPLEX)
        plan = r.route("build the whole thing")
        m = {s.name: s.run.model for s in plan.pipeline}
        assert m["implement"] == Models.GPT54

    def test_multiple_escalations_simultaneously(self):
        r = escalated_router(
            boilerplate=Complexity.COMPLEX,
            test=Complexity.COMPLEX,
            **{"review-resolve-b": Complexity.COMPLEX},
        )
        plan = r.route("build everything from scratch now")
        m = {s.name: s.run.model for s in plan.pipeline}
        assert m["boilerplate"] == Models.SONNET
        assert m["test"] == Models.SONNET
        assert m["review-resolve-b"] == Models.GPT54
        assert m["implement"] == Models.GPT54
        assert m["parallel-plan-a"] == Models.KIMI

    def test_lite_escalation_works(self):
        """Escalation hints apply to lite pipeline steps too."""
        r = escalated_router(test=Complexity.COMPLEX)
        plan = r.route("fix the broken assertion")
        assert plan.mode == "buildx-lite"
        m = {s.name: s.run.model for s in plan.pipeline}
        assert m["test"] == Models.SONNET


# ---------------------------------------------------------------------------
# Tradeoff protocol
# ---------------------------------------------------------------------------

class TestTradeoff:

    def test_tradeoff_mode(self, router):
        plan = router.route("evaluate tradeoffs between REST and GraphQL")
        assert plan.mode == "tradeoff"

    def test_tradeoff_proposals(self, router):
        plan = router.route("compare approaches for caching")
        models = {r.model for r in plan.parallel}
        assert models == {Models.CODEX53, Models.GLM5}

    def test_tradeoff_judge_is_gpt54(self, router):
        plan = router.route("choose between microservices and monolith")
        assert plan.judge is not None
        assert plan.judge.model == Models.GPT54

    def test_tradeoff_has_no_pipeline(self, router):
        plan = router.route("which architecture is better for this case")
        assert plan.pipeline == ()


class TestTradeoffTriggers:
    """Comprehensive natural-language trigger coverage."""

    TRADEOFF_PROMPTS = [
        # Original triggers
        "evaluate tradeoffs between A and B",
        "evaluate tradeoff for caching strategy",
        "compare approaches for X",
        "compare options for deployment",
        "compare designs for the API",
        "compare architectures",
        "choose between SQL and NoSQL",
        "choose among these three",
        "which approach is better",
        "which design is better for us",
        "judge these architectures",
        "judge the designs we proposed",
        # Expanded natural-language triggers
        "what architecture is better for this use case",
        "what design is better here",
        "what approach is better for scalability",
        "which is better for real-time processing",
        "which is better for our use case",
        "pros and cons of using Redis",
        "pros and cons of microservices",
        "should I use PostgreSQL or MongoDB",
        "should I use REST or GraphQL for this API",
        "advantages and disadvantages of event sourcing",
        "tradeoffs of using a monorepo",
        "tradeoffs between caching strategies",
        "tradeoffs for serverless vs containers",
        "REST vs GraphQL",
        "Kafka vs RabbitMQ for our pipeline",
        "weigh the options for deployment",
        "weigh the approaches before we decide",
    ]

    @pytest.mark.parametrize("prompt", TRADEOFF_PROMPTS)
    def test_tradeoff_trigger(self, prompt):
        router = default_router()
        plan = router.route(prompt)
        assert plan.mode == "tradeoff", (
            f"should trigger tradeoff: {prompt!r}"
        )


# ---------------------------------------------------------------------------
# Cache retention
# ---------------------------------------------------------------------------

class TestCacheRetention:

    def test_openai_codex_routes_use_long(self, router):
        plan = router.route("build the whole project from scratch")
        for step in plan.pipeline:
            if step.run.model.startswith("openai-codex/"):
                assert step.run.cache_retention == "long", (
                    f"{step.name} ({step.run.model}) should have long retention"
                )

    def test_opencode_go_routes_use_short(self, router):
        plan = router.route("build the whole project from scratch")
        for step in plan.pipeline:
            if step.run.model.startswith("opencode-go/"):
                assert step.run.cache_retention == "short", (
                    f"{step.name} ({step.run.model}) should have short retention"
                )

    def test_anthropic_routes_use_short(self, router):
        plan = router.route("build the whole project from scratch")
        for step in plan.pipeline:
            if step.run.model.startswith("anthropic/"):
                assert step.run.cache_retention == "short", (
                    f"{step.name} ({step.run.model}) should have short retention"
                )

    def test_tradeoff_cache_retention(self, router):
        plan = router.route("evaluate tradeoffs between X and Y")
        for r in plan.parallel:
            if r.model.startswith("opencode-go/"):
                assert r.cache_retention == "short"
            if r.model.startswith("openai-codex/"):
                assert r.cache_retention == "long"
        assert plan.judge.cache_retention == "long"

    def test_lite_cache_retention(self, router):
        plan = router.route("fix the broken test")
        for step in plan.pipeline:
            if step.run.model.startswith("openai-codex/"):
                assert step.run.cache_retention == "long"
            elif step.run.model.startswith("opencode-go/"):
                assert step.run.cache_retention == "short"
            elif step.run.model.startswith("anthropic/"):
                assert step.run.cache_retention == "short"


# ---------------------------------------------------------------------------
# Guard rails
# ---------------------------------------------------------------------------

class TestGuardRails:

    def test_empty_prompt_rejected(self, router):
        with pytest.raises(PortfolioRoutingError, match="empty"):
            router.route("")

    def test_whitespace_only_prompt_rejected(self, router):
        with pytest.raises(PortfolioRoutingError, match="empty"):
            router.route("   \n\t  ")

    def test_force_claude_flag_rejected(self, router):
        with pytest.raises(PortfolioRoutingError, match="unsupported"):
            router.route("build it --force-claude")

    def test_legacy_use_claude_rejected(self, router):
        with pytest.raises(PortfolioRoutingError, match="unsupported"):
            router.route("build it --use-claude")

    def test_legacy_force_opus_rejected(self, router):
        with pytest.raises(PortfolioRoutingError, match="unsupported"):
            router.route("build it --force-opus")

    def test_legacy_no_opus_rejected(self, router):
        with pytest.raises(PortfolioRoutingError, match="unsupported"):
            router.route("build it --no-opus")


# ---------------------------------------------------------------------------
# Opus containment
# ---------------------------------------------------------------------------

class TestOpusContainment:
    """Verify Opus only appears where warranted."""

    def test_standard_buildx_opus_slots(self, router):
        plan = router.route("build the complete module from scratch")
        opus_steps = {
            s.name for s in plan.pipeline if s.run.model == Models.OPUS
        }
        allowed = {"judge-plan"}
        assert opus_steps == allowed, (
            f"Opus outside allowed slots: {opus_steps - allowed}"
        )

    def test_lite_has_zero_opus(self, router):
        plan = router.route("fix the broken assertion in tests")
        opus_steps = [
            s.name for s in plan.pipeline if s.run.model == Models.OPUS
        ]
        assert opus_steps == [], f"Opus leaked into lite: {opus_steps}"

    def test_escalated_buildx_opus_slots(self):
        r = escalated_router(**{"review-resolve-b": Complexity.COMPLEX})
        plan = r.route("build the whole thing")
        opus_steps = {
            s.name for s in plan.pipeline if s.run.model == Models.OPUS
        }
        allowed = {"judge-plan"}
        assert opus_steps == allowed


class TestAnthropicContainment:
    """Verify Anthropic models only appear in their designated slots."""

    def _anthropic_steps(self, plan):
        return [
            s.name for s in plan.pipeline
            if s.run.model.startswith("anthropic/")
        ]

    def test_standard_buildx_anthropic_slots(self, router):
        plan = router.route("build the complete module from scratch")
        anth = set(self._anthropic_steps(plan))
        # Opus: judge-plan
        # Sonnet: review-resolve-a
        allowed = {"judge-plan", "review-resolve-a"}
        assert anth == allowed, (
            f"Anthropic models outside allowed slots: {anth - allowed}"
        )

    def test_escalated_anthropic_slots(self):
        r = escalated_router(
            boilerplate=Complexity.COMPLEX,
            test=Complexity.COMPLEX,
            **{"review-resolve-b": Complexity.COMPLEX},
        )
        plan = r.route("build everything from scratch now")
        anth = set(self._anthropic_steps(plan))
        allowed = {
            "judge-plan",                          # always opus
            "review-resolve-a",                    # always sonnet
            "boilerplate", "test",                 # escalated → sonnet
            # review-resolve-b escalates to gpt-5.4, not anthropic
        }
        assert anth == allowed

    def test_lite_anthropic_is_only_sonnet(self, router):
        plan = router.route("refactor the data loader")
        for s in plan.pipeline:
            if s.run.model.startswith("anthropic/"):
                assert s.run.model == Models.SONNET, (
                    f"Non-Sonnet Anthropic in lite step {s.name}: {s.run.model}"
                )


# ---------------------------------------------------------------------------
# Convenience constructors
# ---------------------------------------------------------------------------

class TestConvenience:

    def test_default_router_returns_standard(self):
        r = default_router()
        plan = r.route("build the whole project from scratch")
        assert plan.mode == "buildx"

    def test_escalated_router_applies_overrides(self):
        r = escalated_router(boilerplate=Complexity.COMPLEX)
        plan = r.route("build the whole project from scratch")
        bp = next(s for s in plan.pipeline if s.name == "boilerplate")
        assert bp.run.model == Models.SONNET

    def test_full_router_available(self):
        r = full_router()
        plan = r.route("fix the broken test")
        assert plan.mode == "buildx"

