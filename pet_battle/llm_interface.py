from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pet_battle.models import AbilityCard, Pet


class LLMBackend(ABC):
    """
    Abstract swap point for the pet's decision-making brain.

    To wire in a real LLM:
      1. Subclass LLMBackend in a new file (e.g. real_llm.py)
      2. Implement choose_card()
      3. Pass an instance to BattleEngine instead of MockLLM

    No other files need to change.
    """

    @abstractmethod
    def choose_card(
        self,
        pet: "Pet",
        available_cards: list["AbilityCard"],
        enemy_snapshot: dict,
    ) -> tuple["AbilityCard", str]:
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
