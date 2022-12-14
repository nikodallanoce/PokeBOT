from src.minimax.BattleStatus import BattleStatus
from src.minimax.heuristic.Heuristic import Heuristic
from src.engine.stats import estimate_stat


class ShowdownHeuristic(Heuristic):

    def compute(self, battle_node: BattleStatus, depth: int) -> float:
        """
        Evaluate state in the minimax algorithm using the function provided by
        https://ieeexplore.ieee.org/abstract/document/8080435
        :param battle_node: minimax node containing the state information
        :param depth: depth of the node in the minimax tree
        :return: evaluation score of the minimax node
        """
        bot_hp = battle_node.act_poke.current_hp
        opp_hp = battle_node.opp_poke.current_hp
        opp_max_hp = estimate_stat(battle_node.opp_poke.pokemon, "hp")
        score = (bot_hp / battle_node.act_poke.pokemon.max_hp) - 3 * (opp_hp / opp_max_hp) - 0.3 * depth

        return score
