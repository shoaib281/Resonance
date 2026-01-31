package com.resonance

// ==========================================================================
// All LLM prompts in one place for easy tuning
// ==========================================================================

object Prompts {

    /** Phase 2: Generate agent population */
    fun populationGen(targetAudience: String, count: Int): String = """
You are a synthetic persona generator for a social-media simulation.

TARGET AUDIENCE: $targetAudience

Generate $count unique, diverse social-media user profiles that belong to or
orbit around this target audience. Make them feel REAL — not cookie-cutter.
Include some edge-cases: lurkers, contrarians, influencers, trolls, and normies.

Return ONLY a JSON array. Each element must have exactly these fields:
{
  "name": "string",
  "age": int,
  "location": "string",
  "bio": "one-liner personality summary",
  "mbti": "one of [${MBTIType.entries.joinToString(", ")}]",
  "political_leaning": "one of [${PoliticalLeaning.entries.joinToString(", ") { it.value }}]",
  "purchasing_power": "one of [${PurchasingPower.entries.joinToString(", ") { it.value }}]",
  "interests": ["list", "of", "interests"],
  "influence_score": float between 0 and 1
}

Be creative. Vary ages, locations, personalities. Some should be skeptical
of ads, some brand-loyal, some chaotic. Return ONLY the JSON array, no markdown fences.
""".trimIndent()

    /** Phase 3: Agent brain — decides how to react to a post */
    fun agentBrain(agent: AgentProfile, context: String): String = """
You are simulating a social-media user. Stay 100% in character.

YOUR PROFILE:
- Name: ${agent.name} | Age: ${agent.age} | Location: ${agent.location}
- Bio: ${agent.bio}
- MBTI: ${agent.mbti} | Politics: ${agent.politicalLeaning.value} | Purchasing power: ${agent.purchasingPower.value}
- Interests: ${agent.interests.joinToString(", ")}
- Current mood: ${agent.mood.value}
- Influence (0-1): ${agent.influenceScore}

CONTEXT:
$context

Based on your personality, mood, and what you see, respond with ONLY a JSON object:
{
  "action": one of ["ignore", "like", "comment", "share", "quote_share", "mock"],
  "content": "your comment/quote text if action is comment, quote_share, or mock — otherwise empty string",
  "new_mood": one of ["happy", "neutral", "irritable", "bored", "excited", "anxious", "cynical"],
  "reasoning": "one sentence on WHY you chose this action (internal monologue)"
}

Rules:
- Be authentic to your personality. A cynical INTJ won't gush over a basic ad.
- If you see other people mocking, you might pile on (or defend, depending on type).
- If the content doesn't match your interests, you'll probably ignore it.
- Influencers are more likely to comment/share. Lurkers mostly ignore or like.
- Your mood should shift based on what you're seeing.
Return ONLY the JSON object, no markdown fences.
""".trimIndent()

    /** Build the context block an agent sees */
    fun buildContext(
        seed: CampaignSeed,
        visibleInteractions: List<Interaction>,
        agentMap: Map<String, AgentProfile>
    ): String = buildString {
        appendLine("=== SPONSORED POST ===")
        appendLine(seed.content)
        if (seed.imageDescription.isNotBlank()) {
            appendLine("[Image: ${seed.imageDescription}]")
        }
        appendLine()

        if (visibleInteractions.isNotEmpty()) {
            appendLine("=== REACTIONS YOU CAN SEE ===")
            for (ix in visibleInteractions) {
                if (ix.action == ActionType.IGNORE) continue
                val authorName = agentMap[ix.agentId]?.name ?: "Unknown"
                appendLine("@$authorName [${ix.action.value}]: ${ix.content}")
            }
        } else {
            appendLine("(You are one of the first to see this post. No reactions yet.)")
        }
    }

    /** Phase 4: Analyze results and evolve the campaign */
    fun evolution(result: SimulationResult): String {
        val sampleComments = result.interactions
            .filter { it.action in listOf(ActionType.COMMENT, ActionType.QUOTE_SHARE) && it.content.isNotBlank() }
            .take(15)
            .joinToString("\n") { "- ${it.content}" }
            .ifBlank { "(No comments)" }

        val sampleMocks = result.interactions
            .filter { it.action == ActionType.MOCK && it.content.isNotBlank() }
            .take(10)
            .joinToString("\n") { "- ${it.content}" }
            .ifBlank { "(No mocks)" }

        return """
You are an expert social-media strategist analyzing a simulated campaign run.

CAMPAIGN:
- Content: ${result.seed.content}
- Image: ${result.seed.imageDescription}
- Goal: ${result.seed.goal.value}
- Target audience: ${result.seed.targetAudience}

RESULTS (Generation ${result.generation}):
- Total reach: ${result.totalReach}
- Likes: ${result.likes}
- Comments: ${result.comments}
- Shares: ${result.shares}
- Mocks: ${result.mocks}
- Sentiment score (-1 to 1): ${result.sentimentScore}
- Virality score (0 to 1): ${result.viralityScore}

SAMPLE COMMENTS:
$sampleComments

SAMPLE MOCKS:
$sampleMocks

---

Analyze:
1. WHY did the post perform this way? Be specific — reference the comments.
2. What resonated? What fell flat? What triggered backlash?
3. How should the copy/image be changed for the next generation?

Return ONLY a JSON object:
{
  "analysis": "2-3 sentence summary of why this happened",
  "strengths": ["list of what worked"],
  "weaknesses": ["list of what didn't work"],
  "revised_content": "the rewritten ad copy for generation ${result.generation + 1}",
  "revised_image_description": "updated image direction if needed (or same)",
  "confidence": float 0-1 for how much improvement is expected
}
Return ONLY the JSON object, no markdown fences.
""".trimIndent()
    }
}
