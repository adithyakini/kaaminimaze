import streamlit as st
import random
import string

st.set_page_config(page_title="Exorcist Path", layout="centered")

GRID_SIZE = 10
WORDS = ["APPLE", "TRAIN", "WATER", "LIGHT", "PLANT"]

RIDDLES = {
    "APPLE": "Fruit 🍎",
    "TRAIN": "Runs on tracks 🚆",
    "WATER": "You drink it 💧",
    "LIGHT": "Opposite of dark 💡",
    "PLANT": "Grows in soil 🌱"
}

# -----------------------
# INIT
# -----------------------
if "initialized" not in st.session_state:
    grid = [[random.choice(string.ascii_uppercase) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

    # simple straight path
    path = [(0, 0)]
    r, c = 0, 0

    while len(path) < 60:
        if r < GRID_SIZE - 1:
            r += 1
        elif c < GRID_SIZE - 1:
            c += 1
        path.append((r, c))

    # embed words
    idx = 0
    for w in WORDS:
        for ch in w:
            if idx < len(path):
                pr, pc = path[idx]
                grid[pr][pc] = ch
                idx += 1

    st.session_state.grid = grid
    st.session_state.path = path
    st.session_state.player_index = 0
    st.session_state.current_word = ""
    st.session_state.word_index = 0
    st.session_state.awaiting = False
    st.session_state.lives = 3
    st.session_state.question = None
    st.session_state.answer = None
    st.session_state.initialized = True

# -----------------------
# MATH (local, no AI)
# -----------------------
def generate_question():
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    return f"{a} + {b}", str(a + b)

# -----------------------
# MOVE
# -----------------------
def handle_click(i, j):
    idx = st.session_state.player_index
    path = st.session_state.path

    if idx + 1 >= len(path):
        return

    next_pos = path[idx + 1]

    if (i, j) != next_pos:
        return

    st.session_state.player_index += 1

    letter = st.session_state.grid[i][j]
    st.session_state.current_word += letter

    target = WORDS[st.session_state.word_index]

    if st.session_state.current_word == target:
        st.session_state.awaiting = True

    st.rerun()

# -----------------------
# UI
# -----------------------
st.title("🧙 Exorcist Path")

if st.session_state.lives <= 0:
    st.error("💀 Game Over")
    if st.button("Restart"):
        st.session_state.clear()
        st.rerun()
    st.stop()

if st.session_state.word_index >= len(WORDS):
    st.success("👻 You reached the Ghost!")
    st.stop()

target = WORDS[st.session_state.word_index]

st.info(RIDDLES[target])
st.caption(f"Word: {st.session_state.current_word}")
st.caption(f"Lives: {st.session_state.lives}")

# -----------------------
# GRID
# -----------------------
player_pos = st.session_state.path[st.session_state.player_index]

for i in range(GRID_SIZE):
    cols = st.columns(GRID_SIZE)
    for j in range(GRID_SIZE):
        pos = (i, j)

        if pos == player_pos:
            label = "🧙"
        elif pos == st.session_state.path[-1]:
            label = "👻"
        else:
            label = st.session_state.grid[i][j]

        if cols[j].button(label, key=f"{i}-{j}", use_container_width=True):
            handle_click(i, j)

# -----------------------
# DOOR
# -----------------------
if st.session_state.awaiting:
    st.subheader("🚪 Solve to Continue")

    if st.session_state.question is None:
        q, a = generate_question()
        st.session_state.question = q
        st.session_state.answer = a

    st.write(st.session_state.question)
    ans = st.text_input("Answer")

    if st.button("Submit"):
        if ans.strip() == st.session_state.answer:
            st.success("Correct!")
            st.session_state.word_index += 1
            st.session_state.current_word = ""
        else:
            st.error("Wrong!")
            st.session_state.lives -= 1

        st.session_state.awaiting = False
        st.session_state.question = None
        st.rerun()
