
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cant_stop.game_engine import GameState, COL_LENGTHS, COLUMNS, MAX_TEMP_MARKERS
from cant_stop.players.human_player import HumanPlayer
from cant_stop.players.random_ai import RandomAI
from cant_stop.players.rl_agent import RLAgent

def display_board(players, board, locked_columns):
    print("\nPlateau de jeu :")
    for col in COLUMNS:
        line = f"Col {col:>2} ["
        for step in range(1, COL_LENGTHS[col] + 1):
            marker = ""
            for player in players:
                if player.progress.get(col, 0) >= step:
                    marker += player.name[-1]
            if marker == "":
                marker = "."
            marker += ","
            line += marker
        line += "]"
        if col in locked_columns:
            line += " (Verrouillée)"
        print(line)

def play_turn(game_state, player):
    temp_markers = {}
    busted = False
    while True:
        dice = game_state.roll_dice()
        pairs = game_state.get_pairs(dice)
        possible = []
        # Adaptation à la nouvelle architecture : on utilise game_state pour locked_columns et player pour progress
        for a, b in pairs:
            if not game_state.is_column_locked(a) and not game_state.is_column_locked(b):
                # Cas où on peut prendre deux fois la même colonne
                if a == b and ((a in temp_markers and temp_markers[a] < COL_LENGTHS[a]-1) or (a not in temp_markers and len(temp_markers) < MAX_TEMP_MARKERS and player.progress[a] < COL_LENGTHS[a]-1)):
                    possible.append((a,b))
                # Si les deux colonnes sont déjà en cours de progression
                elif a != b and (a in temp_markers and temp_markers[a] < COL_LENGTHS[a]) and (b in temp_markers and temp_markers[b] < COL_LENGTHS[b]):
                    possible.append((a,b))
                # Si on a suffisamment de marqueurs temporaires
                elif a != b and len(temp_markers) + 1 < MAX_TEMP_MARKERS:
                    possible.append((a,b))
                # Vérification de la limite de marqueurs temporaires un à un
                elif a != b and ((a in temp_markers and temp_markers[a] < COL_LENGTHS[a] and len(temp_markers) < MAX_TEMP_MARKERS) or (b in temp_markers and temp_markers[b] < COL_LENGTHS[b] and len(temp_markers) < MAX_TEMP_MARKERS)):
                    possible.append((a,b))
            # Si on ne peut pas prendre les deux, on regarde si on peut prendre un seul
            if (a,b) not in possible:
                for val in (a, b):
                    if not game_state.is_column_locked(val) and ((val in temp_markers and temp_markers[val] < COL_LENGTHS[val]) or (val not in temp_markers and len(temp_markers) < MAX_TEMP_MARKERS)):
                        possible.append((val,))

        if possible:
            choice = player.choose_action(possible, dice, pairs, temp_markers, game_state)
            print(f"{player.name} a choisi la paire {choice}")
            for val in choice:
                if val not in temp_markers:
                    temp_markers[val] = player.progress.get(val, 0)
                temp_markers[val] += 1
        else:
            busted = True
            print(f"{player.name} a busté!")
            break
        print(f"Progression temporaire : {temp_markers}")
        if player.should_continue():
            continue
        else:
            print(f"{player.name} s'arrête et sécurise ses progrès.")
            break
    if not busted:
        for col, val in temp_markers.items():
            player.progress[col] = val
            if player.progress[col] >= COL_LENGTHS[col]:
                game_state.lock_column(col, player)

def main():
    players = [
        RLAgent("Joueur 1"),
        RandomAI("Joueur 2")
    ]
    for p in players:
        p.progress = {col: 0 for col in COLUMNS}
    game_state = GameState(players)
    turn = 0
    while True:
        player = game_state.get_current_player()
        print(f"\n--- Tour {turn} : {player.name} ---")
        play_turn(game_state, player)
        display_board(players, game_state.board, game_state.locked_columns)
        winner = game_state.check_winner()
        if winner:
            print(f"\n🎉 {winner.name} a gagné en complétant 3 colonnes !")
            display_board(players, game_state.board, game_state.locked_columns)
            break
        game_state.next_player()
        turn += 1

if __name__ == "__main__":
    main()
