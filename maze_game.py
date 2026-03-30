import streamlit as st
import random
import string

GRID_SIZE = 6

# ------------------------
# WORD DICTIONARY
# ------------------------
DICTIONARY = [
    "CAT","DOG","SUN","MOON","STAR","FIRE","WIND","TREE","ROCK",
    "NOTE","TONE","STONE","GAME","WORD","PATH","MAZE","GHOST","WIZARD"
]

# prefix set for fast validation
PREFIXES = set()
for word in DICTIONARY:
    for i in range(len(word)):
        PREFIXES.add(word[:i+1])

# ------------------------
# GRID GENERATOR
# ------------------------
def generate_grid():
    return [[random.choice(string.ascii_uppercase) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

# ------------------------
# NEIGHBORS
# ------------------------
def get_neighbors(x, y):
    moves = [(x+1,y),(x-1,y),(x,y+1),(x,y-1)]
    return [(i,j) for i,j in moves if 0 <= i < GRID_SIZE and 0 <= j < GRID_SIZE]

# ------------------------
# VALID MOVES (WORD LOGIC)
# ------------------------
def get_valid_moves(player, current_word, grid, visited):
    valid = []
    for nx, ny in get_neighbors(*player):
        if (nx, ny) not in visited:
            next_word = current_word + grid[nx][ny]
            if next_word in PREFIXES:
                valid.append((nx, ny))
    return valid

# ------------------------
# HINT SYSTEM
# ------------------------
def get_hint(current_word):
    for word in DICTIONARY:
        if word.startswith(current_word) and word != current_word:
            return word
    return None

# ------------------------
# GHOST AI
# ------------------------
def move_ghost(ghost, player):
    gx, gy = ghost
    px, py = player

    if abs(px - gx) > abs(py - gy):
        gx += 1 if px > gx else -1 if px < gx else 0
    else:
        gy += 1 if py > gy else -1 if py < gy else 0

    return (gx, gy)

# ------------------------
# INIT
# ------------------------
if "grid" not in st.session_state:
    st.session_state.grid = generate_grid()
    st.session_state.player = (0,0)
    st.session_state.ghost = (GRID_SIZE-1, GRID_SIZE-1)
    st.session_state.current_word = st.session_state.grid[0][0]
    st.session_state.visited = {(0,0)}
    st.session_state.score = 0
    st.session_state.game_over = False

grid = st.session_state.grid
player = st.session_state.player
ghost = st.session_state.ghost
current_word = st.session_state.current_word

st.title("🧙 Word Maze (Real Mode)")

st.write(f"### Current Word: `{current_word}`")
st.write(f"Score: {st.session_state.score}")

valid_moves = get_valid_moves(player, current_word, grid, st.session_state.visited)

# ------------------------
# GRID RENDER
# ------------------------
for i in range(GRID_SIZE):
    cols = st.columns(GRID_SIZE)
    for j in range(GRID_SIZE):

        label = grid[i][j]

        if (i,j) == player:
            label = "🧙"
        elif (i,j) == ghost:
            label = "👻"
        elif (i,j) in valid_moves:
            label = f"🟩{grid[i][j]}"

        if cols[j].button(label, key=f"{i}-{j}"):

            if st.session_state.game_over:
                continue

            if (i,j) in valid_moves:

                letter = grid[i][j]
                new_word = current_word + letter

                st.session_state.player = (i,j)
                st.session_state.current_word = new_word
                st.session_state.visited.add((i,j))

                # check full word
                if new_word in DICTIONARY:
                    st.success(f"✅ Word formed: {new_word}")
                    st.session_state.score += len(new_word)

                    # reset for next word chain
                    st.session_state.current_word = ""
                    st.session_state.visited = {st.session_state.player}

                # ghost moves
                st.session_state.ghost = move_ghost(ghost, st.session_state.player)

            else:
                st.warning("❌ Invalid move")

# ------------------------
# HINT BUTTON
# ------------------------
if st.button("💡 Hint"):
    hint = get_hint(current_word)
    if hint:
        st.info(f"Try building: {hint}")
    else:
        st.info("No hint available")

# ------------------------
# GAME STATES
# ------------------------
if st.session_state.player == st.session_state.ghost:
    st.error("💀 Ghost caught you!")
    st.session_state.game_over = True

# ------------------------
# RESET
# ------------------------
if st.button("🔄 Restart"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
