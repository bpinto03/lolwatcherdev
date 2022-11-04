import discord
import MysqlOperations as sql
import datetime

from discord.ext import commands
from PlayerLeagueInfo import PlayerLeagueInfo
from Ranking import *
from PromoteTracking import PromoteTracker

CLASSMENT_THUMBNAIL = "https://cdn.icon-icons.com/icons2/2448/PNG/512/winner_podium_icon_148754.png"


class LolRankings(commands.Cog):
    # ==== INIT PART ====
    def __init__(self, bot, promote_tracking : PromoteTracker):
        self.bot = bot
        self.promote = promote_tracking
        self.players = dict() # dict with guild_id and list of players 'guild_id' : [{'username':Example, 'lp':45}, ...]
        self.medal_classement = [':first_place:', ':second_place:', ':third_place:', '\u2000\u2000']
        self.init_players_from_database() # Load all players in all servers
    
    def init_players_from_database(self):
        """Load player in database into self.players.
        """
        for guild in self.bot.guilds:
            players = sql.select_values_from_table(self.bot.cnx, "ranking_registered", ['username', 'last_lp_saved'], "guild_id = '{0}'".format(guild.id))
            if guild.id not in self.players.keys():
                self.players[guild.id] = []
            for username, last_lp in players:
                self.players[guild.id].append({'username':username, 'lp':last_lp})
        
    # ==== UTILITY PART ====
       
    async def ranking_scheduler_func(self):
        """Function used by scheduler.
        Send embed message of ranking to all guilds the bot can see.
        """
        # Send embed message to every servers
        for guild in self.bot.guilds:
            channel_id = self.bot.get_diffusion_channel(guild.id) # Get default channel_id
            
            # If there is no channel_id
            if channel_id == -1:
                print("No default channel set - " + str(guild.id))
                return
            
            channel = await self.bot.fetch_channel(channel_id)
            # If guild id is not registered
            if channel != None and guild.id not in self.players.keys():
                self.players[guild.id] = []
                print("Scheduler function registered " + str(guild.id))
                return
            
            # Register players's lp
            players = self.players[guild.id]
            for player in players:
                lp = self.bot.get_lp(player['username']) # Actualise LP
                # Remove if there is error with player
                if lp < 0:
                    self.remove_renamed_player(player)
                    continue
                player['lp'] = lp
                    
            if channel.permissions_for(guild.me).send_messages:
                    embed_to_display = self.embed_lp_ranking(self.compare_LP_in_DB_with_actual_LP(guild.id)) # Compare LP with database
                    if embed_to_display != None:
                        await channel.send(embed=embed_to_display)
                    else:
                        print("Display tab is useless (Nobody played or Nobody in classement) - " + str(guild.id))
            else:
                print("Permissions missing. - " + str(guild.id) + " " + str(channel_id))
                    
            for player in players:
                sql.update_values_on_table(self.bot.cnx, "ranking_registered", "last_lp_saved = {0}".format(player['lp']), "guild_id = '{0}' AND username = '{1}'"
                                               .format(guild.id, player['username'])) # Update database values
           
    
    def compare_LP_in_DB_with_actual_LP(self, guild_id):
        """This function is used to create list of player with their number of LP won the day.

        Args:
            guild_id (int): Server id to compare.

        Returns:
            list: List of dict representing a player with his LP.
        """
        ret = []
        # Sort by username to make list in DB and in bot coherent.
        DB_values = sorted(sql.select_values_from_table(self.bot.cnx, "ranking_registered", ['username', 'last_lp_saved'],
                                                        "guild_id = '{0}'".format(guild_id)), key=lambda x : x[0])
        # self.players[guild_id] should be [] if guild_id hasn't save players.
        actual_values = sorted(self.players[guild_id], key=lambda x : x['username'])
        if len(actual_values) != len(DB_values): # Error if lists have not the same length.
            print("Error with data " + str(guild_id))
            print(DB_values,  actual_values)
        else:
            for i in range(len(actual_values)):
                ret.append({'username' : actual_values[i]['username'], 'lp' : actual_values[i]['lp'] - DB_values[i][1]})
        return sorted(ret, key=lambda x : x['lp'], reverse=True)
            
    # === UPDATE PART ====
    
    @commands.command(name = "setChannelDiffusion", aliases=['scd', 'setcd'])
    @commands.has_permissions(manage_channels=True)
    async def set_channel_diffusion(self, ctx):
        """Set a channel diffusion to display ranking at midnight. *usage for more information
        """
        guild = ctx.guild
        if guild != None:
            if guild.id not in self.players.keys():
                self.players[guild.id] = []
                print("set_channel_diffusion registered "  + str(guild.id))
            channel_id = ctx.channel.id
            
            if self.bot.get_diffusion_channel(guild.id) == -1:
                sql.add_values_on_table(self.bot.cnx, "ranking_diffusion", [str(guild.id), str(channel_id)])
                
            else:
                sql.update_values_on_table(self.bot.cnx,
                                        "ranking_diffusion",
                                        "channel_diffusion = '" + str(channel_id) + "'",
                                        "guild_id = '" + str(guild.id) + "'" )
            await ctx.channel.send("Diffusion channel for ranking modified.")
            
    @commands.command(name = "clearLPRanking", aliases=['clpr', 'clearlpranking'])
    @commands.has_permissions(manage_messages=True)
    async def clear_lp_ranking(self, ctx):
        """Clear the lp ranking. *usage for more information
        """
        guild = ctx.guild
        if guild != None:
            if guild.id not in self.players.keys():
                self.players[guild.id] = []
                print("clear_lp_ranking registered "  + str(guild.id))
                return
            for player in self.players[guild.id]:
                sql.update_values_on_table(self.bot.cnx, "ranking_registered", "last_lp_saved = {0}".format(player['lp']), "guild_id = '{0}' AND username = '{1}'"
                                               .format(guild.id, player['username'])) # Update database values
            await ctx.channel.send("Cleared LP ranking.")
    
    # ==== ADD PART ====
    def add_player_to_DB(self, guild_id : int, username : str, lp : int):
        """Add player with username to database if the player is already in table it update his LP.

        Args:
            guild_id (int): _description_
            username (str): _description_
            lp (int): _description_
        """
        res = sql.select_values_from_table(self.bot.cnx, "ranking_registered", ['guild_id', 'username'],
                                           "guild_id = '{0}' AND username = '{1}'".format(guild_id, username))
        if res == []:
            sql.add_values_on_table(self.bot.cnx, "ranking_registered", [str(guild_id), username, str(lp)])
        else:
            sql.update_values_on_table(self.bot.cnx, "ranking_registered",
                                      "last_lp_saved = {0}".format(str(lp)),
                                      "guild_id = '{0}' AND username = '{1}'".format(str(guild_id), username))
    
    
    def add_player_to_ranking(self, guild_id : int, username : str):
        """Add player to the ranking in Bot and DB.

        Args:
            guild_id (int): Server id.
            username (str): Username to add.
        """
        
        lp = self.bot.get_lp(username)
        self.players[guild_id].append({'username' : username, 'lp' : lp})
        self.add_player_to_DB(guild_id, username, lp)
        self.promote.add_user(guild_id, username)
        
    @commands.command(name = "addPlayerRanking", aliases=['apr'])
    async def add_player_ranking(self, ctx, *args):
        """Add player to ranking. *usage for more information
        """
        username = " ".join(args)
        guild = ctx.guild
        if guild != None:
            if guild.id not in self.players.keys():
                self.players[guild.id] = []
                print("add_player_ranking registered "  + str(guild.id))
            if username in [u['username'] for u in self.players[guild.id]]:
                await ctx.channel.send(username + " already in ranking.")
            else:
                # Check if player exist
                player = PlayerLeagueInfo(username)
                player.loadData(self.bot.watcher, username, self.bot.region)
                if not player.empty:
                    self.add_player_to_ranking(guild.id, username)
                    await ctx.channel.send("Player **" + username + "** added.")
                else:
                    await ctx.channel.send("Player **" + username + "** not found on riot servers.")
        else:
            await ctx.channel.send("Error while trying to add " + username + " in " + guild.id)
            
    # ==== DELETE PART ====
    def remove_renamed_player(self, player : dict):
        """Remove a renamed username in all servers.

        Args:
            player (dict): Player to remove
        """
        for guild in self.bot.guilds:
            if player in self.players[guild.id]:
                self.players[guild.id].remove(player)
                self.remove_player_from_DB(guild.id, player['username'])
        
    def remove_player_from_DB(self, guild_id : int, username : str):
        """Remove an user from DB.

        Args:
            guild_id (int): Server id
            username (str): Username of player to remove.
        """
        sql.delete_values_on_table(self.bot.cnx, "ranking_registered", "guild_id = '{0}' AND username = '{1}'".format(guild_id, username))
    
    def remove_player_from_ranking(self, guild_id : int, username : str):
        """Remove a player in the bot and in DB.

        Args:
            guild_id (int): Server id
            username (str): Username of player to remove
        """
        for player in self.players[guild_id]:
            if player['username'] == username:
                lp = player['lp'] #get lp of player to remove line in DB
                break
        self.players[guild_id].remove({'username' : username, 'lp' : lp})
        self.remove_player_from_DB(guild_id, username)
        self.promote.remove_user(guild_id, username)
    
    @commands.command(name="removePlayerRanking", aliases=['rpr'])
    async def remove_player_ranking(self, ctx, *args):
        """Remove a player from the ranking. *usage for more information
        """
        username = " ".join(args)
        guild = ctx.guild
        if guild != None:
            if guild.id not in self.players.keys():
                self.players[guild.id] = []
                print("remove_player_ranking registered "  + str(guild.id))
                return
            self.remove_player_from_ranking(guild.id, username)
            await ctx.channel.send("Player **" + username + "** removed.")
        else:
            await ctx.channel.send("Error while trying to delete " + username)
            print("Error while removing" + username + " in " + guild.id)
    
    @commands.command(name="resetRanking", aliases=['rr'])
    @commands.has_permissions(kick_members=True)
    async def reset_ranking(self, ctx):
        """Remove all players in ranking system. *usage for more information
        """
        guild = ctx.guild
        if guild != None:
            guild_id = ctx.guild.id
            if guild.id not in self.players.keys():
                self.players[guild.id] = []
                print("reset_ranking registered "  + str(guild.id))
                return
            for player in [u['username'] for u in self.players[guild_id]]:
                self.promote.remove_user(guild_id, player)
            self.players[guild_id] = []
            sql.delete_values_on_table(self.bot.cnx, "ranking_registered", "guild_id = '{0}'".format(guild_id))
            await ctx.channel.send("All players are deleted.")
        else:
            await ctx.channel.send("Error while trying to reset.")
            print("Error with reset " + guild.id)
    
    # ==== DISPLAY PART ====
    def embed_lp_ranking(self, players : list):
        """Create an embed ranking to send on channel

        Args:
            players (list): List of players and LP to write in embed.
        Returns:
            discord.Embed: Embed message with the ranking of the day.
        """
        medal = 0
        descr = ""
        for player in players:
            if player['lp'] > 0:
                descr = descr + self.medal_classement[medal] + "**" + player['username'] + "** with +" + str(player['lp']) + " LP\n"
            elif player['lp'] < 0:
                descr = descr + self.medal_classement[medal] + "**" + player['username'] + "** with " + str(player['lp']) + " LP\n"
            if 0 <= medal <= 2 : 
                medal += 1
        if descr == "":
            return None
        embed = discord.Embed( title=":military_medal: Ranking of the day :military_medal:", description=descr, color=discord.Colour.dark_red(), timestamp=datetime.datetime.utcnow())
        embed.set_thumbnail(url=CLASSMENT_THUMBNAIL)
        embed.set_footer(text="Number of lp won today")
        return embed
    
    @commands.command(name = "displayPlayersRegisteredRanking", aliases=['dprr'])
    async def display_player_registered_ranking(self, ctx, username=None):
        """Display all players registered in ranking system or if username is specified check if
        he is in ranking system.

        Args:
            ctx (discord.context): Context of command.
        """
        guild = ctx.guild
        players = ""
        if guild != None:
            if guild.id not in self.players.keys():
                self.players[guild.id] = []
                print("display_player_registered_ranking registered "  + str(guild.id))
            else:
                list_of_users = ["**" + player['username'] + "**" for player in self.players[guild.id]]
                if username == None:
                    players = ", ".join(list_of_users)
                    await ctx.channel.send("Players in ranking system : " + players)
                else:
                    if "**" + username + "**" in list_of_users:
                        await ctx.channel.send("Player **" + username + "** is in ranking system.")
                    else:
                        await ctx.channel.send("Player **" + username + "** is not in ranking system.")
                
    
    @commands.command(name = "displayRanking", aliases=['dispR', 'dr'])
    async def display_ranking_of_the_day(self, ctx):
        """Display a ranking of players that won more lp on the day. *usage for more information
        """
        guild = ctx.guild
        if guild != None:
            if guild.id not in self.players.keys():
                self.players[guild.id] = []
                print("display_ranking_of_the_day registering " + str(guild.id))
                return
            
            for player in self.players[ctx.guild.id]:
                lp = self.bot.get_lp(player['username']) # Actualise Lp of player before sending
                if lp < 0:
                    self.remove_renamed_player(player)
                    continue
                player['lp'] = lp
            embed_to_display = self.embed_lp_ranking(self.compare_LP_in_DB_with_actual_LP(ctx.guild.id))
            if embed_to_display != None:
                await ctx.channel.send(embed=embed_to_display)
            else:
                await ctx.channel.send("Ranking is empty (nobody played or is registered).")
        else:
            await ctx.channel.send("Error while trying to display ranking on " + guild.id)
            print("Error while trying to display " + guild.id)
        