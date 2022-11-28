from src.utilities.BattleStatus import BattleStatus
from src.utilities.Heuristic import Heuristic
from src.utilities.stats_utilities import estimate_stat
import numpy as np

# Best parameters for now (0.521/1 1000 matches vs Baseline)
BEST_PARAMETERS = [0.4535852806937534, 0.0594175956625287, 0.2676623723834168, 0.219334751260301]
BEST_PENALTY = 0.04184383589199678


class TeamHeuristic(Heuristic):

    def __init__(self, parameters: list[float] = None, penalty: float = BEST_PENALTY):
        super(TeamHeuristic, self).__init__()
        self.parameters_num = 4
        self.parameters: list[float] = BEST_PARAMETERS if parameters is None else parameters
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
        opp_team_len = 6 - len([pokemon for pokemon in battle_node.opp_team if pokemon.fainted])
        # opp_team_len = 0

        b1 = self.parameters[0]
        b2 = self.parameters[1]
        m1 = self.parameters[2]
        m2 = self.parameters[3]
        p1 = self.penalty

        score = b1 * (team_hp / 6) + b2 * (alive_team / 6) - m1 * (opp_hp / opp_max_hp) - m2 * (
                opp_team_len / 6) - p1 * depth

        return score
