# -- coding: utf-8 --
import discord
import os
import time

from Classment import LolRankings
import mysql_operations as sql

from PlayerLeagueInfo import *
from MatchLeagueInfo import *
from riotwatcher import LolWatcher, ApiError
from discord.ext import commands

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Ajoutez ce que vous voulez comme fonctions dans la classe du bot généralement c'est les + grosses fonctions qui process.
# Les commandes sont là pour mettre le serveur discord en relation avec le bot (En gros c'est pas censé faire bcp de lignes faites au mieux mdrr)
# Pour grouper les commandes, vous pouvez faire des modules avec l'objet discord.Cog (Allez regarder la doc)
# Mettez des commentaires si vous êtes deter, c'est cool pour les autres

# === todo list ===
# lp par jour (avec match_v5 de l'api lol)) (FAIT)
# historique match fini - de 15 min (On going)
# notif auto si demo / rankup

# api match_V5 de lol pour historique des parties

class BotWatcher(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="*")
        #self.watcher = LolWatcher(os.environ['RIOT_API_KEY'])  #Change with your DEV key (go to lol dev portal)
        self.watcher = LolWatcher("RGAPI-4e773a1a-44d3-4462-9177-2328336caacb")  #Change with your DEV key (go to lol dev portal)
        self.region = "euw1"
        self.colormap = {"IRON":discord.Colour.from_rgb(54, 37, 33),
                         "BRONZE":discord.Colour.from_rgb(66, 27, 18),
                         "SILVER":discord.Colour.from_rgb(112, 135, 143),
                         "GOLD":discord.Colour.from_rgb(241, 196, 15),
                         "PLATINUM":discord.Colour.from_rgb(33, 232, 133),
                         "DIAMOND":discord.Colour.from_rgb(58, 42, 116),
                         "MASTER":discord.Colour.from_rgb(180, 142, 214),
                         "GRANDMASTER":discord.Colour.from_rgb(203, 26, 32),
                         "CHALLENGER":discord.Colour.from_rgb(255, 255, 191),
                         "DEFAULT":discord.Colour.from_rgb(0, 0, 0)}
        self.winningColor = {"WIN":discord.Colour.from_rgb(135,206,235),
                         "DEFEAT":discord.Colour.from_rgb(233,150,122)}
        self.scheduler = AsyncIOScheduler(job_defaults={"coalesce" : True, 
                                                        "max_instances" : 5,
                                                        "misfire_grace_time" : 15, 
                                                        "replace_existing" : True}) # Set up scheduler
        self.cnx = sql.connect_database()   # Connexion to DB
        
    @classmethod
    def roman_to_number(cls, roman:str):
        """Convert a roman number to an int.
        Principally used for image link.

        Args:
            roman (str): Roman number in string.

        Returns:
            int : Roman number converted.
        
        Authors:
            Brybry 
        """
        return 1 if roman == "I" else \
               2 if roman == "II" else \
               3 if roman == "III" else \
               4 if roman == "IV" else ""

    def watch_ranked_stats(self, asker : str, alias : str, username : str, region : str ="euw1"):
        """Get all ranked information of username.

        Args:
            username (str): Username of the player
            asker (str): Name of user who asked
            alias (str): Alias of user who asked.
            region (str): Region of username to get.

        Returns:
            discord.Embed: Embed message with all informations about ranked stats of an user to send in discord.
        
        Authors:
            Bryan
        """
        player = PlayerLeagueInfo(username)
        
        try :
            userToWatch = self.watcher.summoner.by_name(region, username)   # Gets Riot user info
        except:
            return discord.Embed.Empty
        
        rank_link = 'DEFAULT'
        
        for data in self.watcher.league.by_summoner(region, userToWatch['id']):
            if data['queueType'] == "RANKED_SOLO_5x5":
                player.loadData(data)
                break

        descr = str(player)

        # Set image rank link
        if not player.empty:
            rank_link = '{}_{}'.format(player.tier, BotWatcher.roman_to_number(str(player.rank)))# RANK_TIER ex: DIAMOND_1
        embed = discord.Embed( title="Rank of " + username, description=descr, colour=self.colormap[player.tier])
        embed.set_thumbnail(url="https://opgg-static.akamaized.net/images/medals/" + \
                                    rank_link.lower() + \
                                    ".png?image=q_auto&image=q_auto,f_auto,w_auto&v=1644907160984&name=Opera&version=83.0.4254.27&major=83&name=Windows&version=10")
        embed.set_footer(text="Asked by " + asker + " alias " + alias)
        return embed

    # Action du bot
    async def on_ready(self):
        """Executed when bot is starting
        """
        
        print("Ready to spy")
        
        #self.notif_new_ranked_game_played()
        # Init rankings commands
        ranking = LolRankings(self)
        self.add_cog(ranking)   # Load all commands from Rankings to Bot
        
        # Execute classements.ranking_scheduler_func every day at 00:00
        self.scheduler.add_job(ranking.ranking_scheduler_func, CronTrigger.from_crontab("0 22 * * *")) #22 = 00:00 CEST
        # Add new jobs here
        self.scheduler.start()  # Start all jobs
        
    
    async def on_message(self, ctx):
        """Executed when a message is posted  

        Args:
            ctx (discord.context): Context of the message
        """
        message = ctx.content
        if not ctx.author.bot and message[0] == self.command_prefix:
            await ctx.delete()
            await self.process_commands(ctx)
        
