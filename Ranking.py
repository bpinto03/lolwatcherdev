class Ranking:
    DIVISION = ['IV', 'III', 'II', 'I', '0']
    TIER = {
            'DEFAULT' : 0,
            'IRON': 0,
            'BRONZE': 400,
            'SILVER': 800,
            'GOLD': 1200,
            'PLATINUM': 1600,
            'DIAMOND': 2000,
            'MASTER': 2400,
            'GRANDMASTER': 2600,
            'CHALLENGER': 3100
            }

    @classmethod
    def __compute_division(cls, division:str) -> int:
        return int(Ranking.DIVISION.index(division)) * 100

    @classmethod
    def __is_high_elo(cls, tier:str) -> bool:
        return Ranking.TIER[tier] >= Ranking.TIER['MASTER']

    @classmethod
    def division_value(cls, division:str):
        return len(Ranking.DIVISION) - Ranking.DIVISION.index(division)

    @classmethod
    def rank_to_LP(cls, tier:str, division:str, rest:str) -> int:
        if division not in Ranking.DIVISION:
            raise ValueError(division + ' division do not exist')
        if tier not in Ranking.TIER:
            raise ValueError(tier + ' tier do not exist')
        lp = int(rest)
        if not Ranking.__is_high_elo(tier):
            if lp < 0 or 100 < lp:  #100 for placement game
                raise ValueError('lp should be between 0 and 100 for low elo')
            lp += Ranking.__compute_division(division)
        return lp + Ranking.TIER[tier]

    @classmethod
    def LP_to_rank(cls, lp:int) -> dict:
        if lp < 0: 
            raise ValueError('league point should be positive')
        res = {}
        for tier, value in list(Ranking.TIER.items())[::-1]:
            if lp - value >= 0:
                res['tier'] = tier
                lp -= value
                break
        if not Ranking.__is_high_elo(res['tier']):
            index = lp // 100
            res['division'] = str(Ranking.DIVISION[index])
            lp -= index * 100
        res['lp'] = str(lp)
        return res
