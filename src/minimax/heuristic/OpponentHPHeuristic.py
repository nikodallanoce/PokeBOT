from src.minimax.heuristic.Heuristic import Heuristic
from src.engine.stats import estimate_stat


class OpponentHPHeuristic(Heuristic):

    def compute(self, battle_node, depth: int) -> float:
        """
        Evaluate state in the minimax algorithm using only the opponent's Pokèmon health points
        :param battle_node: minimax node containing the state information
        :param depth: depth of the node in the minimax tree
        :return: evaluation score of the minimax node
        """
        opp_hp = battle_node.opp_poke.current_hp
        opp_max_hp = estimate_stat(battle_node.opp_poke.pokemon, "hp")

        return - (opp_hp / opp_max_hp)
