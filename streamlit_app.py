import streamlit as st
import pandas as pd

st.set_page_config(page_title="Offer Writing Assistant", layout="wide")
st.title("Offer Writing Assistant")

CSV_FILE = "Offer Writing Assistance Data - Step Log (2).csv"

@st.cache_data
def load_data():
    df = pd.read_csv(CSV_FILE).fillna("")
    df["Step_ID"] = df["Step_ID"].astype(int)

    def parse_step(val):
        val = str(val).strip()
        if val == "" or val.lower() == "nan":
            return None
        return int(float(val))

    df["Next_If_Yes"] = df["Next_If_Yes"].apply(parse_step)
    df["Next_If_No"] = df["Next_If_No"].apply(parse_step)
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

def collect_conditional_steps(start_steps, rows_by_id):
    queue = list(start_steps)
    visited = set()
    conditional_steps = []

    while queue:
        step_id = queue.pop(0)

        if step_id is None or step_id in visited or step_id not in rows_by_id:
            continue

        visited.add(step_id)
        row = rows_by_id[step_id]

        if str(row["Question_Group"]).strip().lower() != "core":
            conditional_steps.append(step_id)

        next_yes = row["Next_If_Yes"]
        next_no = row["Next_If_No"]

        if next_yes is not None and next_yes not in visited:
            queue.append(next_yes)
        if next_no is not None and next_no not in visited:
            queue.append(next_no)

    return conditional_steps

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

if st.button("Load Conditional Questions", type="primary"):
    start_steps = []

    for _, row in core_df.iterrows():
        step_id = int(row["Step_ID"])
        answer = core_answers[step_id]

        if answer == "Yes":
            if row["Next_If_Yes"] is not None:
                start_steps.append(row["Next_If_Yes"])
        else:
            if row["Next_If_No"] is not None:
                start_steps.append(row["Next_If_No"])

    conditional_steps = collect_conditional_steps(start_steps, rows_by_id)
    st.session_state["conditional_steps"] = conditional_steps
    st.session_state["loaded_conditionals"] = True

if st.session_state.get("loaded_conditionals"):
    conditional_steps = st.session_state.get("conditional_steps", [])

    if conditional_steps:
        st.subheader("Conditional Questions")

        conditional_answers = {}
        for step_id in conditional_steps:
            row = rows_by_id[step_id]
            question = clean_question(row["Question"])
            conditional_answers[step_id] = st.radio(
                question,
                ["No", "Yes"],
                horizontal=True,
                key=f"cond_{step_id}"
            )

        if st.button("Generate Final Output"):
            output_log = []

            # Core outputs
            for _, row in core_df.iterrows():
                step_id = int(row["Step_ID"])
                answer = core_answers[step_id]

                if answer == "Yes":
                    append_output(output_log, row["Output_If_Yes"])
                else:
                    append_output(output_log, row["Output_If_No"])

            # Conditional outputs
            for step_id in conditional_steps:
                row = rows_by_id[step_id]
                answer = conditional_answers[step_id]

                if answer == "Yes":
                    append_output(output_log, row["Output_If_Yes"])
                else:
                    append_output(output_log, row["Output_If_No"])

            st.session_state["final_output"] = output_log

if "final_output" in st.session_state:
    st.subheader("Output")
    if st.session_state["final_output"]:
        for item in st.session_state["final_output"]:
            st.markdown(item)
    else:
        st.write("No output generated.")
