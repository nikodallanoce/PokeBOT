from src.utilities.Heuristic import Heuristic
from src.utilities.NodePokemon import NodePokemon
from src.utilities.battle_utilities import *
from src.utilities.stats_utilities import *


class BattleStatus:

    def __init__(self, act_poke: NodePokemon, opp_poke: NodePokemon,
                 avail_switches: list[Pokemon],
                 weather: Weather, terrains: list[Field], opp_conditions: list[SideCondition], ancestor, move: Move):
        self.act_poke = act_poke
        self.opp_poke = opp_poke
        self.avail_switches = avail_switches
        self.weather = weather
        self.terrains = terrains
        self.opp_conditions = opp_conditions
        self.ancestor = ancestor
        self.score = 0
        self.move = move

    def act_poke_avail_actions(self):
        return self.act_poke.moves

    def opp_poke_avail_actions(self):
        return self.opp_poke.moves

    def compute_score(self, heuristic: Heuristic, depth: int):
        score = heuristic.compute(self, depth)
        return score

    def simulate_action(self, move: Move, is_my_turn: bool):
        if is_my_turn:
            damage = compute_damage(move, self.act_poke.pokemon, self.opp_poke.pokemon, self.weather, self.terrains,
                                    self.opp_conditions, self.act_poke.boosts, self.opp_poke.boosts, is_my_turn)["lb"]
            updated_hp = self.opp_poke.current_hp - damage
            if updated_hp <0:
                print()

            att_boost, def_boost = self.compute_updated_boosts(self.act_poke, self.opp_poke, move)

            opp_poke = self.opp_poke.clone(current_hp=updated_hp, boosts=def_boost)
            act_poke = self.act_poke.clone(boosts=att_boost)
            child = BattleStatus(act_poke, opp_poke,
                                 self.avail_switches, self.weather, self.terrains,
                                 self.opp_conditions, self, move)
            return child

        else:
            damage = compute_damage(move, self.opp_poke.pokemon, self.act_poke.pokemon, self.weather, self.terrains,
                                    self.opp_conditions, self.opp_poke.boosts, self.act_poke.boosts, is_my_turn)["ub"]
            att_boost, def_boost = self.compute_updated_boosts(self.opp_poke, self.act_poke, move)
            updated_hp = self.act_poke.current_hp - damage
            act_poke = self.act_poke.clone(current_hp=updated_hp, boosts=def_boost)
            opp_poke = self.opp_poke.clone(boosts=att_boost)
            return BattleStatus(act_poke, opp_poke,
                                self.avail_switches, self.weather, self.terrains,
                                self.opp_conditions, self, move)

    @staticmethod
    def compute_updated_boosts(att_poke: NodePokemon, def_poke: NodePokemon, move: Move):
        att_upd_boosts = att_poke.boosts.copy()
        def_upd_boosts = def_poke.boosts.copy()
        boosts = move.self_boost if move.boosts is None else move.boosts
        if boosts is not None:
            if move.target == 'self':
                for stat_boost, boost in boosts.items():
                    # upd_stats = compute_stat_boost(att_poke.pokemon, stat_boost, boost)
                    att_upd_boosts[stat_boost] += boost
            elif move.target == 'normal':
                for stat_boost, boost in boosts.items():
                    # upd_stats_att = compute_stat_boost(att_poke.pokemon, stat_boost, boost)
                    # att_upd_boosts[stat_boost] = upd_stats_att
                    # upd_stats_def = compute_stat_boost(def_poke.pokemon, stat_boost, boost)
                    def_upd_boosts[stat_boost] += boost

        return att_upd_boosts, def_upd_boosts
