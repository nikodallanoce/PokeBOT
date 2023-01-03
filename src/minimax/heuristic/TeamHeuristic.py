from typing import List
from src.minimax.BattleStatus import BattleStatus
from src.minimax.heuristic.Heuristic import Heuristic
from src.engine.stats import estimate_stat
import numpy as np

# Best parameters for now (I made only a very small random search)
BEST_PARAMETERS = [0.29845110404242714, 0.12477383583753021, 0.18681976327640784, 0.3899552968436348]
BEST_PENALTY = 0.036475451823316817


class TeamHeuristic(Heuristic):

    def __init__(self, parameters: List[float] = None, penalty: float = BEST_PENALTY):
        super(TeamHeuristic, self).__init__()
        self.parameters_num = 4
        self.parameters: List[float] = BEST_PARAMETERS if parameters is None else parameters
        self.parameters = np.array(self.parameters)
        self.penalty: float = penalty

    def compute(self, battle_node: BattleStatus, depth: int) -> float:
        bot_hp = battle_node.act_poke.current_hp
        bot_max_hp = battle_node.act_poke.pokemon.max_hp
        team_hp = bot_hp / bot_max_hp
        for poke in battle_node.avail_switches:
            team_hp += poke.current_hp_fraction

        alive_team = len(battle_node.avail_switches)
        if not battle_node.act_poke.is_fainted():
            alive_team += 1

        opp_hp = battle_node.opp_poke.current_hp
        opp_max_hp = estimate_stat(battle_node.opp_poke.pokemon, "hp")
        # opp_team_len = 6 - len([pokemon for pokemon in battle_node.opp_team if pokemon.fainted])
        opp_team_len = 0

        b1 = self.parameters[0]
        b2 = self.parameters[1]
        m1 = self.parameters[2]
        m2 = self.parameters[3]
        p1 = self.penalty

        score = b1 * (team_hp / 6) + b2 * (alive_team / 6) - m1 * (opp_hp / opp_max_hp) - m2 * (
                opp_team_len / 6) - p1 * depth

        return score
