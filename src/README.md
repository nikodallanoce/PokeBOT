# PokeBOT
This is the main directory of our project which hosts the engine, players and other functions necessary to let the bot work.
## Structure
```bash
📂src
├── 📂engine  # what the bot needs to work flawlessly
│   ├── 📄base_power.py  # base power computation
│   ├── 📄battle_utilities.py  # useful methods to use during a battle
│   ├── 📄damage.py  # damage computation
│   ├── 📄move_effects.py  # computes the drain, heal, recoil etc... of the moves
│   ├── 📄stats.py  # stats computation
│   └── 📄useful_data.py  # stores useful data for the entire engine
├── 📂players  # the bot's playstyles
│   ├── 📄baseline_player.py  # MaxBasePower and BestDamage players
│   ├── 📄MiniMaxPlayer.py  # player that follows a MiniMax strategy
│   └── 📄RuleBasedPLayer.py  # player that acts based on rules
├── 📂strategy  # strategies for different battle mechanics
│   ├── 📄gimmick.py  # gimmick strategies
│   ├── 📄matchup.py  # matchup strategies
│   └── 📄switch.py  # switch strategies
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