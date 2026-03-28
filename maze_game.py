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
    "APPLE": "Fruit that keeps the doctor away 🍎",
    "TRAIN": "Runs on tracks 🚆",
    "WATER": "You drink it 💧"
}

CHAPTER = "Addition"

# -----------------------
# BUILD PATH MAZE (MUST BE ABOVE INIT)
# -----------------------
def build_game():
    grid = [["" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

    # create snake path
    path = []
    r, c = 0, 0
    path.append((r, c))

    for _ in range(1, GRID_SIZE * GRID_SIZE):
        if c < GRID_SIZE - 1:
            c += 1
        else:
            r += 1
            c = 0
        if r < GRID_SIZE:
            path.append((r, c))

    # embed words along path
    full_letters = []
    for w in WORDS:
        full_letters += list(w)

    for (r, c), letter in zip(path, full_letters):
        grid[r][c] = letter

    # fill remaining cells
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if grid[i][j] == "":
                grid[i][j] = random.choice(string.ascii_uppercase)

    st.session_state.grid = grid
    st.session_state.path = path
    st.session_state.full_letters = full_letters


# -----------------------
# INIT
# -----------------------
def init():
    if "grid" not in st.session_state:
        build_game()

    defaults = {
        "player_idx": 0,
        "current_word_progress": "",
        "word_index": 0,
        "awaiting": False,
        "question": None,
        "answer": None,
        "lives": 3,
        "score": 0
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init()

# -----------------------
# AI QUESTION
# -----------------------
def generate_question():
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": "Generate a simple math question and answer. Return JSON with 'question' and 'answer'."
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
            pos = (i, j)
            player_pos = st.session_state.path[st.session_state.player_idx]

            if pos == player_pos:
                label = "🧙"
            elif pos == st.session_state.path[-1]:
                label = "👻"
            else:
                label = st.session_state.grid[i][j]

            if cols[j].button(label, key=f"{i}-{j}", use_container_width=True):
                handle_click(pos)


# -----------------------
# HANDLE MOVE
# -----------------------
def handle_click(pos):
    idx = st.session_state.player_idx

    # next valid step
    if idx + 1 >= len(st.session_state.path):
        return

    next_pos = st.session_state.path[idx + 1]

    if pos != next_pos:
        st.warning("❌ Wrong path!")
        return

    letter = st.session_state.grid[pos[0]][pos[1]]

    st.session_state.current_word_progress += letter
    st.session_state.player_idx += 1

    current_word = WORDS[st.session_state.word_index]

    if st.session_state.current_word_progress == current_word:
        st.success(f"🎉 Word completed: {current_word}")
        st.session_state.awaiting = True

    st.rerun()


# -----------------------
# UI
# -----------------------
st.title("🧙 Exorcist Word Maze")

# GAME OVER
if st.session_state.lives <= 0:
    st.error("💀 Game Over")
    if st.button("Restart"):
        st.session_state.clear()
        st.rerun()
    st.stop()

# ALL WORDS DONE
if st.session_state.word_index >= len(WORDS):
    st.success("👻 Exorcism Complete! You Win!")
    st.stop()

# CURRENT WORD + RIDDLE
current_word = WORDS[st.session_state.word_index]
st.markdown("## 🧩 Riddle")
st.info(WORD_RIDDLES[current_word])
st.caption(f"Progress: {st.session_state.current_word_progress}")

# DRAW GRID
draw()

# -----------------------
# QUESTION GATE
# -----------------------
if st.session_state.awaiting:
    st.markdown("## 🚪 Solve to Proceed")

    if st.session_state.question is None:
        q, a = generate_question()
        st.session_state.question = q
        st.session_state.answer = a

    st.write(st.session_state.question)
    ans = st.text_input("Answer")

    if st.button("Submit"):
        if ans.strip() == st.session_state.answer.strip():
            st.success("🚪 Door opened!")

            st.session_state.current_word_progress = ""
            st.session_state.word_index += 1
            st.session_state.awaiting = False
            st.session_state.question = None

            st.session_state.score += 10

            st.rerun()
        else:
            st.error("❌ Wrong answer!")
            st.session_state.lives -= 1
