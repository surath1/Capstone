
import argparse
import sys
import traceback
from agent.graph import agent


def main():
    parser = argparse.ArgumentParser(description="Run engineering project planner")
    parser.add_argument("--recursion-limit", "-r", type=int, default=100,
                        help="Recursion limit for processing (default: 100)")

    args = parser.parse_args()

    try:
        user_prompt = input("Enter your project prompt: ")
        #logging.info(f"User prompt: {user_prompt}")
        result = agent.invoke(
            {"user_prompt": user_prompt},
            {"recursion_limit": args.recursion_limit}
        )
        #logging.info(f"Final State: {result}")
        print("Final State:", result)
    except KeyboardInterrupt:
        #logging.warning("Operation cancelled by user.")
        print("\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        #logging.error(f"Error: {e}")
        traceback.print_exc()
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()