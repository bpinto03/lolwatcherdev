import discord
import MysqlOperations as sql
from discord.ext import commands
from Ranking import *
import datetime

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
        ret = []
        for element in self.rank_track[guild_id]:
            username = element['username']
            rank = self.bot.get_string_rank(username)
            if rank == "":
                print("Error while trying to get rank for " + username)
                continue
            
            if " " in rank : #is not high elo
                tier, division         = rank.split(" ")
                old_tier, old_division = self.find_user_in_rank_track(guild_id, username)['rank'].split(" ")
            
            else: #is high elo
                tier, division = rank, "I"
                old_tier, old_division = self.find_user_in_rank_track(guild_id, username)['rank'], "I"
            
            # Update if demote or promote
            if Ranking.compare_tier(old_tier, tier) != 0 or Ranking.compare_division(old_division, division) != 0 :
                self.update_user(guild_id, username, rank)
            
            promote_embed_title = ""
            if Ranking.compare_division(old_division, division) < 0: #old_division < division => User promoted to next division
                promote_embed_title =  "**" + username + "** promoted from " + old_tier + " " + old_division + " to " + tier + " " + division
            
            if promote_embed_title == "": # not promoted
                continue
            
            rank = '{}_{}'.format(tier, self.bot.roman_to_number(str(division)))# RANK_TIER ex: DIAMOND_1
            
            #Create embed
            promote_embed = discord.Embed(title = promote_embed_title, colour=self.bot.colormap[tier], timestamp=datetime.datetime.utcnow())
            promote_embed.set_footer(text="Rank Promotion")
            promote_embed.set_image(url="https://opgg-static.akamaized.net/images/medals/" + \
                                    rank.lower() + \
                                    ".png?image=q_auto&image=q_auto,f_auto,w_auto&v=1644907160984&name=Opera&version=83.0.4254.27&major=83&name=Windows&version=10")
        
            ret.append(promote_embed)
        return ret
    
    #@commands.command(name = "promoter", aliases=['pr'])
    #async def basa(self, ctx, *args):
    #    username = " ".join(args)
    #    for u in self.rank_track[ctx.guild.id]:
    #        if u['username'] == username:
    #            self.rank_track[ctx.guild.id].remove(u)
    #            self.rank_track[ctx.guild.id].append({'username' : username, 'rank' : "GOLD IV"})
    #            return
    
    #@commands.command(name = "promote", aliases=['p'])
    #async def add_player_ranking(self, ctx, *args):
    #    for embed in self.compare_rank_track(ctx.guild.id):
    #        await ctx.channel.send(embed=embed)
        
    async def promote_tracker_scheduler_func(self):
        for guild in self.bot.guilds:
            channel_id = self.bot.get_diffusion_channel(guild.id) # Get default channel_id
            
            # If there is no channel_id
            if channel_id == -1:
                print("No default channel set - " + str(guild.id))
                continue
            
            channel = await self.bot.fetch_channel(channel_id)
            # If guild id is not registered
            if channel != None and guild.id not in self.rank_track.keys():
                self.players[guild.id] = []
                print("Promote scheduler function registered " + str(guild.id))
                continue
            
            for embed in self.compare_rank_track(guild.id):
                await channel.send(embed=embed)