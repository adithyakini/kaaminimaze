import streamlit as st
import random
import string
import time
from openai import OpenAI
import json
import os
import base64

# ------------------------
# UTIL
# ------------------------
def get_base64_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def play_autoplay_sound_base64(path):
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    st.markdown(f"""
    <audio autoplay loop>
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
    </audio>
    """, unsafe_allow_html=True)

chucky_base64 = get_base64_image("chucky.png")

# ------------------------
# STYLE
# ------------------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(180deg, #0b0f1a, #111827);
    color: #e5e7eb;
}
button[kind="secondary"] {
    background-color: #1f2937 !important;
    border-radius: 10px !important;
}
button:hover {
    border: 1px solid #22c55e !important;
}
</style>
""", unsafe_allow_html=True)

# ------------------------
# CONFIG
# ------------------------
GRID_SIZE = 10
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
level = st.selectbox("Difficulty", ["easy","medium","hard"])

# ------------------------
# SIDEBAR
# ------------------------
with st.sidebar:
    st.title("📖 The Story")
    st.markdown("""
    👹 Chucky is back causing chaos and hurting children.

    🦸‍♀️ Avika must perform an exorcism.

    ⚡ To reach him, she must solve word paths through a maze.

    👻 Reach the exit and banish him forever.
    """)

    st.title("🧠 How to Play")
    st.markdown("""
    - Enter through the gate 🚪  
    - Follow correct path  
    - Complete words  
    - Avoid wrong tiles  
    - Reach the ghost 👻  
    """)

# ------------------------
# WORDS
# ------------------------
def get_words(level):
    if level == "easy":
        rule = "exactly 4 letter simple words"
    elif level == "medium":
        rule = "exactly 5 letter words"
    else:
        rule = "6+ letter words"

    prompt = f"""
    Generate 10 words:
    - {rule}
    - common and easy
    - no duplicates
    """

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.8,
        messages=[{"role": "user", "content": prompt}]
    )

    return [w.strip().upper() for w in res.choices[0].message.content.split(",")]

# ------------------------
# PATH
# ------------------------
def generate_path():
    path, visited = [], set()
    x,y = 0,0
    path.append((x,y))
    visited.add((x,y))

    while y < GRID_SIZE-1:
        moves = [(1,0),(-1,0),(0,1)]
        random.shuffle(moves)

        for dx,dy in moves:
            nx,ny = x+dx,y+dy
            if 0<=nx<GRID_SIZE and 0<=ny<GRID_SIZE and (nx,ny) not in visited:
                x,y = nx,ny
                path.append((x,y))
                visited.add((x,y))
                break
        else:
            y+=1
            path.append((x,y))
            visited.add((x,y))

    return path

def embed(path, words):
    grid = [[random.choice(string.ascii_uppercase) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    i=0
    for w in words:
        for ch in w:
            if i>=len(path): return grid
            x,y = path[i]
            grid[x][y] = ch
            i+=1
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
        "current_word_index": 0,
        "letters_progress": 0,
        "completed_words": set(),
        "user_interacted": False,
        "jump_done": False,
        "level": level,
        "init": True
    })

# ------------------------
# JUMP SCARE
# ------------------------
if not st.session_state.jump_done:
    st.session_state.jump_done = True

    st.markdown(f"""
    <style>
    .jump {{
        position: fixed;
        top:50%; left:50%;
        transform:translate(-50%,-50%);
        animation: jump 1s forwards;
        z-index:1000;
    }}
    @keyframes jump {{
        0% {{ transform: scale(0.2); opacity:0; }}
        100% {{ transform: scale(2.5); opacity:1; }}
    }}
    </style>
    <div class="jump">
        <img src="data:image/png;base64,{chucky_base64}" width="400">
    </div>
    """, unsafe_allow_html=True)

# ------------------------
# UI
# ------------------------
st.title("🧙 Om Bhool Bhulaiya Swaahaa")

elapsed = int(time.time() - st.session_state.start_time)
st.write(f"⏱ {elapsed}s ❤️ {st.session_state.lives}")

# ------------------------
# CHUCKY NEAR EXIT
# ------------------------
exit_row = st.session_state.exit[0]
y_percent = 10 + (exit_row / GRID_SIZE) * 70

st.markdown(f"""
<style>
.chucky {{
    position: fixed;
    top: {y_percent}vh;
    left: 92vw;
    transform: translate(-50%, -50%);
    animation: pulse 2s infinite;
}}
@keyframes pulse {{
    0% {{ transform: translate(-50%, -50%) scale(1); }}
    50% {{ transform: translate(-50%, -50%) scale(1.6); }}
    100% {{ transform: translate(-50%, -50%) scale(1); }}
}}
</style>
<div class="chucky">
    <img src="data:image/png;base64,{chucky_base64}" width="100">
</div>
""", unsafe_allow_html=True)

# ------------------------
# WORD DISPLAY
# ------------------------
display = []
for i,w in enumerate(st.session_state.words):
    if i in st.session_state.completed_words:
        display.append(w)
    elif i == st.session_state.current_word_index:
        revealed = "".join([c+" " if j < st.session_state.letters_progress else "_ " for j,c in enumerate(w)])
        display.append("👉 "+revealed.strip())
    else:
        hint = ["_"]*len(w)
        hint[0]=w[0]
        hint[len(w)//2]=w[len(w)//2]
        display.append(" ".join(hint))

st.write(" → ".join(display))

# ------------------------
# GRID
# ------------------------
grid = st.session_state.grid
path = st.session_state.path
idx = st.session_state.index

for i in range(GRID_SIZE):
    cols = st.columns(GRID_SIZE+2)

    for j in range(GRID_SIZE+2):

        if j==0:
            cols[j].button("🚪🧙" if i==st.session_state.entry[0] and idx==-1 else "", key=f"{i}-e")
            continue

        if j==GRID_SIZE+1:
            cols[j].button("👻🚪" if i==st.session_state.exit[0] else "", key=f"{i}-x")
            continue

        x,y=i,j-1
        base = grid[x][y]

        if idx>=0 and (x,y)==path[idx]:
            label="🧙"
        elif idx>0 and (x,y) in path[:idx]:
            label=f"🟩{base}"
        elif (x,y) in st.session_state.wrong_tiles:
            label=f"🟥{base}"
        else:
            label=base

        if cols[j].button(label, key=f"{x}-{y}"):

            if not st.session_state.user_interacted:
                st.session_state.user_interacted=True
                play_autoplay_sound_base64("chucky_laugh.mp3")

            if idx==-1:
                if (x,y)==st.session_state.entry:
                    st.session_state.index=0
                    st.rerun()
            else:
                next_idx = idx+1
                if next_idx < len(path) and (x,y)==path[next_idx]:
                    st.session_state.index+=1
                    st.session_state.letters_progress+=1

                    total=0
                    for i,w in enumerate(st.session_state.words):
                        total+=len(w)
                        if st.session_state.index==total-1:
                            st.session_state.completed_words.add(i)
                            st.session_state.current_word_index=i+1
                            st.session_state.letters_progress=0
                            break

                    st.rerun()
                else:
                    st.session_state.lives-=1
                    st.session_state.wrong_tiles.add((x,y))
