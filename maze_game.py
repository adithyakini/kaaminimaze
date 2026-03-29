import streamlit as st
import random
import string

st.set_page_config(page_title="Exorcist WOW", layout="centered")

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
# SAFE SESSION INIT
# -----------------------
defaults = {
    "grid": None,
    "path": None,
    "step": 0,
    "word_index": 0,
    "current_input": "",
    "used_indices": [],
    "lives": 3,
    "awaiting": False,
    "q": None,
    "a": None,
    "feedback": ""
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# -----------------------
# BUILD SNAKE PATH
# -----------------------
def build_game():
    grid = [[random.choice(string.ascii_uppercase) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

    path = []
    for r in range(GRID_SIZE):
        if r % 2 == 0:
            for c in range(GRID_SIZE):
                path.append((r, c))
        else:
            for c in reversed(range(GRID_SIZE)):
                path.append((r, c))

    idx = 0
    for word in WORDS:
        for ch in word:
            r, c = path[idx]
            grid[r][c] = ch
            idx += 1

    return grid, path

if st.session_state.grid is None:
    grid, path = build_game()
    st.session_state.grid = grid
    st.session_state.path = path

# -----------------------
# MATH
# -----------------------
def gen_q():
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    return f"{a} + {b}", str(a + b)

# -----------------------
# LETTER LOGIC
# -----------------------
def click_letter(idx, letter):
    if idx in st.session_state.used_indices:
        return

    st.session_state.current_input += letter
    st.session_state.used_indices.append(idx)

def undo():
    if st.session_state.current_input:
        st.session_state.current_input = st.session_state.current_input[:-1]
        st.session_state.used_indices.pop()

def clear():
    st.session_state.current_input = ""
    st.session_state.used_indices = []

def shuffle_letters():
    st.session_state.letter_order = random.sample(
        list(range(len(WORDS[st.session_state.word_index]))),
        len(WORDS[st.session_state.word_index])
    )

# -----------------------
# SUBMIT WORD
# -----------------------
def submit_word():
    target = WORDS[st.session_state.word_index]

    if st.session_state.current_input == target:
        for _ in target:
            st.session_state.step += 1

        st.session_state.awaiting = True
        st.session_state.feedback = "✅ Correct!"
        clear()
    else:
        st.session_state.feedback = "❌ Try again!"
        clear()

# -----------------------
# UI HEADER
# -----------------------
st.title("🧙 Exorcist WOW")

if st.session_state.lives <= 0:
    st.error("💀 Game Over")
    if st.button("Restart"):
        st.session_state.clear()
        st.rerun()
    st.stop()

if st.session_state.word_index >= len(WORDS):
    st.success("👻 You reached the ghost! Exorcism complete!")
    st.stop()

target = WORDS[st.session_state.word_index]

st.info(RIDDLES[target])

# -----------------------
# WORD SLOTS
# -----------------------
slots = []
for i in range(len(target)):
    if i < len(st.session_state.current_input):
        slots.append(st.session_state.current_input[i])
    else:
        slots.append("_")

st.markdown("### " + " ".join(slots))
st.caption(f"Lives ❤️: {st.session_state.lives}")

if st.session_state.feedback:
    st.write(st.session_state.feedback)

# -----------------------
# LETTER BANK
# -----------------------
letters = list(target)

if "letter_order" not in st.session_state:
    st.session_state.letter_order = list(range(len(letters)))

cols = st.columns(len(letters))

for i, idx in enumerate(st.session_state.letter_order):
    letter = letters[idx]
    disabled = idx in st.session_state.used_indices

    if cols[i].button(letter, disabled=disabled):
        click_letter(idx, letter)
        st.rerun()

# controls
c1, c2, c3, c4 = st.columns(4)

with c1:
    if st.button("Submit"):
        submit_word()
        st.rerun()

with c2:
    if st.button("Undo"):
        undo()
        st.rerun()

with c3:
    if st.button("Clear"):
        clear()
        st.rerun()

with c4:
    if st.button("Shuffle"):
        shuffle_letters()
        st.rerun()

# -----------------------
# GRID DISPLAY
# -----------------------
for i in range(GRID_SIZE):
    cols = st.columns(GRID_SIZE)
    for j in range(GRID_SIZE):
        pos = (i, j)

        if pos in st.session_state.path[:st.session_state.step]:
            label = f"🟨"
        elif pos == st.session_state.path[st.session_state.step]:
            label = "🧙"
        elif pos == st.session_state.path[-1]:
            label = "👻"
        else:
            label = "⬛"

        cols[j].button(label, key=f"{i}-{j}", disabled=True)

# -----------------------
# DOOR SYSTEM
# -----------------------
if st.session_state.awaiting:
    st.subheader("🚪 Solve to Continue")

    if st.session_state.q is None:
        q, a = gen_q()
        st.session_state.q = q
        st.session_state.a = a

    st.write(st.session_state.q)
    ans = st.text_input("Answer")

    if st.button("Submit Answer"):
        if ans.strip() == st.session_state.a:
            st.success("Door opened! ✅")
            st.session_state.word_index += 1
        else:
            st.error("Wrong! Lost a life ❌")
            st.session_state.lives -= 1

        st.session_state.awaiting = False
        st.session_state.q = None
        st.rerun()
