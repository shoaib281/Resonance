"""Phase 3: Tick-based simulation — local random decisions (no API)."""

from __future__ import annotations
import random
import asyncio
from models import (
    AgentProfile, CampaignSeed, Interaction, SimulationResult,
    ActionType, Mood, MBTIType,
)
from social_graph import SocialGraph
from event_bus import EventBus

# Personality-weighted action probabilities
ACTION_WEIGHTS: dict[str, dict[ActionType, float]] = {
    "introvert": {
        ActionType.IGNORE: 0.40, ActionType.LIKE: 0.30, ActionType.COMMENT: 0.10,
        ActionType.SHARE: 0.05, ActionType.QUOTE_SHARE: 0.05, ActionType.MOCK: 0.10,
    },
    "extrovert": {
        ActionType.IGNORE: 0.10, ActionType.LIKE: 0.20, ActionType.COMMENT: 0.30,
        ActionType.SHARE: 0.15, ActionType.QUOTE_SHARE: 0.15, ActionType.MOCK: 0.10,
    },
    "thinker": {
        ActionType.IGNORE: 0.20, ActionType.LIKE: 0.15, ActionType.COMMENT: 0.25,
        ActionType.SHARE: 0.10, ActionType.QUOTE_SHARE: 0.15, ActionType.MOCK: 0.15,
    },
    "feeler": {
        ActionType.IGNORE: 0.15, ActionType.LIKE: 0.35, ActionType.COMMENT: 0.20,
        ActionType.SHARE: 0.15, ActionType.QUOTE_SHARE: 0.10, ActionType.MOCK: 0.05,
    },
}

COMMENT_TEMPLATES = {
    ActionType.COMMENT: [
        "This is actually pretty interesting ngl",
        "Okay but has anyone actually tried this?",
        "Not sure how I feel about this one",
        "This hits different at 3am",
        "Lowkey obsessed with this concept",
        "The algorithm really said here you go",
        "I've been saying this for YEARS",
        "Wait this is actually genius??",
        "My FYP is unhinged today",
        "This is the content I signed up for",
        "Hmm I have mixed feelings about this",
        "Finally someone said it",
        "This resonates hard",
        "Saving this for later",
        "Adding this to my personality",
    ],
    ActionType.QUOTE_SHARE: [
        "Everyone needs to see this immediately",
        "THIS. This right here.",
        "Sharing because my followers need to know",
        "The way this just called me out",
        "No because WHY is this so accurate",
        "Reposting for the culture",
        "My timeline needed this today",
    ],
    ActionType.MOCK: [
        "Who approved this campaign lmaooo",
        "Tell me you're out of touch without telling me",
        "The intern definitely made this one",
        "This is peak cringe and I'm here for it",
        "Brands really think they understand us huh",
        "Ratio + L + didn't ask",
        "This ain't it chief",
        "Sir this is a Wendy's",
        "I can't believe someone got paid to make this",
        "The silence from their marketing team...",
    ],
}

REASONING_TEMPLATES = {
    ActionType.IGNORE: [
        "Not relevant to my interests at all", "Scrolling past this one",
        "Don't have the energy for this today", "Meh, seen better",
    ],
    ActionType.LIKE: [
        "It's decent enough for a like", "Quick dopamine hit, why not",
        "I vibe with this on some level", "Supporting the algorithm",
    ],
    ActionType.COMMENT: [
        "I actually have thoughts on this", "Can't resist dropping my take",
        "This triggered my need to share my opinion", "Engagement bait worked on me",
    ],
    ActionType.SHARE: [
        "My followers would find this interesting", "Sharing to boost my curation cred",
        "This aligns with my brand", "Good content deserves amplification",
    ],
    ActionType.QUOTE_SHARE: [
        "Need to add my commentary to this", "Can't just share without my hot take",
        "This deserves context from me", "Quote sharing for the discourse",
    ],
    ActionType.MOCK: [
        "This is too cringe to let slide", "Someone needs to call this out",
        "My cynical side won today", "The roast potential is too high",
    ],
}


def get_personality_type(agent: AgentProfile) -> str:
    mbti = agent.mbti.value
    if mbti[0] == "I":
        return "introvert"
    if mbti[2] == "T":
        return "thinker"
    if mbti[2] == "F":
        return "feeler"
    return "extrovert"


