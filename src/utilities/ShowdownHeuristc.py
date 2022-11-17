from src.utilities.BattleStatus import BattleStatus
from src.utilities.Heuristic import Heuristic
from src.utilities.stats_utilities import estimate_stat


class ShowdownHeuristic(Heuristic):
    """
    More info: https://ieeexplore.ieee.org/abstract/document/8080435
    """

    def compute(self, battle_node: BattleStatus, depth: int) -> float:
        act_poke_hp = battle_node.act_poke.current_hp
        opp_poke_hp = battle_node.opp_poke.current_hp
        if act_poke_hp < 0:
            act_poke_hp = 0
        if opp_poke_hp < 0:
            opp_poke_hp = 0
        opp_poke_max_hp = estimate_stat(battle_node.opp_poke.pokemon, "hp")
        score = (act_poke_hp / battle_node.act_poke.pokemon.max_hp) - 3 * (opp_poke_hp / opp_poke_max_hp) - 0.3 * depth
        return score
