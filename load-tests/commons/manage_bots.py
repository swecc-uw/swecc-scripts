import argparse
import os
import json
from typing import List, Dict, Any, Optional
import concurrent.futures
from pathlib import Path

from bot import SWECCBot, check_connection

DEFAULT_NUM_BOTS = 10
BOTS_FILE = "bots.json"


def save_bots(bots: List[SWECCBot], filename: str = BOTS_FILE) -> None:
    """Save bots to a JSON file for later use."""
    serialized_bots = [bot.to_dict() for bot in bots]
    with open(filename, "w") as f:
        json.dump(serialized_bots, f, indent=2)
    print(f"Saved {len(bots)} bots to {filename}")


def load_bots(filename: str = BOTS_FILE) -> List[SWECCBot]:
    """Load bots from a JSON file."""
    if not Path(filename).exists():
        print(f"Bots file {filename} not found")
        return []

    try:
        with open(filename, "r") as f:
            data = json.load(f)
        bots = [SWECCBot.from_dict(bot_data) for bot_data in data]
        print(f"Loaded {len(bots)} bots from {filename}")
        return bots
    except Exception as e:
        print(f"Error loading bots from {filename}: {e}")
        return []


def setup_bot(bot_id: int) -> Optional[SWECCBot]:
    """Set up a single bot (register, login, verify)."""
    try:
        bot = SWECCBot.from_idx(bot_id)
        if bot.ensure_authenticated():
            return bot
        return None
    except Exception as e:
        print(f"Error setting up bot {bot_id}: {e}")
        return None


def setup_bots(
    start_id: int = 1, num_bots: int = DEFAULT_NUM_BOTS, max_workers: int = 5
) -> List[SWECCBot]:
    """Set up multiple bots in parallel."""
    if not check_connection():
        print("Could not connect to the server")
        return []

    existing_bots = load_bots()
    existing_ids = {bot.idx for bot in existing_bots}

    bot_ids_to_setup = [
        i for i in range(start_id, start_id + num_bots) if i not in existing_ids
    ]

    if not bot_ids_to_setup:
        print("All requested bots are already set up")
        return existing_bots

    print(f"Setting up {len(bot_ids_to_setup)} new bots...")

    new_bots = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_bot_id = {
            executor.submit(setup_bot, bot_id): bot_id for bot_id in bot_ids_to_setup
        }
        for future in concurrent.futures.as_completed(future_to_bot_id):
            bot_id = future_to_bot_id[future]
            try:
                bot = future.result()
                if bot:
                    new_bots.append(bot)
                    print(f"Bot {bot_id} setup completed")
                else:
                    print(f"Bot {bot_id} setup failed")
            except Exception as e:
                print(f"Bot {bot_id} setup error: {e}")

    all_bots = existing_bots + new_bots

    save_bots(all_bots)

    return all_bots


def main():
    global BOTS_FILE
    """Main function to set up bots from command line."""
    parser = argparse.ArgumentParser(description="Set up bots for load testing")
    parser.add_argument(
        "--num-bots",
        type=int,
        default=DEFAULT_NUM_BOTS,
        help="Number of bots to set up",
    )
    parser.add_argument("--start-id", type=int, default=1, help="Starting ID for bots")
    parser.add_argument(
        "--max-workers",
        type=int,
        default=5,
        help="Maximum number of parallel worker threads",
    )
    parser.add_argument(
        "--bots-file", type=str, default=BOTS_FILE, help="File to save/load bot data"
    )

    args = parser.parse_args()

    BOTS_FILE = args.bots_file

    bots = setup_bots(args.start_id, args.num_bots, args.max_workers)
    print(f"Successfully set up {len(bots)} bots")


if __name__ == "__main__":
    main()
