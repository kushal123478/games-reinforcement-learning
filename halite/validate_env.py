"""
Simple validation test for Halite environment.
"""

from kaggle_environments import make


def simple_test_bot(observation, config):
    """Minimal bot that just returns empty actions."""
    return ""


if __name__ == "__main__":
    print("Creating Halite environment...")
    env = make("halite", configuration={"size": 8, "randomSeed": 42})

    print("Initial state:")
    print(f"  Board size: 8x8")
    print(f"  Configuration: {env.configuration}")

    print("\nEnvironment ready for development!")
    print("\nNext steps:")
    print("1. Study observation structure")
    print("2. Implement action logic")
    print("3. Test with sample matches")
