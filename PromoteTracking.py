import discord
import MysqlOperations as sql
from discord.ext import commands
from Ranking import *

class PromoteTracker(commands.Cog):
    # ==== INIT PART ====
    def __init__(self, bot):
        self.bot = bot
        self.rank_track = {} # LP of every player in every guild
        self.init_rank_track()
        
    def init_rank_track(self):
        for guild in self.bot.guilds:
            players = sql.select_values_from_table(self.bot.cnx, "ranking_registered", ['username'], "guild_id = '{0}'".format(guild.id))
            self.rank_track[guild.id] = []
            
            for element in players:
                username = element[0]
                rank = self.bot.get_string_rank(username)
                self.rank_track[guild.id].append({'username':username, 'rank' : rank})
        
    def find_user_in_rank_track(self, guild_id, username):
        for user in self.rank_track[guild_id]:
            if user['username'] == username:
                return user
        return None
    
    def remove_user(self, guild_id, username):
        user_to_remove = self.find_user_in_rank_track(guild_id, username)
        self.rank_track[guild_id].remove(user_to_remove)
        
    def update_user(self, guild_id, username, rank):
        usernameToUpdate = self.find_user_in_rank_track(guild_id, username)
        self.rank_track[guild_id].remove(usernameToUpdate)
        self.rank_track[guild_id].append({'username': username, 'rank': rank})
        
    def add_user(self, guild_id, username):
        if guild_id not in self.rank_track.keys():
            self.rank_track[guild_id] = []
            print("add_user registered "  + str(guild_id))
        
        self.rank_track[guild_id].append({'username':username, 'rank' : self.bot.get_string_rank(username)})
        
    def compare_rank_track(self, guild_id):
        players = sql.select_values_from_table(self.bot.cnx, "ranking_registered", ['username'], "guild_id = '{0}'".format(guild_id))
        for element in players:
            username = element[0]
            rank = self.bot.get_string_rank(username)
            if rank == "":
                print("Error while trying to get rank for " + username)
                continue
            if " " in rank :
                tier, division         = rank.split(" ")
                old_tier, old_division = self.find_user_in_rank_track(guild_id, username)['rank'].split(" ")
            
            else:
                tier, division = rank, "I"
                old_tier, old_division = self.find_user_in_rank_track(guild_id, username)['rank'], "I"
            print(username, rank)
            print(self.rank_track[guild_id])
            
            if Ranking.compare_tier(old_tier, tier) != 0 or Ranking.compare_division(old_division, division) != 0 :
                self.update_user(guild_id, username, rank)
            
            print(self.rank_track[guild_id])
            
            if Ranking.compare_tier(old_tier, tier) < 0: #old_tier < tier => User promoted to next tier
                return "**" + username + "** promoted from " + old_tier + " to " + tier
                
            if Ranking.compare_division(old_division, division) < 0: #old_division < division => User promoted to next division
                return "**" + username + "** promoted from " + old_tier + " " + old_division + " to " + tier + " " + division
    
    @commands.command(name = "promoter", aliases=['pr'])
    async def basa(self, ctx, *args):
        username = " ".join(args)
        for u in self.rank_track[ctx.guild.id]:
            if u['username'] == username:
                self.rank_track[ctx.guild.id].remove(u)
                self.rank_track[ctx.guild.id].append({'username' : username, 'rank' : "IRON IV"})
                return
    
    @commands.command(name = "promote", aliases=['p'])
    async def add_player_ranking(self, ctx, *args):
        print(self.compare_rank_track(ctx.guild.id))
        
        
    async def promote_tracker_scheduler_func(self):
        pass