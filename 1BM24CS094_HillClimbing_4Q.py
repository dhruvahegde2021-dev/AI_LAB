from random import randint

def printBoard(board, N):
    for i in range(N):
        print(*board[i])

def printState(state):
    print(*state)
    
def compareStates(state1, state2, N):
    for i in range(N):
        if (state1[i] != state2[i]):
            return False
    return True

def fill(board, value, N):
    for i in range(N):
        for j in range(N):
            board[i][j] = value
        
def calculateObjective(board, state, N):
    attacking = 0
    for i in range(N):
        row = state[i]
        col = i - 1
        while (col >= 0 and board[row][col] != 1):
            col -= 1
        if (col >= 0 and board[row][col] == 1):
            attacking += 1
        
        row = state[i]
        col = i + 1
        while (col < N and board[row][col] != 1):
            col += 1
        if (col < N and board[row][col] == 1):
            attacking += 1
        
        row = state[i] - 1
        col = i - 1
        while (col >= 0 and row >= 0 and board[row][col] != 1):
            col -= 1
            row -= 1
        if (col >= 0 and row >= 0 and board[row][col] == 1):
            attacking += 1
        
        row = state[i] + 1
        col = i + 1
        while (col < N and row < N and board[row][col] != 1):
            col += 1
            row += 1
        if (col < N and row < N and board[row][col] == 1):
            attacking += 1
        
        row = state[i] + 1
        col = i - 1
        while (col >= 0 and row < N and board[row][col] != 1):
            col -= 1
            row += 1
        if (col >= 0 and row < N and board[row][col] == 1):
            attacking += 1
        
        row = state[i] - 1
        col = i + 1
        while (col < N and row >= 0 and board[row][col] != 1):
            col += 1
            row -= 1
        if (col < N and row >= 0 and board[row][col] == 1):
            attacking += 1
        
    return int(attacking / 2)

def generateBoard(board, state, N):
    fill(board, 0, N)
    for i in range(N):
        board[state[i]][i] = 1
    
def copyState(state1, state2, N):
    for i in range(N):
        state1[i] = state2[i]
    
def getNeighbour(board, state, N):
    opBoard = [[0 for _ in range(N)] for _ in range(N)]
    opState = [0 for _ in range(N)]

    copyState(opState, state, N)
    generateBoard(opBoard, opState, N)
    opObjective = calculateObjective(opBoard, opState, N)

    NeighbourBoard = [[0 for _ in range(N)] for _ in range(N)]
    NeighbourState = [0 for _ in range(N)]
    copyState(NeighbourState, state, N)
    generateBoard(NeighbourBoard, NeighbourState, N)

    for i in range(N):
        for j in range(N):
            if (j != state[i]):
                NeighbourState[i] = j
                NeighbourBoard[NeighbourState[i]][i] = 1
                NeighbourBoard[state[i]][i] = 0

                temp = calculateObjective(NeighbourBoard, NeighbourState, N)

                if (temp <= opObjective):
                    opObjective = temp
                    copyState(opState, NeighbourState, N)
                    generateBoard(opBoard, opState, N)
                
                NeighbourBoard[NeighbourState[i]][i] = 0
                NeighbourState[i] = state[i]
                NeighbourBoard[state[i]][i] = 1
            
    copyState(state, opState, N)
    fill(board, 0, N)
    generateBoard(board, state, N)

def hillClimbing(board, state, N):
    neighbourBoard = [[0 for _ in range(N)] for _ in range(N)]
    neighbourState = [0 for _ in range(N)]

    copyState(neighbourState, state, N)
    generateBoard(neighbourBoard, neighbourState, N)
    
    while True:
        copyState(state, neighbourState, N)
        generateBoard(board, state, N)

        getNeighbour(neighbourBoard, neighbourState, N)

        if (compareStates(state, neighbourState, N)):
            printBoard(board, N)
            break
        
        elif (calculateObjective(board, state, N) == calculateObjective(neighbourBoard, neighbourState, N)):
            copyState(state, neighbourState, N)
            generateBoard(board, state, N)

if __name__ == "__main__":
    user_input = input("Enter initial state elements: ").strip()
    cleaned_input = user_input.replace(",", " ")
    
    state = [int(x) for x in cleaned_input.split() if x.strip().isdigit()]
    
    if not state:
        state = [3, 1, 2, 0]
        
    N = len(state)
    
    if any(row >= N or row < 0 for row in state):
        print(f"Error: Individual row numbers must be between 0 and {N - 1} for a board of size {N}.")
    else:
        board = [[0 for _ in range(N)] for _ in range(N)]
        generateBoard(board, state, N)
        
        print("\nInitial Custom Board Configuration State:")
        printState(state)
        print("Initial Attacking Pairs Count:", calculateObjective(board, state, N))
        
        print("\nRunning Hill Climbing Peak Search...")
        hillClimbing(board, state, N)
        
        print("\nFinal State Achieved Evaluation Score:", calculateObjective(board, state, N))
