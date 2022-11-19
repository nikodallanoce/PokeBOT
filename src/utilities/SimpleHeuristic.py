from src.utilities.BattleStatus import BattleStatus
from src.utilities.Heuristic import Heuristic
from src.utilities.stats_utilities import estimate_stat


class SimpleHeuristic(Heuristic):

    def compute(self, battle_node: BattleStatus, depth: int) -> float:
        bot_hp = battle_node.act_poke.current_hp
        opp_hp = battle_node.opp_poke.current_hp
        opp_max_hp = estimate_stat(battle_node.opp_poke.pokemon, "hp")
        score = (bot_hp / battle_node.act_poke.pokemon.max_hp) - 3 * (opp_hp / opp_max_hp) - 0.3 * depth
        if battle_node.act_poke.is_fainted():
            score -= 1
        elif battle_node.opp_poke.is_fainted():
            score += 1
        return score
