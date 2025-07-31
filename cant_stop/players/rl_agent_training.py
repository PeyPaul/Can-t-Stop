# rl_agent.py
# Agent RL pour l'environnement Gym

class RLAgent:
    def __init__(self, name):
        self.name = name
        self.progress = {}
        self.completed = set()

    def choose_action(self, possible_actions, dice, pairs, temp_markers, game_state):
        # L'agent RL ne choisit pas ici, c'est l'environnement Gym qui contrôle
        return possible_actions[0]

    def should_continue(self):
        # L'agent RL ne décide pas ici, c'est l'environnement Gym qui contrôle
        return False
