import discord
import MysqlOperations as sql
from discord.ext import commands
from Ranking import *

class PromoteTracker(commands.Cog):
    # ==== INIT PART ====
    def __init__(self, bot):
        self.bot = bot
        self.lp_track = {} # LP of every player in every guild
        
    def init_lp_track(self):
        for guild in self.bot.guilds:
            players = sql.select_values_from_table(self.bot.cnx, "ranking_registered", ['username'], "guild_id = '{0}'".format(guild.id))
            self.lp_track[guild.id] = []
            
            for element in players:
                username = element[0]
                lp = self.bot.get_lp(username)
                self.lp_track[guild.id].append({'username':username, 'lp' : lp})
                if(lp >= 0):
                    print(username, Ranking.LP_to_rank(lp))