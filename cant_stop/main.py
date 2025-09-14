
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cant_stop.game_engine import GameState, COL_LENGTHS, COLUMNS, MAX_TEMP_MARKERS
from cant_stop.players.human_player import HumanPlayer
from cant_stop.players.random_ai import RandomAI
from cant_stop.players.rl_agent import RLAgent
from cant_stop.players.rl_agent_v2 import RLAgent_v2
from cant_stop.players.heuristic_ai import HeuristicAI

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
    rolls_count = 0
    while True:
        dice = game_state.roll_dice()
        pairs = game_state.get_pairs(dice)
        # possible = []
        # for i, (a,b) in enumerate(pairs):
        #     if not game_state.is_column_locked(a) and not game_state.is_column_locked(b):
        #         if a == b:
        #             if a in temp_markers:
        #                 if temp_markers[a] < COL_LENGTHS[a]-1:
        #                     possible.append((a, b))
        #             else:
        #                 if len(temp_markers) < MAX_TEMP_MARKERS and player.progress[a] < COL_LENGTHS[a]-1:
        #                     possible.append((a, b))
        #         else:
        #             if a in temp_markers and b in temp_markers:
        #                 if temp_markers[a] < COL_LENGTHS[a] and temp_markers[b] < COL_LENGTHS[b]:
        #                     possible.append((a, b))
        #             elif a not in temp_markers and b not in temp_markers:
        #                 if len(temp_markers) + 1 <MAX_TEMP_MARKERS:
        #                     possible.append((a, b))
        #             elif a in temp_markers and b not in temp_markers:
        #                 if temp_markers[a] < COL_LENGTHS[a] and len(temp_markers) < MAX_TEMP_MARKERS:
        #                     possible.append((a, b))
        #             else:
        #                 if temp_markers[b] < COL_LENGTHS[b] and len(temp_markers) < MAX_TEMP_MARKERS:
        #                     possible.append((a, b))

        #     if (a,b) not in possible:
        #         for val in (a, b):
        #             if not game_state.is_column_locked(val):
        #                 if val in temp_markers:
        #                     if temp_markers[val] < COL_LENGTHS[val]:
        #                         if val == a:
        #                             possible.append((val,))
        #                         else:
        #                             possible.append((val,))
        #                 else:
        #                     if len(temp_markers) < MAX_TEMP_MARKERS:
        #                         if val == a:
        #                             possible.append((val,))
        #                         else:
        #                             possible.append((val,))
        possible = game_state.available_actions(pairs, temp_markers, player)
        
        if possible:
            choice = player.choose_action(possible, dice, pairs, temp_markers, game_state)
            print(f"{player.name} a choisi la paire {choice}")
            for val in choice:
                if val not in temp_markers:
                    temp_markers[val] = player.progress.get(val, 0)
                temp_markers[val] += 1
            rolls_count += 1

        else:
            busted = True
            print(f"{player.name} a busté!")
            break
        print(f"Progression temporaire : {temp_markers}")
        if player.should_continue(temp_markers=temp_markers, game_state=game_state):
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
        HeuristicAI("Joueur 1", k_risk=0.95, alpha_future=0.5, eps_explore=0.05),
        HumanPlayer("Joueur 2")
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


def simulate_games(num_games=1000, k_values=(0.85, 0.9, 0.95, 1.1, 1.2)):
    """
    Lance num_games parties pour chaque valeur de k dans k_values
    et affiche le nombre de victoires de l'IA heuristique.
    """
    results = {}

    for k in k_values:
        wins = 0
        for _ in range(num_games):
            players = [HeuristicAI("IA", k_risk=k), RandomAI("Random")]
            for p in players:
                p.progress = {col: 0 for col in COLUMNS}

            game_state = GameState(players)
            winner = None

            # Joue la partie jusqu'à avoir un gagnant
            while winner is None:
                player = game_state.get_current_player()
                play_turn(game_state, player)

                winner = game_state.check_winner()
                if not winner:
                    game_state.next_player()

            if winner.name == "IA":
                wins += 1

        results[k] = wins
        print(f"[k={k}] → {wins}/{num_games} victoires ({wins/num_games:.2%})")

    return results










if __name__ == "__main__":
    main()
