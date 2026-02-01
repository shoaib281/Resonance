"""Phase 2: Population generation via OpenAI."""

from __future__ import annotations
import json
import random
from models import AgentProfile, CampaignSeed, MBTIType, PoliticalLeaning, PurchasingPower, Mood
from prompts import population_gen
from llm import chat


async def generate_population(
    seed: CampaignSeed,
    count: int = 30,
) -> list[AgentProfile]:
    batch_size = 5
    agents: list[AgentProfile] = []
    remaining = count

    while remaining > 0:
        batch = min(batch_size, remaining)
        prompt = population_gen(seed.target_audience, batch)

        try:
            raw = await chat(
                system="You are a persona generator. Output ONLY a valid JSON array. No markdown fences, no explanation, no text before or after the JSON.",
                user=prompt,
                max_tokens=2048,
            )
            agents.extend(parse_agent_profiles(raw))
        except Exception as e:
            print(f"  [WARN] Batch generation failed: {e}")

        remaining -= batch

    return agents


def parse_agent_profiles(raw: str) -> list[AgentProfile]:
    cleaned = raw.replace("```json", "").replace("```", "").strip()
    parsed = json.loads(cleaned)

    results = []
    for p in parsed:
        mbti = next((m for m in MBTIType if m.value == p.get("mbti", "")), MBTIType.ENFP)
        pol = next((pl for pl in PoliticalLeaning if pl.value == p.get("political_leaning", "")), PoliticalLeaning.CENTER)
        pp = next((pw for pw in PurchasingPower if pw.value == p.get("purchasing_power", "")), PurchasingPower.MEDIUM)

        results.append(AgentProfile(
            name=p["name"],
            age=p.get("age", 25),
            location=p.get("location", "Unknown"),
            bio=p.get("bio", ""),
            mbti=mbti,
            political_leaning=pol,
            purchasing_power=pp,
            interests=p.get("interests", [])[:3],
            influence_score=max(0.0, min(1.0, p.get("influence_score", 0.5))),
            mood=random.choice(list(Mood)),
        ))
    return results
