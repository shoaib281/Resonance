package com.resonance

import ai.koog.agents.core.agent.AIAgent
import ai.koog.prompt.executor.LLMPromptExecutor
import ai.koog.prompt.llm.OpenAIModels
import kotlinx.serialization.json.Json

// ==========================================================================
// Phase 4: Evolution — Genetic Algorithm
//
// Analyzes the simulation results using a Koog agent, identifies why the
// campaign failed or succeeded, and rewrites the campaign for the next gen.
//
// The fitness function is goal-aware:
//   - BRAND_AWARENESS: weights reach + positive sentiment
//   - CLICKS: weights shares (proxy for clicks) + reach
//   - CONTROVERSY: weights volume (comments + mocks), ignores sentiment
//   - ENGAGEMENT: balanced across all metrics
// ==========================================================================

suspend fun analyzeAndEvolve(
    executor: LLMPromptExecutor,
    result: SimulationResult,
): Pair<CampaignSeed, EvolutionResponse> {
    val prompt = Prompts.evolution(result)

    val agent = AIAgent(
        promptExecutor = executor,
        systemPrompt = "You are a social media strategist. You respond ONLY with valid JSON. No markdown, no explanation.",
        llmModel = OpenAIModels.Chat.GPT4o,
    )

    val raw = agent.run(prompt)

    val cleaned = raw
        .replace("```json", "")
        .replace("```", "")
        .trim()

    val json = Json { ignoreUnknownKeys = true; isLenient = true }
    val analysis = json.decodeFromString<EvolutionResponse>(cleaned)

    val newSeed = CampaignSeed(
        content = analysis.revised_content.ifBlank { result.seed.content },
        imageDescription = analysis.revised_image_description.ifBlank { result.seed.imageDescription },
        goal = result.seed.goal,
        targetAudience = result.seed.targetAudience,
    )

    return Pair(newSeed, analysis)
}

// ==========================================================================
// Fitness scoring
//
// TODO: Tune these weights based on your priorities.
// TODO: Add message distortion tracking — compare original copy to
//       quote_share texts to measure how the message mutates as it spreads.
// ==========================================================================

fun computeFitness(result: SimulationResult): Double {
    return when (result.seed.goal) {
        Goal.BRAND_AWARENESS -> {
            0.6 * norm(result.totalReach.toDouble(), 0.0, 100.0) +
            0.4 * norm(result.sentimentScore, -1.0, 1.0)
        }
        Goal.CLICKS -> {
            0.7 * norm(result.shares.toDouble(), 0.0, 50.0) +
            0.3 * norm(result.totalReach.toDouble(), 0.0, 100.0)
        }
        Goal.CONTROVERSY -> {
            0.5 * norm((result.comments + result.mocks).toDouble(), 0.0, 80.0) +
            0.5 * norm(result.totalReach.toDouble(), 0.0, 100.0)
        }
        Goal.ENGAGEMENT -> {
            0.3 * norm(result.totalReach.toDouble(), 0.0, 100.0) +
            0.3 * norm(result.comments.toDouble(), 0.0, 50.0) +
            0.2 * norm(result.shares.toDouble(), 0.0, 50.0) +
            0.2 * norm(result.sentimentScore, -1.0, 1.0)
        }
    }
}

private fun norm(value: Double, min: Double, max: Double): Double =
    ((value - min) / (max - min)).coerceIn(0.0, 1.0)
