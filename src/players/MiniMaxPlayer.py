from typing import Optional

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
                                            start_timer_on_battle_start=start_timer_on_battle_start,
                                            start_listening=start_listening,
                                            ping_interval=ping_interval, ping_timeout=ping_timeout, team=team)
        self.heuristic: Heuristic = heuristic
        self.max_depth: int = max_depth
        self.verbose: bool = verbose
        self.best_stats_pokemon: int = 0

    def choose_move(self, battle):
        if battle.turn == 1:
            self.best_stats_pokemon = max([sum(pokemon.base_stats.values()) for pokemon in battle.team.values()])
        weather, terrains, bot_conditions, opp_conditions = retrieve_battle_status(battle).values()
        opp_max_hp = compute_stat(battle.opponent_active_pokemon, "hp", weather, terrains)
        opp_team = [poke for poke in battle.opponent_team.values() if poke.status != Status.FNT and not poke.active]
        root_battle_status = BattleStatus(
            NodePokemon(battle.active_pokemon, is_act_poke=True, moves=battle.available_moves),
            NodePokemon(battle.opponent_active_pokemon, is_act_poke=False, current_hp=opp_max_hp,
                        moves=list(battle.opponent_active_pokemon.moves.values())),
            battle.available_switches, opp_team, battle.weather, terrains,
            opp_conditions, None, Gen8Move('splash'), True)

        best_move = self.get_best_move(battle, root_battle_status)
        dynamax: bool = False
        my_team = [poke for poke in list(battle.team.values()) if poke.status != Status.FNT and not poke.active]
        if battle.can_dynamax:
            dynamax = self.__should_dynamax(battle.active_pokemon, my_team)
        if self.verbose: self.print_chosen_move(battle, best_move, opp_conditions, terrains, weather)

        return self.create_order(best_move, dynamax=dynamax)

    def __should_dynamax(self, bot_pokemon: Pokemon, bot_team: list[Pokemon]) -> bool:
        # If the pokèmon is the last one alive, use the dynamax
        if len(bot_team) == 0:
            return True

        # If the current pokèmon is the best one in terms of base stats and the matchup is favorable, then dynamax
        if sum(bot_pokemon.base_stats.values()) == self.best_stats_pokemon \
                and bot_pokemon.current_hp_fraction >= 0.65:
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
            #print(str(depth) + " bot -> " + str(node))
            for poss_act in node.act_poke_avail_actions():
                new_state = node.simulate_action(poss_act, is_my_turn)
                # if node.move_first or isinstance(poss_act, Pokemon):
                #     child_score, child_node = self.alphabeta(new_state, depth, alpha, beta, False)
                # else:
                #     child_score, child_node = self.alphabeta(new_state, depth - 1, alpha, beta, False)
                child_score, child_node = self.alphabeta(new_state, depth, alpha, beta, False)
                if score < child_score:
                    ret_node = child_node
                score = max(score, child_score)
                if score >= beta:
                    break  # beta cutoff
                alpha = max(alpha, score)

            #print(str(depth) + " bot -> " + str(ret_node))
            return score, ret_node
        else:
            score = float('inf')
            ret_node = node
            #print(str(depth) + " bot -> " + str(node))
            for poss_act in node.opp_poke_avail_actions():
                new_state = node.simulate_action(poss_act, is_my_turn)
                child_score, child_node = self.alphabeta(new_state, depth + 1, alpha, beta, True)
                #print(str(depth) + " opp -> " + str(child_node))
                if score > child_score:
                    ret_node = child_node
                score = min(score, child_score)
                if score <= alpha:
                    break  # alpha cutoff
                beta = min(beta, score)

            #print(str(depth) + " opp -> " + str(ret_node))
            return score, ret_node

    @staticmethod
    def opponent_loose(node: BattleStatus) -> bool:
        return node.opp_poke.is_fainted() and len(node.opp_poke_avail_actions()) == 0

    @staticmethod
    def player_loose(node: BattleStatus) -> bool:
        return node.act_poke.is_fainted() and len(node.act_poke_avail_actions()) == 0

    def is_terminal_node(self, node: BattleStatus) -> bool:
        return self.player_loose(node) or self.opponent_loose(node)
