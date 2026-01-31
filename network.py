"""
Social network graph management for Mimetic.
Supports both static Plotly and animated streamlit-agraph visualizations.
"""
import random
import networkx as nx
import plotly.graph_objects as go
from agents import Agent, Mood


def create_social_graph(agents: list[Agent], connectivity: float = 0.15) -> nx.DiGraph:
    """
    Create a social network graph with realistic connection patterns.
    Uses preferential attachment - influential agents get more followers.
    """
    G = nx.DiGraph()

    # Add all agents as nodes
    for agent in agents:
        G.add_node(
            agent.id,
            name=agent.name,
            archetype=agent.archetype,
            influence=agent.influence_score,
            mood=agent.mood.value,
            age=agent.age,
        )

    # Create connections using modified preferential attachment
    agent_dict = {a.id: a for a in agents}

    for agent in agents:
        # Number of people to follow (based on activity level)
        n_following = int(agent.activity_level * len(agents) * connectivity)
        n_following = max(1, min(n_following, len(agents) - 1))

        # Prefer to follow influential people
        other_agents = [a for a in agents if a.id != agent.id]
        weights = [a.influence_score ** 2 for a in other_agents]
        total = sum(weights)
        probs = [w / total for w in weights]

        # Select who to follow
        following = random.choices(other_agents, weights=probs, k=min(n_following, len(other_agents)))

        for followed in following:
            if not G.has_edge(agent.id, followed.id):
                G.add_edge(agent.id, followed.id)
                agent.following.append(followed.id)
                followed.followers.append(agent.id)

    return G


def get_mood_color(mood: str) -> str:
    """Get node color based on mood."""
    mood_colors = {
        "happy": "#22c55e",      # Green
        "excited": "#84cc16",    # Lime
        "neutral": "#6b7280",    # Gray
        "skeptical": "#f59e0b",  # Amber
        "annoyed": "#f97316",    # Orange
        "angry": "#ef4444",      # Red
    }
    return mood_colors.get(mood, "#6b7280")


def get_archetype_shape(archetype: str) -> str:
    """Get node shape based on archetype."""
    shapes = {
        "The Influencer": "star",
        "The Expert": "diamond",
        "The Troll": "triangle",
        "The Lurker": "dot",
    }
    return shapes.get(archetype, "dot")


def create_agraph_config():
    """Create configuration for streamlit-agraph with physics simulation."""
    from streamlit_agraph import Config

    return Config(
        width="100%",
        height=500,
        directed=True,
        physics={
            "enabled": True,
            "solver": "forceAtlas2Based",
            "forceAtlas2Based": {
                "gravitationalConstant": -50,
                "centralGravity": 0.01,
                "springLength": 100,
                "springConstant": 0.08,
                "damping": 0.4,
                "avoidOverlap": 0.5
            },
            "stabilization": {
                "enabled": True,
                "iterations": 100,
                "updateInterval": 25
            }
        },
        hierarchical=False,
        nodeHighlightBehavior=True,
        highlightColor="#7c3aed",
        collapsible=False,
        node={
            "labelProperty": "label",
            "renderLabel": True,
        },
        link={
            "labelProperty": "label",
            "renderLabel": False,
            "color": "rgba(255,255,255,0.1)",
        }
    )


def create_agraph_nodes_edges(
    G: nx.DiGraph,
    agents: list[Agent],
    engaged_agents: set = None,
    active_agents: set = None,
    interactions: list[tuple] = None
):
    """Create nodes and edges for streamlit-agraph visualization."""
    from streamlit_agraph import Node, Edge

    agent_dict = {a.id: a for a in agents}
    engaged_agents = engaged_agents or set()
    active_agents = active_agents or set()
    interactions = interactions or []

    nodes = []
    edges = []

    # Create interaction lookup for edge highlighting
    interaction_pairs = {(src, tgt): sent for src, tgt, sent in interactions}

    for agent in agents:
        # Determine node appearance based on state
        is_engaged = agent.id in engaged_agents
        is_active = agent.id in active_agents

        # Base size on influence
        size = 15 + (agent.influence_score * 25)

        # Color based on mood
        color = get_mood_color(agent.mood.value)

        # Glow effect for active/engaged nodes
        if is_active:
            # Currently interacting - bright glow
            border_color = "#ffffff"
            border_width = 4
            size *= 1.3
        elif is_engaged:
            # Has engaged - subtle highlight
            border_color = "#a855f7"
            border_width = 2
        else:
            # Not yet engaged - dimmed
            border_color = "rgba(255,255,255,0.2)"
            border_width = 1
            color = _dim_color(color, 0.4)

        nodes.append(Node(
            id=agent.id,
            label=agent.name,
            size=size,
            color={
                "background": color,
                "border": border_color,
                "highlight": {
                    "background": "#a855f7",
                    "border": "#ffffff"
                }
            },
            borderWidth=border_width,
            borderWidthSelected=4,
            font={"color": "#ffffff", "size": 10},
            title=f"{agent.name}\n{agent.archetype}\nMood: {agent.mood.value}\nInfluence: {agent.influence_score:.0%}",
            shape="dot",
            shadow={
                "enabled": is_active,
                "color": color,
                "size": 20,
                "x": 0,
                "y": 0
            }
        ))

    # Create edges
    for edge in G.edges():
        source, target = edge

        # Check if this edge was part of a recent interaction
        sentiment = interaction_pairs.get((source, target))
        if sentiment is not None:
            # Interaction edge - colored by sentiment
            if sentiment > 0.2:
                edge_color = "rgba(34, 197, 94, 0.8)"  # Green
                width = 3
            elif sentiment < -0.2:
                edge_color = "rgba(239, 68, 68, 0.8)"  # Red
                width = 3
            else:
                edge_color = "rgba(147, 51, 234, 0.8)"  # Purple
                width = 2
        else:
            # Regular edge
            edge_color = "rgba(255, 255, 255, 0.08)"
            width = 1

        edges.append(Edge(
            source=source,
            target=target,
            color=edge_color,
            width=width,
            smooth={"enabled": True, "type": "continuous"}
        ))

    return nodes, edges


