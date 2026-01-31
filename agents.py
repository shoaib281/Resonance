"""
Agent system for Mimetic - AI personas with distinct personalities and behaviors.
"""
import random
import json
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class Mood(Enum):
    HAPPY = "happy"
    NEUTRAL = "neutral"
    ANNOYED = "annoyed"
    ANGRY = "angry"
    EXCITED = "excited"
    SKEPTICAL = "skeptical"


class PoliticalLeaning(Enum):
    LEFT = "progressive"
    CENTER_LEFT = "center-left"
    CENTER = "moderate"
    CENTER_RIGHT = "center-right"
    RIGHT = "conservative"


MBTI_TYPES = [
    "INTJ", "INTP", "ENTJ", "ENTP",
    "INFJ", "INFP", "ENFJ", "ENFP",
    "ISTJ", "ISFJ", "ESTJ", "ESFJ",
    "ISTP", "ISFP", "ESTP", "ESFP"
]

ARCHETYPES = [
    ("The Influencer", "trendy, image-conscious, loves sharing discoveries"),
    ("The Skeptic", "critical thinker, questions everything, needs proof"),
    ("The Early Adopter", "tech-savvy, loves new things, opinion leader"),
    ("The Traditionalist", "values stability, prefers trusted brands"),
    ("The Bargain Hunter", "price-conscious, always looking for deals"),
    ("The Activist", "cause-driven, passionate about social issues"),
    ("The Lurker", "observes more than participates, rarely comments"),
    ("The Troll", "provocative, enjoys stirring controversy"),
    ("The Supporter", "positive, encouraging, builds community"),
    ("The Expert", "knowledgeable, provides detailed insights"),
]

NAMES = [
    "Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Quinn", "Avery",
    "Skyler", "Dakota", "Phoenix", "River", "Sage", "Blake", "Drew", "Jamie",
    "Reese", "Cameron", "Hayden", "Parker", "Rowan", "Finley", "Emery", "Kai",
    "Charlie", "Sam", "Pat", "Robin", "Jesse", "Lee", "Max", "Zoe", "Nina",
    "Omar", "Priya", "Chen", "Fatima", "Luis", "Aisha", "Yuki", "Dmitri"
]


@dataclass
class Agent:
    """Represents a synthetic social media user."""
    id: str
    name: str
    age: int
    archetype: str
    archetype_description: str
    mbti: str
    political_leaning: PoliticalLeaning
    income_level: str  # low, medium, high
    interests: list[str]
    mood: Mood = Mood.NEUTRAL
    influence_score: float = 0.5  # 0-1, affects how much they influence others
    susceptibility: float = 0.5  # 0-1, how easily influenced by others
    activity_level: float = 0.5  # 0-1, how often they engage
    followers: list[str] = field(default_factory=list)
    following: list[str] = field(default_factory=list)

    def get_persona_prompt(self) -> str:
        """Generate a prompt describing this agent's persona."""
        return f"""You are {self.name}, a {self.age}-year-old social media user.

Personality Type: {self.mbti}
Archetype: {self.archetype} - {self.archetype_description}
Political Leaning: {self.political_leaning.value}
Income Level: {self.income_level}
Interests: {', '.join(self.interests)}
Current Mood: {self.mood.value}
Influence Level: {"High" if self.influence_score > 0.7 else "Medium" if self.influence_score > 0.4 else "Low"}

You respond authentically as this persona would. Your comments should reflect your personality, mood, and biases.
Keep responses short (1-3 sentences) like real social media comments."""

    def to_dict(self) -> dict:
        """Convert agent to dictionary for display."""
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "archetype": self.archetype,
            "mbti": self.mbti,
            "political_leaning": self.political_leaning.value,
            "income_level": self.income_level,
            "interests": self.interests,
            "mood": self.mood.value,
            "influence_score": self.influence_score,
            "followers": len(self.followers),
            "following": len(self.following),
        }


INTEREST_POOLS = {
    "tech": ["AI", "startups", "gadgets", "programming", "crypto", "gaming"],
    "lifestyle": ["fitness", "travel", "food", "fashion", "wellness", "home decor"],
    "culture": ["music", "movies", "art", "books", "podcasts", "memes"],
    "business": ["investing", "entrepreneurship", "marketing", "finance", "career"],
    "social": ["politics", "environment", "social justice", "community", "volunteering"],
}


def generate_agent(agent_id: int, target_demographic: Optional[str] = None) -> Agent:
    """Generate a random agent with consistent personality traits."""
    archetype, archetype_desc = random.choice(ARCHETYPES)

    # Age distribution based on social media demographics
    age_weights = [0.05, 0.25, 0.30, 0.20, 0.15, 0.05]
    age_ranges = [(13, 17), (18, 24), (25, 34), (35, 44), (45, 54), (55, 70)]
    age_range = random.choices(age_ranges, weights=age_weights)[0]
    age = random.randint(*age_range)

    # Select interests (2-4 from different pools)
    interest_categories = random.sample(list(INTEREST_POOLS.keys()), k=random.randint(2, 3))
    interests = []
    for cat in interest_categories:
        interests.extend(random.sample(INTEREST_POOLS[cat], k=random.randint(1, 2)))

    # Influence and activity vary by archetype
    influence_modifiers = {
        "The Influencer": (0.7, 0.9),
        "The Expert": (0.6, 0.8),
        "The Early Adopter": (0.5, 0.7),
        "The Lurker": (0.1, 0.3),
        "The Troll": (0.3, 0.6),
    }

    influence_range = influence_modifiers.get(archetype, (0.3, 0.6))
    influence_score = random.uniform(*influence_range)

    activity_modifiers = {
        "The Lurker": (0.1, 0.3),
        "The Influencer": (0.7, 0.95),
        "The Troll": (0.6, 0.9),
        "The Activist": (0.6, 0.85),
    }

    activity_range = activity_modifiers.get(archetype, (0.3, 0.7))
    activity_level = random.uniform(*activity_range)

    return Agent(
        id=f"agent_{agent_id}",
        name=random.choice(NAMES) + str(random.randint(10, 99)),
        age=age,
        archetype=archetype,
        archetype_description=archetype_desc,
        mbti=random.choice(MBTI_TYPES),
        political_leaning=random.choice(list(PoliticalLeaning)),
        income_level=random.choices(["low", "medium", "high"], weights=[0.3, 0.5, 0.2])[0],
        interests=interests,
        mood=random.choice(list(Mood)),
        influence_score=influence_score,
        susceptibility=random.uniform(0.2, 0.8),
        activity_level=activity_level,
    )


def generate_population(size: int = 50, target_demographic: Optional[str] = None) -> list[Agent]:
    """Generate a population of agents."""
    return [generate_agent(i, target_demographic) for i in range(size)]
