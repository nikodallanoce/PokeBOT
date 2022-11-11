# PokeBOT
Artificial Intelligence Fundamentals project for the a.y. 2022/2023.
- **Group name:** Elite Three
- **Group members:** [Niko Dalla Noce](https://github.com/nikodallanoce), [Giuseppe Lombardi](https://github.com/icezimmer), [Alessandro Ristori](https://github.com/RistoAle97)

## Pokemon battle bot
We developed a battle bot that you can play against on a [public server](https://play.pokemonshowdown.com/), the bot can assume different strategies depending on your choice.
### Basic playstyle
- **MaxBasePower**, the bot chooses the move with the best base power ignoring status moves, it switches to a random pokèmon only when one faints.
- **BestDamage**, the bot will choose the move with best damage, computed by taking into account many modifiers, and it will switch to the best pokémon in terms of type-matchup only when the current one faints.

### Enhanced playstyle
- **RuleBased**, the bot acts based on hard-coded rules based on the matchup score between it and the opponent pokémon. This version can switch and use moves that can boost stats, set entry hazards and give a status condition.
- **ExpectMiniMax**, the bot acts on an expect-minimax fashion by looking for some moves ahead in order to choose the best course of action.

## How to challenge the bot
First, you need to create a registered account for the bot on the [public server](https://play.pokemonshowdown.com/), then clone the repo
```bash
git clone https://github.com/nikodallanoce/PokeBOT
```
You also need to install all the required packages
```bash
pip install -r requirements.txt
```
After doing that, you can run the following command
```bash
python run_bot.py --user bot_username --password bot_password
```
If no username or password are passed, then the bot will try to retrieve such information from the environment variables *BotAIF_username* and *BotAIF_password*, if this doesn't work it will give an error.

Moreover, the command accepts some other arguments in order to change the bot's behaviour:
- You can choose how many challenges the bot will accept (default to 1) by using, as an example, ```--matches 10```, once those matches are ended the bot will stop.
- As default the bot uses the rule-based player, you can use ```--player``` followed by the player acronym to change such thing.
  - **MBP** for the MaxBasePower player.
  - **BD** for the BestDamage player.
  - **RB** for the RuleBased player.
  - **MM** for the minimax player.
- You can save the bot results in csv file by using ```--save```, such file is then stored inside the *bot_data* directory.

Have fun playing with the bot.

## Setting up a local server
If you want to run our bot, or your own, in a local server, then you can use the ```Dockerfile``` that you can find here inside the repo. First, copy the ```Dockerfile``` or clone the repo
```bash
git clone https://github.com/nikodallanoce/PokeBOT
```
Then modify the following lines inside the ```Dockerfile``` with the bot's username and password from the public server (you should have already registered the bot's account)
```dockerfile
ENV BotAIF_username=your_bot_username
ENV BotAIF_password=your_bot_password
```
Create a new docker image and container, this should be done only once
```bash
docker run --name pokemoncontainer -p 8000:8000 -it pokemon
```
You can now start your container
```bash
docker start pokemoncontainer
```
The local server should be running and your container's logs should look like this
```
RESTORE CHATROOM: lobby
RESTORE CHATROOM: staff
Worker 1 now listening on 0.0.0.0:8000
Test your server at http://localhost:8000
```
If so, then everything is fine, you can test the various players against each other.