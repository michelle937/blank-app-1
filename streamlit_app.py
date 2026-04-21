import streamlit as st
import pandas as pd

st.set_page_config(page_title="Offer Writing Assistant", layout="wide")
st.title("Offer Writing Assistant")

CSV_FILE = "Offer Writing Assistance Data - Step Log (2).csv"

@st.cache_data
def load_data():
    df = pd.read_csv(CSV_FILE).fillna("")
    df["Step_ID"] = df["Step_ID"].astype(int)
    df["Next_If_Yes"] = df["Next_If_Yes"].apply(lambda x: int(x) if str(x).strip() not in ["", "nan"] else None)
    df["Next_If_No"] = df["Next_If_No"].apply(lambda x: int(x) if str(x).strip() not in ["", "nan"] else None)
    return df

df = load_data()
rows_by_id = {int(row["Step_ID"]): row for _, row in df.iterrows()}
core_df = df[df["Question_Group"].str.strip().str.lower() == "core"].sort_values("Step_ID")

def clean_question(text):
    text = str(text).strip()
    if text and not text.endswith("?"):
        text += "?"
    return text

def append_output(output_list, text):
    text = str(text).strip()
    if text:
        output_list.append(text)

st.subheader("Core Questions")

core_answers = {}
for _, row in core_df.iterrows():
    step_id = int(row["Step_ID"])
    question = clean_question(row["Question"])
    core_answers[step_id] = st.radio(
        question,
        ["No", "Yes"],
        horizontal=True,
        key=f"core_{step_id}"
    )

if st.button("Generate Offer Guidance", type="primary"):
    output_log = []
    queue = []
    visited = set()

    for _, row in core_df.iterrows():
        step_id = int(row["Step_ID"])
        answer = core_answers[step_id]

        if answer == "Yes":
            append_output(output_log, row["Output_If_Yes"])
            if row["Next_If_Yes"] is not None:
                queue.append(row["Next_If_Yes"])
        else:
            append_output(output_log, row["Output_If_No"])
            if row["Next_If_No"] is not None:
                queue.append(row["Next_If_No"])

    st.session_state["queue"] = queue
    st.session_state["visited"] = visited
    st.session_state["output_log"] = output_log
    st.session_state["rows_by_id"] = rows_by_id
    st.session_state["started"] = True

if st.session_state.get("started"):
    queue = st.session_state.get("queue", [])
    visited = st.session_state.get("visited", set())
    output_log = st.session_state.get("output_log", [])
    rows_by_id = st.session_state.get("rows_by_id", {})

    st.subheader("Conditional Questions")

    idx = 0
    while idx < len(queue):
        step_id = queue[idx]

        if step_id in visited or step_id not in rows_by_id:
            idx += 1
            continue

        row = rows_by_id[step_id]
        visited.add(step_id)

        question = clean_question(row["Question"])
        answer = st.radio(
            question,
            ["No", "Yes"],
            horizontal=True,
            key=f"cond_{step_id}"
        )

        if answer == "Yes":
            append_output(output_log, row["Output_If_Yes"])
            next_step = row["Next_If_Yes"]
        else:
            append_output(output_log, row["Output_If_No"])
            next_step = row["Next_If_No"]

        if next_step is not None and next_step not in visited and next_step not in queue:
            queue.append(next_step)

        idx += 1

    st.subheader("Output")

    if output_log:
        for item in output_log:
            st.markdown(item)
    else:
        st.write("No output generated.")
