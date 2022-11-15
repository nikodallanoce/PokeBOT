from src.utilities.BattleStatus import BattleStatus
from src.utilities.Heuristic import Heuristic
from src.utilities.stats_utilities import estimate_stat


class SimpleHeuristic(Heuristic):

    def compute(self, battle_node: BattleStatus) -> float:
        act_poke_hp = battle_node.act_poke.current_hp
        opp_poke_hp = battle_node.opp_poke.current_hp
        if act_poke_hp < 0:
            act_poke_hp = 0
        if opp_poke_hp < 0:
            opp_poke_hp = 0
        opp_poke_max_hp = estimate_stat(battle_node.opp_poke.pokemon, "hp")
        score = (act_poke_hp / battle_node.act_poke.pokemon.max_hp) - (opp_poke_hp / opp_poke_max_hp)
        return score
