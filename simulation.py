"""
Simulation engine for Mimetic - orchestrates agent interactions and content spread.
"""
import random
import time
from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum
import networkx as nx

from agents import Agent, Mood, generate_population
from network import create_social_graph, get_neighbors, propagate_mood


class InteractionType(Enum):
    COMMENT = "comment"
    LIKE = "like"
    SHARE = "share"
    REPLY = "reply"
    IGNORE = "ignore"


@dataclass
class Comment:
    """Represents a comment in the simulation."""
    agent_id: str
    agent_name: str
    content: str
    sentiment: float  # -1 to 1
    timestamp: float
    parent_id: Optional[str] = None  # For replies
    likes: int = 0
    shares: int = 0


@dataclass
class Campaign:
    """Represents a marketing campaign being tested."""
    content: str
    goal: str  # awareness, engagement, controversy
    target_demographic: str
    image_url: Optional[str] = None


@dataclass
class SimulationMetrics:
    """Tracks simulation statistics."""
    total_comments: int = 0
    total_likes: int = 0
    total_shares: int = 0
    positive_sentiment: int = 0
    negative_sentiment: int = 0
    neutral_sentiment: int = 0
    reach: int = 0  # Unique agents who saw the content
    engagement_rate: float = 0.0
    viral_coefficient: float = 0.0  # Average shares per engaged user


@dataclass
class SimulationState:
    """Holds the complete state of a simulation run."""
    agents: list[Agent]
    graph: nx.DiGraph
    campaign: Campaign
    comments: list[Comment] = field(default_factory=list)
    interactions: list[tuple] = field(default_factory=list)  # (source, target, sentiment)
    engaged_agents: set = field(default_factory=set)
    metrics: SimulationMetrics = field(default_factory=SimulationMetrics)
    current_step: int = 0
    is_running: bool = False


class LLMProvider:
    """Handles LLM API calls for generating agent responses."""

    def __init__(self, provider: str = "openai", api_key: Optional[str] = None):
        self.provider = provider
        self.api_key = api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            if self.provider == "openai":
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            elif self.provider == "anthropic":
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    def generate_comment(
        self,
        agent: Agent,
        campaign: Campaign,
        context: list[Comment] = None,
        replying_to: Optional[Comment] = None
    ) -> tuple[str, float]:
        """Generate a comment from an agent's perspective. Returns (comment, sentiment)."""

        # Build context from previous comments
        context_str = ""
        if context:
            recent = context[-5:]  # Last 5 comments
            context_str = "\n\nRecent comments on this post:\n"
            for c in recent:
                context_str += f"- {c.agent_name}: \"{c.content}\"\n"

        reply_context = ""
        if replying_to:
            reply_context = f"\n\nYou are replying to {replying_to.agent_name} who said: \"{replying_to.content}\""

        prompt = f"""{agent.get_persona_prompt()}

A brand has posted the following content on social media:
"{campaign.content}"

Campaign goal: {campaign.goal}
Target audience: {campaign.target_demographic}
{context_str}{reply_context}

Based on your persona, write a short social media comment (1-2 sentences max) reacting to this post.
Also rate your sentiment from -1 (very negative) to 1 (very positive).

Respond in this exact format:
COMMENT: [your comment]
SENTIMENT: [number between -1 and 1]"""

        try:
            client = self._get_client()

            if self.provider == "openai":
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=150,
                    temperature=0.9,
                )
                text = response.choices[0].message.content
            elif self.provider == "anthropic":
                response = client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=150,
                    messages=[{"role": "user", "content": prompt}],
                )
                text = response.content[0].text

            # Parse response
            lines = text.strip().split('\n')
            comment = ""
            sentiment = 0.0

            for line in lines:
                if line.startswith("COMMENT:"):
                    comment = line.replace("COMMENT:", "").strip()
                elif line.startswith("SENTIMENT:"):
                    try:
                        sentiment = float(line.replace("SENTIMENT:", "").strip())
                        sentiment = max(-1, min(1, sentiment))
                    except:
                        sentiment = 0.0

            return comment, sentiment

        except Exception as e:
            # Fallback to rule-based generation
            return self._generate_fallback_comment(agent, campaign, replying_to)

    def _generate_fallback_comment(
        self,
        agent: Agent,
        campaign: Campaign,
        replying_to: Optional[Comment] = None
    ) -> tuple[str, float]:
        """Generate a comment without API access (rule-based fallback)."""

        archetype_responses = {
            "The Influencer": [
                ("Obsessed with this! My followers need to see this ", 0.8),
                ("This is giving exactly what it needs to give", 0.6),
                ("Not sure this fits my aesthetic tbh", -0.2),
            ],
            "The Skeptic": [
                ("Source? I'm gonna need more info on this", -0.3),
                ("Interesting but I have questions...", 0.0),
                ("This seems too good to be true", -0.4),
            ],
            "The Early Adopter": [
                ("Finally! I've been waiting for something like this", 0.7),
                ("This could be huge. Getting in early", 0.6),
                ("Innovative concept, curious to see how it develops", 0.4),
            ],
            "The Traditionalist": [
                ("What was wrong with the old way?", -0.3),
                ("I'll stick with what I know works", -0.2),
                ("If it ain't broke...", -0.1),
            ],
            "The Bargain Hunter": [
                ("What's the price point though?", 0.0),
                ("Anyone got a discount code?", 0.1),
                ("Looks expensive for what it is", -0.3),
            ],
            "The Activist": [
                ("But is it sustainable? What about the workers?", -0.2),
                ("Love to see brands taking a stand!", 0.6),
                ("This doesn't align with my values", -0.5),
            ],
            "The Lurker": [
                (".", 0.0),
                ("Interesting", 0.1),
                ("Hmm", 0.0),
            ],
            "The Troll": [
                ("Imagine falling for this lmao", -0.7),
                ("This is what's wrong with society", -0.6),
                ("ratio", -0.3),
            ],
            "The Supporter": [
                ("Love this! Keep up the great work!", 0.8),
                ("So happy to see this!", 0.7),
                ("This made my day!", 0.9),
            ],
            "The Expert": [
                ("From a technical standpoint, this is solid", 0.5),
                ("I've seen similar approaches fail before", -0.2),
                ("The implementation could be better, but the concept is sound", 0.3),
            ],
        }

        responses = archetype_responses.get(agent.archetype, [("Interesting post", 0.0)])

        # Mood influences response selection
        if agent.mood in [Mood.ANGRY, Mood.ANNOYED]:
            # Bias toward negative responses
            negative_responses = [(r, s) for r, s in responses if s < 0]
            if negative_responses:
                responses = negative_responses

        elif agent.mood in [Mood.HAPPY, Mood.EXCITED]:
            # Bias toward positive responses
            positive_responses = [(r, s) for r, s in responses if s > 0]
            if positive_responses:
                responses = positive_responses

        comment, sentiment = random.choice(responses)

        # Add reply context
        if replying_to:
            prefixes = ["@" + replying_to.agent_name + " ", "Replying to this - ", "^ This. "]
            comment = random.choice(prefixes) + comment

        return comment, sentiment


