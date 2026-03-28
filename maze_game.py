import streamlit as st
from openai import OpenAI
import json
import random

# -----------------------
# CONFIG
# -----------------------
st.set_page_config(page_title="Math Maze", layout="centered")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

GRID_SIZE = 3
GOAL = [1, 1]

CHAPTERS = [
    "Place Value",
    "Adding in your head",
    "Exploring addition",
    "Subtracting in your head",
    "Exploring subtraction",
    "Multiplying",
    "Dividing",
    "Fractions of objects"
]

# -----------------------
# INIT STATE
# -----------------------
def init():
    defaults = {
        "chapter": None,
        "player": [0, 0],
        "enemy": [2, 2],
        "visited": {(0, 0)},
        "lives": 3,
        "score": 0,
        "difficulty": 1,
        "question": None,
        "answer": None,
        "awaiting": False,
        "target": None
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init()

# -----------------------
# SOUND (simple)
# -----------------------
def play_sound(type):
    sounds = {
        "correct": "https://www.soundjay.com/buttons/sounds/button-3.mp3",
        "wrong": "https://www.soundjay.com/buttons/sounds/button-10.mp3",
        "win": "https://www.soundjay.com/misc/sounds/bell-ringing-05.mp3"
    }
    st.markdown(f"""
        <audio autoplay>
        <source src="{sounds[type]}" type="audio/mp3">
        </audio>
    """, unsafe_allow_html=True)

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
            "content": f"Question: {q}\nAnswer: {a}\nGive short hint."
        }]
    )
    return res.choices[0].message.content


def adjust_difficulty(correct):
    if correct:
        st.session_state.difficulty += 0.2
    else:
        st.session_state.difficulty = max(1, st.session_state.difficulty - 0.3)

# -----------------------
# ENEMY AI (chase player)
# -----------------------
def move_enemy():
    er, ec = st.session_state.enemy
    pr, pc = st.session_state.player

    if er < pr:
        er += 1
    elif er > pr:
        er -= 1
    elif ec < pc:
        ec += 1
    elif ec > pc:
        ec -= 1

    st.session_state.enemy = [er, ec]

# -----------------------
# DRAW MAZE (CLICKABLE)
# -----------------------
def draw_maze():
    st.markdown("### 🗺️ Maze")

    for i in range(GRID_SIZE):
        cols = st.columns(GRID_SIZE)

        for j in range(GRID_SIZE):

            pos = [i, j]
            is_player = pos == st.session_state.player
            is_enemy = pos == st.session_state.enemy
            is_goal = pos == GOAL
            visited = tuple(pos) in st.session_state.visited

            # Fog
            if not visited:
                color = "#111"
                label = ""
            else:
                if is_player:
                    color = "#4CAF50"
                    label = "🧙"
                elif is_enemy:
                    color = "#9C27B0"
                    label = "👻"
                elif is_goal:
                    color = "#FF5722"
                    label = "🔥"
                else:
                    color = "#2196F3"
                    label = ""

            if cols[j].button(label or " ", key=f"{i}-{j}"):
                handle_click(pos, visited)

            cols[j].markdown(f"""
                <div style="
                    margin-top:-65px;
                    height:65px;
                    background:{color};
                    border-radius:10px;
                "></div>
            """, unsafe_allow_html=True)

# -----------------------
# CLICK HANDLER
# -----------------------
def handle_click(pos, visited):
    pr, pc = st.session_state.player
    r, c = pos

    # Only adjacent moves allowed
    if abs(pr - r) + abs(pc - c) != 1:
        return

    st.session_state.target = pos

    q, a = generate_question(st.session_state.chapter)
    st.session_state.question = q
    st.session_state.answer = a
    st.session_state.awaiting = True

    st.rerun()

# -----------------------
# UI
# -----------------------
st.title("🧩 Math Maze: Exorcism Quest")

# -----------------------
# CHAPTER
# -----------------------
if not st.session_state.chapter:
    ch = st.selectbox("Choose Chapter", CHAPTERS)

    if st.button("Start Game"):
        st.session_state.chapter = ch
        st.rerun()

    st.stop()

# -----------------------
# HUD
# -----------------------
c1, c2, c3 = st.columns(3)
c1.metric("❤️ Lives", st.session_state.lives)
c2.metric("⭐ Score", st.session_state.score)
c3.metric("🧠 Difficulty", round(st.session_state.difficulty, 1))

st.divider()

# -----------------------
# GAME OVER
# -----------------------
if st.session_state.lives <= 0:
    st.error("💀 Game Over")
    play_sound("wrong")

    if st.button("Restart"):
        st.session_state.clear()
        st.rerun()

    st.stop()

# -----------------------
# DRAW MAZE
# -----------------------
draw_maze()

# -----------------------
# WIN
# -----------------------
if st.session_state.player == GOAL:
    st.success("🔥 FINAL ROOM")

    q, a = generate_question(st.session_state.chapter)
    st.write(q)

    user = st.text_input("Final Answer")

    if st.button("Perform Exorcism"):
        if user.strip() == a.strip():
            play_sound("win")
            st.success("✨ YOU WIN!")
        else:
            play_sound("wrong")
            st.error("❌ Failed!")

    st.stop()

# -----------------------
# QUESTION GATE
# -----------------------
if st.session_state.awaiting:
    st.markdown("## 🧠 Solve to Move")

    st.write(st.session_state.question)
    user = st.text_input("Your Answer")

    if st.button("Submit"):
        correct = user.strip() == st.session_state.answer.strip()
        adjust_difficulty(correct)

        if correct:
            play_sound("correct")
            st.success("🚪 Move successful!")

            st.session_state.player = st.session_state.target
            st.session_state.visited.add(tuple(st.session_state.player))
            st.session_state.score += int(10 * st.session_state.difficulty)

            move_enemy()

            # Enemy catches player
            if st.session_state.enemy == st.session_state.player:
                st.error("👻 The ghost caught you!")
                st.session_state.lives -= 1

            st.session_state.awaiting = False
            st.rerun()

        else:
            play_sound("wrong")
            st.error("👻 Wrong!")
            st.session_state.lives -= 1

            hint = generate_hint(
                st.session_state.question,
                st.session_state.answer
            )
            st.info(f"💡 {hint}")
