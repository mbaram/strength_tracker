import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('training.db', check_same_thread=False)
c = conn.cursor()

st.sidebar.header("👤 Who are you?")

# Load existing user list
try:
    user_list = pd.read_sql_query(
        "SELECT DISTINCT user FROM workouts WHERE user IS NOT NULL", conn)["user"].tolist()
except:
    user_list = []

# Sidebar user selector
selected_user = st.sidebar.selectbox("Select your name", options=[""] + user_list)
new_user = st.sidebar.text_input("Or enter a new name:")

# Determine final user name
current_user = new_user.strip() if new_user else selected_user

# If no user selected or entered, stop the app
if not current_user:
    st.warning("Please select or enter your name in the sidebar to continue.")
    st.stop()

# Create table if not exists
c.execute('''
    CREATE TABLE IF NOT EXISTS workouts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exercise TEXT,
        weight REAL,
        reps INTEGER,
        sets INTEGER,
        date DATE DEFAULT (DATE('now'))
    )
''')
conn.commit()

# Add user column if it doesn't exist
try:
    c.execute("ALTER TABLE workouts ADD COLUMN user TEXT")
    conn.commit()
except sqlite3.OperationalError:
    pass  # Ignore if it already exists

st.title("🏋️ Strength Training Tracker")
st.subheader("Track your workouts and see your progress")

# Input form
st.header("Log a New Workout")
with st.form("log_workout"):

    col1, col2 = st.columns(2)
    with col1:
        exercise = st.text_input("Exercise Name", placeholder="e.g., Bench Press")
    with col2:
        weight = st.number_input("Weight (kg)", min_value=0.0, step=0.5)

    reps = st.number_input("Reps", min_value=1, step=1)
    sets = st.number_input("Sets", min_value=1, step=1)
    submit = st.form_submit_button("Log Workout")

    if submit:
        c.execute("INSERT INTO workouts (user, exercise, weight, reps, sets) VALUES (?, ?, ?, ?, ?)",
                  (current_user, exercise, weight, reps, sets))
        conn.commit()
        st.success(f"Workout logged for {current_user}!")

# Display past logs
st.header("Workout History")

# Load data from the database
df = pd.read_sql_query("SELECT * FROM workouts ORDER BY date DESC", conn)
df = df[df["user"] == current_user]

# Show only the data for the current user
if not df.empty and "user" in df.columns:
    df = df[df["user"] == current_user]
    st.dataframe(df)
else:
    st.info("No workout data yet — log something to get started!")

# 🔹 Add metrics block here
if not df.empty:
    last_weight = df.iloc[0]["weight"]
    max_lift = df["weight"].max()

    col1, col2, col3 = st.columns(3)
    col1.metric("Last Weight", f"{last_weight} kg")
    col2.metric("Best Lift", f"{max_lift} kg")
    col3.metric("Logged Sessions", len(df))

st.header("📈 Progress Charts")

if not df.empty:
    selected_exercise = st.selectbox("Choose exercise to visualize:", df["exercise"].unique())

    exercise_df = df[df["exercise"] == selected_exercise].copy()

    # Ensure date column is sorted and clean
    exercise_df = exercise_df.sort_values("date")
    exercise_df["date_str"] = pd.to_datetime(exercise_df["date"]).dt.strftime('%Y-%m-%d')

    fig = px.line(
        exercise_df,
        x="date_str",
        y="weight",
        markers=True,
        title=f"{current_user}'s Progress: {selected_exercise}"
    )
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Weight (kg)",
        title=dict(x=0.5),  # Center the title
        xaxis=dict(type="category", tickangle=0)
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Log some workouts to see charts!")

# 🔹 Delete entry section
if not df.empty:
    user_entries = df.copy()  # Already filtered by current_user above

    # Build labels including the unique ID
    user_entries["entry_label"] = user_entries.apply(
        lambda row: f"{row['id']} | {row['date']} | {row['exercise']} | {row['weight']}kg × {row['reps']} × {row['sets']}",
        axis=1
    )

    selected_label = st.selectbox("Select an entry to delete:", user_entries["entry_label"].tolist())
    confirm_delete = st.checkbox("✅ Confirm deletion")

    if st.button("Delete Selected Entry", key="delete_button"):
        if confirm_delete:
            # Extract ID from the label
            entry_id = int(selected_label.split(" | ")[0])

            # Use ID to delete the exact row
            c.execute("DELETE FROM workouts WHERE id = ?", (entry_id,))
            conn.commit()

            st.success("✅ Entry deleted!")
            st.rerun()
        else:
            st.warning("⚠️ Please confirm before deleting.")

# Optionally close connection (safe in Streamlit app)
# conn.close()
