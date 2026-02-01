"""Phase 4: Fitness evaluation and LLM-powered campaign evolution."""

from __future__ import annotations
import json
from models import CampaignSeed, SimulationResult, Goal, ActionType
from prompts import evolution as evolution_prompt
from llm import chat


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


async def analyze_and_evolve(result: SimulationResult) -> tuple[CampaignSeed, dict]:
    prompt = evolution_prompt(result)

    raw = await chat(
        system="You are a marketing strategist. Return ONLY valid JSON. No markdown.",
        user=prompt,
        max_tokens=1024,
    )

    cleaned = raw.replace("```json", "").replace("```", "").strip()
    data = json.loads(cleaned)

    new_seed = CampaignSeed(
        content=data.get("revised_content", result.seed.content),
        image_description=data.get("revised_image_description", result.seed.image_description),
        goal=result.seed.goal,
        target_audience=result.seed.target_audience,
    )

    return new_seed, data
