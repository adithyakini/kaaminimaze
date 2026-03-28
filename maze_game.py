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

MAZE_LENGTH = 5

# -----------------------
# STATE INIT
# -----------------------
def init():
    defaults = {
        "chapter": None,
        "step": 0,
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
# AI: SAFE JSON GENERATION
# -----------------------
def generate_question(chapter):
    prompt = f"""
    Generate ONE simple math question for a child based on: {chapter}.

    Return STRICT JSON ONLY:
    {{
      "question": "text",
      "answer": "number or short text"
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    data = json.loads(response.choices[0].message.content)
    return data["question"], str(data["answer"])


def generate_hint(question, answer):
    prompt = f"""
    Question: {question}
    Answer: {answer}

    Give a very short hint for a child. Do NOT reveal the answer.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


# -----------------------
# UI HEADER
# -----------------------
st.title("🧩 Math Maze: Exorcism Quest")

# -----------------------
# CHAPTER SELECT
# -----------------------
if not st.session_state.chapter:
    st.subheader("Choose your Chapter")

    chapter = st.selectbox("Select Topic", CHAPTERS)

    if st.button("Enter Maze"):
        st.session_state.chapter = chapter
        st.session_state.step = 0
        st.session_state.lives = 3
        st.session_state.score = 0

        q, a = generate_question(chapter)
        st.session_state.question = q
        st.session_state.answer = a

        st.rerun()

    st.stop()

# -----------------------
# HUD
# -----------------------
col1, col2, col3 = st.columns(3)
col1.metric("❤️ Lives", st.session_state.lives)
col2.metric("⭐ Score", st.session_state.score)
col3.metric("🧭 Room", f"{st.session_state.step}/{MAZE_LENGTH}")

st.divider()

# -----------------------
# GAME OVER
# -----------------------
if st.session_state.lives <= 0:
    st.error("💀 The spirit consumed you... Game Over!")

    if st.button("Restart Game"):
        st.session_state.clear()
        st.rerun()

    st.stop()

# -----------------------
# BOSS ROOM
# -----------------------
if st.session_state.step >= MAZE_LENGTH:
    st.success("🔥 You reached the center of the maze!")

    st.markdown("## 🕯️ Final Exorcism Question")

    q, a = generate_question(st.session_state.chapter)

    st.write(q)
    user = st.text_input("Your Answer", key="boss")

    if st.button("Perform Exorcism"):
        if user.strip() == a.strip():
            st.success("✨ EXORCISM COMPLETE! You win!")
        else:
            st.error("❌ The ritual failed... try again!")

    st.stop()

# -----------------------
# NORMAL ROOM
# -----------------------
st.markdown(f"## 🚪 Room {st.session_state.step + 1}")
st.write(st.session_state.question)

user_answer = st.text_input("Your Answer", key=f"input_{st.session_state.step}")

colA, colB = st.columns(2)

with colA:
    if st.button("Submit Answer"):
        correct = st.session_state.answer

        if user_answer.strip() == correct.strip():
            st.success("✅ Door unlocked!")
            st.session_state.score += 10
            st.session_state.step += 1

            q, a = generate_question(st.session_state.chapter)
            st.session_state.question = q
            st.session_state.answer = a

            st.rerun()

        else:
            st.error("❌ Wrong! The spirit attacks!")
            st.session_state.lives -= 1

            hint = generate_hint(st.session_state.question, correct)
            st.info(f"💡 Hint: {hint}")

with colB:
    if st.button("Skip (no points)"):
        st.session_state.step += 1
        q, a = generate_question(st.session_state.chapter)
        st.session_state.question = q
        st.session_state.answer = a
        st.rerun()
