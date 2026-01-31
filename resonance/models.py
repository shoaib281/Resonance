"""
Core data models for the Resonance simulation.
"""
from __future__ import annotations

import uuid
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Goal(str, Enum):
    BRAND_AWARENESS = "brand_awareness"
    CLICKS = "clicks"
    CONTROVERSY = "controversy"
    ENGAGEMENT = "engagement"


class MBTIType(str, Enum):
    INTJ = "INTJ"; INTP = "INTP"; ENTJ = "ENTJ"; ENTP = "ENTP"
    INFJ = "INFJ"; INFP = "INFP"; ENFJ = "ENFJ"; ENFP = "ENFP"
    ISTJ = "ISTJ"; ISFJ = "ISFJ"; ESTJ = "ESTJ"; ESFJ = "ESFJ"
    ISTP = "ISTP"; ISFP = "ISFP"; ESTP = "ESTP"; ESFP = "ESFP"


class PoliticalLeaning(str, Enum):
    FAR_LEFT = "far_left"
    LEFT = "left"
    CENTER_LEFT = "center_left"
    CENTER = "center"
    CENTER_RIGHT = "center_right"
    RIGHT = "right"
    FAR_RIGHT = "far_right"


class PurchasingPower(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    LUXURY = "luxury"


class Mood(str, Enum):
    HAPPY = "happy"
    NEUTRAL = "neutral"
    IRRITABLE = "irritable"
    BORED = "bored"
    EXCITED = "excited"
    ANXIOUS = "anxious"
    CYNICAL = "cynical"


class ActionType(str, Enum):
    IGNORE = "ignore"
    LIKE = "like"
    COMMENT = "comment"
    SHARE = "share"
    QUOTE_SHARE = "quote_share"  # share with own commentary — message distortion
    MOCK = "mock"


# ---------------------------------------------------------------------------
# Campaign seed (Phase 1 input)
# ---------------------------------------------------------------------------

class CampaignSeed(BaseModel):
    """The DNA the user provides."""
    content: str = Field(..., description="The ad copy / post text")
    image_description: str = Field("", description="Description of image/video if any")
    goal: Goal = Goal.ENGAGEMENT
    target_audience: str = Field(..., description="Free-text audience description, e.g. 'Gen Z gamers in London'")


# ---------------------------------------------------------------------------
# Agent identity
# ---------------------------------------------------------------------------

class AgentProfile(BaseModel):
    """A single synthetic social-media user."""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str
    age: int
    location: str
    bio: str  # one-liner personality summary

    # psychographics
    mbti: MBTIType
    political_leaning: PoliticalLeaning
    purchasing_power: PurchasingPower
    interests: list[str]

    # dynamic state
    mood: Mood = Mood.NEUTRAL
    influence_score: float = Field(default=0.5, ge=0.0, le=1.0)

    # social graph edges (agent ids)
    following: list[str] = Field(default_factory=list)
    followers: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Interaction records
# ---------------------------------------------------------------------------

class Interaction(BaseModel):
    """A single action taken by an agent during the simulation."""
    agent_id: str
    action: ActionType
    content: str = ""  # comment text / quote text
    in_reply_to: Optional[str] = None  # interaction id this is responding to
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    tick: int = 0  # simulation step


class SimulationResult(BaseModel):
    """Aggregated outcome of one simulation run."""
    generation: int
    seed: CampaignSeed
    interactions: list[Interaction] = Field(default_factory=list)

    # analytics (computed after the run)
    total_reach: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    mocks: int = 0
    sentiment_score: float = 0.0  # -1 to 1
    virality_score: float = 0.0   # 0 to 1
    message_distortion: float = 0.0  # how much the message changed as it spread

    def compute_analytics(self) -> None:
        self.likes = sum(1 for i in self.interactions if i.action == ActionType.LIKE)
        self.comments = sum(1 for i in self.interactions if i.action in (ActionType.COMMENT, ActionType.MOCK))
        self.shares = sum(1 for i in self.interactions if i.action in (ActionType.SHARE, ActionType.QUOTE_SHARE))
        self.mocks = sum(1 for i in self.interactions if i.action == ActionType.MOCK)
        self.total_reach = self.likes + self.comments + self.shares

        total = len([i for i in self.interactions if i.action != ActionType.IGNORE])
        if total > 0:
            positive = self.likes + self.shares
            negative = self.mocks
            self.sentiment_score = round((positive - negative) / total, 3)
            self.virality_score = round(self.shares / total, 3)
