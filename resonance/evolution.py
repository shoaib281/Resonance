"""
Phase 4 — Evolution / Genetic Algorithm.

Analyzes simulation results, identifies why the campaign failed or succeeded,
and uses the LLM to rewrite the campaign content for the next generation.
"""
from __future__ import annotations

import json

import anthropic

from .models import CampaignSeed, Goal, SimulationResult

# ---------------------------------------------------------------------------
# Analysis prompt — the "fitness function" brain
# ---------------------------------------------------------------------------

ANALYSIS_PROMPT = """\
You are an expert social-media strategist analyzing a simulated campaign run.

CAMPAIGN:
- Content: {content}
- Image: {image_description}
- Goal: {goal}
- Target audience: {target_audience}

RESULTS (Generation {generation}):
- Total reach: {total_reach}
- Likes: {likes}
- Comments: {comments}
- Shares: {shares}
- Mocks: {mocks}
- Sentiment score (-1 to 1): {sentiment_score}
- Virality score (0 to 1): {virality_score}

SAMPLE COMMENTS (what the synthetic audience actually said):
{sample_comments}

SAMPLE MOCKS (negative reactions):
{sample_mocks}

---

Analyze:
1. WHY did the post perform this way?  Be specific — reference the comments.
2. What resonated?  What fell flat?  What triggered backlash?
3. How should the copy/image be changed for the next generation?

Return ONLY a JSON object:
{{
  "analysis": "2-3 sentence summary of why this happened",
  "strengths": ["list of what worked"],
  "weaknesses": ["list of what didn't work"],
  "revised_content": "the rewritten ad copy for generation {next_gen}",
  "revised_image_description": "updated image direction if needed (or same)",
  "confidence": float 0-1 for how much improvement is expected
}}"""


def analyze_and_evolve(
    client: anthropic.Anthropic,
    result: SimulationResult,
    model: str = "claude-sonnet-4-20250514",
) -> tuple[CampaignSeed, dict]:
    """
    Take a SimulationResult, analyze it, and produce an evolved CampaignSeed
    for the next generation.

    Returns (new_seed, analysis_data).
    """
    # Gather sample comments and mocks for the prompt
    comments = [
        ix for ix in result.interactions
        if ix.action.value in ("comment", "quote_share") and ix.content
    ]
    mocks = [ix for ix in result.interactions if ix.action.value == "mock" and ix.content]

    sample_comments_text = "\n".join(
        f"- {ix.content}" for ix in comments[:15]
    ) or "(No comments)"

    sample_mocks_text = "\n".join(
        f"- {ix.content}" for ix in mocks[:10]
    ) or "(No mocks)"

    prompt = ANALYSIS_PROMPT.format(
        content=result.seed.content,
        image_description=result.seed.image_description,
        goal=result.seed.goal.value,
        target_audience=result.seed.target_audience,
        generation=result.generation,
        total_reach=result.total_reach,
        likes=result.likes,
        comments=result.comments,
        shares=result.shares,
        mocks=result.mocks,
        sentiment_score=result.sentiment_score,
        virality_score=result.virality_score,
        sample_comments=sample_comments_text,
        sample_mocks=sample_mocks_text,
        next_gen=result.generation + 1,
    )

    response = client.messages.create(
        model=model,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text
    if "```" in raw:
        raw = raw.split("```json")[-1].split("```")[0]

    analysis = json.loads(raw)

    new_seed = CampaignSeed(
        content=analysis["revised_content"],
        image_description=analysis.get("revised_image_description", result.seed.image_description),
        goal=result.seed.goal,
        target_audience=result.seed.target_audience,
    )

    return new_seed, analysis


# ---------------------------------------------------------------------------
# Fitness scoring — decides if we keep evolving
# ---------------------------------------------------------------------------

def compute_fitness(result: SimulationResult) -> float:
    """
    Compute a 0-1 fitness score based on the campaign goal.

    TODO: You can tune these weights to match your priorities.
    """
    goal = result.seed.goal

    if goal == Goal.BRAND_AWARENESS:
        # Maximize reach + positive sentiment
        return 0.6 * _norm(result.total_reach, 0, 100) + 0.4 * _norm(result.sentiment_score, -1, 1)

    elif goal == Goal.CLICKS:
        # Maximize shares (proxy for clicks) + reach
        return 0.7 * _norm(result.shares, 0, 50) + 0.3 * _norm(result.total_reach, 0, 100)

    elif goal == Goal.CONTROVERSY:
        # Maximize engagement volume (comments + mocks) — sentiment doesn't matter
        return 0.5 * _norm(result.comments + result.mocks, 0, 80) + 0.5 * _norm(result.total_reach, 0, 100)

    elif goal == Goal.ENGAGEMENT:
        # Balanced: reach + comments + positive sentiment
        return (
            0.3 * _norm(result.total_reach, 0, 100)
            + 0.3 * _norm(result.comments, 0, 50)
            + 0.2 * _norm(result.shares, 0, 50)
            + 0.2 * _norm(result.sentiment_score, -1, 1)
        )

    return 0.0


def _norm(value: float, min_val: float, max_val: float) -> float:
    """Normalize a value to 0-1 range."""
    return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))
