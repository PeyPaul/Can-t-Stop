from cant_stop_engine import Game, ConsolePlayer
import random

class ConsoleUI:
    def choose_action(self, player, possible_actions, dice, pairs):
        print(f"\n{player.name}, à toi de jouer !")
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

    def should_continue(self, player):
        while True:
            choice = input("Souhaites-tu continuer ? (o/n) : ").lower()
            if choice in ["o", "n"]:
                return choice == "o"
            print("Entrée invalide. Réponds par 'o' ou 'n'.")

    def notify_bust(self, player):
        print(f"{player.name} a busté!")

    def notify_stop(self, player):
        print(f"{player.name} s'arrête et sécurise ses progrès.")

    def start_turn(self, player, turn):
        print(f"\n--- Tour {turn} : {player.name} ---")

    def display_temp_progress(self, player, temp_markers):
        print(f"Progression temporaire : {temp_markers}")

    def display_board(self, players, board, locked_columns):
        print("\nPlateau de jeu :")
        for col in range(2, 13):
            line = f"Col {col:>2} ["
            for step in range(1, board[col] + 1):
                marker = ""
                for player in players:
                    if player.progress[col] >= step:
                        marker += player.name[-1]
                if marker == "":
                    marker = "."
                marker += ","
                line += marker
            line += "]"
            if col in locked_columns:
                line += " (Verrouillée)"
            print(line)

    def declare_winner(self, player):
        print(f"\n🎉 {player.name} a gagné en complétant 3 colonnes !")


def main():
    ui = ConsoleUI()
    players = [
        ConsolePlayer("Joueur 1", is_human=True),
        ConsolePlayer("Joueur 2", is_human=False)
    ]
    game = Game(players, ui)
    game.play_game()


if __name__ == "__main__":
    main()
