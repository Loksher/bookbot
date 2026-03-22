"""
Web server for multiplayer pet battle test sessions.

Run with:
    pip install flask
    flask --app server run --host=0.0.0.0

Then expose publicly via ngrok or similar:
    ngrok http 5000
"""
from __future__ import annotations

import contextlib
import copy
import io
import uuid

from flask import Flask, abort, redirect, render_template, request, url_for

from pet_battle.battle_engine import BattleEngine
from pet_battle.catalog import make_custom_pet
from pet_battle.mock_llm import MockLLM

app = Flask(__name__)

# ---------------------------------------------------------------------------
# In-memory state — resets every time the server restarts.
# Fine for a quick test session with a handful of players.
# ---------------------------------------------------------------------------

# pet_id -> {id, owner, name, archetype, pet: Pet, personality: dict}
_pets: dict[str, dict] = {}

# battle_id -> {id, pet_a_name, pet_b_name, pet_a_max_hp, pet_b_max_hp,
#               winner, turns, turns_data: list[dict]}
_battles: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template(
        "index.html",
        pets=list(_pets.values()),
        battles=list(_battles.values()),
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        owner = (request.form.get("owner") or "Unknown").strip() or "Unknown"
        name = (request.form.get("name") or "Pet").strip() or "Pet"
        archetype = request.form.get("archetype", "drifter")

        # Sliders come in as integers 1–10; convert to 0.0–1.0 floats.
        def _slider(field: str) -> float:
            try:
                return int(request.form.get(field, 5)) / 10.0
            except (ValueError, TypeError):
                return 0.5

        pet = make_custom_pet(
            name=name,
            archetype=archetype,
            aggression=_slider("aggression"),
            caution=_slider("caution"),
            cunning=_slider("cunning"),
            bold=_slider("bold"),
        )

        pet_id = str(uuid.uuid4())[:8]
        _pets[pet_id] = {
            "id": pet_id,
            "owner": owner,
            "name": name,
            "archetype": archetype,
            "pet": pet,
            "personality": pet.personality.to_dict(),
        }
        return redirect(url_for("index"))

    return render_template("register.html")


@app.route("/battle", methods=["POST"])
def start_battle():
    pet_a_id = request.form.get("pet_a", "")
    pet_b_id = request.form.get("pet_b", "")

    if not pet_a_id or not pet_b_id or pet_a_id == pet_b_id:
        return redirect(url_for("index"))
    if pet_a_id not in _pets or pet_b_id not in _pets:
        abort(404)

    # Deep-copy so the registered pet objects stay pristine for rematches.
    pet_a = copy.deepcopy(_pets[pet_a_id]["pet"])
    pet_b = copy.deepcopy(_pets[pet_b_id]["pet"])

    engine = BattleEngine(pet_a, pet_b, MockLLM(), MockLLM())

    # Suppress the CLI print output — we render the log in the browser instead.
    with contextlib.redirect_stdout(io.StringIO()):
        result = engine.run_battle()

    # Build a JSON-friendly turn list for the browser viewer.
    turns_data: list[dict] = []
    prev_hp_a = pet_a.max_hp
    prev_hp_b = pet_b.max_hp
    for rec in result.battle_log:
        turns_data.append({
            "turn": rec.turn_number,
            "pet_a_card": rec.pet_a_card.name,
            "pet_a_card_type": rec.pet_a_card_type,
            "pet_a_flavor": rec.pet_a_flavor,
            "pet_a_swapped": rec.swapped_a,
            "pet_a_hp": rec.pet_a_hp_after,
            "pet_a_hp_change": max(0, prev_hp_a - rec.pet_a_hp_after),
            "pet_b_card": rec.pet_b_card.name,
            "pet_b_card_type": rec.pet_b_card_type,
            "pet_b_flavor": rec.pet_b_flavor,
            "pet_b_swapped": rec.swapped_b,
            "pet_b_hp": rec.pet_b_hp_after,
            "pet_b_hp_change": max(0, prev_hp_b - rec.pet_b_hp_after),
        })
        prev_hp_a = rec.pet_a_hp_after
        prev_hp_b = rec.pet_b_hp_after

    battle_id = str(uuid.uuid4())[:8]
    _battles[battle_id] = {
        "id": battle_id,
        "pet_a_id": pet_a_id,
        "pet_b_id": pet_b_id,
        "pet_a_name": _pets[pet_a_id]["name"],
        "pet_b_name": _pets[pet_b_id]["name"],
        "pet_a_owner": _pets[pet_a_id]["owner"],
        "pet_b_owner": _pets[pet_b_id]["owner"],
        "pet_a_max_hp": pet_a.max_hp,
        "pet_b_max_hp": pet_b.max_hp,
        "winner": result.winner.name if result.winner else None,
        "turns": result.turns,
        "turns_data": turns_data,
    }
    return redirect(url_for("view_battle", battle_id=battle_id))


@app.route("/battle/<battle_id>")
def view_battle(battle_id: str):
    battle = _battles.get(battle_id)
    if not battle:
        abort(404)
    return render_template("battle.html", battle=battle)
