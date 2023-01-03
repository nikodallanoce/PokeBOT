from src.minimax.BattleStatus import BattleStatus
from src.minimax.heuristic.Heuristic import Heuristic
from src.engine.stats import estimate_stat


class SimpleHeuristic(Heuristic):

    def compute(self, battle_node: BattleStatus, depth: int) -> float:
        """
        Evaluate state in the minimax algorithm using only the knowledge of the two active pokémon in the battle
        :param battle_node: minimax node containing the state information
        :param depth: depth of the node in the minimax tree
        :return: evaluation score of the minimax node
        """
        bot_hp = battle_node.act_poke.current_hp
        opp_hp = battle_node.opp_poke.current_hp
        opp_max_hp = estimate_stat(battle_node.opp_poke.pokemon, "hp")
        score = (bot_hp / battle_node.act_poke.pokemon.max_hp) - (
                opp_hp / opp_max_hp)

        return score
