# Can't Stop AI Project  

## 📌 Overview  
This project implements an intelligent agent that plays the board game **"Can't Stop"**.  
The goal of the project is to explore different approaches to building an AI player, ranging from **reinforcement learning** to **probabilistic heuristics**, and to compare their performance.  

The project provides:  
- A **complete game engine** for *Can't Stop* (dice rolling, turn management, column locking).  
- A **terminal interface** that allows:  
  - Human vs Human  
  - Human vs AI  
  - AI vs AI matches  
- Multiple types of AI players:  
  - **RandomAI** – a purely random agent.  
  - **RLAgent** – a reinforcement learning agent trained using PPO and Gym.  
  - **HeuristicAI** – a probability-based agent that significantly outperforms RLAgent.  

This repository aims to serve as both a learning project and a practical demonstration of applying AI techniques to a real game environment.

---

## 🎲 Game Rules (Quick Recap)  
- The game is played with **4 dice**.  
- At each turn, the player rolls the dice, selects **two pairs**, and advances temporary markers on the corresponding columns (based on the sums of the pairs).  
- A player may have at most **3 active temporary markers** at a time.  
- If no legal combination can be chosen, the player **busts** and loses all temporary progress for this turn.  
- The player can **stop at any time** to secure progress.  
- Once a player **completes a column**, it is locked and no other player can use it.  
- The first player to **lock 3 columns** wins.  

---

## 🛠️ Technical Implementation  

### 1. Game Engine  
- Fully implemented in Python, object-oriented design.  
- Handles dice rolling, column lengths, player progression, column locking, turn rotation, and win conditions.  

### 2. Gym Environment  
- A custom **OpenAI Gym environment** was created for training reinforcement learning agents.  
- **Action masking** is implemented to prevent the RL agent from selecting invalid actions.  
- Observations include:  
  - Player and opponent progress (per column)  
  - Locked columns  
  - Number of completed columns  
  - Available actions (encoded)  

### 3. Reinforcement Learning Approach  
- **PPO (Proximal Policy Optimization)** was used with Stable-Baselines3.  
- Reward shaping included:  
  - Positive reward for completing columns and winning the game.  
  - Negative reward for busting or losing.  
  - Small incentives for finishing the game quickly.  
- Despite experimentation with reward tuning and observation design, RL agents struggled to consistently outperform `RandomAI`.  

### 4. Heuristic Approach  
- The final solution uses a **probability-based heuristic agent**:  
  - Calculates the **probability of busting** given the current dice roll and temporary markers.  
  - Decides whether to continue or stop based on risk thresholds.  
  - Prioritizes columns that maximize the chance of completing 3 columns efficiently.  
- This agent is **much stronger** than the RL approach and consistently beats `RandomAI`.  

---

## 📊 Results  

| Agent           | Win Rate vs RandomAI | Avg. Game Length | Notes |
|-----------------|--------------------|----------------|------|
| RandomAI        | ~50%               | ~40 turns      | Baseline |
| RLAgent (PPO)   | ~52–55%            | Similar to RandomAI | Small improvement despite long training |
| HeuristicAI     | **>95%**           | Shorter games  | Plays much more aggressively and efficiently. Can easily beat human players |

Key takeaway: **The heuristic agent is both faster and more effective than the RL approach.**

---

## 🚀 How to Run  

### Install Dependencies  
```bash
pip install -r requirements.txt
```

You can modify the players and their characteristics directly in `main.py` at line 103. THen to launch the game : 

```bash
python cant_stop/main.py
```
---

## 🔮 Future Work  

- Improve heuristic strategy with **dynamic risk thresholds** (adjusting risk-taking based on opponent’s progress).
- Hybrid approach: Use RL to fine-tune parameters of the heuristic policy.
- Implement a web-based interface to visualize matches more intuitively.

---

## 💡 Key Learnings  

- **Action masking** is crucial for RL in combinatorial games like Can't Stop.
- Reward shaping is challenging: agents can exploit unintended behaviors.
- In this case, a **well-designed heuristic** outperforms reinforcement learning, showing that domain knowledge can beat brute-force learning when state/action space is complex but manageable.

