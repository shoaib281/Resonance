# Mimetic

**Evolutionary Marketing Sandbox - Synthetic Social Network Simulation**

Mimetic is a multi-agent AI system that simulates a social network populated by diverse synthetic personas. Drop your marketing campaign into this "digital petri dish" and watch how it spreads, mutates, and resonates with different audience segments.

## Features

- **50-100 AI Agents** with distinct personalities (MBTI types, archetypes, political leanings)
- **Social Graph Simulation** - agents follow, influence, and react to each other
- **Real-time Visualization** - watch engagement spread through the network
- **Sentiment Analysis** - track positive, negative, and neutral reactions
- **Emergent Behavior** - discover unexpected viral patterns and controversies
- **Campaign Insights** - get actionable feedback on your content

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys (Optional)

For AI-generated comments, copy the environment template and add your API key:

```bash
cp .env.example .env
# Edit .env with your OpenAI or Anthropic API key
```

Without API keys, the simulation uses rule-based responses (still functional but less nuanced).

### 3. Run the Application

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

## Usage

1. **Enter Campaign Content** - Your ad copy, social post, or marketing message
2. **Set Campaign Goal** - Brand awareness, engagement, controversy, or conversion
3. **Define Target Audience** - Describe your intended demographic
4. **Adjust Settings** - Number of agents, network connectivity, simulation steps
5. **Run Simulation** - Watch agents react in real-time
6. **Analyze Insights** - Review sentiment, engagement rates, and viral potential

## Agent Archetypes

| Archetype | Behavior |
|-----------|----------|
| The Influencer | Trend-conscious, high engagement, shares content widely |
| The Skeptic | Questions everything, needs proof, critical comments |
| The Early Adopter | Tech-savvy, loves new things, opinion leader |
| The Traditionalist | Values stability, resistant to change |
| The Bargain Hunter | Price-focused, always looking for deals |
| The Activist | Cause-driven, passionate about social issues |
| The Lurker | Observes more than participates, rarely comments |
| The Troll | Provocative, enjoys stirring controversy |
| The Supporter | Positive, encouraging, builds community |
| The Expert | Knowledgeable, provides detailed technical insights |

## Tech Stack

- **Frontend**: Streamlit
- **Graph Visualization**: Plotly + NetworkX
- **LLM Integration**: OpenAI GPT-4o-mini / Anthropic Claude
- **Agent Framework**: Custom multi-agent system

## Project Structure

```
mimetic/
├── app.py           # Main Streamlit application
├── agents.py        # Agent personas and generation
├── network.py       # Social graph management
├── simulation.py    # Simulation engine
├── requirements.txt # Python dependencies
└── .env.example     # Environment template
```

## IC Hack 26 - Resonance

Built for IC Hack 26, targeting the "Emergent Behavior" theme. Mimetic demonstrates how complex, unpredictable patterns emerge from simple agent interactions - viral trends, pile-ons, and sentiment cascades that couldn't be predicted by analyzing individual agents.
