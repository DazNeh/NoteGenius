import os
import streamlit as st
import requests

st.set_page_config(page_title="NoteGenius", layout="wide")
st.title("NoteGenius")
st.markdown("Fast, clear summaries, insights & quizzes from your documents.")

@st.cache_data
def blob(uploaded):
    # Avoid re-uploading identical files on reruns
    return uploaded.getvalue()

# Form for file + task selection
with st.form("analyze"):
    file = st.file_uploader("Choose a document", type=["txt", "pdf", "docx"])
    choice = st.radio("What do you need?", ["Insights & Summary", "Quiz"])
    go = st.form_submit_button("Analyze")

if go and file:
    # Map UI choice to backend action
    action_map = {"Insights & Summary": "all", "Quiz": "quiz"}
    backend_action = action_map[choice]

    # Send file + action to API
    files = {"file": (file.name, blob(file))}
    data = {"action": backend_action}
    url = os.getenv("BACKEND_URL", "http://localhost:8000") + "/analyze"

    with st.spinner("Analyzing..."):
        res = requests.post(url, files=files, data=data)

    if res.status_code != 200:
        st.error(f"Error {res.status_code}: {res.text}")
    else:
        st.session_state["result"] = res.json()
        st.session_state["action"] = backend_action

# Once we have a result, always show it (so the quiz survives selections)
if "result" in st.session_state:
    data = st.session_state["result"]
    act = st.session_state["action"]

    if act == "all":
        st.header("Summary")
        st.markdown(data["summary"])

        st.header("Key Insights")
        for bullet in data.get("insights", []):
            st.markdown(f"- {bullet}")

    if act == "quiz":
        st.header("Quiz Time!")
        for i, q in enumerate(data.get("quiz", []), 1):
            st.subheader(f"Q{i}. {q['question']}")
            key = f"ans_{i}"
            # Initialize to placeholder if first render
            if key not in st.session_state:
                st.session_state[key] = "—"

            answer = st.selectbox("Your answer", ["—"] + q["options"], key=key)
            if answer != "—":
                idx = q["options"].index(answer)
                if idx == q["answer_index"]:
                    st.success("That’s correct!")
                else:
                    correct = q["options"][q["answer_index"]]
                    st.error(f"Oops, the right answer is: {correct}")
