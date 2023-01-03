from src.minimax.BattleStatus import BattleStatus
from src.minimax.heuristic.Heuristic import Heuristic
from src.engine.stats import estimate_stat


class SimpleHeuristic(Heuristic):

    def compute(self, battle_node: BattleStatus, depth: int) -> float:
        bot_hp = battle_node.act_poke.current_hp
        opp_hp = battle_node.opp_poke.current_hp
        # bot_hp = (bot_hp / battle_node.act_poke.pokemon.max_hp) + bot_hp / 1e3

        opp_max_hp = estimate_stat(battle_node.opp_poke.pokemon, "hp")
        # opp_hp = (opp_hp / opp_max_hp) + opp_hp / 1e3
        # score = bot_hp - opp_hp - 0.2 * depth
        score = (bot_hp / battle_node.act_poke.pokemon.max_hp) - 2 * (
                opp_hp / opp_max_hp)

        return score
