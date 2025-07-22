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
    def __init__(self, name):
        self.name = name
        self.progress = {col: 0 for col in COLUMNS}  # Position définitive
        self.completed = set()

class Game:
    def __init__(self):
        self.players = [Player("Joueur 1"), Player("Joueur 2")]
        self.current_player_index = 0
        self.board = {col: [] for col in COLUMNS}  # Liste des joueurs qui ont terminé chaque colonne
        self.locked_columns = set() # set des colonnes verrouillées

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

    def play_turn(self, player):
        temp_markers = {}
        busted = False

        while True:
            dice = self.roll_dice()
            pairs = self.get_pairs(dice)
            
            ### ici commence le choix des actions
            
            #random.shuffle(pairs)

            move_made = False
            possible = []
            for a, b in pairs:
                for val in (a, b):
                    if val in temp_markers or len(temp_markers) < MAX_TEMP_MARKERS: # Vérification de la limite de marqueurs temporaires un à un
                        if a in temp_markers or b in temp_markers or len(temp_markers) + 1 < MAX_TEMP_MARKERS: # Vérification de la limite jointe de marqueurs temporaires
                            if a not in self.locked_columns and b not in self.locked_columns: # Vérification si les colonnes ne sont pas verrouillées
                                possible.append(val)

                if possible:
                    for val in possible:
                        if val not in temp_markers:
                            temp_markers[val] = player.progress[val]
                        temp_markers[val] += 1
                        if temp_markers[val] >= COL_LENGTHS[val]:
                            self.locked_columns.add(val) # Verrouillage de la colonne
                            player.completed.add(val)
                            temp_markers[val] = COL_LENGTHS[val]
                    move_made = True
                    break

            if not move_made:
                busted = True
                print(f"{player.name} a busté!")
                print(f"Paires de dés : {pairs}")
                break

            if random.random() < 0.5:
                print(f"{player.name} décide de continuer.")
                print(f"Progression temporaire : {temp_markers}")
                continue
            else:
                print(f"{player.name} s'arrête et sécurise ses progrès.")
                print(f"Progression temporaire sécurisée : {temp_markers}")
                break

        if not busted:
            for col, val in temp_markers.items():
                player.progress[col] = val

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
