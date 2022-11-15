FROM ubuntu:22.10

RUN apt update
RUN apt-get install git nodejs npm curl nano -y

# Cloning showdown
WORKDIR /root/
RUN git clone https://github.com/smogon/pokemon-showdown.git
WORKDIR /root/pokemon-showdown

# Setting up config
RUN cp -r config/config-example.js config/config.js

# Changing to correct node version
RUN npm install -g n
RUN n 14.18.2

# Setup
RUN npm install

RUN apt-get -y install wget python3-pip
RUN pip3 install poke-env
RUN pip3 install pandas

#comment
WORKDIR /root/
RUN git clone https://github.com/nikodallanoce/PokeBOT.git players
ENV BotAIF_username=your_bot_username
ENV BotAIF_password=your_bot_password
WORKDIR /root/players
CMD cd ~/pokemon-showdown/ && node pokemon-showdown start --no-security