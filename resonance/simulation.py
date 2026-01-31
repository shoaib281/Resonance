"""
Phase 3 — The Simulation Engine.

Runs tick-based simulation where agents see the post (or see others' reactions)
and decide how to act.  Supports second-order interactions and viral spread.
"""
from __future__ import annotations

import json
import random
from typing import Optional

import anthropic
import networkx as nx

from .models import (
    ActionType,
    AgentProfile,
    CampaignSeed,
    Interaction,
    Mood,
    SimulationResult,
)

# ---------------------------------------------------------------------------
# System prompt for each agent's "brain"
# ---------------------------------------------------------------------------

AGENT_BRAIN_PROMPT = """\
You are simulating a social-media user.  Stay 100% in character.

YOUR PROFILE:
- Name: {name} | Age: {age} | Location: {location}
- Bio: {bio}
- MBTI: {mbti} | Politics: {political_leaning} | Purchasing power: {purchasing_power}
- Interests: {interests}
- Current mood: {mood}
- Influence (0-1): {influence_score}

CONTEXT:
{context}

Based on your personality, mood, and what you see, respond with ONLY a JSON object:
{{
  "action": one of ["ignore", "like", "comment", "share", "quote_share", "mock"],
  "content": "your comment/quote text if action is comment, quote_share, or mock — otherwise empty string",
  "new_mood": one of ["happy", "neutral", "irritable", "bored", "excited", "anxious", "cynical"],
  "reasoning": "one sentence on WHY you chose this action (internal monologue)"
}}

Rules:
- Be authentic to your personality.  A cynical INTJ won't gush over a basic ad.
- If you see other people mocking, you might pile on (or defend, depending on type).
- If the content doesn't match your interests, you'll probably ignore it.
- Influencers are more likely to comment/share.  Lurkers mostly ignore or like.
- Your mood should shift based on what you're seeing."""


def _build_agent_context(
    agent: AgentProfile,
    seed: CampaignSeed,
    visible_interactions: list[Interaction],
    agents_map: dict[str, AgentProfile],
) -> str:
    """Build the context block the agent sees — the post + any visible reactions."""
    parts = []

    # The original post
    parts.append(f"=== SPONSORED POST ===\n{seed.content}")
    if seed.image_description:
        parts.append(f"[Image: {seed.image_description}]")
    parts.append(f"Campaign goal (hidden from user, for your info): {seed.goal.value}")
    parts.append("")

    # Reactions the agent can see
    if visible_interactions:
        parts.append("=== REACTIONS YOU CAN SEE ===")
        for ix in visible_interactions:
            author = agents_map.get(ix.agent_id)
            author_name = author.name if author else "Unknown"
            if ix.action == ActionType.IGNORE:
                continue
            parts.append(f"@{author_name} [{ix.action.value}]: {ix.content}")
    else:
        parts.append("(You are one of the first to see this post.  No reactions yet.)")

    return "\n".join(parts)


