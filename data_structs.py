class ReplayData():
    def __init__(self, replay_name, player_name, build_name, match_datetime, macro_score):
        self.replay_name = replay_name
        self.player_name = player_name
        self.build_name = build_name
        self.match_datetime = match_datetime
        self.macro_score = macro_score

class ScoreTimePair():
    def __init__(self, score, time):
        self.score = score
        self.time = time

class SupplyNamePair():
    def __init__(self, supply, name):
        self.supply = supply
        self.name = name