def _dim_color(hex_color: str, factor: float) -> str:
    """Dim a hex color by a factor."""
    hex_color = hex_color.lstrip('#')
    r = int(int(hex_color[0:2], 16) * factor)
    g = int(int(hex_color[2:4], 16) * factor)
    b = int(int(hex_color[4:6], 16) * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


def visualize_graph(
    G: nx.DiGraph,
    agents: list[Agent],
    interactions: list[tuple] = None,
    highlight_nodes: list[str] = None,
    title: str = "Social Network"
) -> go.Figure:
    """Create a static Plotly visualization (fallback)."""

    # Use spring layout for positioning
    pos = nx.spring_layout(G, k=2, iterations=50, seed=42)

    agent_dict = {a.id: a for a in agents}

    # Create edge traces
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='rgba(255,255,255,0.1)'),
        hoverinfo='none',
        mode='lines',
    )

    # Create interaction edge traces (highlighted)
    interaction_traces = []
    if interactions:
        for source, target, sentiment in interactions[-15:]:
            if source in pos and target in pos:
                x0, y0 = pos[source]
                x1, y1 = pos[target]
                color = "#22c55e" if sentiment > 0 else "#ef4444" if sentiment < 0 else "#a855f7"
                interaction_traces.append(go.Scatter(
                    x=[x0, x1], y=[y0, y1],
                    line=dict(width=3, color=color),
                    hoverinfo='none',
                    mode='lines',
                    opacity=0.8
                ))

    # Create node traces
    node_x = []
    node_y = []
    node_colors = []
    node_sizes = []
    node_text = []
    node_borders = []

    highlight_set = set(highlight_nodes) if highlight_nodes else set()

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

        agent = agent_dict.get(node)
        if agent:
            color = get_mood_color(agent.mood.value)
            size = 15 + (agent.influence_score * 25)
            text = f"{agent.name}<br>{agent.archetype}<br>Mood: {agent.mood.value}"

            if node not in highlight_set:
                color = _dim_color(color, 0.4)
        else:
            color = "#6b7280"
            size = 15
            text = node

        node_colors.append(color)
        node_sizes.append(size)
        node_text.append(text)
        node_borders.append("#ffffff" if node in highlight_set else "rgba(255,255,255,0.2)")

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        text=node_text,
        marker=dict(
            showscale=False,
            color=node_colors,
            size=node_sizes,
            line=dict(width=2, color=node_borders)
        )
    )

    # Create figure
    fig = go.Figure(
        data=[edge_trace] + interaction_traces + [node_trace],
        layout=go.Layout(
            title=dict(text=title, font=dict(size=14, color="#ffffff")),
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
        )
    )

    return fig


def get_neighbors(G: nx.DiGraph, agent_id: str, depth: int = 1) -> set:
    """Get all agents within a certain connection depth."""
    neighbors = set()

    current_level = {agent_id}
    for _ in range(depth):
        next_level = set()
        for node in current_level:
            next_level.update(G.successors(node))
            next_level.update(G.predecessors(node))
        neighbors.update(next_level)
        current_level = next_level

    neighbors.discard(agent_id)
    return neighbors


def propagate_mood(G: nx.DiGraph, agents: list[Agent], source_id: str, mood_change: Mood):
    """Propagate mood changes through the network based on influence."""
    agent_dict = {a.id: a for a in agents}
    source = agent_dict.get(source_id)

    if not source:
        return

    # Get followers (people who follow the source)
    followers = list(G.predecessors(source_id))

    for follower_id in followers:
        follower = agent_dict.get(follower_id)
        if follower:
            # Probability of mood influence based on source influence and follower susceptibility
            influence_prob = source.influence_score * follower.susceptibility
            if random.random() < influence_prob * 0.3:
                follower.mood = mood_change
