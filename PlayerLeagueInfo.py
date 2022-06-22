class PlayerLeagueInfo():
    """Store all ranking information about a player

    Authors:
        Matchi
    """

    def __init__(self, user:str):
        self.user = user
        self.empty = True
        self.tier = 'DEFAULT'
        self.rank = 0
        self.wins = 0
        self.losses = 0
        self.lp = 0

    def loadData(self, data:dict) -> None:
        """Load ranking information in this object

        Args:
            self (PlayerLeagueInfo): this object
            data (dict): ranking information
        
        Author:
            Matchi
        """
        self.empty = False
        self.tier = data['tier']
        self.rank = data['rank']
        self.wins = data['wins']
        self.losses = data['losses']
        self.lp = data['leaguePoints']

    def winrate(self) -> float:
        """Return the winrate of the player

        Args:
            self (PlayerLeagueInfo): this object

        Returns:
            The winrate of the player
            
        Author:
            Matchi
        """
        return 0 if self.wins + self.losses == 0 \
                else round(100 * self.wins / (self.wins + self.losses), 2)

    def __str__(self) -> str:
        if self.empty:
            return '{} n\'est pas classé.'.format(self.user)
        res = [
            "\nWins : {}".format(self.wins),
            "Looses : {}".format(self.losses),
            "Winrate : {}%".format(self.winrate()),
            "Rank : {} {}".format(self.tier, self.rank),
            "Lp : {}".format(self.lp)
            ]
        return '\n'.join(res)
        


