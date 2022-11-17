from src.utilities.Heuristic import Heuristic
from src.utilities.NodePokemon import NodePokemon
from src.utilities.battle_utilities import *
from src.utilities.stats_utilities import *


class BattleStatus:

    def __init__(self, act_poke: NodePokemon, opp_poke: NodePokemon,
                 avail_moves: list[Move],
                 avail_switches: list[Pokemon],
                 weather: Weather, terrains: list[Field], opp_conditions: list[SideCondition], ancestor, move: Move):
        self.act_poke = act_poke
        self.opp_poke = opp_poke
        self.avail_moves = avail_moves
        self.avail_switches = avail_switches
        self.weather = weather
        self.terrains = terrains
        self.opp_conditions = opp_conditions
        self.ancestor = ancestor
        self.score = 0
        self.move = move

    def act_poke_avail_actions(self):
        return self.avail_moves

    def opp_poke_avail_actions(self):
        return self.opp_poke.moves

    def compute_score(self, heuristic: Heuristic, depth: int):
        score = heuristic.compute(self, depth)
        return score

    def simulate_turn(self, move: Move, is_my_turn: bool):
        if is_my_turn:
            damage = compute_damage(move, self.act_poke.pokemon, self.opp_poke.pokemon, self.weather, self.terrains,
                                    self.opp_conditions, is_my_turn)["ub"]
            updated_hp = self.opp_poke.current_hp - damage
            opp_poke = self.opp_poke.clone(current_hp=updated_hp)

            child = BattleStatus(self.act_poke, opp_poke,
                                 self.avail_moves.copy(), self.avail_switches, self.weather, self.terrains,
                                 self.opp_conditions, self, move)
            return child

        else:
            damage = compute_damage(move, self.opp_poke.pokemon, self.act_poke.pokemon, self.weather, self.terrains,
                                    self.opp_conditions, is_my_turn)["ub"]
            updated_hp = self.opp_poke.current_hp - damage
            act_poke = self.act_poke.clone(current_hp=updated_hp)

            return BattleStatus(act_poke, self.opp_poke, self.avail_moves.copy(), self.avail_switches,
                                self.weather, self.terrains, self.opp_conditions, self, move)
