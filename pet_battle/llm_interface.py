from __future__ import annotations

# `abc` stands for Abstract Base Class — it's part of the standard library.
# ABC and abstractmethod together let you define a *contract*: a set of
# methods that any subclass MUST implement. If a subclass forgets one,
# Python raises a TypeError when you try to create an instance of it.
from abc import ABC, abstractmethod

# TYPE_CHECKING is False at runtime, but True when a type-checker (like mypy
# or your IDE) is analysing the code. The imports inside this block are only
# for the type checker — they never run, so you avoid circular imports.
# (llm_interface.py doesn't actually need models.py at runtime because the
# type hints are just strings, thanks to `from __future__ import annotations`.)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pet_battle.models import AbilityCard, Pet


# Inheriting from ABC (written as `class Foo(ABC):`) marks this class as
# abstract. You can't do `LLMBackend()` directly — it only exists to be
# subclassed. Think of it as a template or contract.
class LLMBackend(ABC):
    """
    Abstract swap point for the pet's decision-making brain.

    To wire in a real LLM:
      1. Subclass LLMBackend in a new file (e.g. real_llm.py)
      2. Implement choose_card()
      3. Pass an instance to BattleEngine instead of MockLLM

    No other files need to change.
    """

    # @abstractmethod means: "every subclass must override this method."
    # Notice the body is just `...` (an ellipsis). It's a valid Python
    # expression used as a placeholder — same idea as `pass`, but
    # conventionally used in abstract methods and type stubs.
    @abstractmethod
    def choose_card(
        self,
        pet: "Pet",
        available_cards: list["AbilityCard"],
        enemy_snapshot: dict,
    ) -> tuple["AbilityCard", str]:
        # `tuple[X, Y]` is a fixed-length sequence where the first item
        # has type X and the second has type Y. Unlike a list, a tuple is
        # *immutable* — you can't change it after creation.
        # Returning a tuple is a clean way to return two related values
        # from a function without creating a whole new class.
        """
        Given the pet's state and available cards, choose one to play.

        Args:
            pet: The acting pet (full state available).
            available_cards: Cards not on cooldown this turn.
            enemy_snapshot: {"name": str, "hp": int, "max_hp": int} — no card info.

        Returns:
            (chosen_card, flavor_text) — one sentence describing the action.
        """
        ...
