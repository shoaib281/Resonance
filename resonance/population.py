"""
Phase 2 — Agent Population Generator.

Uses an LLM to generate diverse, psychographically-rich agent profiles
that match the target audience, then wires them into a social graph.
"""
from __future__ import annotations

import json
import random
from typing import Optional

import anthropic
import networkx as nx

from .models import (
    AgentProfile,
    CampaignSeed,
    MBTIType,
    Mood,
    PoliticalLeaning,
    PurchasingPower,
)

# ---------------------------------------------------------------------------
# LLM-powered agent generation
# ---------------------------------------------------------------------------

AGENT_GEN_PROMPT = """\
You are a synthetic persona generator for a social-media simulation.

TARGET AUDIENCE: {target_audience}

Generate {count} unique, diverse social-media user profiles that belong to or
orbit around this target audience.  Make them feel REAL — not cookie-cutter.
Include some edge-cases: lurkers, contrarians, influencers, trolls, and normies.

Return ONLY a JSON array.  Each element must have exactly these fields:
{{
  "name": "string",
  "age": int,
  "location": "string",
  "bio": "one-liner personality summary",
  "mbti": "one of {mbti_values}",
  "political_leaning": "one of {pol_values}",
  "purchasing_power": "one of {pp_values}",
  "interests": ["list", "of", "interests"],
  "influence_score": float between 0 and 1
}}

Be creative.  Vary ages, locations, personalities.  Some should be skeptical
of ads, some brand-loyal, some chaotic."""


def generate_agents_via_llm(
    client: anthropic.Anthropic,
    seed: CampaignSeed,
    count: int = 50,
    model: str = "claude-sonnet-4-20250514",
) -> list[AgentProfile]:
    """Call the LLM to produce diverse agent profiles."""

    prompt = AGENT_GEN_PROMPT.format(
        target_audience=seed.target_audience,
        count=count,
        mbti_values=", ".join(m.value for m in MBTIType),
        pol_values=", ".join(p.value for p in PoliticalLeaning),
        pp_values=", ".join(p.value for p in PurchasingPower),
    )

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text
    # Strip markdown fences if present
    if "```" in raw:
        raw = raw.split("```json")[-1].split("```")[0]

    profiles_data = json.loads(raw)
    agents: list[AgentProfile] = []
    for p in profiles_data:
        agents.append(AgentProfile(
            name=p["name"],
            age=p["age"],
            location=p["location"],
            bio=p["bio"],
            mbti=MBTIType(p["mbti"]),
            political_leaning=PoliticalLeaning(p["political_leaning"]),
            purchasing_power=PurchasingPower(p["purchasing_power"]),
            interests=p["interests"],
            influence_score=p.get("influence_score", 0.5),
            mood=random.choice(list(Mood)),
        ))
    return agents


# ---------------------------------------------------------------------------
# Social graph construction
# ---------------------------------------------------------------------------

def build_social_graph(agents: list[AgentProfile], edge_probability: float = 0.15) -> nx.DiGraph:
    """
    Build a directed social graph using preferential attachment weighted by
    influence score.  High-influence agents attract more followers.

    Returns a networkx DiGraph and mutates agent.following / agent.followers.
    """
    G = nx.DiGraph()
    agent_map = {a.id: a for a in agents}

    for a in agents:
        G.add_node(a.id, agent=a)

    # Wire edges: each agent decides who to follow
    for a in agents:
        for b in agents:
            if a.id == b.id:
                continue
            # Probability of following scales with target's influence
            p = edge_probability * b.influence_score
            # Same-interest boost
            shared = set(a.interests) & set(b.interests)
            if shared:
                p += 0.05 * len(shared)
            p = min(p, 0.8)

            if random.random() < p:
                G.add_edge(a.id, b.id)
                a.following.append(b.id)
                b.followers.append(a.id)

    return G


def get_influencers(agents: list[AgentProfile], top_n: int = 5) -> list[AgentProfile]:
    """Return the top-N agents by follower count."""
    return sorted(agents, key=lambda a: len(a.followers), reverse=True)[:top_n]
