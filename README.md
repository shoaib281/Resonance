# Resonance

Social media campaign simulator built with [JetBrains Koog](https://www.jetbrains.com/koog/). Generates a population of psychographically diverse AI agents, drops a post into their synthetic feed, and watches what happens — pile-ons, viral cascades, echo chambers, mocking. Then rewrites the campaign and runs it again until it works.

Built at IC Hack 26.

## How it works

**Phase 1 — The Seed.** You provide the ad copy, an image description, a goal (brand awareness / clicks / controversy / engagement), and a target audience.

**Phase 2 — The Population.** A Koog agent generates 30–100 synthetic social media users with full psychographic profiles: MBTI type, political leaning, purchasing power, interests, current mood, and influence score. They're wired into a directed social graph using preferential attachment — high-influence agents attract more followers, shared interests boost connection probability.

**Phase 3 — The Simulation.** The post drops into the feed. Tick 0: influencers and a random sample see it first. Tick 1+: agents only see the post if someone they follow shared or commented on it. Each agent decides independently (via its own LLM call) whether to ignore, like, comment, share, quote-share, or mock — staying in character based on their personality, mood, and what reactions they can see. Second-order effects emerge naturally: if an influencer mocks the product, their followers pile on.

**Phase 4 — Evolution.** The system analyzes the synthetic comment threads, identifies what worked and what triggered backlash, rewrites the ad copy, and runs the simulation again. Repeats until the campaign hits a fitness threshold or max generations.

## Setup

```bash
# Requires JDK 17+
export OPENAI_API_KEY="your-key"
./gradlew run
```

## Configuration

Edit `Main.kt` to change:
- Campaign content, image, goal, and target audience
- Number of agents (30 for speed, 100 for depth)
- Number of ticks per generation
- Max generations and fitness threshold

## Project structure

```
src/main/kotlin/com/resonance/
├── Main.kt           # Entry point and orchestration loop
├── Models.kt         # Data types: AgentProfile, Interaction, SimulationResult
├── Prompts.kt        # All LLM prompts (centralized for tuning)
├── SocialGraph.kt    # Directed graph with preferential attachment
├── Population.kt     # Phase 2: LLM-powered persona generation
├── Simulation.kt     # Phase 3: Tick-based simulation engine
└── Evolution.kt      # Phase 4: Fitness scoring + campaign rewriting
```

## Built with

- [Koog](https://docs.koog.ai/) — JetBrains Kotlin AI agent framework
- OpenAI GPT-4o via Koog executor
- kotlinx-serialization for JSON parsing
- kotlinx-coroutines for async execution
