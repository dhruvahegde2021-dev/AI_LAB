import math
import random


def get_cost(state):
    """Calculates the number of conflicting pairs of queens (minimization objective)."""
    conflicts = 0
    n = len(state)
    for i in range(n):
        for j in range(i + 1, n):
            # Check row conflict
            if state[i] == state[j]:
                conflicts += 1
            # Check diagonal conflict
            elif abs(state[i] - state[j]) == abs(i - j):
                conflicts += 1
    return conflicts


def get_random_neighbour(state):
    """Line 4: Generates a neighbor by moving one random queen to a different row."""
    neighbour = list(state)
    col = random.randint(0, 7)
    current_row = state[col]

    # Pick a new random row that is different from the current row
    new_row = random.choice([r for r in range(8) if r != current_row])
    neighbour[col] = new_row
    return neighbour


def simulated_annealing_8queens(initial_temp=10.0, cooling_rate=0.99, max_steps=1000):
    # Line 1: current <- initial state (randomly place 1 queen per column)
    current = [random.randint(0, 7) for _ in range(8)]
    current_cost = get_cost(current)

    # Line 2: T <- a large positive value
    T = initial_temp

    step = 0
    # Line 3: while T > 0 do (plus a step limit to guarantee termination)
    while T > 0.0001 and current_cost > 0 and step < max_steps:
        # Line 4: next <- a random neighbour of current
        next_state = get_random_neighbour(current)
        next_cost = get_cost(next_state)

        # Line 5: ΔE <- current.cost - next.cost
        delta_E = current_cost - next_cost

        # Line 6: if ΔE > 0 then
        if delta_E > 0:
            # Line 7: current <- next
            current = next_state
            current_cost = next_cost
        # Line 8: else
        else:
            # Line 9: current <- next with probability p = e^(ΔE / T)
            p = math.exp(delta_E / T)
            if random.random() < p:
                current = next_state
                current_cost = next_cost

        # Line 11: decrease T
        T = T * cooling_rate
        step += 1

    # Line 13: return current
    return current, current_cost


def print_board(state):
    """Visualizes the 8x8 chessboard arrangement."""
    for row in range(8):
        line = ""
        for col in range(8):
            if state[col] == row:
                line += " Q "
            else:
                line += " . "
        print(line)


# --- Example Execution ---
if __name__ == "__main__":
    solution, conflicts = simulated_annealing_8queens()

    print(f"Final State (Columns 0-7 Rows): {solution}")
    print(f"Remaining Conflicts: {conflicts}\n")
    print("Chessboard Visualization:")
    print_board(solution)
