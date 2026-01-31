package com.resonance

import ai.koog.agents.core.agent.AIAgent
import ai.koog.prompt.executor.LLMPromptExecutor
import ai.koog.prompt.llm.OpenAIModels
import kotlinx.serialization.json.Json
import kotlin.random.Random

// ==========================================================================
// Phase 3: Tick-based Simulation Engine
//
// Each synthetic persona gets its own Koog AIAgent call to decide how they
// react to the post. The simulation runs in ticks:
//
//   Tick 0: Seed viewers (influencers + random sample) see the post directly.
//   Tick 1+: Agents see the post ONLY if someone they follow shared/commented.
//            This is where second-order effects + viral cascades emerge.
//
// Key emergent behaviors:
//   - Pile-ons: if influencer mocks, followers join in
//   - Viral spread: shares propagate to new subgraphs
//   - Message distortion: quote_shares reframe the original content
//   - Echo chambers: agents in tight clusters amplify each other
// ==========================================================================

suspend fun runSimulation(
    executor: LLMPromptExecutor,
    seed: CampaignSeed,
    agents: List<AgentProfile>,
    graph: SocialGraph,
    numTicks: Int = 3,
    generation: Int = 1,
): SimulationResult {
    val agentMap = agents.associateBy { it.id }
    val allInteractions = mutableListOf<Interaction>()
    val agentsWhoSawPost = mutableSetOf<String>()
    val influencerIds = graph.getInfluencers(5).map { it.id }.toSet()

    // Tick 0: initial exposure — influencers + random 30%
    val initialViewers = buildSet {
        addAll(influencerIds)
        addAll(agents.shuffled().take(agents.size / 3).map { it.id })
    }

    for (tick in 0 until numTicks) {
        val viewerIds: Set<String> = if (tick == 0) {
            initialViewers
        } else {
            // --- SECOND-ORDER SPREAD ---
            // Agents see the post if someone they follow shared or quoted it
            val sharers = allInteractions
                .filter { it.action in listOf(ActionType.SHARE, ActionType.QUOTE_SHARE) }
                .map { it.agentId }
                .toSet()

            val commenters = allInteractions
                .filter { it.action in listOf(ActionType.COMMENT, ActionType.MOCK) }
                .map { it.agentId }
                .toSet()

            val newViewers = mutableSetOf<String>()

            // Everyone following a sharer sees it (share = explicit distribution)
            for (sharerId in sharers) {
                val sharer = agentMap[sharerId] ?: continue
                newViewers.addAll(sharer.followers.filter { it !in agentsWhoSawPost })
            }

            // 30% chance the algorithm surfaces it to followers of commenters
            // (simulates algorithmic amplification)
            for (commenterId in commenters) {
                val commenter = agentMap[commenterId] ?: continue
                for (followerId in commenter.followers) {
                    if (followerId !in agentsWhoSawPost && Random.nextDouble() < 0.3) {
                        newViewers.add(followerId)
                    }
                }
            }

            newViewers
        }

        println("    Tick $tick: ${viewerIds.size} agents viewing")

        for (agentId in viewerIds) {
            if (agentId in agentsWhoSawPost && tick > 0) continue
            agentsWhoSawPost.add(agentId)

            val agent = agentMap[agentId] ?: continue

            // What can this agent see?
            // Reactions from people they follow + reactions from top influencers
            val visible = allInteractions.filter { ix ->
                ix.agentId in agent.following || ix.agentId in influencerIds
            }

            val context = Prompts.buildContext(seed, visible, agentMap)

            val (action, content, newMood) = simulateAgentReaction(executor, agent, context)
            agent.mood = newMood

            allInteractions.add(
                Interaction(
                    agentId = agent.id,
                    action = action,
                    content = content,
                    tick = tick,
                )
            )
        }
    }

    return SimulationResult(
        generation = generation,
        seed = seed,
        interactions = allInteractions,
    ).also { it.computeAnalytics() }
}

// ---------------------------------------------------------------------------
// Run a single agent's reaction through a Koog AIAgent
// ---------------------------------------------------------------------------

private suspend fun simulateAgentReaction(
    executor: LLMPromptExecutor,
    agent: AgentProfile,
    context: String,
): Triple<ActionType, String, Mood> {
    val systemPrompt = buildString {
        appendLine("You are roleplaying as ${agent.name}, a ${agent.age}-year-old from ${agent.location}.")
        appendLine("Bio: ${agent.bio}")
        appendLine("You respond ONLY with valid JSON. No markdown, no explanation.")
    }

    val userPrompt = Prompts.agentBrain(agent, context)

    val koogAgent = AIAgent(
        promptExecutor = executor,
        systemPrompt = systemPrompt,
        llmModel = OpenAIModels.Chat.GPT4o,
    )

    return try {
        val raw = koogAgent.run(userPrompt)
        parseAgentAction(raw, agent.mood)
    } catch (e: Exception) {
        println("      [WARN] Agent ${agent.name} errored: ${e.message}")
        Triple(ActionType.IGNORE, "", agent.mood)
    }
}

// ---------------------------------------------------------------------------
// JSON parsing
// ---------------------------------------------------------------------------

private val jsonParser = Json { ignoreUnknownKeys = true; isLenient = true }

fun parseAgentAction(raw: String, fallbackMood: Mood): Triple<ActionType, String, Mood> {
    val cleaned = raw
        .replace("```json", "")
        .replace("```", "")
        .trim()

    return try {
        val resp = jsonParser.decodeFromString<AgentActionResponse>(cleaned)
        Triple(
            ActionType.fromValue(resp.action),
            resp.content,
            Mood.fromValue(resp.new_mood),
        )
    } catch (e: Exception) {
        Triple(ActionType.IGNORE, "", fallbackMood)
    }
}