async def _run_agent_turn(
    client: anthropic.Anthropic,
    agent: AgentProfile,
    context: str,
    model: str = "claude-sonnet-4-20250514",
) -> tuple[ActionType, str, Mood]:
    """Ask the LLM to act as this agent and return their action."""
    prompt = AGENT_BRAIN_PROMPT.format(
        name=agent.name,
        age=agent.age,
        location=agent.location,
        bio=agent.bio,
        mbti=agent.mbti.value,
        political_leaning=agent.political_leaning.value,
        purchasing_power=agent.purchasing_power.value,
        interests=", ".join(agent.interests),
        mood=agent.mood.value,
        influence_score=agent.influence_score,
        context=context,
    )

    response = client.messages.create(
        model=model,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text
    if "```" in raw:
        raw = raw.split("```json")[-1].split("```")[0]

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: agent ignores
        return ActionType.IGNORE, "", agent.mood

    action = ActionType(data.get("action", "ignore"))
    content = data.get("content", "")
    new_mood = Mood(data.get("new_mood", agent.mood.value))

    return action, content, new_mood


# ---------------------------------------------------------------------------
# Simulation runner
# ---------------------------------------------------------------------------

def run_simulation(
    client: anthropic.Anthropic,
    seed: CampaignSeed,
    agents: list[AgentProfile],
    graph: nx.DiGraph,
    num_ticks: int = 3,
    generation: int = 1,
    model: str = "claude-sonnet-4-20250514",
) -> SimulationResult:
    """
    Run the full tick-based simulation.

    Tick 0: Seed agents (top influencers + random sample) see the post directly.
    Tick 1+: Agents see the post + reactions from people they follow.
    """
    agents_map = {a.id: a for a in agents}
    all_interactions: list[Interaction] = []
    interaction_by_agent: dict[str, list[Interaction]] = {}
    agents_who_saw_post: set[str] = set()

    # --- Tick 0: Initial exposure ---
    # Top influencers + random 30% see it first
    influencers = sorted(agents, key=lambda a: len(a.followers), reverse=True)[:5]
    random_sample = random.sample(agents, k=min(len(agents) // 3, len(agents)))
    initial_viewers = list({a.id for a in influencers + random_sample})

    for tick in range(num_ticks):
        if tick == 0:
            viewer_ids = initial_viewers
        else:
            # Agents see the post if someone they follow shared/quoted it
            viewer_ids = []
            for ix in all_interactions:
                if ix.action in (ActionType.SHARE, ActionType.QUOTE_SHARE):
                    sharer = agents_map[ix.agent_id]
                    for follower_id in sharer.followers:
                        if follower_id not in agents_who_saw_post:
                            viewer_ids.append(follower_id)
            # Also add people who follow someone who commented
            for ix in all_interactions:
                if ix.action in (ActionType.COMMENT, ActionType.MOCK):
                    commenter = agents_map[ix.agent_id]
                    for follower_id in commenter.followers:
                        if follower_id not in agents_who_saw_post:
                            if random.random() < 0.3:  # 30% chance algo shows it
                                viewer_ids.append(follower_id)

            viewer_ids = list(set(viewer_ids))

        for agent_id in viewer_ids:
            agent = agents_map[agent_id]
            agents_who_saw_post.add(agent_id)

            # What interactions can this agent see?
            # They see reactions from people they follow
            visible = [
                ix for ix in all_interactions
                if ix.agent_id in agent.following or ix.agent_id in [a.id for a in influencers]
            ]

            context = _build_agent_context(agent, seed, visible, agents_map)
            action, content, new_mood = _run_agent_turn_sync(
                client, agent, context, model
            )

            agent.mood = new_mood

            ix = Interaction(
                agent_id=agent.id,
                action=action,
                content=content,
                tick=tick,
            )
            all_interactions.append(ix)
            interaction_by_agent.setdefault(agent.id, []).append(ix)

    result = SimulationResult(
        generation=generation,
        seed=seed,
        interactions=all_interactions,
    )
    result.compute_analytics()
    return result


def _run_agent_turn_sync(
    client: anthropic.Anthropic,
    agent: AgentProfile,
    context: str,
    model: str = "claude-sonnet-4-20250514",
) -> tuple[ActionType, str, Mood]:
    """Synchronous wrapper for agent turn (used in tick loop)."""
    prompt = AGENT_BRAIN_PROMPT.format(
        name=agent.name,
        age=agent.age,
        location=agent.location,
        bio=agent.bio,
        mbti=agent.mbti.value,
        political_leaning=agent.political_leaning.value,
        purchasing_power=agent.purchasing_power.value,
        interests=", ".join(agent.interests),
        mood=agent.mood.value,
        influence_score=agent.influence_score,
        context=context,
    )

    response = client.messages.create(
        model=model,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text
    if "```" in raw:
        raw = raw.split("```json")[-1].split("```")[0]

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return ActionType.IGNORE, "", agent.mood

    action = ActionType(data.get("action", "ignore"))
    content = data.get("content", "")
    new_mood = Mood(data.get("new_mood", agent.mood.value))

    return action, content, new_mood
