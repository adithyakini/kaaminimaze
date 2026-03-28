import streamlit as st
from openai import OpenAI
import json
import random
import string

# -----------------------
# CONFIG
# -----------------------
st.set_page_config(page_title="Math Word Maze", layout="centered")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

GRID_SIZE = 7
GOAL = [3, 3]

WORDS = [
    "APPLE", "GRAPE", "MANGO", "PEACH",
    "HOUSE", "PLANT", "TRAIN", "SNAKE",
    "WATER", "LIGHT", "EARTH", "BRIDGE",
    "FLOWER", "GARDEN", "MARKET"
]

WORD_RIDDLES = {
    "APPLE": "I am a fruit that keeps the doctor away 🍎",
    "GRAPE": "I grow in bunches and can become wine 🍇",
    "MANGO": "I am the king of fruits in India 🥭",
    "PEACH": "I am soft, sweet, and fuzzy 🍑",
    "HOUSE": "You live inside me 🏠",
    "PLANT": "I grow in soil and need sunlight 🌱",
    "TRAIN": "I run on tracks and carry people 🚆",
    "SNAKE": "I slither and hiss 🐍",
    "WATER": "You drink me every day 💧",
    "LIGHT": "I help you see in the dark 💡",
    "EARTH": "You live on me 🌍",
    "BRIDGE": "I connect two places 🌉",
    "FLOWER": "I bloom and smell nice 🌸",
    "GARDEN": "A place full of plants 🌿",
    "MARKET": "You buy things here 🛒"
}

CHAPTERS = [
    "Place Value",
    "Addition",
    "Subtraction",
    "Multiplication",
    "Division"
]

# -----------------------
# INIT STATE
# -----------------------
def init():
    defaults = {
        "chapter": None,
        "player": [0, 0],
        "enemy": [6, 6],
        "visited": {(0, 0)},
        "path": [],
        "current_word": "",
        "letter_grid": None,
        "valid_words": [],
        "target_word": None,
        "awaiting": False,
        "question": None,
        "answer": None,
        "lives": 3,
        "score": 0,
        "difficulty": 1
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init()

# -----------------------
# GENERATE MAZE
# -----------------------
def generate_letter_maze():
    grid = [["" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    placed_words = []

    for word in random.sample(WORDS, 4):
        for _ in range(200):
            r = random.randint(0, GRID_SIZE - 1)
            c = random.randint(0, GRID_SIZE - 1)
            direction = random.choice([(0,1),(1,0),(0,-1),(-1,0)])

            positions = []
            rr, cc = r, c

            for ch in word:
                if 0 <= rr < GRID_SIZE and 0 <= cc < GRID_SIZE:
                    positions.append((rr, cc))
                    rr += direction[0]
                    cc += direction[1]
                else:
                    break

            if len(positions) == len(word):
                for (rr, cc), ch in zip(positions, word):
                    grid[rr][cc] = ch
                placed_words.append(word)
                break

    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if grid[i][j] == "":
                grid[i][j] = random.choice(string.ascii_uppercase)

    return grid, placed_words

if st.session_state.letter_grid is None:
    grid, words = generate_letter_maze()
    st.session_state.letter_grid = grid
    st.session_state.valid_words = words
    st.session_state.target_word = random.choice(words)

# -----------------------
# AI
# -----------------------
def generate_question(chapter):
    level = round(st.session_state.difficulty)

    prompt = f"""
    Generate ONE math question.
    Topic: {chapter}
    Difficulty: {level}

    Return JSON:
    {{
      "question": "...",
      "answer": "..."
    }}
    """

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    data = json.loads(res.choices[0].message.content)
    return data["question"], str(data["answer"])

def generate_hint(q, a):
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"Question: {q}\nAnswer: {a}\nGive hint."
        }]
    )
    return res.choices[0].message.content

def adjust_difficulty(correct):
    if correct:
        st.session_state.difficulty += 0.2
    else:
        st.session_state.difficulty = max(1, st.session_state.difficulty - 0.3)

# -----------------------
# ENEMY
# -----------------------
def move_enemy():
    er, ec = st.session_state.enemy
    pr, pc = st.session_state.player

    if er < pr: er += 1
    elif er > pr: er -= 1
    elif ec < pc: ec += 1
    elif ec > pc: ec -= 1

    st.session_state.enemy = [er, ec]

