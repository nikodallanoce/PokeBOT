from src.utilities.Heuristic import Heuristic
from src.engine.stats import estimate_stat


class OpponentHPHeuristic(Heuristic):

    def compute(self, battle_node, depth: int) -> float:
        opp_hp = battle_node.opp_poke.current_hp
        opp_max_hp = estimate_stat(battle_node.opp_poke.pokemon, "hp")

        bot_hp = battle_node.act_poke.current_hp
        bot_max_hp = battle_node.act_poke.pokemon.max_hp
        return - opp_hp
        # return (1 - (opp_hp / opp_max_hp)) + (bot_hp /bot_max_hp)