class SimulationEngine:
    """Orchestrates the multi-agent simulation."""

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        use_llm: bool = True
    ):
        self.llm = llm_provider or LLMProvider()
        self.use_llm = use_llm
        self.state: Optional[SimulationState] = None

    def initialize(
        self,
        campaign: Campaign,
        num_agents: int = 50,
        connectivity: float = 0.15
    ) -> SimulationState:
        """Initialize a new simulation."""
        agents = generate_population(num_agents, campaign.target_demographic)
        graph = create_social_graph(agents, connectivity)

        self.state = SimulationState(
            agents=agents,
            graph=graph,
            campaign=campaign,
        )

        return self.state

    def step(self, on_event: Optional[Callable] = None) -> list[Comment]:
        """Execute one simulation step. Returns new comments generated."""
        if not self.state:
            raise ValueError("Simulation not initialized")

        new_comments = []
        self.state.current_step += 1

        # Determine which agents will engage this step
        for agent in self.state.agents:
            if agent.id in self.state.engaged_agents:
                # Already engaged - might reply to comments
                if random.random() < agent.activity_level * 0.2:
                    # Possibly reply to a comment
                    if self.state.comments:
                        target_comment = random.choice(self.state.comments[-10:])
                        comment = self._generate_interaction(
                            agent,
                            InteractionType.REPLY,
                            replying_to=target_comment
                        )
                        if comment:
                            new_comments.append(comment)
                            if on_event:
                                on_event("reply", agent, comment)
            else:
                # New agent - decide whether to engage
                engagement_chance = agent.activity_level * 0.4

                # Increase chance if followers have engaged
                follower_engagement = sum(
                    1 for f in agent.following
                    if f in self.state.engaged_agents
                )
                if follower_engagement > 0:
                    engagement_chance += 0.1 * follower_engagement

                if random.random() < engagement_chance:
                    # Agent decides to engage
                    action = self._decide_action(agent)

                    if action == InteractionType.COMMENT:
                        comment = self._generate_interaction(agent, action)
                        if comment:
                            new_comments.append(comment)
                            if on_event:
                                on_event("comment", agent, comment)

                    elif action == InteractionType.LIKE:
                        self.state.metrics.total_likes += 1
                        if on_event:
                            on_event("like", agent, None)

                    elif action == InteractionType.SHARE:
                        self.state.metrics.total_shares += 1
                        # Sharing exposes content to follower's followers
                        self._propagate_exposure(agent)
                        if on_event:
                            on_event("share", agent, None)

                    self.state.engaged_agents.add(agent.id)
                    self.state.metrics.reach = len(self.state.engaged_agents)

        self._update_metrics()
        return new_comments

    def _decide_action(self, agent: Agent) -> InteractionType:
        """Decide what action an agent will take based on their personality."""
        weights = {
            InteractionType.COMMENT: agent.activity_level * 0.4,
            InteractionType.LIKE: 0.4,
            InteractionType.SHARE: agent.influence_score * 0.2,
            InteractionType.IGNORE: (1 - agent.activity_level) * 0.3,
        }

        # Modify based on archetype
        if agent.archetype == "The Lurker":
            weights[InteractionType.COMMENT] *= 0.2
            weights[InteractionType.LIKE] *= 1.5
        elif agent.archetype == "The Influencer":
            weights[InteractionType.SHARE] *= 2
        elif agent.archetype == "The Troll":
            weights[InteractionType.COMMENT] *= 2

        actions = list(weights.keys())
        probs = list(weights.values())
        total = sum(probs)
        probs = [p / total for p in probs]

        return random.choices(actions, weights=probs)[0]

    def _generate_interaction(
        self,
        agent: Agent,
        interaction_type: InteractionType,
        replying_to: Optional[Comment] = None
    ) -> Optional[Comment]:
        """Generate a comment or reply from an agent."""
        if interaction_type not in [InteractionType.COMMENT, InteractionType.REPLY]:
            return None

        if self.use_llm and self.llm.api_key:
            content, sentiment = self.llm.generate_comment(
                agent,
                self.state.campaign,
                self.state.comments,
                replying_to
            )
        else:
            content, sentiment = self.llm._generate_fallback_comment(
                agent,
                self.state.campaign,
                replying_to
            )

        comment = Comment(
            agent_id=agent.id,
            agent_name=agent.name,
            content=content,
            sentiment=sentiment,
            timestamp=time.time(),
            parent_id=replying_to.agent_id if replying_to else None,
        )

        self.state.comments.append(comment)
        self.state.metrics.total_comments += 1

        # Update sentiment metrics
        if sentiment > 0.2:
            self.state.metrics.positive_sentiment += 1
        elif sentiment < -0.2:
            self.state.metrics.negative_sentiment += 1
        else:
            self.state.metrics.neutral_sentiment += 1

        # Record interaction for visualization
        if replying_to:
            self.state.interactions.append((agent.id, replying_to.agent_id, sentiment))

        # Sentiment affects agent's mood
        self._update_mood(agent, sentiment)

        return comment

    def _update_mood(self, agent: Agent, sentiment: float):
        """Update agent's mood based on their interaction."""
        if sentiment > 0.5:
            agent.mood = random.choice([Mood.HAPPY, Mood.EXCITED])
        elif sentiment < -0.5:
            agent.mood = random.choice([Mood.ANNOYED, Mood.ANGRY])
        elif sentiment < -0.2:
            agent.mood = Mood.SKEPTICAL

        # Propagate mood through network
        propagate_mood(self.state.graph, self.state.agents, agent.id, agent.mood)

    def _propagate_exposure(self, agent: Agent):
        """When an agent shares, their followers become aware of the content."""
        followers = list(self.state.graph.predecessors(agent.id))
        for follower_id in followers:
            if follower_id not in self.state.engaged_agents:
                # Follower is now "aware" - increased chance to engage next step
                pass  # The engagement chance increase is handled in step()

    def _update_metrics(self):
        """Update simulation metrics."""
        if self.state.metrics.reach > 0:
            total_engagements = (
                self.state.metrics.total_comments +
                self.state.metrics.total_likes +
                self.state.metrics.total_shares
            )
            self.state.metrics.engagement_rate = total_engagements / self.state.metrics.reach

        if self.state.metrics.total_comments + self.state.metrics.total_likes > 0:
            self.state.metrics.viral_coefficient = (
                self.state.metrics.total_shares /
                (self.state.metrics.total_comments + self.state.metrics.total_likes)
            )

    def get_insights(self) -> dict:
        """Generate insights from the simulation results."""
        if not self.state or not self.state.comments:
            return {"error": "No simulation data available"}

        # Analyze sentiment distribution
        sentiments = [c.sentiment for c in self.state.comments]
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0

        # Find most engaging archetypes
        archetype_engagement = {}
        agent_dict = {a.id: a for a in self.state.agents}
        for comment in self.state.comments:
            agent = agent_dict.get(comment.agent_id)
            if agent:
                archetype_engagement[agent.archetype] = archetype_engagement.get(agent.archetype, 0) + 1

        # Find key influencers
        influencer_comments = [
            (c, agent_dict.get(c.agent_id))
            for c in self.state.comments
            if agent_dict.get(c.agent_id) and agent_dict.get(c.agent_id).influence_score > 0.7
        ]

        return {
            "total_reach": self.state.metrics.reach,
            "engagement_rate": f"{self.state.metrics.engagement_rate:.1%}",
            "viral_coefficient": f"{self.state.metrics.viral_coefficient:.2f}",
            "average_sentiment": avg_sentiment,
            "sentiment_breakdown": {
                "positive": self.state.metrics.positive_sentiment,
                "neutral": self.state.metrics.neutral_sentiment,
                "negative": self.state.metrics.negative_sentiment,
            },
            "top_archetypes": sorted(
                archetype_engagement.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            "influencer_reactions": len(influencer_comments),
            "total_comments": self.state.metrics.total_comments,
            "total_shares": self.state.metrics.total_shares,
            "total_likes": self.state.metrics.total_likes,
        }
