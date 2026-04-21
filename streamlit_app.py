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
core_df = df[df["Question_Group"].astype(str).str.strip().str.lower() == "core"].sort_values("Step_ID")

def clean_question(text):
    text = str(text).strip()
    if text and not text.endswith("?"):
        text += "?"
    return text

def append_output(output_list, text):
    text = str(text).strip()
    if text:
        output_list.append(text)

def add_next_step(queue, visited, next_step):
    if next_step is not None and next_step in rows_by_id and next_step not in visited and next_step not in queue:
        queue.append(next_step)

# initialize session state
if "phase" not in st.session_state:
    st.session_state.phase = "core"

if "core_answers" not in st.session_state:
    st.session_state.core_answers = {}

if "conditional_answers" not in st.session_state:
    st.session_state.conditional_answers = {}

if "queue" not in st.session_state:
    st.session_state.queue = []

if "visited" not in st.session_state:
    st.session_state.visited = set()

if "output_log" not in st.session_state:
    st.session_state.output_log = []

# CORE PHASE
st.subheader("Core Questions")

for _, row in core_df.iterrows():
    step_id = int(row["Step_ID"])
    question = clean_question(row["Question"])

    saved_value = st.session_state.core_answers.get(step_id, "No")
    answer = st.radio(
        question,
        ["No", "Yes"],
        index=0 if saved_value == "No" else 1,
        horizontal=True,
        key=f"core_{step_id}"
    )
    st.session_state.core_answers[step_id] = answer

if st.session_state.phase == "core":
    if st.button("Start Conditional Questions", type="primary"):
        queue = []
        visited = set()

        for _, row in core_df.iterrows():
            step_id = int(row["Step_ID"])
            answer = st.session_state.core_answers[step_id]

            if answer == "Yes":
                add_next_step(queue, visited, row["Next_If_Yes"])
            else:
                add_next_step(queue, visited, row["Next_If_No"])

        st.session_state.queue = queue
        st.session_state.visited = visited
        st.session_state.phase = "conditional"

# CONDITIONAL PHASE
if st.session_state.phase == "conditional":
    if st.session_state.queue:
        current_step = st.session_state.queue[0]
        row = rows_by_id[current_step]

        # if a core row somehow appears again, use stored answer and skip asking
        if str(row["Question_Group"]).strip().lower() == "core":
            st.session_state.visited.add(current_step)
            st.session_state.queue.pop(0)

            stored_answer = st.session_state.core_answers.get(current_step, "No")
            next_step = row["Next_If_Yes"] if stored_answer == "Yes" else row["Next_If_No"]
            add_next_step(st.session_state.queue, st.session_state.visited, next_step)
            st.rerun()

        st.subheader("Conditional Question")
        st.write(clean_question(row["Question"]))

        saved_value = st.session_state.conditional_answers.get(current_step, "No")
        cond_answer = st.radio(
            "Select answer",
            ["No", "Yes"],
            index=0 if saved_value == "No" else 1,
            horizontal=True,
            key=f"cond_{current_step}"
        )

        if st.button("Next Conditional Question", type="primary"):
            st.session_state.conditional_answers[current_step] = cond_answer
            st.session_state.visited.add(current_step)
            st.session_state.queue.pop(0)

            next_step = row["Next_If_Yes"] if cond_answer == "Yes" else row["Next_If_No"]
            add_next_step(st.session_state.queue, st.session_state.visited, next_step)

            st.rerun()

    else:
        st.subheader("All conditional questions are complete")

        if st.button("Generate Final Output", type="primary"):
            output_log = []

            # core outputs
            for _, row in core_df.iterrows():
                step_id = int(row["Step_ID"])
                answer = st.session_state.core_answers.get(step_id, "No")

                if answer == "Yes":
                    append_output(output_log, row["Output_If_Yes"])
                else:
                    append_output(output_log, row["Output_If_No"])

            # conditional outputs
            for step_id, answer in st.session_state.conditional_answers.items():
                row = rows_by_id[step_id]

                if answer == "Yes":
                    append_output(output_log, row["Output_If_Yes"])
                else:
                    append_output(output_log, row["Output_If_No"])

            st.session_state.output_log = output_log
            st.session_state.phase = "done"
            st.rerun()

# FINAL OUTPUT
if st.session_state.phase == "done":
    st.subheader("Output")

    if st.session_state.output_log:
        for item in st.session_state.output_log:
            st.markdown(item)
    else:
        st.write("No output generated.")

    if st.button("Start Over"):
        for key in [
            "phase",
            "core_answers",
            "conditional_answers",
            "queue",
            "visited",
            "output_log",
        ]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
