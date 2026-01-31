"""Directed social graph with preferential attachment."""

from __future__ import annotations
import random
from models import AgentProfile


class SocialGraph:
    def __init__(self, agents: list[AgentProfile]):
        self.agents = agents
        self.agent_map: dict[str, AgentProfile] = {a.id: a for a in agents}
        self.edges: list[tuple[str, str]] = []

    def build(self):
        """Wire edges based on influence score + shared interests."""
        for a in self.agents:
            a.followers = []
            a.following = []

        for a in self.agents:
            for b in self.agents:
                if a.id == b.id:
                    continue
                shared = len(set(a.interests) & set(b.interests))
                prob = 0.05 + (b.influence_score * 0.3) + (shared * 0.15)
                if random.random() < min(prob, 0.7):
                    a.following.append(b.id)
                    b.followers.append(a.id)
                    self.edges.append((a.id, b.id))

    @property
    def edge_count(self) -> int:
        return len(self.edges)

    def get_influencers(self, n: int = 5) -> list[AgentProfile]:
        return sorted(self.agents, key=lambda a: len(a.followers), reverse=True)[:n]

    def get_followers_of(self, agent_id: str) -> list[str]:
        agent = self.agent_map.get(agent_id)
        return agent.followers if agent else []

    def get_following(self, agent_id: str) -> list[str]:
        agent = self.agent_map.get(agent_id)
        return agent.following if agent else []

    def to_graph_data(self) -> dict:
        """Return nodes and edges for frontend visualization."""
        nodes = [{"id": a.id, "name": a.name, "influence": a.influence_score,
                   "mbti": a.mbti.value, "mood": a.mood.value,
                   "followers": len(a.followers)} for a in self.agents]
        edges = [{"source": s, "target": t} for s, t in self.edges]
        return {"nodes": nodes, "edges": edges}
