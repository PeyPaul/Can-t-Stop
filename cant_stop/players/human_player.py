# human_player.py
# Interface console pour joueur humain

class HumanPlayer:
    def __init__(self, name):
        self.name = name
        self.progress = {}
        self.completed = set()

    def choose_action(self, possible_actions, dice, pairs):
        print(f"\n{self.name}, à toi de jouer !")
        print(f"Dés tirés : {dice}")
        print(f"Paires disponibles : {pairs}")
        print("Actions possibles :")
        for i, action in enumerate(possible_actions):
            print(f"{i}: {action}")
        while True:
            try:
                idx = int(input("Choisis l'action à jouer (numéro) : "))
                if 0 <= idx < len(possible_actions):
                    return possible_actions[idx]
            except ValueError:
                pass
            print("Entrée invalide. Réessaie.")

    def should_continue(self):
        while True:
            choice = input("Souhaites-tu continuer ? (o/n) : ").lower()
            if choice in ["o", "n"]:
                return choice == "o"
            print("Entrée invalide. Réponds par 'o' ou 'n'.")
