from dotenv import load_dotenv
import argparse

_ = load_dotenv()
from litewebagent.core.agent_factory import setup_prompting_web_agent
from litewebagent.utils.playwright_manager import setup_playwright


def main(args):
    # Use the features from command-line arguments
    features = args.features.split(',') if args.features else None
    branching_factor = args.branching_factor if args.branching_factor else None

    playwright_manager = setup_playwright(log_folder=args.log_folder, storage_state='state.json', headless=False)
    agent = setup_prompting_web_agent(args.starting_url, args.goal, playwright_manager=playwright_manager, model_name=args.model, agent_type=args.agent_type,
                            features=features, branching_factor=branching_factor, log_folder=args.log_folder,
                            storage_state=args.storage_state)

    response = agent.send_prompt(args.plan)
    print(response)
    print(agent.messages)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run web automation tasks with different agent types.")
    parser.add_argument('--agent_type', type=str, default="PromptAgent",
                        choices=["PromptAgent"],
                        help="Type of agent to use (default: FunctionCallingAgent)")
    parser.add_argument('--model', type=str, default="gpt-4o-mini",
                        help="Model to use for the agent (default: gpt-4o-mini)")
    parser.add_argument('--starting_url', type=str, required=True,
                        help="Starting URL for the web automation task")
    parser.add_argument('--plan', type=str, required=True,
                        help="Plan for the web automation task")
    parser.add_argument('--goal', type=str, required=True,
                        help="Goal for the web automation task")
    parser.add_argument('--storage_state', type=str, default="state.json",
                        help="Storage state json file")
    parser.add_argument('--features', type=str, default="axtree",
                        help="Comma-separated list of features to use (default: None, which uses all features)")
    parser.add_argument('--branching_factor', type=int, default=None)
    parser.add_argument('--log_folder', type=str, default='log', help='Path to the log folder')
    args = parser.parse_args()
    main(args)