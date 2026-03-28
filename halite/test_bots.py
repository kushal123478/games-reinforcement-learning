"""
Test harness for running Halite games and collecting statistics.
"""

from kaggle_environments import make
from bots.random_bot import random_bot
from bots.greedy_bot import greedy_bot


def run_match(agent1_fn, agent2_fn, size=16, seed=None):
    """Run a single match between two agents."""
    config = {"size": size}
    if seed is not None:
        config["randomSeed"] = seed

    env = make("halite", configuration=config)
    env.reset()

    result = env.run([agent1_fn, agent2_fn])

    rewards = env.state[0].reward if hasattr(env.state[0], 'reward') else None

    return result, rewards


def run_tournament(agents_dict, num_matches=5, size=16):
    """Run a round-robin tournament."""
    results = {name: {"wins": 0, "total": 0, "rewards": []} for name in agents_dict}

    for agent1_name in agents_dict:
        for agent2_name in agents_dict:
            if agent1_name == agent2_name:
                continue

            for match_num in range(num_matches):
                print(f"Match: {agent1_name} vs {agent2_name} (Game {match_num + 1})")
                result, rewards = run_match(
                    agents_dict[agent1_name],
                    agents_dict[agent2_name],
                    size=size,
                    seed=match_num
                )

                # Extract winner (first agent wins if reward > 0)
                if rewards and rewards[0] > rewards[1]:
                    results[agent1_name]["wins"] += 1
                    results[agent2_name]["total"] += 1
                elif rewards:
                    results[agent2_name]["wins"] += 1
                    results[agent1_name]["total"] += 1

                results[agent1_name]["total"] += 1
                results[agent2_name]["total"] += 1

                if rewards:
                    results[agent1_name]["rewards"].append(rewards[0])
                    results[agent2_name]["rewards"].append(rewards[1])

    return results


if __name__ == "__main__":
    agents = {
        "random": random_bot,
        "greedy": greedy_bot,
    }

    print("Running Halite tournament...")
    results = run_tournament(agents, num_matches=2, size=8)

    print("\n" + "=" * 50)
    print("TOURNAMENT RESULTS")
    print("=" * 50)
    for agent_name, stats in results.items():
        total_games = stats["total"]
        wins = stats["wins"]
        if total_games > 0:
            win_rate = wins / total_games
            print(f"{agent_name:15} | Wins: {wins:2}/{total_games:2} ({win_rate:.1%})")
