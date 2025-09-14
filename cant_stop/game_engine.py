# game_engine.py
# Règles du jeu : état, transitions, vérifications
import random

COL_LENGTHS = {
    2: 3, 3: 5, 4: 7, 5: 9, 6: 11, 7: 13, 8: 11, 9: 9, 10: 7, 11: 5, 12: 3
}
MAX_TEMP_MARKERS = 3
COLUMNS = list(COL_LENGTHS.keys())

class GameState:
    def __init__(self, players):
        self.players = players
        self.current_player_index = 0
        self.board = {col: [] for col in COLUMNS}
        self.locked_columns = set()

    def roll_dice(self):
        return [random.randint(1, 6) for _ in range(4)]

    def get_pairs(self, dice):
        return [
            (dice[0] + dice[1], dice[2] + dice[3]),
            (dice[0] + dice[2], dice[1] + dice[3]),
            (dice[0] + dice[3], dice[1] + dice[2])
        ]

    def is_column_locked(self, col):
        return col in self.locked_columns

    def lock_column(self, col, player):
        self.locked_columns.add(col)
        player.completed.add(col)
        self.board[col].append(player.name)

    def next_player(self):
        self.current_player_index = (self.current_player_index + 1) % len(self.players)

    def get_current_player(self):
        return self.players[self.current_player_index]

    def check_winner(self):
        for player in self.players:
            if len(player.completed) >= 3:
                return player
        return None
    
    def available_actions(self, pairs, temp_markers, player):
        possible = []
        for i, (a,b) in enumerate(pairs):
            if not self.is_column_locked(a) and not self.is_column_locked(b):
                if a == b:
                    if a in temp_markers:
                        if temp_markers[a] < COL_LENGTHS[a]-1:
                            possible.append((a, b))
                    else:
                        if len(temp_markers) < MAX_TEMP_MARKERS and player.progress[a] < COL_LENGTHS[a]-1:
                            possible.append((a, b))
                else:
                    if a in temp_markers and b in temp_markers:
                        if temp_markers[a] < COL_LENGTHS[a] and temp_markers[b] < COL_LENGTHS[b]:
                            possible.append((a, b))
                    elif a not in temp_markers and b not in temp_markers:
                        if len(temp_markers) + 1 <MAX_TEMP_MARKERS:
                            possible.append((a, b))
                    elif a in temp_markers and b not in temp_markers:
                        if temp_markers[a] < COL_LENGTHS[a] and len(temp_markers) < MAX_TEMP_MARKERS:
                            possible.append((a, b))
                    else:
                        if temp_markers[b] < COL_LENGTHS[b] and len(temp_markers) < MAX_TEMP_MARKERS:
                            possible.append((a, b))

            if (a,b) not in possible:
                for val in (a, b):
                    if not self.is_column_locked(val):
                        if val in temp_markers:
                            if temp_markers[val] < COL_LENGTHS[val]:
                                if val == a:
                                    possible.append((val,))
                                else:
                                    possible.append((val,))
                        else:
                            if len(temp_markers) < MAX_TEMP_MARKERS:
                                if val == a:
                                    possible.append((val,))
                                else:
                                    possible.append((val,))
        return possible
    
    def apply_action(self, choice, temp_markers, player):
        for val in choice:
            if val not in temp_markers:
                temp_markers[val] = player.progress.get(val, 0)
            temp_markers[val] += 1
        return temp_markers
    
    def to_dict(self, temp_markers=None, dice=None):
        """
        Retourne un état JSON-sérialisable du jeu.
        temp_markers et dice doivent être fournis par l'appelant si besoin.
        """
        # Récupère les infos des joueurs
        players_info = []
        for p in self.players:
            players_info.append({
                "name": p.name,
                "progress": dict(p.progress),
                "completed": list(p.completed)
            })

        # Plateau (qui a verrouillé quoi)
        board_info = {col: list(names) for col, names in self.board.items()}

        # Joueur courant
        current_player = self.get_current_player().name

        # Dés (si fournis)
        dice_info = list(dice) if dice is not None else None

        # Colonnes verrouillées
        locked_columns = list(self.locked_columns)

        # Actions possibles (si temp_markers et dice sont fournis)
        available_moves = []
        if temp_markers is not None and dice is not None:
            pairs = self.get_pairs(dice)
            available_moves = self.available_actions(pairs, temp_markers, self.get_current_player())

        # Partie terminée ?
        winner = self.check_winner()
        game_over = winner is not None

        return {
            "players": players_info,
            "board": board_info,
            "locked_columns": locked_columns,
            "current_player": current_player,
            "dice": dice_info,
            "available_moves": available_moves,
            "game_over": game_over,
            "winner": winner.name if winner else None
        }