lolw = BotWatcher() # Create a bot instance

# add bot command in this part

@lolw.command(name="usage", aliases=["u", "Help", "HELP", "h"])
async def send_help(ctx):
    """Send help
    """
    help_message = """```\n========================= My command list =========================
Basic commands :
    *rank [username] - Aliases : rang / elo
        Show username's elo.
        
    *usage - Aliases
        Send this message
        
Ranking commands:
    *addPlayerRanking [username] - Aliases : apr
        Add player to the ranking system. 
        
    *clearLPRanking - Aliases : clpr / clearlpranking
        Clear lp of all players in ranking. (Manage messages right is necessary)
    
    *displayPlayersRegisteredRanking [optional - username] - Aliases : dprr
        If username is not filled, it display every username registered in ranking else, it display if the username is registered or not.
        
    *displayRanking - Aliases : dispR / dr
        Display a ranking of players that won more lp on the day. When you first register a player, is LP gained is 0, we do not see past games.
    
    *removePlayerRanking [username] - Aliases : rpr
        Remove username from ranking system.
    
    *resetRanking - Aliases  : rr
        Reset all player of ranking system. (Kick user right is necessary)
    
    *setChannelDiffusion - Aliases : scd / setcd
        Set this channel diffusion for LP ranking. (Manage channel right is necessary)
        
```"""
    await ctx.author.send(help_message)

@lolw.command(name="rank", aliases=["Rank", "Rang", "rang", "elo", "Elo"])
async def send_rank(ctx, *args):
    """ Send user's elo. *usage for more information
    """
    username = " ".join(args)
    discord_user = ctx.author
    embed_message = lolw.watch_ranked_stats(discord_user.name, discord_user.display_name, username)
    if embed_message != discord.Embed.Empty:
        await ctx.channel.send(embed=embed_message)
    else:
        await ctx.channel.send("User not found on riot servers.")
    
#lolw.run(os.environ['BOT_API_KEY']) #For Prod
lolw.run("OTQ0Nzc3OTkzMzM3ODM1NTMw.YhGjEg.QMXYukVeryN5Nngady999-R0cVE") # For tests
# Si vous voulez créer un bot de test vous pouvez en générer une dans le developer portal de discord (faut créer une app puis un bot dans l'app).
# Dans ce cas, l'appli sera link avec votre bot
# Comme le bot est en ligne sur heroku jsp si c'est votre instance qui sera utilisée quand vous lancez le programme.
