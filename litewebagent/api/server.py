from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from litewebagent.core.agent_factory import setup_prompting_web_agent
from litewebagent.utils.playwright_manager import setup_playwright
import argparse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AutomationConfig(BaseModel):
    starting_url: str
    goal: str
    plan: str
    model: str
    features: str
    elements_filter: str
    branching_factor: int
    agent_type: str
    storage_state: str
    log_folder: str

def run_automation(config: AutomationConfig):
    features = config.features.split(',') if config.features else None
    
    playwright_manager = setup_playwright(
        log_folder=config.log_folder,
        storage_state=config.storage_state,
        headless=False
    )
    
    agent = setup_prompting_web_agent(
        config.starting_url,
        config.goal,
        playwright_manager=playwright_manager,
        model_name=config.model,
        agent_type=config.agent_type,
        features=features,
        elements_filter=config.elements_filter,
        branching_factor=config.branching_factor,
        log_folder=config.log_folder,
        storage_state=config.storage_state
    )
    
    return agent.send_prompt(config.plan)

@app.post("/automate")
async def start_automation(config: AutomationConfig, background_tasks: BackgroundTasks):
    print(config)
    background_tasks.add_task(run_automation, config)
    return {"status": "Automation started"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5001)
    args = parser.parse_args()
    
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=args.port)