def compute_action(agent: AgentProfile, has_visible_mocks: bool, interest_match: bool) -> ActionType:
    ptype = get_personality_type(agent)
    weights = dict(ACTION_WEIGHTS[ptype])

    # Mood modifiers
    if agent.mood in (Mood.IRRITABLE, Mood.CYNICAL):
        weights[ActionType.MOCK] *= 2.0
        weights[ActionType.IGNORE] *= 0.7
    elif agent.mood in (Mood.HAPPY, Mood.EXCITED):
        weights[ActionType.LIKE] *= 1.5
        weights[ActionType.SHARE] *= 1.5
        weights[ActionType.MOCK] *= 0.3
    elif agent.mood == Mood.BORED:
        weights[ActionType.IGNORE] *= 1.8

    # Influence modifier — high influence = more likely to comment/share
    if agent.influence_score > 0.5:
        weights[ActionType.COMMENT] *= 1.5
        weights[ActionType.SHARE] *= 1.5
        weights[ActionType.QUOTE_SHARE] *= 1.5
    elif agent.influence_score < 0.2:
        weights[ActionType.IGNORE] *= 1.5
        weights[ActionType.LIKE] *= 1.3

    # Social pressure — if others are mocking, pile-on effect
    if has_visible_mocks:
        if agent.mood in (Mood.IRRITABLE, Mood.CYNICAL):
            weights[ActionType.MOCK] *= 2.5
        else:
            weights[ActionType.MOCK] *= 1.4

    # Interest match
    if not interest_match:
        weights[ActionType.IGNORE] *= 2.0
    else:
        weights[ActionType.COMMENT] *= 1.5
        weights[ActionType.SHARE] *= 1.3

    # Weighted random selection
    actions = list(weights.keys())
    w = [weights[a] for a in actions]
    return random.choices(actions, weights=w, k=1)[0]


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

    # Extract keywords from seed for interest matching
    seed_words = set(seed.content.lower().split() + seed.target_audience.lower().split())

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
        has_mocks = any(ix.action == ActionType.MOCK for ix in interactions)

        for aid in active_ids:
            if aid in seen:
                continue
            seen.add(aid)
            agent = agent_map.get(aid)
            if not agent:
                continue

            # Check interest overlap
            interest_match = any(
                interest.lower() in seed_words or any(w in interest.lower() for w in seed_words)
                for interest in agent.interests
            )

            action = compute_action(agent, has_mocks, interest_match)

            # Generate content
            content = ""
            if action in COMMENT_TEMPLATES:
                content = random.choice(COMMENT_TEMPLATES[action])

            reasoning = random.choice(REASONING_TEMPLATES[action])

            # Mood shift
            mood_shift_map = {
                ActionType.LIKE: [Mood.HAPPY, Mood.NEUTRAL, Mood.EXCITED],
                ActionType.COMMENT: [Mood.EXCITED, Mood.NEUTRAL, Mood.HAPPY],
                ActionType.SHARE: [Mood.EXCITED, Mood.HAPPY],
                ActionType.QUOTE_SHARE: [Mood.EXCITED, Mood.HAPPY, Mood.NEUTRAL],
                ActionType.MOCK: [Mood.CYNICAL, Mood.IRRITABLE, Mood.BORED],
                ActionType.IGNORE: [Mood.BORED, Mood.NEUTRAL],
            }
            new_mood = random.choice(mood_shift_map.get(action, [Mood.NEUTRAL]))
            agent.mood = new_mood

            interaction = Interaction(
                agent_id=agent.id, tick=tick, action=action,
                content=content, reasoning=reasoning, new_mood=new_mood,
            )
            interactions.append(interaction)

            if action != ActionType.IGNORE:
                has_mocks = has_mocks or (action == ActionType.MOCK)

            await bus.emit("reaction", {
                "agentId": agent.id,
                "agentName": agent.name,
                "action": action.value,
                "content": content,
                "reasoning": reasoning,
                "mood": new_mood.value,
                "tick": tick,
            })

            # Small delay for visual effect
            await asyncio.sleep(0.15)

    return SimulationResult(seed=seed, generation=generation, interactions=interactions)
