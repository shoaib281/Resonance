"""Phase 4: Fitness evaluation and campaign evolution — local (no API)."""

from __future__ import annotations
import random
from models import CampaignSeed, SimulationResult, Goal, ActionType


def compute_fitness(result: SimulationResult) -> float:
    n = len(result.interactions)
    if n == 0:
        return 0.0

    engagement = result.total_reach / n
    sentiment = (result.sentiment_score + 1) / 2
    virality = result.virality_score
    mock_rate = result.mocks / n

    goal = result.seed.goal
    if goal == Goal.ENGAGEMENT:
        return 0.4 * engagement + 0.3 * sentiment + 0.2 * virality + 0.1 * (1 - mock_rate)
    elif goal == Goal.BRAND_AWARENESS:
        return 0.3 * engagement + 0.2 * sentiment + 0.4 * virality + 0.1 * (1 - mock_rate)
    elif goal == Goal.CLICKS:
        return 0.5 * engagement + 0.2 * sentiment + 0.2 * virality + 0.1 * (1 - mock_rate)
    elif goal == Goal.CONTROVERSY:
        return 0.2 * engagement + 0.1 * sentiment + 0.3 * virality + 0.4 * mock_rate
    return 0.5


EVOLUTION_STRATEGIES = [
    "Leaned into humor and self-awareness to reduce mock rate",
    "Shifted tone to be more authentic and less corporate",
    "Added community-driven language to increase shares",
    "Reduced clickbait feel, focused on genuine value proposition",
    "Made the CTA more subtle and conversational",
    "Injected trending cultural references for relatability",
    "Pivoted from hard sell to storytelling approach",
    "Emphasized social proof and FOMO elements",
]

STRENGTH_POOL = [
    "Strong emotional hook", "Relatable tone", "Good meme potential",
    "Clear value proposition", "Conversational language", "Visual appeal",
    "Timely cultural reference", "Authentic voice", "Shareable format",
]

WEAKNESS_POOL = [
    "Too corporate-sounding", "Lacks authenticity", "Missed target demographic",
    "Tone-deaf to audience", "Over-promising", "Generic messaging",
    "Trying too hard", "No clear CTA", "Alienating fringe groups",
]


async def analyze_and_evolve(result: SimulationResult) -> tuple[CampaignSeed, dict]:
    # Analyze what happened
    mock_rate = result.mocks / max(1, len(result.interactions))
    share_rate = result.shares / max(1, len(result.interactions))

    strengths = random.sample(STRENGTH_POOL, random.randint(1, 3))
    weaknesses = random.sample(WEAKNESS_POOL, random.randint(1, 3))

    # "Evolve" the content — mutate the copy
    original = result.seed.content
    mutations = [
        f"{original} (But seriously, you'll love it.)",
        original.replace(".", "!") if "." in original else original + " No cap.",
        f"POV: {original}",
        f"Hot take: {original}",
        original + " Tag someone who needs this.",
        f"Okay hear me out... {original}",
        f"Nobody asked but: {original}",
    ]

    # Pick strategy based on performance
    if mock_rate > 0.3:
        analysis = "High mock rate suggests the tone felt inauthentic. Pivoting to self-aware humor."
        revised = f"We know what you're thinking. But actually: {original}"
    elif share_rate > 0.2:
        analysis = "Strong share rate indicates resonance. Doubling down on what works."
        revised = random.choice(mutations)
    else:
        analysis = random.choice(EVOLUTION_STRATEGIES)
        revised = random.choice(mutations)

    new_seed = CampaignSeed(
        content=revised,
        image_description=result.seed.image_description,
        goal=result.seed.goal,
        target_audience=result.seed.target_audience,
    )

    data = {
        "analysis": analysis,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "revised_content": revised,
        "confidence": round(random.uniform(0.4, 0.85), 2),
    }

    return new_seed, data
