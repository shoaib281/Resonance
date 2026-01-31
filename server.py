"""FastAPI server — serves UI and streams simulation events via SSE."""

from __future__ import annotations
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from models import CampaignSeed, Goal
from social_graph import SocialGraph
from population import generate_population
from simulation import run_simulation
from evolution import compute_fitness, analyze_and_evolve
from event_bus import EventBus

app = FastAPI(title="Resonance")
bus = EventBus()

app.mount("/static", StaticFiles(directory="static"), name="static")


class CampaignRequest(BaseModel):
    content: str
    image_description: str = ""
    goal: str = "engagement"
    target_audience: str
    num_agents: int = 12
    num_ticks: int = 2
    max_generations: int = 2


@app.get("/", response_class=HTMLResponse)
async def index():
    with open("static/index.html") as f:
        return HTMLResponse(f.read())


@app.get("/events")
async def events(request: Request):
    queue = bus.subscribe()

    async def stream():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield {"data": data}
                except asyncio.TimeoutError:
                    yield {"data": '{"type":"ping"}'}
        finally:
            bus.unsubscribe(queue)

    return EventSourceResponse(stream())


@app.post("/run")
async def run_campaign(req: CampaignRequest):
    seed = CampaignSeed(
        content=req.content,
        image_description=req.image_description,
        goal=next((g for g in Goal if g.value == req.goal), Goal.ENGAGEMENT),
        target_audience=req.target_audience,
    )
    asyncio.create_task(run_pipeline(seed, req.num_agents, req.num_ticks, req.max_generations))
    return {"status": "started"}


async def run_pipeline(seed: CampaignSeed, num_agents: int, num_ticks: int, max_generations: int):
    try:
        # Phase 2: Generate population
        await bus.emit("phase", {"phase": 2, "message": f"Generating {num_agents} Agent Personas"})
        agents = await generate_population(seed, num_agents)
        if not agents:
            await bus.emit("error", {"message": "Failed to generate agents."})
            return
        for a in agents:
            await bus.emit("agent_created", a.to_dict())

        graph = SocialGraph(agents)
        graph.build()
        influencers = graph.get_influencers(5)
        await bus.emit("graph_built", {
            "edges": graph.edge_count,
            "influencers": [f"{a.name} ({len(a.followers)} followers)" for a in influencers],
            "graph": graph.to_graph_data(),
        })

        current_seed = seed

        for gen in range(1, max_generations + 1):
            # Phase 3: Simulate
            await bus.emit("phase", {"phase": 3, "message": f"Generation {gen} — Running Simulation"})
            result = await run_simulation(current_seed, agents, graph, num_ticks, gen, bus)

            fitness = compute_fitness(result)
            await bus.emit("result", {
                "generation": gen,
                "likes": result.likes,
                "comments": result.comments,
                "shares": result.shares,
                "mocks": result.mocks,
                "sentiment": round(result.sentiment_score, 3),
                "virality": round(result.virality_score, 3),
                "fitness": round(fitness, 3),
            })

            if fitness >= 0.75:
                await bus.emit("done", {"generation": gen})
                return

            if gen < max_generations:
                # Phase 4: Evolve
                await bus.emit("phase", {"phase": 4, "message": f"Evolving Campaign (Gen {gen} → {gen + 1})"})
                new_seed, analysis = await analyze_and_evolve(result)
                await bus.emit("evolution", {
                    "generation": gen,
                    "analysis": analysis.get("analysis", ""),
                    "strengths": analysis.get("strengths", []),
                    "weaknesses": analysis.get("weaknesses", []),
                    "revised_content": new_seed.content,
                })
                current_seed = new_seed

        await bus.emit("done", {"generation": max_generations})

    except Exception as e:
        import traceback
        traceback.print_exc()
        await bus.emit("error", {"message": str(e)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8080, reload=False)
