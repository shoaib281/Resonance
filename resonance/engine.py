"""
Main orchestrator — ties all 4 phases together into the evolutionary loop.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import anthropic
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .evolution import analyze_and_evolve, compute_fitness
from .models import CampaignSeed, Goal, SimulationResult
from .population import build_social_graph, generate_agents_via_llm, get_influencers
from .simulation import run_simulation

console = Console()


def run_resonance(
    seed: CampaignSeed,
    num_agents: int = 30,
    num_ticks: int = 3,
    max_generations: int = 3,
    fitness_threshold: float = 0.75,
    model: str = "claude-sonnet-4-20250514",
    output_dir: str = "runs",
) -> list[SimulationResult]:
    """
    Full Resonance pipeline:
      1. Generate agents
      2. Build social graph
      3. Run simulation
      4. Analyze + evolve
      5. Repeat until fitness threshold or max generations
    """
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

    os.makedirs(output_dir, exist_ok=True)
    all_results: list[SimulationResult] = []
    current_seed = seed

    # --- Phase 2: Generate population (once — agents persist across generations) ---
    console.print(Panel("Phase 2: Generating Agent Population", style="bold cyan"))
    agents = generate_agents_via_llm(client, seed, count=num_agents, model=model)
    console.print(f"  Created {len(agents)} agents")

    graph = build_social_graph(agents)
    console.print(f"  Social graph: {graph.number_of_edges()} connections")

    top = get_influencers(agents)
    console.print(f"  Top influencers: {', '.join(a.name for a in top)}")

    for gen in range(1, max_generations + 1):
        console.print(Panel(f"Generation {gen} — Simulation", style="bold green"))
        console.print(f"  Content: {current_seed.content[:80]}...")

        # --- Phase 3: Run simulation ---
        result = run_simulation(
            client=client,
            seed=current_seed,
            agents=agents,
            graph=graph,
            num_ticks=num_ticks,
            generation=gen,
            model=model,
        )
        all_results.append(result)

        # Print results table
        _print_result_table(result)

        # Compute fitness
        fitness = compute_fitness(result)
        console.print(f"\n  [bold]Fitness score: {fitness:.3f}[/bold] (threshold: {fitness_threshold})")

        # Save generation data
        gen_path = Path(output_dir) / f"gen_{gen}.json"
        gen_path.write_text(json.dumps({
            "generation": gen,
            "seed": current_seed.model_dump(),
            "fitness": fitness,
            "analytics": {
                "total_reach": result.total_reach,
                "likes": result.likes,
                "comments": result.comments,
                "shares": result.shares,
                "mocks": result.mocks,
                "sentiment_score": result.sentiment_score,
                "virality_score": result.virality_score,
            },
            "interactions": [ix.model_dump() for ix in result.interactions],
        }, indent=2))

        if fitness >= fitness_threshold:
            console.print(Panel(
                f"Fitness {fitness:.3f} >= {fitness_threshold} — Campaign optimized!",
                style="bold green",
            ))
            break

        if gen < max_generations:
            # --- Phase 4: Evolve ---
            console.print(Panel(f"Phase 4: Evolving (Gen {gen} → {gen+1})", style="bold yellow"))
            new_seed, analysis = analyze_and_evolve(client, result, model=model)
            console.print(f"  Analysis: {analysis.get('analysis', 'N/A')}")
            console.print(f"  Strengths: {analysis.get('strengths', [])}")
            console.print(f"  Weaknesses: {analysis.get('weaknesses', [])}")
            console.print(f"  New copy: {new_seed.content[:80]}...")
            current_seed = new_seed

            # TODO: Optionally mutate agent moods between generations based on
            # how the last generation went.  e.g. if Gen 1 was mocked heavily,
            # agents might start Gen 2 more cynical.

    return all_results


def _print_result_table(result: SimulationResult) -> None:
    table = Table(title=f"Generation {result.generation} Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Total Reach", str(result.total_reach))
    table.add_row("Likes", str(result.likes))
    table.add_row("Comments", str(result.comments))
    table.add_row("Shares", str(result.shares))
    table.add_row("Mocks", str(result.mocks))
    table.add_row("Sentiment", f"{result.sentiment_score:+.3f}")
    table.add_row("Virality", f"{result.virality_score:.3f}")

    console.print(table)

    # Print some sample comments
    comments = [ix for ix in result.interactions if ix.content]
    if comments:
        console.print("\n  [bold]Sample reactions:[/bold]")
        for ix in comments[:8]:
            console.print(f"    [{ix.action.value}] {ix.content[:100]}")
