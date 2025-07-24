# random_ai.py
# IA simple pour Can't Stop
import random

class RandomAI:
    def __init__(self, name):
        self.name = name
        self.progress = {}
        self.completed = set()

    def choose_action(self, possible_actions, dice, pairs):
        random.shuffle(possible_actions)
        return possible_actions[0]

    def should_continue(self):
        return random.random() < 0.75