# -----------------------
# DRAW GRID
# -----------------------
def draw_maze():
    st.markdown("### 🔤 Word Maze")

    for i in range(GRID_SIZE):
        cols = st.columns(GRID_SIZE)

        for j in range(GRID_SIZE):
            letter = st.session_state.letter_grid[i][j]
            pos = (i, j)

            is_player = [i, j] == st.session_state.player
            is_enemy = [i, j] == st.session_state.enemy
            in_path = pos in st.session_state.path

            if is_player:
                label = f"🧙 {letter}"
            elif is_enemy:
                label = f"👻 {letter}"
            elif in_path:
                label = f"🟨 {letter}"
            else:
                label = letter

            if cols[j].button(label, key=f"{i}-{j}", use_container_width=True):
                handle_click(pos)

# -----------------------
# HANDLE CLICK
# -----------------------
def handle_click(pos):
    pr, pc = st.session_state.player
    r, c = pos

    if abs(pr - r) + abs(pc - c) != 1:
        return

    if pos in st.session_state.path:
        return

    st.session_state.player = [r, c]
    st.session_state.path.append(pos)

    letter = st.session_state.letter_grid[r][c]
    st.session_state.current_word += letter

    st.rerun()

# -----------------------
# UI
# -----------------------
st.title("🧩 Math Word Maze")

if not st.session_state.chapter:
    ch = st.selectbox("Choose Chapter", CHAPTERS)
    if st.button("Start Game"):
        st.session_state.chapter = ch
        st.rerun()
    st.stop()

# HUD
c1, c2, c3 = st.columns(3)
c1.metric("❤️ Lives", st.session_state.lives)
c2.metric("⭐ Score", st.session_state.score)
c3.metric("🧠 Difficulty", round(st.session_state.difficulty, 1))

st.divider()

# GAME OVER
if st.session_state.lives <= 0:
    st.error("💀 Game Over")
    if st.button("Restart"):
        st.session_state.clear()
        st.rerun()
    st.stop()

# RIDDLE
st.markdown("## 🧩 Riddle Hint")
riddle = WORD_RIDDLES.get(st.session_state.target_word, "Find the hidden word!")
st.info(f"💡 {riddle}")
st.caption(f"Word length: {len(st.session_state.target_word)}")

# DRAW
draw_maze()

# WORD DISPLAY
st.markdown(f"### 🔤 Current Word: `{st.session_state.current_word}`")

# CONTROLS
c1, c2, c3 = st.columns(3)

with c1:
    if st.button("↩️ Undo"):
        if st.session_state.path:
            st.session_state.path.pop()
            st.session_state.current_word = st.session_state.current_word[:-1]
            if st.session_state.path:
                st.session_state.player = list(st.session_state.path[-1])
            else:
                st.session_state.player = [0, 0]
            st.rerun()

with c2:
    if st.button("🧹 Clear"):
        st.session_state.path = []
        st.session_state.current_word = ""
        st.rerun()

with c3:
    if st.button("🔄 New Maze"):
        grid, words = generate_letter_maze()
        st.session_state.letter_grid = grid
        st.session_state.valid_words = words
        st.session_state.target_word = random.choice(words)
        st.session_state.player = [0, 0]
        st.session_state.path = []
        st.session_state.current_word = ""
        st.rerun()

# WORD CHECK
if st.session_state.current_word == st.session_state.target_word:
    st.success(f"🎉 Solved: {st.session_state.target_word}")

    if not st.session_state.awaiting:
        q, a = generate_question(st.session_state.chapter)
        st.session_state.question = q
        st.session_state.answer = a
        st.session_state.awaiting = True

elif len(st.session_state.current_word) > len(st.session_state.target_word):
    st.warning("❌ Not matching riddle. Reset.")
    st.session_state.path = []
    st.session_state.current_word = ""

# QUESTION GATE
if st.session_state.awaiting:
    st.markdown("## 🚪 Solve to Unlock")

    st.write(st.session_state.question)
    user = st.text_input("Answer")

    if st.button("Submit"):
        correct = user.strip() == st.session_state.answer.strip()
        adjust_difficulty(correct)

        if correct:
            st.success("🚪 Unlocked!")
            st.session_state.score += int(10 * st.session_state.difficulty)

            st.session_state.path = []
            st.session_state.current_word = ""
            st.session_state.awaiting = False

            st.session_state.target_word = random.choice(st.session_state.valid_words)

            move_enemy()

            if st.session_state.enemy == st.session_state.player:
                st.error("👻 Ghost caught you!")
                st.session_state.lives -= 1

            st.rerun()
        else:
            st.error("👻 Wrong!")
            st.session_state.lives -= 1

            hint = generate_hint(
                st.session_state.question,
                st.session_state.answer
            )
            st.info(f"💡 {hint}")
