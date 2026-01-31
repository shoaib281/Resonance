"""All data models for the Resonance simulation."""

from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
import uuid
import random


class Goal(str, Enum):
    ENGAGEMENT = "engagement"
    BRAND_AWARENESS = "brand_awareness"
    CLICKS = "clicks"
    CONTROVERSY = "controversy"


class MBTIType(str, Enum):
    INTJ = "INTJ"; INTP = "INTP"; ENTJ = "ENTJ"; ENTP = "ENTP"
    INFJ = "INFJ"; INFP = "INFP"; ENFJ = "ENFJ"; ENFP = "ENFP"
    ISTJ = "ISTJ"; ISFJ = "ISFJ"; ESTJ = "ESTJ"; ESFJ = "ESFJ"
    ISTP = "ISTP"; ISFP = "ISFP"; ESTP = "ESTP"; ESFP = "ESFP"


class PoliticalLeaning(str, Enum):
    FAR_LEFT = "far_left"; LEFT = "left"; CENTER_LEFT = "center_left"
    CENTER = "center"; CENTER_RIGHT = "center_right"
    RIGHT = "right"; FAR_RIGHT = "far_right"


class PurchasingPower(str, Enum):
    LOW = "low"; MEDIUM = "medium"; HIGH = "high"; LUXURY = "luxury"


class Mood(str, Enum):
    HAPPY = "happy"; NEUTRAL = "neutral"; IRRITABLE = "irritable"
    BORED = "bored"; EXCITED = "excited"; ANXIOUS = "anxious"; CYNICAL = "cynical"


class ActionType(str, Enum):
    IGNORE = "ignore"; LIKE = "like"; COMMENT = "comment"
    SHARE = "share"; QUOTE_SHARE = "quote_share"; MOCK = "mock"


@dataclass
class CampaignSeed:
    content: str
    image_description: str
    goal: Goal
    target_audience: str


@dataclass
class AgentProfile:
    name: str
    age: int
    location: str
    bio: str
    mbti: MBTIType
    political_leaning: PoliticalLeaning
    purchasing_power: PurchasingPower
    interests: list[str]
    influence_score: float
    mood: Mood = field(default_factory=lambda: random.choice(list(Mood)))
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    followers: list[str] = field(default_factory=list)
    following: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "age": self.age,
            "location": self.location, "bio": self.bio,
            "mbti": self.mbti.value, "political_leaning": self.political_leaning.value,
            "purchasing_power": self.purchasing_power.value,
            "interests": self.interests, "influence_score": self.influence_score,
            "mood": self.mood.value,
        }


@dataclass
class Interaction:
    agent_id: str
    tick: int
    action: ActionType
    content: str = ""
    reasoning: str = ""
    new_mood: Mood = Mood.NEUTRAL


@dataclass
class SimulationResult:
    seed: CampaignSeed
    generation: int
    interactions: list[Interaction]

    @property
    def total_reach(self) -> int:
        return len([i for i in self.interactions if i.action != ActionType.IGNORE])

    @property
    def likes(self) -> int:
        return len([i for i in self.interactions if i.action == ActionType.LIKE])

    @property
    def comments(self) -> int:
        return len([i for i in self.interactions if i.action == ActionType.COMMENT])

    @property
    def shares(self) -> int:
        return len([i for i in self.interactions if i.action in (ActionType.SHARE, ActionType.QUOTE_SHARE)])

    @property
    def mocks(self) -> int:
        return len([i for i in self.interactions if i.action == ActionType.MOCK])

    @property
    def sentiment_score(self) -> float:
        weights = {ActionType.LIKE: 0.3, ActionType.COMMENT: 0.2, ActionType.SHARE: 0.5,
                   ActionType.QUOTE_SHARE: 0.3, ActionType.MOCK: -0.6, ActionType.IGNORE: 0.0}
        if not self.interactions:
            return 0.0
        total = sum(weights.get(i.action, 0.0) for i in self.interactions)
        return max(-1.0, min(1.0, total / len(self.interactions)))

    @property
    def virality_score(self) -> float:
        if not self.interactions:
            return 0.0
        viral = len([i for i in self.interactions if i.action in (ActionType.SHARE, ActionType.QUOTE_SHARE, ActionType.COMMENT)])
        return min(1.0, viral / len(self.interactions))
