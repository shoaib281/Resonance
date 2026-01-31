"""Phase 2: Population generation — local random (no API)."""

from __future__ import annotations
import random
from models import AgentProfile, CampaignSeed, MBTIType, PoliticalLeaning, PurchasingPower, Mood

FIRST_NAMES = [
    "Alex", "Jordan", "Maya", "Kai", "Priya", "Sam", "Luna", "Marcus", "Zara", "Theo",
    "Nadia", "Oscar", "Fatima", "Leo", "Ava", "Ravi", "Chloe", "Mateo", "Isla", "Darius",
    "Mina", "Elias", "Yuki", "Aiden", "Rosa", "Nico", "Suki", "Devon", "Layla", "Felix",
    "Tara", "Hugo", "Amira", "Jasper", "Stella", "Rio", "Ivy", "Dante", "Freya", "Samir",
    "Quinn", "Vera", "Atlas", "Noor", "Ezra", "Lila", "Otis", "Sage", "Milo", "Iris",
]

LOCATIONS = [
    "Brooklyn, NY", "London, UK", "Lagos, NG", "Tokyo, JP", "Berlin, DE",
    "Mumbai, IN", "São Paulo, BR", "Toronto, CA", "Sydney, AU", "Seoul, KR",
    "Austin, TX", "Portland, OR", "Paris, FR", "Nairobi, KE", "Dubai, AE",
    "Amsterdam, NL", "Melbourne, AU", "Chicago, IL", "Bangkok, TH", "Cape Town, ZA",
]

BIO_TEMPLATES = [
    "Chronically online {interest} nerd", "Hot takes and {interest}", "Just vibing tbh",
    "{interest} enthusiast | opinions are my own", "Sarcasm is my love language",
    "Professional overthinker", "touch grass advocate", "{interest} + coffee = me",
    "chaos agent", "lurker turned poster", "recovering doomscroller",
    "memes > meetings", "hot take machine", "silent observer",
    "digital nomad | {interest}", "ratio king", "just here for the drama",
]

INTEREST_POOL = [
    "tech", "fashion", "gaming", "music", "food", "fitness", "politics",
    "crypto", "art", "travel", "memes", "sports", "anime", "sustainability",
    "startups", "photography", "coffee", "film", "design", "books",
]


async def generate_population(
    seed: CampaignSeed,
    count: int = 30,
) -> list[AgentProfile]:
    names = random.sample(FIRST_NAMES, min(count, len(FIRST_NAMES)))
    agents = []

    for i in range(count):
        name = names[i] if i < len(names) else f"User{random.randint(100,999)}"
        interests = random.sample(INTEREST_POOL, random.randint(1, 3))
        bio_template = random.choice(BIO_TEMPLATES)
        bio = bio_template.format(interest=interests[0]) if "{interest}" in bio_template else bio_template

        agents.append(AgentProfile(
            name=name,
            age=random.randint(16, 55),
            location=random.choice(LOCATIONS),
            bio=bio,
            mbti=random.choice(list(MBTIType)),
            political_leaning=random.choice(list(PoliticalLeaning)),
            purchasing_power=random.choice(list(PurchasingPower)),
            interests=interests,
            influence_score=round(random.betavariate(2, 5), 2),  # skewed low, few influencers
            mood=random.choice(list(Mood)),
        ))

    return agents
