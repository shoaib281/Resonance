package com.resonance

import kotlin.random.Random

// ==========================================================================
// Social Graph — pure Kotlin, no external graph lib needed
// ==========================================================================

/**
 * Directed social graph. Nodes are agent IDs, edges represent "follows".
 * Built with preferential attachment weighted by influence score.
 */
class SocialGraph(val agents: List<AgentProfile>) {

    private val adjacency: MutableMap<String, MutableSet<String>> = mutableMapOf()
    private val agentMap: Map<String, AgentProfile> = agents.associateBy { it.id }

    val edgeCount: Int get() = adjacency.values.sumOf { it.size }

    init {
        for (a in agents) {
            adjacency[a.id] = mutableSetOf()
        }
    }

    /**
     * Wire up the graph. Each agent decides who to follow based on:
     * - Target's influence score (higher = more likely to be followed)
     * - Shared interests (boost probability)
     * - Base edge probability
     */
    fun build(baseProbability: Double = 0.15) {
        for (a in agents) {
            for (b in agents) {
                if (a.id == b.id) continue

                var p = baseProbability * b.influenceScore

                // Shared interest boost
                val shared = a.interests.intersect(b.interests.toSet())
                p += 0.05 * shared.size
                p = p.coerceAtMost(0.8)

                if (Random.nextDouble() < p) {
                    adjacency[a.id]!!.add(b.id)
                    a.following.add(b.id)
                    b.followers.add(a.id)
                }
            }
        }
    }

    /** Get all agents that [agentId] follows. */
    fun getFollowing(agentId: String): Set<String> = adjacency[agentId] ?: emptySet()

    /** Get top N agents by follower count. */
    fun getInfluencers(topN: Int = 5): List<AgentProfile> =
        agents.sortedByDescending { it.followers.size }.take(topN)

    /** Get agents who follow anyone in [agentIds]. */
    fun getFollowersOf(agentIds: Set<String>): Set<String> {
        val result = mutableSetOf<String>()
        for (agent in agents) {
            if (agent.following.any { it in agentIds }) {
                result.add(agent.id)
            }
        }
        return result
    }
}
