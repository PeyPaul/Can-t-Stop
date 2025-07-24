import random

# Constantes du jeu
COL_LENGTHS = {
    2: 3, 3: 5, 4: 7, 5: 9, 6: 11, 7: 13,
    8: 11, 9: 9, 10: 7, 11: 5, 12: 3
}

MAX_TEMP_MARKERS = 3
COLUMNS = list(COL_LENGTHS.keys())

class Player:
    def __init__(self, name, is_human=False):
        self.name = name
        self.is_human = is_human
        self.progress = {col: 0 for col in COLUMNS}
        self.completed = set()

class Game:
    def __init__(self, players, ui):
        self.players = players
        self.ui = ui
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

    def get_possible_actions(self, player, temp_markers, pairs):
        possible = []
        for a, b in pairs:
            if a not in self.locked_columns and b not in self.locked_columns:
                if a == b and (
                    (a in temp_markers and temp_markers[a] < COL_LENGTHS[a] - 1) or
                    (a not in temp_markers and len(temp_markers) < MAX_TEMP_MARKERS and player.progress[a] < COL_LENGTHS[a] - 1)
                ):
                    possible.append((a, b))
                elif a != b and (
                    (a in temp_markers and temp_markers[a] < COL_LENGTHS[a]) and
                    (b in temp_markers and temp_markers[b] < COL_LENGTHS[b])
                ):
                    possible.append((a, b))
                elif a != b and len(temp_markers) + 1 < MAX_TEMP_MARKERS:
                    possible.append((a, b))
                elif a != b and (
                    (a in temp_markers and temp_markers[a] < COL_LENGTHS[a] and len(temp_markers) < MAX_TEMP_MARKERS) or
                    (b in temp_markers and temp_markers[b] < COL_LENGTHS[b] and len(temp_markers) < MAX_TEMP_MARKERS)
                ):
                    possible.append((a, b))
            if (a, b) not in possible:
                for val in (a, b):
                    if val not in self.locked_columns and (
                        (val in temp_markers and temp_markers[val] < COL_LENGTHS[val]) or
                        (val not in temp_markers and len(temp_markers) < MAX_TEMP_MARKERS)
                    ):
                        possible.append((val,))
        return possible

    def play_turn(self, player):
        temp_markers = {}
        busted = False

        while True:
            dice = self.roll_dice()
            pairs = self.get_pairs(dice)
            possible = self.get_possible_actions(player, temp_markers, pairs)

            if possible:
                choice = self.ui.choose_action(player, possible, dice, pairs)
                for val in choice:
                    if val not in temp_markers:
                        temp_markers[val] = player.progress[val]
                    temp_markers[val] += 1
            else:
                busted = True
                self.ui.notify_bust(player)
                break

            self.ui.display_temp_progress(player, temp_markers)

            if self.ui.should_continue(player):
                continue
            else:
                self.ui.notify_stop(player)
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
            if len(player.completed) >= 3:
                return player
        return None

    def play_game(self):
        turn = 0
        while True:
            player = self.players[self.current_player_index]
            self.ui.start_turn(turn, player)
            self.play_turn(player)
            self.ui.display_board(self)
            winner = self.check_winner()
            if winner:
                self.ui.declare_winner(winner, self)
                break
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            turn += 1