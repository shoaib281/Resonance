package com.resonance

import ai.koog.agents.core.agent.AIAgent
import ai.koog.prompt.executor.LLMPromptExecutor
import ai.koog.prompt.llm.OpenAIModels
import kotlinx.serialization.json.Json

// ==========================================================================
// Phase 2: Population Generation via Koog Agent
//
// Uses a Koog AIAgent to generate diverse synthetic personas that match
// the target audience. The LLM produces a JSON array of profiles with
// psychographics, interests, and influence scores.
// ==========================================================================

suspend fun generatePopulation(
    executor: LLMPromptExecutor,
    seed: CampaignSeed,
    count: Int = 30,
): List<AgentProfile> {
    val prompt = Prompts.populationGen(seed.targetAudience, count)

    val agent = AIAgent(
        promptExecutor = executor,
        systemPrompt = "You are a persona generator. You output ONLY valid JSON arrays. No markdown, no explanation.",
        llmModel = OpenAIModels.Chat.GPT4o,
    )

    val raw = agent.run(prompt)

    return parseAgentProfiles(raw)
}

/**
 * Parse the LLM's JSON response into AgentProfile objects.
 */
fun parseAgentProfiles(raw: String): List<AgentProfile> {
    val cleaned = raw
        .replace("```json", "")
        .replace("```", "")
        .trim()

    val json = Json { ignoreUnknownKeys = true; isLenient = true }
    val parsed = json.decodeFromString<List<AgentGenResponse>>(cleaned)

    return parsed.map { p ->
        AgentProfile(
            name = p.name,
            age = p.age,
            location = p.location,
            bio = p.bio,
            mbti = MBTIType.entries.firstOrNull { it.name == p.mbti } ?: MBTIType.ENFP,
            politicalLeaning = PoliticalLeaning.entries.firstOrNull { it.value == p.political_leaning }
                ?: PoliticalLeaning.CENTER,
            purchasingPower = PurchasingPower.entries.firstOrNull { it.value == p.purchasing_power }
                ?: PurchasingPower.MEDIUM,
            interests = p.interests,
            influenceScore = p.influence_score.coerceIn(0.0, 1.0),
            mood = Mood.entries.random(),
        )
    }
}
