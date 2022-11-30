import math
from typing import Optional

import numpy as np
from poke_env import PlayerConfiguration, ServerConfiguration
from poke_env.environment import Battle
from poke_env.player import Player
from poke_env.teambuilder import Teambuilder
from poke_env.environment.status import Status

from src.utilities.BattleStatus import BattleStatus
from src.utilities.Heuristic import Heuristic
from src.utilities.NodePokemon import NodePokemon
from src.utilities.battle_utilities import *
from src.utilities.stats_utilities import compute_stat
from src.utilities.SimpleHeuristic import SimpleHeuristic
from src.utilities.utilities import matchups_to_string


class MiniMaxPlayer(Player):

    def __init__(self,
                 heuristic: Optional[Heuristic] = SimpleHeuristic(),
                 max_depth: Optional[int] = 2,
                 verbose: bool = False,
                 player_configuration: Optional[PlayerConfiguration] = None,
                 *,
                 avatar: Optional[int] = None,
                 battle_format: str = "gen8randombattle",
                 log_level: Optional[int] = None,
                 max_concurrent_battles: int = 1,
                 save_replays: Union[bool, str] = False,
                 server_configuration: Optional[ServerConfiguration] = None,
                 start_timer_on_battle_start: bool = False,
                 start_listening: bool = True,
                 ping_interval: Optional[float] = 20.0,
                 ping_timeout: Optional[float] = 20.0,
                 team: Optional[Union[str, Teambuilder]] = None,
                 ):
        super(MiniMaxPlayer, self).__init__(player_configuration=player_configuration, avatar=avatar,
                                            battle_format=battle_format, log_level=log_level,
                                            max_concurrent_battles=max_concurrent_battles, save_replays=save_replays,
                                            server_configuration=server_configuration,
                                            start_timer_on_battle_start=True,
                                            start_listening=start_listening,
                                            ping_interval=ping_interval, ping_timeout=ping_timeout, team=team)
        self.heuristic: Heuristic = heuristic
        self.max_depth: int = max_depth
        self.verbose: bool = verbose
        self.previous_pokemon = None
        self.max_team_matchup: int = -8
        self.toxic_turn: int = 0

    def choose_move(self, battle):

        # Retrieve both active pokémon
        bot_pokemon: Pokemon = battle.active_pokemon
        opp_pokemon: Pokemon = battle.opponent_active_pokemon

        # Retrieve all the other pokèmon in the team that are still alive
        bot_team = [pokemon for pokemon in battle.team.values()
                    if not pokemon.active and not pokemon.fainted]

        # Retrieve all the pokémon in the opponent's team
        opp_team_pokemon = 6 - len([pokemon for pokemon in battle.opponent_team.values()
                                    if not pokemon.active and pokemon.fainted])

        # Retrieve weather, terrains and side conditions
        weather, terrains, bot_conditions, opp_conditions = retrieve_battle_status(battle).values()

        # Compute the hp of both pokémon
        # bot_hp = bot_pokemon.current_hp
        opp_max_hp = compute_stat(opp_pokemon, "hp", weather, terrains)
        opp_hp = int(opp_max_hp * opp_pokemon.current_hp_fraction)

        best_switch, bot_matchup, outspeed_p, team_matchups = self.best_switch_on_matchup(battle, bot_pokemon, bot_team,
                                                                                          opp_pokemon, terrains,
                                                                                          weather)
        if self.__should_switch(bot_pokemon, bot_matchup, outspeed_p) and battle.available_switches:
            self.previous_pokemon = bot_pokemon
            if self.verbose:
                print("Switching to {0}\n{1}".format(best_switch.species, "-" * 110))
            return self.create_order(best_switch)

        if battle.available_moves:
            opp_team = [poke for poke in battle.opponent_team.values() if not poke.active]
            avail_switches = battle.available_switches

            available_moves = battle.available_moves
            available_moves.sort(reverse=True, key=lambda x: int(x.base_power))
            root_battle_status = BattleStatus(
                NodePokemon(battle.active_pokemon, is_act_poke=True, moves=available_moves),
                NodePokemon(battle.opponent_active_pokemon, is_act_poke=False, current_hp=opp_max_hp,
                            moves=list(battle.opponent_active_pokemon.moves.values())),
                avail_switches, opp_team, battle.weather, terrains,
                opp_conditions, None, Gen8Move('splash'), True)

            can_defeat, best_move = False, Gen8Move('splash')
            if root_battle_status.move_first and len(battle.available_moves) > 0:
                can_defeat, best_move = self.hit_if_act_poke_can_outspeed(battle, terrains, opp_max_hp, opp_conditions)
            if len(battle.available_moves) == 0 or can_defeat is not True:
                best_move = self.get_best_move(battle, root_battle_status)
            dynamax: bool = False
            my_team = [poke for poke in list(battle.team.values()) if poke.status != Status.FNT and not poke.active]
            if battle.can_dynamax and not isinstance(best_move, Pokemon):
                dynamax = self.should_dynamax(battle.active_pokemon, my_team, bot_matchup)
            if self.verbose: self.print_chosen_move(battle, best_move, opp_conditions, terrains, weather)

            return self.create_order(best_move, dynamax=dynamax)

        elif battle.available_switches:
            # Update the matchup for each remaining pokèmon in the team
            for pokemon in bot_team:
                team_matchups.update({pokemon: self.__matchup_on_types(pokemon, opp_pokemon)})

            # Choose the new active pokèmon
            self.max_team_matchup = max(team_matchups.values()) if len(team_matchups) > 0 else -8
            best_switch = self.__compute_best_switch(team_matchups, opp_pokemon, weather, terrains)
            self.previous_pokemon = bot_pokemon
            if self.verbose:
                print("Switching to {0}\n{1}".format(best_switch.species, "-" * 110))

            return self.create_order(best_switch)

        return self.choose_random_move(battle)

    def best_switch_on_matchup(self, battle, bot_pokemon, bot_team, opp_pokemon, terrains, weather):
        # Compute matchup scores for every remaining pokémon in the team
        bot_matchup = self.__matchup_on_types(bot_pokemon, opp_pokemon)
        team_matchups = dict()
        for pokemon in bot_team:
            team_matchups.update({pokemon: self.__matchup_on_types(pokemon, opp_pokemon)})
        # Set the best pokémon in terms of stats
        if battle.turn == 1:
            self.best_stats_pokemon = max([sum(pokemon.base_stats.values()) for pokemon in battle.team.values()])
        # If we switched pokémon, then update the bot's infos
        if not self.previous_pokemon:
            self.previous_pokemon = bot_pokemon
        elif bot_pokemon.species != self.previous_pokemon.species:
            self.previous_pokemon = bot_pokemon
            self.toxic_turn = 0
        else:
            bot_pokemon._first_turn = False
            if bot_pokemon.status is Status.TOX:
                self.toxic_turn += 1
        # Compute the best pokémon the bot can switch to
        self.max_team_matchup = max(team_matchups.values()) if len(team_matchups) > 0 else -8
        best_switch = self.__compute_best_switch(team_matchups, opp_pokemon, weather, terrains)
        # Compute the probability of outpseeding the opponent pokémon
        outspeed_p, opp_spe_lb, opp_spe_ub = outspeed_prob(bot_pokemon, opp_pokemon, weather, terrains).values()
        if self.verbose and bot_pokemon.current_hp != 0:
            print("Turn {0}\n".format(battle.turn))
            print(bot_status_to_string(bot_pokemon, opp_pokemon, weather, terrains))
            print("Current matchup: {0}\nTeam matchups: {1}".format(bot_matchup, matchups_to_string(team_matchups)))

        return best_switch, bot_matchup, outspeed_p, team_matchups

    def choose_move_old(self, battle):
        if battle.turn == 1:
            self.best_stats_pokemon = max([sum(pokemon.base_stats.values()) for pokemon in battle.team.values()])
        weather, terrains, bot_conditions, opp_conditions = retrieve_battle_status(battle).values()
        opp_max_hp = compute_stat(battle.opponent_active_pokemon, "hp", weather, terrains)
        opp_team = [poke for poke in battle.opponent_team.values() if poke.status != Status.FNT and not poke.active]
        avail_switches = battle.available_switches

        available_moves = battle.available_moves
        available_moves.sort(reverse=True, key=lambda x: int(x.base_power))
        root_battle_status = BattleStatus(
            NodePokemon(battle.active_pokemon, is_act_poke=True, moves=available_moves),
            NodePokemon(battle.opponent_active_pokemon, is_act_poke=False, current_hp=opp_max_hp,
                        moves=list(battle.opponent_active_pokemon.moves.values())),
            avail_switches, opp_team, battle.weather, terrains,
            opp_conditions, None, Gen8Move('splash'), True)

        can_defeat, best_move = False, Gen8Move('splash')
        if root_battle_status.move_first and len(battle.available_moves) > 0:
            can_defeat, best_move = self.hit_if_act_poke_can_outspeed(battle, terrains, opp_max_hp, opp_conditions)
        if len(battle.available_moves) == 0 or can_defeat is not True:
            best_move = self.get_best_move(battle, root_battle_status)
        dynamax: bool = False
        my_team = [poke for poke in list(battle.team.values()) if poke.status != Status.FNT and not poke.active]
        if battle.can_dynamax and not isinstance(best_move, Pokemon):
            dynamax = self.should_dynamax(battle.active_pokemon, my_team)
        if self.verbose: self.print_chosen_move(battle, best_move, opp_conditions, terrains, weather)

        return self.create_order(best_move, dynamax=dynamax)

    def hit_if_act_poke_can_outspeed(self, battle: AbstractBattle, terrains: list[Field], opp_max_hp: int,
                                     opp_conditions: list) -> tuple[bool, Move]:
        opp_hp = math.ceil(opp_max_hp * battle.opponent_active_pokemon.current_hp_fraction)
        for move in battle.available_moves:
            battle_status = BattleStatus(
                NodePokemon(battle.active_pokemon, is_act_poke=True, moves=battle.available_moves),
                NodePokemon(battle.opponent_active_pokemon, is_act_poke=False, current_hp=opp_hp,
                            moves=list(battle.opponent_active_pokemon.moves.values())),
                [], [], battle.weather, terrains,
                opp_conditions, None, move, True)
            opp_is_fainted = battle_status.simulate_action(move, True).opp_poke.is_fainted()
            if opp_is_fainted:
                return True, move
        return False, Gen8Move('splash')

    def should_dynamax(self, bot_pokemon: Pokemon, bot_team: list[Pokemon], matchup: float) -> bool:
        # If the pokèmon is the last one alive, use the dynamax
        if len(bot_team) == 0:
            return True

        # If the current pokèmon is the best one in terms of base stats and the matchup is favorable, then dynamax
        if sum(bot_pokemon.base_stats.values()) == self.best_stats_pokemon \
                and matchup >= 1 and bot_pokemon.current_hp_fraction >= 0.8:
            return True

        if bot_pokemon.current_hp_fraction == 1:
            # If the current pokèmon is the last one at full hp, use dynamax on it
            if len([pokemon for pokemon in bot_team if pokemon.current_hp_fraction == 1]) == 0:
                return True
            else:
                # If the current matchup is the best one, and it's favourable, then dynamax
                if matchup >= self.max_team_matchup and matchup > 2:
                    return True

        if matchup >= self.max_team_matchup and matchup > 2 and bot_pokemon.current_hp_fraction == 1:
            return True

        return False

    @staticmethod
    def print_chosen_move(battle, best_move, opp_conditions, terrains, weather):
        if isinstance(best_move, Move):
            for mo in battle.available_moves:
                damage = compute_damage(mo, battle.active_pokemon, battle.opponent_active_pokemon, weather,
                                        terrains, opp_conditions, battle.active_pokemon.boosts,
                                        battle.opponent_active_pokemon.boosts, True)["lb"]
                chs_mv = mo.id + " : " + mo.type.name + " dmg: " + str(damage)
                if mo.id == best_move.id:
                    chs_mv += "♦"
                print(chs_mv)
        elif isinstance(best_move, Pokemon):
            chs_mv = best_move
            print(chs_mv)

        print()

    def get_best_move(self, battle: AbstractBattle, root_battle_status: BattleStatus) -> Pokemon | Move:
        ris = self.alphabeta(root_battle_status, 0, float('-inf'), float('+inf'), True)
        node: BattleStatus = ris[1]
        best_move = self.choose_random_move(battle)  # il bot ha fatto U-turn e node diventava none
        if node is not None and node.move != Gen8Move('splash'):
            best_move = node.move  # self.choose_random_move(battle)
            curr_node = node
            while curr_node.ancestor is not None:
                best_move = curr_node.move
                curr_node = curr_node.ancestor
        return best_move

    @staticmethod
    def __type_advantage(attacker: Pokemon, defender: Pokemon) -> float:
        type_gain = max([defender.damage_multiplier(attacker_type)
                         for attacker_type in attacker.types if attacker_type is not None])
        return type_gain

    @staticmethod
    def __move_type_advantage(bot_pokemon: Pokemon, opponent_pokemon: Pokemon, opponent_type_adv: float) -> float:
        # Consider the bot move-type match-up
        bot_type_gain = [opponent_pokemon.damage_multiplier(move_bot)
                         for move_bot in bot_pokemon.moves.values() if
                         move_bot.category is not MoveCategory.STATUS]
        bot_type_gain = max(bot_type_gain) if len(bot_type_gain) > 0 else 1
        # Consider the opponent move-type match-up
        opponent_type_gain = 0
        if len(opponent_pokemon.moves) > 0:
            for move_opp in opponent_pokemon.moves.values():
                if move_opp.category is not MoveCategory.STATUS:
                    opponent_type_gain_iter = bot_pokemon.damage_multiplier(move_opp)
                    if opponent_type_gain_iter > opponent_type_gain:
                        opponent_type_gain = opponent_type_gain_iter

        if opponent_type_gain < opponent_type_adv and len(opponent_pokemon.moves) < 4:
            return bot_type_gain - opponent_type_adv

        return bot_type_gain - opponent_type_gain

    def __should_switch(self, bot_pokemon: Pokemon, matchup: float, outspeed_p: float) -> bool:
        # Do not switch out the pokèmon if it is dynamaxed unless there is a very bad matchup
        if bot_pokemon.is_dynamaxed:
            if matchup <= -4:
                return True

            return False

        # We can switch out if there are matchups better than the current one
        if self.max_team_matchup > matchup:
            # The "toxic" status is one of the worst status, we need to attenuate its effects by switching
            if bot_pokemon.status is Status.TOX and matchup - self.toxic_turn <= -2:
                return True

            # If one of the defense stat was decreased too much, switch out to not take heavy hits
            if bot_pokemon.boosts["def"] <= -2 or bot_pokemon.boosts["spd"] <= -2:
                return True

            # If the attack stat was decreased too much and the pokèmon is a physical attacker, switch out
            if bot_pokemon.base_stats["atk"] > bot_pokemon.boosts["spa"]:
                if matchup <= -1.5 or bot_pokemon.boosts["atk"] <= -2:
                    return True

            # If the special attack stat was decreased too much and the pokèmon is a special attacker, switch out
            if bot_pokemon.base_stats["spa"] > bot_pokemon.boosts["atk"]:
                if matchup <= -1.5 or bot_pokemon.boosts["spa"] <= -2:
                    return True

            # Switch out if the matchup is on the opponent's favor
            if matchup <= -1.5:
                return True
            elif matchup <= -1 and outspeed_p <= 0.5:
                return True

        return False

    def __compute_best_switch(self,
                              team_matchups: dict[Pokemon, float],
                              opp_pokemon: Pokemon,
                              weather: Weather,
                              terrains: list[Field]) -> Union[Pokemon | None]:
        if team_matchups:
            # Retrieve all the pokémon in the team with the best matchup
            best_switches = {pokemon: pokemon.stats for pokemon, matchup in team_matchups.items()
                             if matchup == self.max_team_matchup}

            # Keep those that can outspeed the opponent's pokémon
            outspeed_opp = [pokemon for pokemon, _ in best_switches.items()
                            if outspeed_prob(pokemon, opp_pokemon, weather, terrains)["outspeed_p"] > 0.6]
            if outspeed_opp:
                switch_choice = np.random.randint(0, len(outspeed_opp))
                return outspeed_opp[switch_choice]
            else:
                best_switches = list(best_switches.keys())
                switch_choice = np.random.randint(0, len(best_switches))
                return best_switches[switch_choice]
        else:
            return None

    def __matchup_on_types(self, bot_pokemon: Pokemon, opponent_pokemon: Pokemon) -> float:
        bot_type_adv = self.__type_advantage(bot_pokemon, opponent_pokemon)
        opponent_type_adv = self.__type_advantage(opponent_pokemon, bot_pokemon)
        poke_adv = bot_type_adv - opponent_type_adv
        move_adv = self.__move_type_advantage(bot_pokemon, opponent_pokemon, opponent_type_adv)
        return poke_adv + move_adv

    def alphabeta(self, node: BattleStatus, depth: int, alpha: float, beta: float, is_my_turn: bool) -> tuple[
        float, BattleStatus]:
        """
        (* Initial call *) alphabeta(origin, 0, −inf, +inf, TRUE)
        """
        if depth == self.max_depth or self.is_terminal_node(node):
            score = node.compute_score(self.heuristic, depth)
            node.score = score
            return score, node
        if is_my_turn:
            score = float('-inf')
            ret_node = node
            # print(str(depth) + " bot -> " + str(node))
            for poss_act in node.act_poke_avail_actions():
                new_state = node.simulate_action(poss_act, is_my_turn)
                child_score, child_node = self.alphabeta(new_state, depth, alpha, beta, False)
                if score < child_score:
                    ret_node = child_node
                score = max(score, child_score)
                if score >= beta:
                    break  # beta cutoff
                alpha = max(alpha, score)

            # print(str(depth) + " bot -> " + str(ret_node))
            return score, ret_node
        else:
            score = float('inf')
            ret_node = node
            # print(str(depth) + " bot -> " + str(node))
            for poss_act in node.opp_poke_avail_actions():
                new_state = node.simulate_action(poss_act, is_my_turn)
                child_score, child_node = self.alphabeta(new_state, depth + 1, alpha, beta, True)
                if score > child_score:
                    ret_node = child_node
                score = min(score, child_score)
                if score <= alpha:
                    break  # alpha cutoff
                beta = min(beta, score)

            # print(str(depth) + " opp -> " + str(ret_node))
            return score, ret_node

    @staticmethod
    def opponent_loose(node: BattleStatus) -> bool:
        return node.opp_poke.is_fainted() and len(node.opp_poke_avail_actions()) == 0

    @staticmethod
    def player_loose(node: BattleStatus) -> bool:
        return node.act_poke.is_fainted() and len(node.act_poke_avail_actions()) == 0

    def is_terminal_node(self, node: BattleStatus) -> bool:
        return self.player_loose(node) or self.opponent_loose(node)
