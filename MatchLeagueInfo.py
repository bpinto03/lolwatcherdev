class MatchLeagueInfo():
    """Store all information about a match

    Authors:
        Natnat
    """

    def __init__(self):
        self.username = ""
        self.puuid = 0
        self.gameDuration = 0
        self.player_game_info = None
        self.championName = 0
        self.teamId = 0
        self.team = None
        self.win = ""
        self.gameLength = 0

    def get_player_info_by_puuid(self, userPuuid:int, value:dict):
        """Return player info

        Args:
            self (GameLeagueInfo): this object
            userPuuid: puuid ot the player
            value: info of all the players in the game

        Returns:
            Dict of info of our current user
            
        Author:
            Natnat
        """
        for i in range(len(value["info"]["participants"])):
            if value["info"]["participants"][i]["puuid"] == userPuuid :
                return value["info"]["participants"][i]


    def get_team_info_by_teamId(self, teamId:int, value:dict):
        """Return player info

        Args:
            self (GameLeagueInfo): this object
            teamid: teamid ot the player
            value: info of all the players in the game

        Returns:
            Dict of info of our current user team
            
        Author:
            Natnat
        """
        if value["info"]["teams"][0]["teamId"] == teamId:
            return value["info"]["teams"][0]
        return value["info"]["teams"][1]


    def loadData(self, gameInfo:list) -> None:
        """Load game information in this object

        Args:
            self (GameLeagueInfo): this object
            gameInfo (list(dict((username, puuid): MatchDto))): game information
        
        Author:
            Natnat
        """
        key = list(gameInfo.keys())
        value = gameInfo.get(key[0])
        self.username, self.puuid = key[0]
        self.gameDuration = value["info"]["gameDuration"]
        self.player_game_info = self.get_player_info_by_puuid(self.puuid, value)
        self.championName = self.player_game_info["championName"]
        self.teamId = self.player_game_info["teamId"]
        self.team = self.get_team_info_by_teamId(self.teamId, value)
        self.win = "WIN" if self.team["win"] == True else "DEFEAT"
        self.gameLength = round(self.player_game_info["challenges"]["gameLength"]/60)


    def total_cs(self) -> int:
        """Return total cs of the player

        Args:
            self (GameLeagueInfo): this object

        Returns:
            The total cs of the player
            
        Author:
            Natnat
        """
        return self.player_game_info["totalMinionsKilled"] + self.player_game_info["neutralMinionsKilled"]


    def __str__(self) -> str:
        res = [
            "\n{}".format(self.win),
            "{}".format(self.championName),
            "{}".format(str(self.player_game_info["kills"]) + "/" + str(self.player_game_info["deaths"]) + "/" + str(self.player_game_info["assists"])),
            "{}  KDA".format(str(round(self.player_game_info["challenges"]["kda"],2))),
            "{} ({}) CS".format(str(self.total_cs()), str(round((self.total_cs()/self.gameLength),1))),
            "C/Kill {}% !MAL CALCULÉ".format(str(int(self.player_game_info["challenges"]["killParticipation"]*100))) #pas correct
            ]
        return '\n'.join(res)
        


