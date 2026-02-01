"""Phase 3: Tick-based simulation with LLM-powered agent brains."""

from __future__ import annotations
import json
import random
import asyncio
from models import (
    AgentProfile, CampaignSeed, Interaction, SimulationResult,
    ActionType, Mood,
)
from social_graph import SocialGraph
from prompts import agent_brain, build_context
from event_bus import EventBus
from llm import chat


async def run_simulation(
    seed: CampaignSeed,
    agents: list[AgentProfile],
    graph: SocialGraph,
    num_ticks: int,
    generation: int,
    bus: EventBus,
) -> SimulationResult:
    interactions: list[Interaction] = []
    agent_map = {a.id: a for a in agents}
    seen: set[str] = set()

    for tick in range(num_ticks):
        await bus.emit("tick", {"tick": tick, "total": num_ticks})

        if tick == 0:
            influencers = {a.id for a in graph.get_influencers(5)}
            sample_size = max(1, len(agents) * 30 // 100)
            random_set = {a.id for a in random.sample(agents, min(sample_size, len(agents)))}
            active_ids = list(influencers | random_set)
        else:
            spreaders = {ix.agent_id for ix in interactions
                         if ix.action in (ActionType.SHARE, ActionType.QUOTE_SHARE, ActionType.COMMENT)}
            active_ids = []
            for sid in spreaders:
                for fid in graph.get_followers_of(sid):
                    if fid not in seen:
                        active_ids.append(fid)
            active_ids = list(set(active_ids))

        if not active_ids:
            continue

        random.shuffle(active_ids)

        # Process agents in concurrent batches of 5
        batch_size = 5
        for i in range(0, len(active_ids), batch_size):
            batch = active_ids[i:i + batch_size]
            tasks = []
            for aid in batch:
                if aid in seen:
                    continue
                seen.add(aid)
                agent = agent_map.get(aid)
                if not agent:
                    continue
                visible = [ix for ix in interactions if ix.action != ActionType.IGNORE][-10:]
                context = build_context(seed, visible, agent_map)
                tasks.append(process_agent(agent, context, tick, bus))

            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, Interaction):
                    interactions.append(r)
                elif isinstance(r, Exception):
                    print(f"  [WARN] Agent failed: {r}")

    return SimulationResult(seed=seed, generation=generation, interactions=interactions)


async def process_agent(
    agent: AgentProfile,
    context: str,
    tick: int,
    bus: EventBus,
) -> Interaction:
    prompt = agent_brain(agent, context)

    raw = await chat(
        system="You are a social-media user simulator. Return ONLY valid JSON. No markdown.",
        user=prompt,
        max_tokens=512,
    )

    cleaned = raw.replace("```json", "").replace("```", "").strip()
    data = json.loads(cleaned)

    action = ActionType(data.get("action", "ignore"))
    new_mood = next((m for m in Mood if m.value == data.get("new_mood", "neutral")), Mood.NEUTRAL)
    agent.mood = new_mood

    interaction = Interaction(
        agent_id=agent.id,
        tick=tick,
        action=action,
        content=data.get("content", ""),
        reasoning=data.get("reasoning", ""),
        new_mood=new_mood,
    )

    await bus.emit("reaction", {
        "agentId": agent.id,
        "agentName": agent.name,
        "action": action.value,
        "content": interaction.content,
        "reasoning": interaction.reasoning,
        "mood": new_mood.value,
        "tick": tick,
    })

    return interaction
