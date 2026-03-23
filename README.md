# Pet Battle Arena

A turn-based pet battle game with personality-driven AI decision-making. Two pets fight using ability cards; each pet's AI weights its choices based on a personality profile that drifts slightly after every battle.

Built as a [Boot.dev](https://www.boot.dev) learning project.

---

## Running the game

### CLI mode (two demo pets fight each other)

```bash
python main.py
```

### Web multiplayer mode (a handful of players over a browser)

```bash
pip install flask
flask --app server run --host=0.0.0.0
```

Visit `http://localhost:5000`. For remote players, expose the port with a tool like [ngrok](https://ngrok.com):

```bash
ngrok http 5000
```

Each player opens the URL in their browser, registers a pet (name, archetype, personality sliders), then anyone in the lobby can kick off a battle and watch the animated turn-by-turn replay.

---

## How a battle works

- Each turn both pets simultaneously pick an ability card, weighted by their personality.
- Cards resolve in **speed-tier order** (fast cards fire before slow ones). Pet speed is the tiebreaker within the same tier.
- **Intuition** gives a pet a chance to "glimpse" the enemy's card and swap to a faster counter — higher intuition means more frequent glimpses.
- Special card effects: **shield** (+DEF for one turn), **drain** (steal HP), **stun** (enemy skips next turn).
- After the battle each pet's personality nudges toward how it actually fought, and may earn a trait like `scrappy` or `calculated`.

---

## Project layout

```
main.py                   CLI entry point
server.py                 Flask web server for multiplayer sessions
pet_battle/
    models.py             Dataclasses — Pet, AbilityCard, PersonalityProfile, etc.
    catalog.py            Card and pet definitions; make_custom_pet() for web mode
    battle_engine.py      Turn loop, speed resolution, intuition checks
    mock_llm.py           Personality-weighted card picker (no network calls)
    llm_interface.py      Abstract base — swap in a real LLM by subclassing this
    personality.py        Post-battle personality drift
    cli.py                Pretty-print helpers for terminal output
templates/                Jinja2 HTML templates for the web server
```

### Swapping in a real LLM

1. Create `pet_battle/real_llm.py`, subclass `LLMBackend`, implement `choose_card()`.
2. Pass `RealLLM()` instead of `MockLLM()` to `BattleEngine` in `main.py` or `server.py`.
3. Add your HTTP client (`httpx`, `anthropic`, etc.) to `requirements.txt`.

No other files need to change.
