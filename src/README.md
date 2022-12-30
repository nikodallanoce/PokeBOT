# PokeBOT
This is the main directory of our project which hosts the engine, players and other functions necessary to let the bot work.
## Structure
```bash
📂src
├── 📂engine
│   ├── 📄base_power.py
│   ├── 📄battle_utilities.py
│   ├── 📄damage.py
│   ├── 📄move_effects.py
│   ├── 📄stats.py
│   └── 📄useful_data.py
├── 📂players
│   ├── 📄baseline_player.py
│   ├── 📄MiniMaxPlayer.py
│   └── 📄RuleBasedPLayer.py
├── 📂utilities
│   ├── 📄BattleStatus.py
│   ├── 📄Heuristic.py
│   ├── 📄NodePokemon.py
│   ├── 📄OpponentHPHeuristic.py
│   ├── 📄RandomSearch.py
│   ├── 📄ShowdownHeuristic.py
│   ├── 📄SimpleHeuristic.py
│   ├── 📄TeamHeuristic.py
│   └── 📄utilities.py
└── 📄README.md
```