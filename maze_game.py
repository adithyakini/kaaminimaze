import streamlit as st
import random
import string
import time
from openai import OpenAI

level = st.selectbox("Difficulty", ["easy","medium","hard"])
GRID_SIZE = 10

#-------------
# get AI words
#-------------
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def get_words(level):

    if level == "easy":
        rule = "exactly 3 letters"
    elif level == "medium":
        rule = "4 to 5 letters"
    else:
        rule = "6 or more letters"

    prompt = f"""
    Generate 5 common English words.

    Rules:
    - Each word must be {rule}
    - Words must be simple and common
    - No rare or obscure words

    Return ONLY comma-separated words.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.choices[0].message.content.strip()

    words = [w.strip().upper() for w in text.split(",")]

    return words
words = get_words(level)
st.write("DEBUG words:", words)

# ------------------------
# BRANCHING PATH GENERATION
# ------------------------
def generate_branching_path(words):
    grid = [[random.choice(string.ascii_uppercase) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

    main_path = []
    x, y = 0, 0

    for word in words:
        for ch in word:
            grid[x][y] = ch
            main_path.append((x,y))

            # random branching direction
            moves = [(1,0),(0,1),(-1,0),(0,-1)]
            random.shuffle(moves)

            for dx, dy in moves:
                nx, ny = x+dx, y+dy
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE and (nx,ny) not in main_path:
                    x, y = nx, ny
                    break

    # add fake branches
    for _ in range(20):
        bx = random.randint(0, GRID_SIZE-1)
        by = random.randint(0, GRID_SIZE-1)
        if (bx,by) not in main_path:
            grid[bx][by] = random.choice(string.ascii_uppercase)

    return grid, main_path


# ------------------------
# INIT
# ------------------------

if "init" not in st.session_state or st.session_state.get("level") != level:

    words = get_words(level)

    grid, path = generate_branching_path(words)

    entry_tile = path[0]
    exit_tile = path[-1]

    st.session_state.entry = entry_tile
    st.session_state.exit = exit_tile
    st.session_state.words = words
    st.session_state.grid = grid
    st.session_state.path = path
    st.session_state.level = level

    st.session_state.index = -1   # 👈 outside grid
    st.session_state.lives = 3
    st.session_state.wrong_tiles = set()
    st.session_state.start_time = time.time()
    st.session_state.finished = False

    st.session_state.init = True

if "leaderboard" not in st.session_state:
    st.session_state.leaderboard = []
# ------------------------
# TIMER
# ------------------------
elapsed = int(time.time() - st.session_state.start_time)

st.title("🧙 Word Maze Escape")
st.write(f"⏱️ Time: {elapsed}s | ❤️ Lives: {st.session_state.lives}")
st.write(f"Words: {' → '.join(st.session_state.words)}")

grid = st.session_state.grid
path = st.session_state.path
idx = st.session_state.index

# ------------------------
# ENTRY / EXIT VISUAL
# ------------------------
st.write("🚪 Entry Gate (Wizard starts outside)")
st.write("🚪 Exit Gate (Ghost waiting outside)")

# ------------------------
# GRID UI (UPDATED)
# ------------------------
for i in range(GRID_SIZE):
    cols = st.columns(GRID_SIZE + 2)  # 👈 extra space for entry/exit

    for j in range(GRID_SIZE + 2):

        # LEFT SIDE (Wizard entry)
        if j == 0:
            if i == st.session_state.entry[0]:
                label = "🚪🧙" if st.session_state.index == -1 else "🚪"
            else:
                label = ""
            cols[j].button(label, key=f"{i}-entry")
            continue

        # RIGHT SIDE (Ghost exit)
        if j == GRID_SIZE + 1:
            if i == st.session_state.exit[0]:
                label = "👻🚪"
            else:
                label = ""
            cols[j].button(label, key=f"{i}-exit")
            continue

        # NORMAL GRID
        x, y = i, j-1
        base = grid[x][y]

        # Wizard on path
        if st.session_state.index >= 0 and st.session_state.index < len(path) and (x,y) == path[st.session_state.index]:
            label = "🧙"

        # Completed path
        elif st.session_state.index >= 0 and (x,y) in path[:st.session_state.index]:
            label = f"🟩{base}"

        # Wrong tiles
        elif (x,y) in st.session_state.wrong_tiles:
            label = f"🟥{base}"

        else:
            label = base

        if cols[j].button(label, key=f"{x}-{y}"):

            if st.session_state.finished:
                continue

            # FIRST MOVE (enter gate)
            if st.session_state.index == -1 and (x,y) == st.session_state.entry:
                st.session_state.index = 0
                st.rerun()

            # NORMAL PATH MOVE
            elif (
                st.session_state.index >= 0
                and st.session_state.index < len(path)
                and (x,y) == path[st.session_state.index]
            ):
                st.session_state.index += 1
                st.rerun()

            # WRONG MOVE
            else:
                st.session_state.lives -= 1
                st.session_state.wrong_tiles.add((x,y))
                st.warning("❌ Wrong path!")

                if st.session_state.lives <= 0:
                    st.error("💀 Game Over")
                    st.session_state.finished = True

# ------------------------
# WIN
# ------------------------
if st.session_state.index >= len(path):
    st.success("✨ Om Bhoor bhuva swaha tatsavitur varenyam bhargo devasya deemahi prachodayaaaaat!!! The exorcism of Kamala is now complete.")
    st.session_state.finished = True

# ------------------------
# LEADERBOARD
# ------------------------
st.subheader("🏆 Leaderboard")

for i, s in enumerate(sorted(st.session_state.leaderboard)[:5]):
    st.write(f"{i+1}. {s}s")

# ------------------------
# RESET
# ------------------------
if st.button("🔄 New Game"):
    st.session_state.clear()
    st.rerun()
