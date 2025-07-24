import random

# Constantes du jeu
COL_LENGTHS = {
    2: 3,
    3: 5,
    4: 7,
    5: 9,
    6: 11,
    7: 13,
    8: 11,
    9: 9,
    10: 7,
    11: 5,
    12: 3
}

MAX_TEMP_MARKERS = 3
COLUMNS = list(COL_LENGTHS.keys())

class Player:
    def __init__(self, name, is_human=False):
        self.name = name
        self.is_human = is_human
        self.progress = {col: 0 for col in COLUMNS}  # Position définitive
        self.completed = set()

class Game:
    def __init__(self):
        self.players = [
            Player("Joueur 1", is_human=True),
            Player("Joueur 2", is_human=False)
        ]
        self.current_player_index = 0
        self.board = {col: [] for col in COLUMNS}  # Liste des joueurs qui ont terminé chaque colonne
        self.locked_columns = set()

    def roll_dice(self):
        return [random.randint(1, 6) for _ in range(4)]

    def get_pairs(self, dice):
        return [
            (dice[0] + dice[1], dice[2] + dice[3]),
            (dice[0] + dice[2], dice[1] + dice[3]),
            (dice[0] + dice[3], dice[1] + dice[2])
        ]

    def display_board(self):
        print("\nPlateau de jeu :")
        for col in range(2, 13):
            line = f"Col {col:>2} ["
            for step in range(1, COL_LENGTHS[col] + 1):
                marker = ""
                for player in self.players:
                    if player.progress[col] >= step:
                        marker += player.name[-1]  # Dernière lettre du nom
                if marker == "":
                    marker = "."
                marker += ","
                line += marker
            line += "]"
            if col in self.locked_columns:
                line += " (Verrouillée)"
            print(line)

    def choose_action(self, player, possible, dice, pairs):
        if player.is_human:
            print(f"\n{player.name}, à toi de jouer !")
            print(f"Dés tirés : {dice}")
            print(f"Paires disponibles : {pairs}")
            print(f"Actions possibles :")
            for i, action in enumerate(possible):
                print(f"{i}: {action}")
            while True:
                try:
                    idx = int(input("Choisis l'action à jouer (numéro) : "))
                    if 0 <= idx < len(possible):
                        return possible[idx]
                except ValueError:
                    pass
                print("Entrée invalide. Réessaie.")
        else:
            random.shuffle(possible)
            return possible[0]

    def should_continue(self, player):
        if player.is_human:
            while True:
                choice = input("Souhaites-tu continuer ? (o/n) : ").lower()
                if choice in ["o", "n"]:
                    return choice == "o"
                print("Entrée invalide. Réponds par 'o' ou 'n'.")
        else:
            return random.random() < 0.75

    def play_turn(self, player):
        temp_markers = {}
        busted = False

        while True:
            dice = self.roll_dice()
            pairs = self.get_pairs(dice)
            possible = []

            for a, b in pairs:
                if a not in self.locked_columns and b not in self.locked_columns:
                    if a == b and ((a in temp_markers and temp_markers[a] < COL_LENGTHS[a]-1) or (a not in temp_markers and len(temp_markers) < MAX_TEMP_MARKERS and player.progress[a] < COL_LENGTHS[a]-1)):
                        possible.append((a,b))
                    elif a != b and (a in temp_markers and temp_markers[a] < COL_LENGTHS[a]) and (b in temp_markers and temp_markers[b] < COL_LENGTHS[b]):
                        possible.append((a,b))
                    elif a != b and len(temp_markers) + 1 < MAX_TEMP_MARKERS:
                        possible.append((a,b))
                    elif a != b and ((a in temp_markers and temp_markers[a] < COL_LENGTHS[a] and len(temp_markers) < MAX_TEMP_MARKERS) or (b in temp_markers and temp_markers[b] < COL_LENGTHS[b] and len(temp_markers) < MAX_TEMP_MARKERS)):
                        possible.append((a,b))
                if (a,b) not in possible:
                    for val in (a, b):
                        if val not in self.locked_columns and ((val in temp_markers and temp_markers[val] < COL_LENGTHS[val]) or (val not in temp_markers and len(temp_markers) < MAX_TEMP_MARKERS)):
                            possible.append((val,))

            if possible:
                choice = self.choose_action(player, possible, dice, pairs)
                print(f"{player.name} a choisi la paire {choice}")
                for val in choice:
                    if val not in temp_markers:
                        temp_markers[val] = player.progress[val]
                    temp_markers[val] += 1
            else:
                busted = True
                print(f"{player.name} a busté!")
                break

            print(f"Progression temporaire : {temp_markers}")

            if self.should_continue(player):
                continue
            else:
                print(f"{player.name} s'arrête et sécurise ses progrès.")
                break

        if not busted:
            for col, val in temp_markers.items():
                player.progress[col] = val
                if player.progress[col] >= COL_LENGTHS[col]:
                    self.locked_columns.add(col)
                    player.completed.add(col)
                    self.board[col].append(player.name)

    def check_winner(self):
        for player in self.players:
            print(f"{player.name} a complété les colonnes : {player.completed}")
            if len(player.completed) >= 3:
                return player
        return None

    def play_game(self):
        turn = 0
        while True:
            player = self.players[self.current_player_index]
            print(f"\n--- Tour {turn} : {player.name} ---")
            self.play_turn(player)
            self.display_board()

            winner = self.check_winner()
            if winner:
                print(f"\n🎉 {winner.name} a gagné en complétant 3 colonnes !")
                self.display_board()
                break

            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            turn += 1

if __name__ == "__main__":
    game = Game()
    game.play_game()
