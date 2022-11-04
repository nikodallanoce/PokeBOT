from poke_env.environment import Pokemon, Battle, Move, MoveCategory, Weather, Field
from poke_env.player import Player
from src.utilities.battle_utilities import compute_damage, outspeed_prob, compute_move_accuracy,\
    PROTECTING_MOVES, ENTRY_HAZARDS, ANTI_HAZARDS_MOVES


class RuleBasedPlayer(Player):

    verbose = False

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

    @staticmethod
    def __move_with_max_damage(attacker: Pokemon, defender: Pokemon, weather: Weather, terrain: Field,
                               is_bot: bool) -> {Move: float}:
        max_damage = -1
        max_damage_move = None
        for move in attacker.moves.values():
            damage = compute_damage(move, attacker, defender, weather, terrain, is_bot, verbose=False)
            if damage > max_damage:
                max_damage = damage
                max_damage_move = move

        return {max_damage_move: max_damage}

    def __matchup_on_types(self, bot_pokemon: Pokemon, opponent_pokemon: Pokemon) -> float:
        # outspeed_p = outspeed_prob(bot_pokemon, opponent_pokemon)
        bot_type_adv = self.__type_advantage(bot_pokemon, opponent_pokemon)
        opponent_type_adv = self.__type_advantage(opponent_pokemon, bot_pokemon)
        poke_adv = bot_type_adv - opponent_type_adv
        move_adv = self.__move_type_advantage(bot_pokemon, opponent_pokemon, bot_type_adv)
        return poke_adv + move_adv

    @staticmethod
    def __should_switch(bot_matchup: float, team_matchups: dict) -> bool:
        max_team_matchup = max(team_matchups.values()) if len(team_matchups) > 0 else -8
        return False

    @staticmethod
    def __should_dynamax(bot_pokemon: Pokemon, bot_team: list, bot_matchup: float, team_matchups: dict) -> bool:
        max_team_matchup = max(team_matchups.values()) if len(team_matchups) > 0 else -8
        if len(bot_team) == 0:
            dynamax = True
        elif bot_pokemon.current_hp_fraction == 1:
            if len([pokemon for pokemon in bot_team if pokemon.current_hp_fraction == 1]) == 0:
                dynamax = True
            else:
                if bot_matchup >= max_team_matchup and bot_matchup > 2:
                    dynamax = True
                else:
                    dynamax = False
        else:
            if bot_matchup >= max_team_matchup and bot_matchup > 4:
                dynamax = True
            else:
                dynamax = False

        return dynamax

    def choose_move(self, battle: Battle):
        # Retrieve both active pokèmon
        bot_pokemon: Pokemon = battle.active_pokemon
        opponent_pokemon: Pokemon = battle.opponent_active_pokemon

        # Retrieve weather and terrain
        weather = None if len(battle.weather.keys()) == 0 else next(iter(battle.weather.keys()))
        terrain = None if len(battle.fields.keys()) == 0 else next(iter(battle.fields.keys()))

        # Retrieve all the other pokèmon in the team that are still alive
        bot_team = [pokemon for pokemon in battle.team.values()
                    if pokemon is not bot_pokemon and not pokemon.fainted]

        # Compute matchup scores for every remaining pokèmon in the team
        bot_matchup = self.__matchup_on_types(bot_pokemon, opponent_pokemon)
        team_matchups = dict()
        for pokemon in bot_team:
            team_matchups.update({pokemon: self.__matchup_on_types(pokemon, opponent_pokemon)})

        # Switch out if there are available switches and the bot gains in terms of matchup by doing so
        if battle.available_switches and self.__should_switch(bot_matchup, team_matchups):
            switch = max(team_matchups, key=lambda pokemon: team_matchups[pokemon])
            return self.create_order(switch)

        # Choose one available move
        if battle.available_moves:
            bot_moves = dict()
            for move in battle.available_moves:
                # If we don't know any move of the opponent, the matchup is slightly against, then use a protecting move
                if move.id in PROTECTING_MOVES and len(opponent_pokemon.moves) == 0 and bot_matchup < -1:
                    return self.create_order(move)

                # We can use a move that puts an entry hazard if it isn't already present
                opponent_team_size = 6 - len([pokemon for pokemon in battle.opponent_team.values() if pokemon.fainted])
                if move.id in ENTRY_HAZARDS and opponent_team_size >= 4\
                        and ENTRY_HAZARDS[move.id] not in battle.opponent_side_conditions:
                    return self.create_order(move)

                # We can remove any entry hazard on our side if we have enough pokèmon remaining on our team
                if move.id in ANTI_HAZARDS_MOVES and len(bot_team) >= 1 and len(battle.side_conditions) > 0:
                    return self.create_order(move)

                # if len(move.boosts) > 0 and bot_matchup >= 1:
                    # return self.create_order(move)

                # In any other case, compute the damage and accuracy of the move
                damage = compute_damage(move, bot_pokemon, opponent_pokemon, weather, terrain, True, self.verbose)
                accuracy = compute_move_accuracy(move, bot_pokemon, opponent_pokemon, weather, terrain, self.verbose)
                bot_moves.update({move: {"damage": damage, "accuracy": accuracy}})

            # Keep those moves with the max damage
            max_damage = max([damage_accuracy["damage"] for damage_accuracy in bot_moves.values()])
            max_damage_moves = {move: bot_move["accuracy"] for move, bot_move in bot_moves.items()
                                if bot_move["damage"] == max_damage}

            # Choose the move with the best accuracy
            best_move = max(max_damage_moves, key=lambda move_accuracy: max_damage_moves[move_accuracy])

            # Use the dynamax if convenient
            dynamax = False
            if battle.can_dynamax:
                dynamax = self.__should_dynamax(bot_pokemon, bot_team, bot_matchup, team_matchups)

            return self.create_order(best_move, dynamax=dynamax)
        elif battle.available_switches:
            switch = max(team_matchups, key=lambda pokemon: team_matchups[pokemon])
            return self.create_order(switch)

        return self.choose_random_move(battle)
