"""
AI Pet Battle Game — vertical slice entry point.

Run:
    python main.py

Add `random.seed(42)` below for a deterministic debug run.
"""
# `import` makes code from another file available here.
# Standard library modules (like `json`) come first by convention,
# then your own project's modules.
import json

# `from X import Y` imports just the name Y from module X.
# After this line you can write `make_ember()` instead of `catalog.make_ember()`.
from pet_battle.catalog import make_ember, make_glacius
from pet_battle.mock_llm import MockLLM
from pet_battle.battle_engine import BattleEngine

# `import X as alias` imports the whole module under a shorter name.
# Useful when you'll call many things from the module (personality.update,
# personality.something_else, ...) — avoids a long list of `from` imports.
import pet_battle.personality as personality
import pet_battle.cli as cli


def main() -> None:
    # Uncomment for reproducible output during debugging:
    # import random; random.seed(42)
    #
    # Setting a seed makes random "deterministic" — the same seed always
    # produces the same sequence of random numbers. Useful when you want
    # to reproduce a specific battle to debug it.

    # Call the factory functions to get fresh Pet instances.
    # We do NOT use module-level constants for pets because Pet objects
    # are mutable — HP and cooldowns change during battle.
    pet_a = make_ember()
    pet_b = make_glacius()

    # Two separate MockLLM instances — one brain per pet.
    # They're identical classes but independent objects, so their
    # random choices don't interfere with each other.
    llm_a = MockLLM()
    llm_b = MockLLM()

    # Create the engine and run the battle.
    # `engine` holds references to all four objects; `run_battle()` uses them.
    engine = BattleEngine(pet_a, pet_b, llm_a, llm_b)
    result = engine.run_battle()

    # Post-battle: update each pet's personality based on how they fought.
    # We pass `result` (which contains the full battle log) to each call.
    print("=" * 60)
    print("  Post-battle personality update")
    print("=" * 60)
    personality.update(pet_a, result)
    personality.update(pet_b, result)

    cli.print_personality_update(pet_a)
    cli.print_personality_update(pet_b)


# This block only runs when you execute `python main.py` directly.
# If another file does `import main`, the block is SKIPPED — which prevents
# the battle from running automatically on import.
#
# `__name__` is a special variable Python sets automatically:
#   - When you run a file directly: __name__ == "__main__"
#   - When a file is imported:      __name__ == the module's name (e.g. "main")
if __name__ == "__main__":
    main()
