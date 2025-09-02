# random_ai.py
# IA simple pour Can't Stop
import random

class RandomAI:
    def __init__(self, name):
        self.name = name
        self.progress = {}
        self.completed = set()

    def choose_action(self, possible_actions, dice, pairs, temp_markers=None, game_state=None):
        random.shuffle(possible_actions)
        return possible_actions[0]

    def should_continue(self, temp_markers=None, game_state=None):
        return random.random() < 0.75
