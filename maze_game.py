import streamlit as st
import random
import string
import time
from openai import OpenAI

GRID_SIZE = 10
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ------------------------
# DIFFICULTY
# ------------------------
level = st.selectbox("Difficulty", ["easy","medium","hard"])

# ------------------------
# WORD GENERATION
# ------------------------
def get_words(level):

    if level == "easy":
        rule = "exactly 3 letters"
    elif level == "medium":
        rule = "4 to 5 letters"
    else:
        rule = "6 or more letters"

    prompt = f"""
    Generate 10 unique English words.

    Rules:
    - Each word must be {rule}
    - Avoid very common words like CAT, DOG, SUN
    - Return ONLY comma-separated words
    """

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.9,
        messages=[{"role": "user", "content": prompt}]
    )

    return [w.strip().upper() for w in res.choices[0].message.content.split(",")]

# ------------------------
# PATH
# ------------------------
def generate_path():
    path = []
    x, y = 0, 0
    visited = set()

    while y < GRID_SIZE - 1:
        path.append((x,y))
        visited.add((x,y))

        moves = [(1,0),(-1,0),(0,1)]
        random.shuffle(moves)

        for dx,dy in moves:
            nx,ny = x+dx,y+dy
            if 0<=nx<GRID_SIZE and 0<=ny<GRID_SIZE and (nx,ny) not in visited:
                x,y = nx,ny
                break
        else:
            y += 1

    path.append((x,y))
    return path

def embed(path, words):
    grid = [[random.choice(string.ascii_uppercase) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    i = 0
    for w in words:
        for ch in w:
            if i >= len(path):
                return grid
            x,y = path[i]
            grid[x][y] = ch
            i += 1
    return grid

# ------------------------
# INIT
# ------------------------
if "init" not in st.session_state or st.session_state.level != level:

    path = generate_path()
    words = get_words(level)
    grid = embed(path, words)

    st.session_state.update({
        "grid": grid,
        "path": path,
        "words": words,
        "entry": path[0],
        "exit": path[-1],
        "index": -1,
        "lives": 3,
        "wrong_tiles": set(),
        "start_time": time.time(),
        "finished": False,
        "current_word_index": 0,
        "letters_progress": 0,
        "completed_words": set(),
        "level": level,
        "init": True
    })

# ------------------------
# TIMER
# ------------------------
elapsed = int(time.time() - st.session_state.start_time)

# ------------------------
# UI
# ------------------------
st.title("🧙 Om Bhool Bhulaiya Swaahaa")
st.write(f"⏱ {elapsed}s ❤️ {st.session_state.lives}")

# ------------------------
# WORD DISPLAY (PARTIAL)
# ------------------------
display = []

for i, w in enumerate(st.session_state.words):

    if i in st.session_state.completed_words:
        display.append(w)

    elif i == st.session_state.current_word_index:
        reveal = "".join([
            c+" " if j < st.session_state.letters_progress else "_ "
            for j,c in enumerate(w)
        ])
        display.append("👉 " + reveal.strip())

    else:
        hint = " ".join([
            c if j in (0,len(w)-1) else "_"
            for j,c in enumerate(w)
        ])
        display.append(hint)

st.write(" → ".join(display))

# ------------------------
# GRID
# ------------------------
grid = st.session_state.grid
path = st.session_state.path
idx = st.session_state.index

for i in range(GRID_SIZE):
    cols = st.columns(GRID_SIZE + 2)

    for j in range(GRID_SIZE + 2):

        if j == 0:
            cols[j].button("🚪🧙" if i==st.session_state.entry[0] and idx==-1 else "", key=f"{i}-e")
            continue

        if j == GRID_SIZE+1:
            cols[j].button("👻🚪" if i==st.session_state.exit[0] else "", key=f"{i}-x")
            continue

        x,y = i, j-1
        base = grid[x][y]

        # wizard
        if idx >= 0 and (x,y) == path[idx]:
            label = "🧙"

        # path
        elif idx > 0 and (x,y) in path[:idx]:
            label = f"🟩{base}"

        # wrong
        elif (x,y) in st.session_state.wrong_tiles:
            label = f"🟥{base}"

        else:
            label = base

        if cols[j].button(label, key=f"{x}-{y}"):

            if idx == -1:
                if (x,y) == st.session_state.entry:
                    st.session_state.index = 0
                    st.rerun()
            else:
                next_idx = idx + 1

                if next_idx < len(path) and (x,y) == path[next_idx]:

                    st.session_state.index += 1
                    st.session_state.letters_progress += 1

                    word = st.session_state.words[st.session_state.current_word_index]

                    if st.session_state.letters_progress >= len(word):
                        st.session_state.completed_words.add(st.session_state.current_word_index)
                        st.session_state.current_word_index += 1
                        st.session_state.letters_progress = 0

                    st.rerun()

                else:
                    st.session_state.lives -= 1
                    st.session_state.wrong_tiles.add((x,y))

            if st.session_state.lives <= 0:
                st.session_state.finished = True
                st.error("💀 Game Over")
