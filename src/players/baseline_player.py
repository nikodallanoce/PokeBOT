from poke_env.environment import Move, Pokemon
from poke_env.player import Player
from poke_env.teambuilder import Teambuilder
from poke_env import PlayerConfiguration, ServerConfiguration
from src.utilities.battle_utilities import compute_damage, outspeed_prob, retrieve_battle_status, bot_status_to_string
from typing import Optional, Union


class BestDamagePlayer(Player):

    def __init__(self,
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
                 verbose: bool = False,
                 can_switch: bool = False
                 ):
        super(BestDamagePlayer, self).__init__(player_configuration=player_configuration, avatar=avatar,
                                               battle_format=battle_format, log_level=log_level,
                                               max_concurrent_battles=max_concurrent_battles, save_replays=save_replays,
                                               server_configuration=server_configuration,
                                               start_timer_on_battle_start=start_timer_on_battle_start,
                                               start_listening=start_listening,
                                               ping_interval=ping_interval, ping_timeout=ping_timeout, team=team)
        self.verbose = verbose
        self.can_switch = can_switch

    def choose_move(self, battle):
        bot_pokemon: Pokemon = battle.active_pokemon
        opp_pokemon: Pokemon = battle.opponent_active_pokemon
        weather, terrains, bot_conditions, opp_conditions = retrieve_battle_status(battle).values()
        if battle.available_moves:
            if self.verbose:
                print("Turn {0}".format(battle.turn))
                print(bot_status_to_string(bot_pokemon, opp_pokemon, weather, terrains))

            best_move: Move = max(battle.available_moves,
                                  key=lambda move: compute_damage(move, bot_pokemon, opp_pokemon, weather,
                                                                  terrains, opp_conditions, True)["ub"])
            if self.verbose:
                print("Outspeed probability {0}".format(
                    outspeed_prob(bot_pokemon, opp_pokemon, weather, terrains, False)["outspeed_p"]))
                print("Best move: {0}, type: {1}\n{2}".format(best_move.id, best_move.type, "-" * 110))

            gimmick = False
            if battle.can_dynamax:
                gimmick = True

            return self.create_order(best_move, dynamax=gimmick)
        else:
            if battle.available_switches and self.can_switch:
                max_type_gain = -5
                max_type_gain_pokemon = None
                for pokemon in battle.available_switches:
                    # Consider the bot type match-up
                    bot_type_gain = max([opp_pokemon.damage_multiplier(switch_type)
                                         for switch_type in pokemon.types if switch_type is not None])

                    # Consider the opponent type match-up
                    opponent_type_gain = max([pokemon.damage_multiplier(opponent_type)
                                              for opponent_type in opp_pokemon.types if opponent_type is not None])
                    type_gain = bot_type_gain - opponent_type_gain
                    if max_type_gain < type_gain:
                        max_type_gain = type_gain
                        max_type_gain_pokemon = pokemon

                if self.verbose:
                    print("Switching to: {0}\n{1}".format(max_type_gain_pokemon, "-" * 100))
                return self.create_order(max_type_gain_pokemon)

            return self.choose_random_move(battle)


class MaxBasePowerPlayer(Player):

    def __init__(self,
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
                 verbose: bool = False
                 ):
        super(MaxBasePowerPlayer, self).__init__(player_configuration=player_configuration, avatar=avatar,
                                                 battle_format=battle_format, log_level=log_level,
                                                 max_concurrent_battles=max_concurrent_battles,
                                                 save_replays=save_replays, server_configuration=server_configuration,
                                                 start_timer_on_battle_start=start_timer_on_battle_start,
                                                 start_listening=start_listening,
                                                 ping_interval=ping_interval, ping_timeout=ping_timeout, team=team)
        self.verbose = verbose

    def choose_move(self, battle):
        if battle.available_moves:
            weather, terrains, _, _ = retrieve_battle_status(battle).values()
            if self.verbose:
                print("Turn {0}".format(battle.turn))
                print(bot_status_to_string(battle.active_pokemon, battle.opponent_active_pokemon, weather, terrains))

            best_move: Move = max(battle.available_moves, key=lambda move: move.base_power)
            gimmick = False
            if battle.can_dynamax:
                gimmick = True

            if self.verbose:
                print("Best move: {0}, type: {1}\n{2}".format(best_move.id, best_move.type, "-" * 110))

            return self.create_order(best_move, dynamax=gimmick)
        else:
            return self.choose_random_move(battle)
