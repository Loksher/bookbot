"""
AI Pet Battle Game — vertical slice entry point.

Run:
    python main.py

Add `random.seed(42)` below for a deterministic debug run.
"""
import json
from pet_battle.catalog import make_ember, make_glacius
from pet_battle.mock_llm import MockLLM
from pet_battle.battle_engine import BattleEngine
import pet_battle.personality as personality
import pet_battle.cli as cli


def main() -> None:
    # Uncomment for reproducible output during debugging:
    # import random; random.seed(42)

    pet_a = make_ember()
    pet_b = make_glacius()

    llm_a = MockLLM()
    llm_b = MockLLM()

    engine = BattleEngine(pet_a, pet_b, llm_a, llm_b)
    result = engine.run_battle()

    # Post-battle personality update
    print("=" * 60)
    print("  Post-battle personality update")
    print("=" * 60)
    personality.update(pet_a, result)
    personality.update(pet_b, result)

    cli.print_personality_update(pet_a)
    cli.print_personality_update(pet_b)


if __name__ == "__main__":
    main()
