"""All LLM prompts in one place for easy tuning."""

from models import AgentProfile, CampaignSeed, Interaction, SimulationResult, ActionType


def population_gen(target_audience: str, count: int) -> str:
    return f"""Generate {count} diverse social-media user profiles for audience: "{target_audience}".
Mix: lurkers, influencers, trolls, normies, contrarians.
Return ONLY a JSON array. No markdown. Each object:
{{"name":"string","age":int,"location":"string","bio":"short","mbti":"INTJ|ENFP|etc","political_leaning":"left|center|right|far_left|far_right|center_left|center_right","purchasing_power":"low|medium|high|luxury","interests":["a","b"],"influence_score":0.0-1.0}}
Keep bios under 10 words. Keep interests to 3 items max."""


def agent_brain(agent: AgentProfile, context: str) -> str:
    return f"""You are simulating a social-media user. Stay 100% in character.

YOUR PROFILE:
- Name: {agent.name} | Age: {agent.age} | Location: {agent.location}
- Bio: {agent.bio}
- MBTI: {agent.mbti.value} | Politics: {agent.political_leaning.value} | Purchasing power: {agent.purchasing_power.value}
- Interests: {', '.join(agent.interests)}
- Current mood: {agent.mood.value}
- Influence (0-1): {agent.influence_score}

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
- Be authentic to your personality. A cynical INTJ won't gush over a basic ad.
- If you see other people mocking, you might pile on (or defend, depending on type).
- If the content doesn't match your interests, you'll probably ignore it.
- Influencers are more likely to comment/share. Lurkers mostly ignore or like.
- Your mood should shift based on what you're seeing.
Return ONLY the JSON object, no markdown fences."""


def build_context(seed: CampaignSeed, visible: list[Interaction], agent_map: dict[str, AgentProfile]) -> str:
    lines = ["=== SPONSORED POST ===", seed.content]
    if seed.image_description:
        lines.append(f"[Image: {seed.image_description}]")
    lines.append("")

    if visible:
        lines.append("=== REACTIONS YOU CAN SEE ===")
        for ix in visible:
            if ix.action == ActionType.IGNORE:
                continue
            name = agent_map.get(ix.agent_id, None)
            author = name.name if name else "Unknown"
            lines.append(f"@{author} [{ix.action.value}]: {ix.content}")
    else:
        lines.append("(You are one of the first to see this post. No reactions yet.)")
    return "\n".join(lines)


def evolution(result: SimulationResult) -> str:
    sample_comments = "\n".join(
        f"- {i.content}" for i in result.interactions
        if i.action in (ActionType.COMMENT, ActionType.QUOTE_SHARE) and i.content
    )[:15] or "(No comments)"

    sample_mocks = "\n".join(
        f"- {i.content}" for i in result.interactions
        if i.action == ActionType.MOCK and i.content
    )[:10] or "(No mocks)"

    return f"""You are an expert social-media strategist analyzing a simulated campaign run.

CAMPAIGN:
- Content: {result.seed.content}
- Image: {result.seed.image_description}
- Goal: {result.seed.goal.value}
- Target audience: {result.seed.target_audience}

RESULTS (Generation {result.generation}):
- Total reach: {result.total_reach}
- Likes: {result.likes}
- Comments: {result.comments}
- Shares: {result.shares}
- Mocks: {result.mocks}
- Sentiment score (-1 to 1): {result.sentiment_score:.2f}
- Virality score (0 to 1): {result.virality_score:.2f}

SAMPLE COMMENTS:
{sample_comments}

SAMPLE MOCKS:
{sample_mocks}

---

Analyze:
1. WHY did the post perform this way? Be specific — reference the comments.
2. What resonated? What fell flat? What triggered backlash?
3. How should the copy/image be changed for the next generation?

Return ONLY a JSON object:
{{
  "analysis": "2-3 sentence summary of why this happened",
  "strengths": ["list of what worked"],
  "weaknesses": ["list of what didn't work"],
  "revised_content": "the rewritten ad copy for generation {result.generation + 1}",
  "revised_image_description": "updated image direction if needed (or same)",
  "confidence": float 0-1 for how much improvement is expected
}}
Return ONLY the JSON object, no markdown fences."""
