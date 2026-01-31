"""
Resonance — Social Media Campaign Simulator

Usage:
    python main.py

Set ANTHROPIC_API_KEY in your environment before running.
"""
from resonance.engine import run_resonance
from resonance.models import CampaignSeed, Goal


def main():
    # -----------------------------------------------------------------------
    # Phase 1: THE SEED — Edit this to test your campaign
    # -----------------------------------------------------------------------
    seed = CampaignSeed(
        content=(
            "Introducing CloudBite — the protein bar that actually tastes good. "
            "No cap. 30g protein, zero guilt. Fuel your grind. "
            "Use code CLOUDBITE20 for 20% off. Link in bio."
        ),
        image_description=(
            "Bright neon-lit product shot of a protein bar on a gaming desk "
            "next to a RGB keyboard and energy drink. Gen-Z aesthetic."
        ),
        goal=Goal.ENGAGEMENT,
        target_audience="Gen Z gamers and gym-goers in London, aged 18-25",
    )

    # -----------------------------------------------------------------------
    # Run the full pipeline
    # -----------------------------------------------------------------------
    results = run_resonance(
        seed=seed,
        num_agents=30,        # Number of synthetic users (30 for speed, 100 for depth)
        num_ticks=3,          # Simulation rounds per generation
        max_generations=3,    # Max evolutionary cycles
        fitness_threshold=0.7,
        model="claude-sonnet-4-20250514",   # Change to haiku for speed / opus for quality
    )

    print(f"\nCompleted {len(results)} generation(s).")
    print(f"Final fitness: {results[-1].sentiment_score:.3f} sentiment, "
          f"{results[-1].virality_score:.3f} virality")


if __name__ == "__main__":
    main()
