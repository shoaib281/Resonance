package com.resonance

import ai.koog.prompt.executor.llms.all.simpleOpenAIExecutor
import kotlinx.coroutines.runBlocking

// ==========================================================================
// Resonance — Social Media Campaign Simulator
//
// Built with JetBrains Koog framework.
// Set OPENAI_API_KEY in your environment before running.
//
// Flow:
//   Phase 1: User provides the "seed" (content, goal, audience)
//   Phase 2: Koog agent generates 30-100 diverse synthetic personas
//   Phase 3: Tick-based simulation — agents react, share, mock, cascade
//   Phase 4: LLM analyzes results, rewrites copy, runs again (evolution)
// ==========================================================================

fun main() = runBlocking {
    val apiKey = System.getenv("OPENAI_API_KEY")
        ?: error("Set OPENAI_API_KEY environment variable")

    val executor = simpleOpenAIExecutor(apiKey)

    // =====================================================================
    // PHASE 1: THE SEED — Edit this to test your campaign
    // =====================================================================
    val seed = CampaignSeed(
        content = """
            Introducing CloudBite — the protein bar that actually tastes good.
            No cap. 30g protein, zero guilt. Fuel your grind.
            Use code CLOUDBITE20 for 20% off. Link in bio.
        """.trimIndent(),
        imageDescription = """
            Bright neon-lit product shot of a protein bar on a gaming desk
            next to an RGB keyboard and energy drink. Gen-Z aesthetic.
        """.trimIndent(),
        goal = Goal.ENGAGEMENT,
        targetAudience = "Gen Z gamers and gym-goers in London, aged 18-25",
    )

    // Config
    val numAgents = 30          // 30 for speed, 50-100 for depth
    val numTicks = 3            // Simulation rounds per generation
    val maxGenerations = 3      // Max evolutionary cycles
    val fitnessThreshold = 0.70 // Stop if fitness exceeds this

    println("╔══════════════════════════════════════════════════════════════╗")
    println("║                    R E S O N A N C E                        ║")
    println("║          Social Media Campaign Simulator                    ║")
    println("║                 Built with Koog                             ║")
    println("╚══════════════════════════════════════════════════════════════╝")
    println()

    // =====================================================================
    // PHASE 2: GENERATE POPULATION
    // =====================================================================
    println("═══ Phase 2: Generating $numAgents Agent Personas ═══")
    val agents = generatePopulation(executor, seed, numAgents)
    println("  Created ${agents.size} agents")

    val graph = SocialGraph(agents)
    graph.build()
    println("  Social graph: ${graph.edgeCount} connections")

    val influencers = graph.getInfluencers(5)
    println("  Top influencers: ${influencers.joinToString(", ") { "${it.name} (${it.followers.size} followers)" }}")
    println()

    // =====================================================================
    // EVOLUTION LOOP
    // =====================================================================
    var currentSeed = seed
    val allResults = mutableListOf<SimulationResult>()

    for (gen in 1..maxGenerations) {
        // --- Phase 3: Simulate ---
        println("═══ Generation $gen: Running Simulation ═══")
        println("  Content: ${currentSeed.content.take(80)}...")
        println()

        val result = runSimulation(
            executor = executor,
            seed = currentSeed,
            agents = agents,
            graph = graph,
            numTicks = numTicks,
            generation = gen,
        )
        allResults.add(result)

        // Print results
        printResults(result)

        // Compute fitness
        val fitness = computeFitness(result)
        println("  Fitness: ${"%.3f".format(fitness)} (threshold: $fitnessThreshold)")
        println()

        if (fitness >= fitnessThreshold) {
            println("✓ Fitness ${"%.3f".format(fitness)} >= $fitnessThreshold — Campaign optimized!")
            break
        }

        if (gen < maxGenerations) {
            // --- Phase 4: Evolve ---
            println("═══ Phase 4: Evolving (Gen $gen → ${gen + 1}) ═══")
            val (newSeed, analysis) = analyzeAndEvolve(executor, result)

            println("  Analysis: ${analysis.analysis}")
            println("  Strengths: ${analysis.strengths}")
            println("  Weaknesses: ${analysis.weaknesses}")
            println("  New copy: ${newSeed.content.take(80)}...")
            println()

            currentSeed = newSeed

            // TODO: Optionally mutate agent moods between generations.
            // If Gen N was mocked heavily, agents could start Gen N+1 more cynical.
            // You could also add/remove agents to simulate audience churn.
        }
    }

    // =====================================================================
    // FINAL SUMMARY
    // =====================================================================
    println("═══════════════════════════════════════════════════════")
    println("  FINAL SUMMARY: ${allResults.size} generation(s) completed")
    for (r in allResults) {
        val f = computeFitness(r)
        println("  Gen ${r.generation}: reach=${r.totalReach} likes=${r.likes} comments=${r.comments} " +
                "shares=${r.shares} mocks=${r.mocks} sentiment=${"%.2f".format(r.sentimentScore)} " +
                "fitness=${"%.3f".format(f)}")
    }
    println("═══════════════════════════════════════════════════════")

    executor.close()
}

fun printResults(result: SimulationResult) {
    println("  ┌────────────────────────────────────┐")
    println("  │ Generation ${result.generation} Results               │")
    println("  ├──────────────┬─────────────────────┤")
    println("  │ Total Reach  │ ${result.totalReach.toString().padEnd(19)} │")
    println("  │ Likes        │ ${result.likes.toString().padEnd(19)} │")
    println("  │ Comments     │ ${result.comments.toString().padEnd(19)} │")
    println("  │ Shares       │ ${result.shares.toString().padEnd(19)} │")
    println("  │ Mocks        │ ${result.mocks.toString().padEnd(19)} │")
    println("  │ Sentiment    │ ${"%.3f".format(result.sentimentScore).padEnd(19)} │")
    println("  │ Virality     │ ${"%.3f".format(result.viralityScore).padEnd(19)} │")
    println("  └──────────────┴─────────────────────┘")

    val sampleReactions = result.interactions.filter { it.content.isNotBlank() }.take(8)
    if (sampleReactions.isNotEmpty()) {
        println("  Sample reactions:")
        for (ix in sampleReactions) {
            println("    [${ix.action.value}] ${ix.content.take(100)}")
        }
    }
    println()
}
