import streamlit as st
from openai import OpenAI
import json
import random
import string

# -----------------------
# CONFIG
# -----------------------
st.set_page_config(page_title="Exorcist Maze", layout="centered")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

GRID_SIZE = 7

WORDS = ["APPLE", "TRAIN", "WATER"]

WORD_RIDDLES = {
    "APPLE": "Fruit that keeps doctor away",
    "TRAIN": "Runs on tracks",
    "WATER": "You drink it"
}

CHAPTER = "Addition"

# -----------------------
# INIT
# -----------------------
def init():
    if "grid" not in st.session_state:
        build_game()

    if "player_idx" not in st.session_state:
        st.session_state.player_idx = 0

    if "current_word_progress" not in st.session_state:
        st.session_state.current_word_progress = ""

    if "word_index" not in st.session_state:
        st.session_state.word_index = 0

    if "awaiting" not in st.session_state:
        st.session_state.awaiting = False

init()

# -----------------------
# BUILD PATH MAZE
# -----------------------
def build_game():
    grid = [["" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

    path = []
    r, c = 0, 0
    path.append((r, c))

    # create snake path
    for i in range(1, GRID_SIZE * GRID_SIZE):
        if c < GRID_SIZE - 1:
            c += 1
        else:
            r += 1
            c = 0
        if r < GRID_SIZE:
            path.append((r, c))

    # embed words along path
    full_path_letters = []
    for w in WORDS:
        full_path_letters += list(w)

    for (r, c), letter in zip(path, full_path_letters):
        grid[r][c] = letter

    # fill rest
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if grid[i][j] == "":
                grid[i][j] = random.choice(string.ascii_uppercase)

    st.session_state.grid = grid
    st.session_state.path = path
    st.session_state.full_letters = full_path_letters

# -----------------------
# AI QUESTION
# -----------------------
def generate_question():
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": "Give simple math question and answer JSON"
        }],
        response_format={"type": "json_object"}
    )

    data = json.loads(res.choices[0].message.content)
    return data["question"], str(data["answer"])

# -----------------------
# DRAW GRID
# -----------------------
def draw():
    for i in range(GRID_SIZE):
        cols = st.columns(GRID_SIZE)
        for j in range(GRID_SIZE):

            idx = st.session_state.player_idx
            pos = (i, j)

            if pos == st.session_state.path[idx]:
                label = "🧙"
            elif pos == st.session_state.path[-1]:
                label = "👻"
            else:
                label = st.session_state.grid[i][j]

            if cols[j].button(label, key=f"{i}-{j}"):
                handle_click(pos)

# -----------------------
# HANDLE MOVE
# -----------------------
def handle_click(pos):
    idx = st.session_state.player_idx
    next_pos = st.session_state.path[idx + 1] if idx + 1 < len(st.session_state.path) else None

    if pos != next_pos:
        st.warning("Wrong path!")
        return

    letter = st.session_state.grid[pos[0]][pos[1]]
    st.session_state.current_word_progress += letter
    st.session_state.player_idx += 1

    current_word = WORDS[st.session_state.word_index]

    # check word completion
    if st.session_state.current_word_progress == current_word:
        st.success(f"Word solved: {current_word}")
        st.session_state.awaiting = True

    st.rerun()

# -----------------------
# UI
# -----------------------
st.title("🧙 Exorcist Word Maze")

# show riddle
current_word = WORDS[st.session_state.word_index]
st.info(f"💡 Riddle: {WORD_RIDDLES[current_word]}")
st.caption(f"Progress: {st.session_state.current_word_progress}")

draw()

# -----------------------
# QUESTION GATE
# -----------------------
if st.session_state.awaiting:
    st.markdown("## 🚪 Solve to proceed")

    q, a = generate_question()
    st.write(q)
    ans = st.text_input("Answer")

    if st.button("Submit"):
        if ans.strip() == a.strip():
            st.success("Door opened!")

            st.session_state.current_word_progress = ""
            st.session_state.word_index += 1
            st.session_state.awaiting = False

            st.rerun()
        else:
            st.error("Wrong!")

# -----------------------
# WIN
# -----------------------
if st.session_state.player_idx >= len(st.session_state.full_letters) - 1:
    st.success("👻 Exorcism Complete! You Win!")
