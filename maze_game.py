import streamlit as st
from openai import OpenAI
import json

# -----------------------
# CONFIG
# -----------------------
st.set_page_config(page_title="Math Maze", layout="centered")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

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

GRID_SIZE = 3
GOAL = [1, 1]

# -----------------------
# INIT STATE
# -----------------------
def init():
    defaults = {
        "chapter": None,
        "player_pos": [0, 0],
        "visited": {(0, 0)},
        "lives": 3,
        "score": 0,
        "difficulty": 1,
        "question": None,
        "answer": None,
        "awaiting_answer": False,
        "next_pos": None
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init()

# -----------------------
# AI FUNCTIONS
# -----------------------
def generate_question(chapter):
    level = round(st.session_state.difficulty)

    prompt = f"""
    Generate ONE math question.

    Topic: {chapter}
    Difficulty: {level} (1 easy → 5 hard)

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
            "content": f"Question: {q}\nAnswer: {a}\nGive a short hint for a child."
        }]
    )
    return res.choices[0].message.content


def adjust_difficulty(correct):
    if correct:
        st.session_state.difficulty += 0.2
    else:
        st.session_state.difficulty = max(1, st.session_state.difficulty - 0.3)

# -----------------------
# MAZE DRAW
# -----------------------
def draw_maze():
    st.markdown("### 🗺️ Maze")

    for i in range(GRID_SIZE):
        cols = st.columns(GRID_SIZE)
        for j in range(GRID_SIZE):

            is_player = [i, j] == st.session_state.player_pos
            is_goal = [i, j] == GOAL
            visited = (i, j) in st.session_state.visited

            if not visited:
                color = "#111"
                content = ""
            else:
                if is_player:
                    color = "#4CAF50"
                    content = "🧙"
                elif is_goal:
                    color = "#FF5722"
                    content = "🔥"
                else:
                    color = "#2196F3"
                    content = ""

            cols[j].markdown(f"""
                <div style="
                    height:80px;
                    background:{color};
                    border-radius:10px;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    font-size:28px;
                ">
                    {content}
                </div>
            """, unsafe_allow_html=True)

# -----------------------
# MOVES
# -----------------------
def get_moves():
    r, c = st.session_state.player_pos
    moves = []

    if r > 0:
        moves.append(("⬆️ Up", [r-1, c]))
    if r < GRID_SIZE - 1:
        moves.append(("⬇️ Down", [r+1, c]))
    if c > 0:
        moves.append(("⬅️ Left", [r, c-1]))
    if c < GRID_SIZE - 1:
        moves.append(("➡️ Right", [r, c+1]))

    return moves

# -----------------------
# UI
# -----------------------
st.title("🧩 Math Maze: Exorcism Quest")

# -----------------------
# CHAPTER SELECT
# -----------------------
if not st.session_state.chapter:
    st.subheader("Choose your Chapter")
    ch = st.selectbox("Select Topic", CHAPTERS)

    if st.button("Enter Maze"):
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

    if st.button("Restart"):
        st.session_state.clear()
        st.rerun()

    st.stop()

# -----------------------
# DRAW MAZE
# -----------------------
draw_maze()

st.divider()

# -----------------------
# WIN
# -----------------------
if st.session_state.player_pos == GOAL:
    st.success("🔥 FINAL ROOM")

    q, a = generate_question(st.session_state.chapter)
    st.write(q)

    user = st.text_input("Final Answer")

    if st.button("Perform Exorcism"):
        if user.strip() == a.strip():
            st.success("✨ YOU WIN!")
        else:
            st.error("❌ Failed!")

    st.stop()

# -----------------------
# MOVEMENT
# -----------------------
st.markdown("## 🚪 Choose Direction")

for label, pos in get_moves():
    if st.button(label):
        st.session_state.next_pos = pos
        q, a = generate_question(st.session_state.chapter)
        st.session_state.question = q
        st.session_state.answer = a
        st.session_state.awaiting_answer = True
        st.rerun()

# -----------------------
# QUESTION GATE
# -----------------------
if st.session_state.awaiting_answer:
    st.markdown("## 🧠 Solve to Move")

    st.write(st.session_state.question)
    user = st.text_input("Your Answer")

    if st.button("Submit"):
        correct = user.strip() == st.session_state.answer.strip()

        adjust_difficulty(correct)

        if correct:
            st.success("🚪 Unlocked!")
            st.balloons()

            st.session_state.player_pos = st.session_state.next_pos
            st.session_state.visited.add(tuple(st.session_state.player_pos))

            st.session_state.score += int(10 * st.session_state.difficulty)
            st.session_state.awaiting_answer = False
            st.rerun()
        else:
            st.error("👻 Wrong!")
            st.session_state.lives -= 1

            hint = generate_hint(
                st.session_state.question,
                st.session_state.answer
            )
            st.info(f"💡 {hint}")
