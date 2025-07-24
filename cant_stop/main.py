from cant_stop.game_engine import GameState, COL_LENGTHS, COLUMNS
from cant_stop.players.human_player import HumanPlayer
from cant_stop.players.random_ai import RandomAI

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
        # Logique de génération des actions possibles (à adapter)
        for a, b in pairs:
            if not game_state.is_column_locked(a) and not game_state.is_column_locked(b):
                possible.append((a, b))
        if possible:
            choice = player.choose_action(possible, dice, pairs)
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
        HumanPlayer("Joueur 1"),
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
