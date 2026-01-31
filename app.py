"""
Mimetic - Synthetic Social Network Simulation
A marketing campaign testing platform using multi-agent AI systems.
"""
import streamlit as st
import time
import os
from dotenv import load_dotenv
from streamlit_agraph import agraph, Node, Edge, Config

from agents import generate_population, Mood
from network import (
    create_social_graph,
    create_agraph_nodes_edges,
    create_agraph_config,
    get_mood_color,
    visualize_graph
)
from simulation import SimulationEngine, Campaign, LLMProvider

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Mimetic",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for clean, modern UI
st.markdown("""
<style>
    /* Dark theme base */
    .stApp {
        background: #0a0a0f;
    }

    /* Hide default streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Main header styling */
    .main-title {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0;
        letter-spacing: -1px;
    }

    .sub-title {
        text-align: center;
        color: #6b7280;
        font-size: 1rem;
        margin-top: 0.5rem;
        margin-bottom: 2rem;
    }

    /* Card styling */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.5rem;
        backdrop-filter: blur(10px);
    }

    /* Metric cards */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin: 1rem 0;
    }

    .metric-card {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border: 1px solid rgba(102, 126, 234, 0.2);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #fff;
        margin: 0;
    }

    .metric-label {
        font-size: 0.75rem;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 0.25rem;
    }

    /* Comment feed */
    .feed-container {
        max-height: 500px;
        overflow-y: auto;
        padding-right: 0.5rem;
    }

    .comment-bubble {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.75rem;
        border-left: 3px solid #667eea;
        animation: slideIn 0.3s ease-out;
    }

    .comment-bubble.positive {
        border-left-color: #22c55e;
        background: rgba(34, 197, 94, 0.05);
    }

    .comment-bubble.negative {
        border-left-color: #ef4444;
        background: rgba(239, 68, 68, 0.05);
    }

    .comment-bubble.neutral {
        border-left-color: #6b7280;
    }

    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateX(-10px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    .comment-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.25rem;
    }

    .comment-name {
        font-weight: 600;
        color: #a78bfa;
        font-size: 0.9rem;
    }

    .comment-archetype {
        font-size: 0.7rem;
        color: #6b7280;
        background: rgba(255, 255, 255, 0.05);
        padding: 2px 6px;
        border-radius: 4px;
    }

    .comment-text {
        color: #e5e7eb;
        font-size: 0.9rem;
        line-height: 1.4;
    }

    /* Sentiment badge */
    .sentiment-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 4px;
    }

    .sentiment-dot.positive { background: #22c55e; }
    .sentiment-dot.negative { background: #ef4444; }
    .sentiment-dot.neutral { background: #6b7280; }

    /* Status indicator */
    .status-bar {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.75rem 1rem;
        background: rgba(102, 126, 234, 0.1);
        border-radius: 8px;
        margin-bottom: 1rem;
    }

    .pulse-dot {
        width: 10px;
        height: 10px;
        background: #22c55e;
        border-radius: 50%;
        animation: pulse 1.5s infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(1.2); }
    }

    .status-text {
        color: #d1d5db;
        font-size: 0.9rem;
    }

    /* Legend */
    .legend {
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
        margin: 1rem 0;
        padding: 0.75rem;
        background: rgba(0, 0, 0, 0.3);
        border-radius: 8px;
    }

    .legend-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.75rem;
        color: #9ca3af;
    }

    .legend-color {
        width: 12px;
        height: 12px;
        border-radius: 50%;
    }

    /* Insights panel */
    .insight-card {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 16px;
        padding: 1.5rem;
        margin-top: 1rem;
    }

    .insight-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #fff;
        margin-bottom: 1rem;
    }

    /* Sidebar styling */
    .sidebar .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        border-radius: 8px;
        transition: all 0.3s ease;
    }

    .sidebar .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }

    /* Section headers */
    .section-header {
        font-size: 0.85rem;
        font-weight: 600;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin: 1.5rem 0 0.75rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Graph container */
    .graph-container {
        background: rgba(0, 0, 0, 0.3);
        border-radius: 16px;
        padding: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
    }

    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 3px;
    }

    ::-webkit-scrollbar-thumb {
        background: rgba(102, 126, 234, 0.5);
        border-radius: 3px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: rgba(102, 126, 234, 0.7);
    }

    /* Streamlit element overrides */
    .stTextArea textarea {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        color: #fff !important;
    }

    .stTextInput input {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        color: #fff !important;
    }

    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
    }

    div[data-baseweb="select"] > div {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }

    .stSlider > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
    }

    .stProgress > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    defaults = {
        "simulation_engine": None,
        "simulation_state": None,
        "is_running": False,
        "comments_display": [],
        "current_step": 0,
        "active_agents": set(),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_header():
    """Render the application header."""
    st.markdown('<h1 class="main-title">Mimetic</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-title">Evolutionary Marketing Sandbox • Test campaigns in a synthetic social network</p>',
        unsafe_allow_html=True
    )


def render_sidebar():
    """Render the sidebar with campaign configuration."""
    with st.sidebar:
        st.markdown("### Campaign Setup")

        # Campaign Content
        st.markdown('<p class="section-header">Content</p>', unsafe_allow_html=True)
        campaign_content = st.text_area(
            "Campaign Message",
            placeholder="Enter your marketing message, ad copy, or post content...",
            height=100,
            label_visibility="collapsed"
        )

        # Campaign Goal
        st.markdown('<p class="section-header">Objective</p>', unsafe_allow_html=True)
        campaign_goal = st.selectbox(
            "Goal",
            ["brand_awareness", "engagement", "controversy", "conversion"],
            format_func=lambda x: {
                "brand_awareness": "🎯 Brand Awareness",
                "engagement": "💬 Engagement",
                "controversy": "🔥 Viral Controversy",
                "conversion": "💰 Conversions"
            }.get(x, x),
            label_visibility="collapsed"
        )

        # Target Demographics
        st.markdown('<p class="section-header">Target Audience</p>', unsafe_allow_html=True)
        target_demo = st.text_input(
            "Demographics",
            placeholder="e.g., Gen Z tech enthusiasts",
            label_visibility="collapsed"
        )

        # Simulation Parameters
        st.markdown('<p class="section-header">Simulation</p>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            num_agents = st.slider("Agents", 20, 100, 50, 10)
        with col2:
            num_steps = st.slider("Steps", 5, 30, 15, 5)

        connectivity = st.slider("Connectivity", 0.05, 0.30, 0.15, 0.05)

        # API Configuration
        with st.expander("🔑 API Settings"):
            provider = st.selectbox(
                "Provider",
                ["none (rule-based)", "openai", "anthropic"],
            )

            api_key = None
            if provider != "none (rule-based)":
                api_key = st.text_input(
                    "API Key",
                    type="password",
                    value=os.getenv("OPENAI_API_KEY", "") if provider == "openai"
                          else os.getenv("ANTHROPIC_API_KEY", ""),
                )

            st.session_state.llm_provider = provider
            st.session_state.api_key = api_key

        st.markdown("---")

        # Action Button
        run_disabled = not campaign_content.strip()

        if st.button(
            "🚀 Run Simulation",
            type="primary",
            use_container_width=True,
            disabled=run_disabled
        ):
            return {
                "content": campaign_content,
                "goal": campaign_goal,
                "target": target_demo or "General audience",
                "num_agents": num_agents,
                "connectivity": connectivity,
                "num_steps": num_steps,
            }

        if run_disabled:
            st.caption("Enter campaign content to start")

    return None


def render_metrics_row(metrics):
    """Render the metrics in a row."""
    cols = st.columns(4)

    with cols[0]:
        st.metric("Reach", f"{metrics.reach}", delta=None)
    with cols[1]:
        st.metric("Comments", f"{metrics.total_comments}")
    with cols[2]:
        st.metric("Shares", f"{metrics.total_shares}")
    with cols[3]:
        engagement = f"{metrics.engagement_rate:.0%}" if metrics.reach > 0 else "0%"
        st.metric("Engagement", engagement)


def render_comment(comment, agent_dict):
    """Render a single comment in the feed."""
    agent = agent_dict.get(comment.agent_id)
    archetype = agent.archetype if agent else "Unknown"

    if comment.sentiment > 0.2:
        sentiment_class = "positive"
    elif comment.sentiment < -0.2:
        sentiment_class = "negative"
    else:
        sentiment_class = "neutral"

    st.markdown(f"""
    <div class="comment-bubble {sentiment_class}">
        <div class="comment-header">
            <span class="sentiment-dot {sentiment_class}"></span>
            <span class="comment-name">{comment.agent_name}</span>
            <span class="comment-archetype">{archetype}</span>
        </div>
        <div class="comment-text">{comment.content}</div>
    </div>
    """, unsafe_allow_html=True)


def render_legend():
    """Render the mood legend."""
    st.markdown("""
    <div class="legend">
        <div class="legend-item"><div class="legend-color" style="background: #22c55e;"></div> Happy/Excited</div>
        <div class="legend-item"><div class="legend-color" style="background: #6b7280;"></div> Neutral</div>
        <div class="legend-item"><div class="legend-color" style="background: #f59e0b;"></div> Skeptical</div>
        <div class="legend-item"><div class="legend-color" style="background: #ef4444;"></div> Angry/Annoyed</div>
        <div class="legend-item"><div class="legend-color" style="background: #a855f7; border: 2px solid #fff;"></div> Active</div>
    </div>
    """, unsafe_allow_html=True)


def render_status(step, total_steps, num_engaged):
    """Render the simulation status bar."""
    st.markdown(f"""
    <div class="status-bar">
        <div class="pulse-dot"></div>
        <span class="status-text">Step {step}/{total_steps} • {num_engaged} agents engaged</span>
    </div>
    """, unsafe_allow_html=True)


def render_insights(insights):
    """Render the insights panel."""
    avg_sentiment = insights.get("average_sentiment", 0)
    if avg_sentiment > 0.2:
        reception = ("Positive", "#22c55e")
    elif avg_sentiment < -0.2:
        reception = ("Negative", "#ef4444")
    else:
        reception = ("Mixed", "#f59e0b")

    st.markdown(f"""
    <div class="insight-card">
        <div class="insight-title">Simulation Insights</div>
        <p><strong>Overall Reception:</strong> <span style="color: {reception[1]}; font-weight: 600;">{reception[0]}</span> (avg sentiment: {avg_sentiment:.2f})</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Top Engaging Archetypes**")
        for archetype, count in insights.get("top_archetypes", [])[:4]:
            st.markdown(f"- {archetype}: `{count}` interactions")

    with col2:
        st.markdown("**Sentiment Breakdown**")
        breakdown = insights.get("sentiment_breakdown", {})
        total = sum(breakdown.values()) or 1

        for label, count in [("Positive", breakdown.get("positive", 0)),
                            ("Neutral", breakdown.get("neutral", 0)),
                            ("Negative", breakdown.get("negative", 0))]:
            pct = count / total * 100
            color = {"Positive": "#22c55e", "Neutral": "#6b7280", "Negative": "#ef4444"}[label]
            st.markdown(f"""
            <div style="margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: #9ca3af;">
                    <span>{label}</span>
                    <span>{count} ({pct:.0f}%)</span>
                </div>
                <div style="background: rgba(255,255,255,0.1); border-radius: 4px; height: 8px; margin-top: 4px;">
                    <div style="background: {color}; width: {pct}%; height: 100%; border-radius: 4px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)


def get_agraph_config():
    """Get the agraph configuration with physics."""
    return Config(
        width="100%",
        height=500,
        directed=True,
        physics={
            "enabled": True,
            "solver": "forceAtlas2Based",
            "forceAtlas2Based": {
                "gravitationalConstant": -80,
                "centralGravity": 0.005,
                "springLength": 150,
                "springConstant": 0.05,
                "damping": 0.4,
                "avoidOverlap": 0.8
            },
            "stabilization": {
                "enabled": True,
                "iterations": 150,
                "updateInterval": 25
            }
        },
        hierarchical=False,
        nodeHighlightBehavior=True,
        highlightColor="#a855f7",
        collapsible=False,
        node={"labelProperty": "label", "renderLabel": True},
        link={"labelProperty": "label", "renderLabel": False}
    )


def create_graph_elements(state, active_agents=None):
    """Create nodes and edges for the agraph."""
    active_agents = active_agents or set()
    interaction_pairs = {}
    for src, tgt, sent in (state.interactions or [])[-20:]:
        interaction_pairs[(src, tgt)] = sent

    nodes = []
    edges = []
    agent_dict = {a.id: a for a in state.agents}

    for agent in state.agents:
        is_engaged = agent.id in state.engaged_agents
        is_active = agent.id in active_agents

        size = 15 + (agent.influence_score * 25)
        color = get_mood_color(agent.mood.value)

        if is_active:
            border_color = "#ffffff"
            border_width = 4
            size *= 1.4
        elif is_engaged:
            border_color = "#a855f7"
            border_width = 2
        else:
            border_color = "rgba(255,255,255,0.2)"
            border_width = 1
            # Dim the color
            hex_color = color.lstrip('#')
            r = int(int(hex_color[0:2], 16) * 0.3)
            g = int(int(hex_color[2:4], 16) * 0.3)
            b = int(int(hex_color[4:6], 16) * 0.3)
            color = f"#{r:02x}{g:02x}{b:02x}"

        nodes.append(Node(
            id=agent.id,
            label=agent.name if (is_engaged or is_active) else "",
            size=size,
            color=color,
            borderWidth=border_width,
            borderWidthSelected=4,
            font={"color": "#ffffff" if is_engaged else "rgba(255,255,255,0.3)", "size": 10},
            title=f"{agent.name}\n{agent.archetype}\nMood: {agent.mood.value}",
            shape="dot",
        ))

    for edge in state.graph.edges():
        source, target = edge
        sentiment = interaction_pairs.get((source, target))

        if sentiment is not None:
            if sentiment > 0.2:
                edge_color = "rgba(34, 197, 94, 0.9)"
                width = 4
            elif sentiment < -0.2:
                edge_color = "rgba(239, 68, 68, 0.9)"
                width = 4
            else:
                edge_color = "rgba(168, 85, 247, 0.9)"
                width = 3
        else:
            edge_color = "rgba(255, 255, 255, 0.05)"
            width = 1

        edges.append(Edge(
            source=source,
            target=target,
            color=edge_color,
            width=width,
        ))

    return nodes, edges


def run_simulation(config):
    """Initialize and return a new simulation."""
    use_llm = config.get("provider") != "none (rule-based)"
    provider = "openai" if "openai" in str(st.session_state.get("llm_provider", "")) else "anthropic"

    llm = LLMProvider(
        provider=provider,
        api_key=st.session_state.get("api_key")
    )

    engine = SimulationEngine(llm_provider=llm, use_llm=use_llm and bool(st.session_state.get("api_key")))

    campaign = Campaign(
        content=config["content"],
        goal=config["goal"],
        target_demographic=config["target"]
    )

    state = engine.initialize(
        campaign=campaign,
        num_agents=config["num_agents"],
        connectivity=config["connectivity"]
    )

    return engine, state


def main():
    """Main application entry point."""
    init_session_state()
    render_header()

    config = render_sidebar()

    if config:
        # New simulation requested
        engine, state = run_simulation(config)

        st.session_state.simulation_engine = engine
        st.session_state.simulation_state = state
        st.session_state.comments_display = []
        st.session_state.is_running = True

        agent_dict = {a.id: a for a in state.agents}

        # Layout
        col_graph, col_feed = st.columns([3, 2])

        with col_graph:
            st.markdown('<p class="section-header">Network Visualization</p>', unsafe_allow_html=True)
            render_legend()
            graph_placeholder = st.empty()
            status_placeholder = st.empty()

        with col_feed:
            st.markdown('<p class="section-header">Live Comment Feed</p>', unsafe_allow_html=True)
            feed_placeholder = st.empty()

        # Metrics row
        metrics_placeholder = st.empty()

        # Progress
        progress_bar = st.progress(0)

        # Run simulation
        for step in range(config["num_steps"]):
            # Get agents that will be active this step
            pre_engaged = set(state.engaged_agents)
            new_comments = engine.step()
            post_engaged = set(state.engaged_agents)
            newly_active = post_engaged - pre_engaged

            st.session_state.comments_display.extend(new_comments)

            # Update progress
            progress = (step + 1) / config["num_steps"]
            progress_bar.progress(progress)

            # Update status
            with status_placeholder:
                render_status(step + 1, config["num_steps"], len(state.engaged_agents))

            # Update graph with physics animation
            with graph_placeholder:
                nodes, edges = create_graph_elements(state, newly_active)
                agraph(nodes=nodes, edges=edges, config=get_agraph_config())

            # Update feed
            with feed_placeholder.container():
                st.markdown('<div class="feed-container">', unsafe_allow_html=True)
                for comment in reversed(st.session_state.comments_display[-12:]):
                    render_comment(comment, agent_dict)
                st.markdown('</div>', unsafe_allow_html=True)

            # Update metrics
            with metrics_placeholder.container():
                render_metrics_row(state.metrics)

            time.sleep(0.5)

        progress_bar.empty()
        status_placeholder.empty()

        st.success("✅ Simulation complete!")

        # Final insights
        insights = engine.get_insights()
        render_insights(insights)

        st.session_state.is_running = False

    elif st.session_state.simulation_state:
        # Show previous results
        state = st.session_state.simulation_state
        engine = st.session_state.simulation_engine
        agent_dict = {a.id: a for a in state.agents}

        col_graph, col_feed = st.columns([3, 2])

        with col_graph:
            st.markdown('<p class="section-header">Network Visualization</p>', unsafe_allow_html=True)
            render_legend()
            nodes, edges = create_graph_elements(state, set())
            agraph(nodes=nodes, edges=edges, config=get_agraph_config())

        with col_feed:
            st.markdown('<p class="section-header">Comment Feed</p>', unsafe_allow_html=True)
            st.markdown('<div class="feed-container">', unsafe_allow_html=True)
            for comment in reversed(st.session_state.comments_display[-15:]):
                render_comment(comment, agent_dict)
            st.markdown('</div>', unsafe_allow_html=True)

        render_metrics_row(state.metrics)

        insights = engine.get_insights()
        render_insights(insights)

    else:
        # Welcome state
        st.markdown("""
        <div class="glass-card" style="text-align: center; padding: 3rem;">
            <h2 style="color: #fff; margin-bottom: 1rem;">Welcome to Mimetic</h2>
            <p style="color: #9ca3af; max-width: 500px; margin: 0 auto;">
                Configure your marketing campaign in the sidebar and watch how AI agents
                with distinct personalities react, comment, and spread your content through
                a simulated social network.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Preview network
        st.markdown('<p class="section-header" style="margin-top: 2rem;">Preview Network</p>', unsafe_allow_html=True)
        render_legend()

        preview_agents = generate_population(40)
        preview_graph = create_social_graph(preview_agents, 0.12)

        # Create preview nodes/edges
        nodes = []
        edges = []

        for agent in preview_agents:
            color = get_mood_color(agent.mood.value)
            size = 12 + (agent.influence_score * 20)

            nodes.append(Node(
                id=agent.id,
                label="",
                size=size,
                color=color,
                borderWidth=1,
                font={"color": "rgba(255,255,255,0.5)", "size": 8},
                title=f"{agent.name}\n{agent.archetype}",
                shape="dot",
            ))

        for edge in preview_graph.edges():
            edges.append(Edge(
                source=edge[0],
                target=edge[1],
                color="rgba(255, 255, 255, 0.08)",
                width=1,
            ))

        agraph(nodes=nodes, edges=edges, config=get_agraph_config())


if __name__ == "__main__":
    main()
