import json


class Seelie():
    seelie_json = []
    equilibrium_level = 0
    trailblaze_level = 0
    server = ""
    goals = []

    def _bake_goals(self):
        for goal in self.seelie_json["goals"]:
            if goal["type"] == "character":
                self.goals.append(self.GoalCharacter(goal))
            elif goal["type"] == "trace":
                self.goals.append(self.GoalTrace(goal))

    def get_goal_trace(self, character_name : str):
        for goal in self.goals:
            if goal.type == "trace" and goal.character == character_name:
                print(goal.skill_a_level)
                break
        return None

    def get_goals(self):
        for goal in self.seelie_json["goals"]:
            print(goal["type"])

    def __init__(self, json_str: str):
        self.seelie_json = json.loads(json_str)
        self.trailblaze_level = self.seelie_json["tl"]
        self.equilibrium_level = self.seelie_json["el"]
        self.server = self.seelie_json["server"]
        self._bake_goals()

    class Goal():
        id = 0
        type = "null"

        def __init__(self, goal):
            self.type = goal["type"]
            self.id = goal["id"]

    class GoalCharacter(Goal):
        character = ""
        eidolon = 0
        current_level = 0
        current_asc = 0

        goal_level = 0
        goal_asc = 0

        def __init__(self, goal):
            super().__init__(goal)
            self.character = goal["character"]
            self.eidolon = goal["eidolon"]
            self.current_level = goal["current"]["level"]
            self.current_asc = goal["current"]["asc"]
            self.goal_level = goal["goal"]["asc"]
            self.goal_asc = goal["goal"]["asc"]

    class GoalTrace(Goal):
        character = ""

        skill_a_level = 0
        skill_e_level = 0
        skill_q_level = 0
        skill_t_level = 0
        skill_a_goal = 0
        skill_e_goal = 0
        skill_q_goal = 0
        skill_t_goal = 0

        bonus_l1 = None
        bonus_a2m = None
        bonus_a2s = None
        bonus_a3s1 = None
        bonus_a3s2 = None
        bonus_a4m = None
        bonus_a4s = None
        bonus_a5s1 = None
        bonus_a5s2 = None
        bonus_a6m = None
        bonus_a6s = None
        bonus_l75 = None
        bonus_l80 = None

        def get_bonus(self, key, goal):
            if key in goal.keys:
                return goal[key]["done"]
            return None

        def __init__(self, goal):
            super().__init__(goal)
            self.character = goal["character"]

            self.skill_a_level = goal["basic"]["current"]
            self.skill_e_level = goal["skill"]["current"]
            self.skill_q_level = goal["ultimate"]["current"]
            self.skill_t_level = goal["talent"]["current"]
            self.skill_a_goal = goal["basic"]["goal"]
            self.skill_e_goal = goal["skill"]["goal"]
            self.skill_q_goal = goal["ultimate"]["goal"]
            self.skill_t_goal = goal["talent"]["goal"]
            '''
            self.bonus_l1 = self.get_bonus("l1", goal)
            self.bonus_a2m = self.get_bonus("a2m", goal)
            self.bonus_a2s = self.get_bonus("a2s", goal)
            self.bonus_a3s1 = self.get_bonus("a3s", goal)
            self.bonus_a3s2 = self.get_bonus("a3s", goal)
            self.bonus_a4m = self.get_bonus("bonus-trace-1-1", goal)
            self.bonus_a4s = self.get_bonus("bonus-trace-1-1", goal)
            self.bonus_a5s1 = self.get_bonus("bonus-trace-1-1", goal)
            self.bonus_a5s2 = self.get_bonus("bonus-trace-1-1", goal)
            self.bonus_a6m = self.get_bonus("bonus-trace-1-1", goal)
            self.bonus_a6s = self.get_bonus("bonus-trace-1-1", goal)
            self.bonus_l75 = self.get_bonus("bonus-trace-1-1", goal)
            self.bonus_l80 = self.get_bonus("bonus-trace-1-1", goal)
            '''

if __name__ == "__main__":
    with open('seelie.json', mode='r+', encoding='utf-8') as f:
        s = f.read()
        Seelie(s).get_goal_trace("dan_heng_imbibitor_lunae")
