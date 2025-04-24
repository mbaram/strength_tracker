import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('training.db', check_same_thread=False)
c = conn.cursor()

# Create table if not exists
c.execute('''
    CREATE TABLE IF NOT EXISTS workouts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exercise TEXT,
        weight REAL,
        reps INTEGER,
        sets INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

st.title("Strength Training Tracker")

# Input form
st.header("Log a New Workout")
with st.form("log_workout"):
    exercise = st.text_input("Exercise Name", placeholder="e.g., Deadlift")
    weight = st.number_input("Weight (kg)", min_value=0.0, step=0.5)
    reps = st.number_input("Reps", min_value=1, step=1)
    sets = st.number_input("Sets", min_value=1, step=1)
    submit = st.form_submit_button("Log Workout")

    if submit:
        c.execute("INSERT INTO workouts (exercise, weight, reps, sets) VALUES (?, ?, ?, ?)",
                  (exercise, weight, reps, sets))
        conn.commit()
        st.success(f"Workout logged: {exercise} - {weight}kg x {reps} reps x {sets} sets")

# Display past logs
st.header("Workout History")
df = pd.read_sql_query("SELECT * FROM workouts ORDER BY timestamp DESC", conn)
st.dataframe(df)



st.header("📈 Progress Charts")

# Let user pick an exercise to plot
if not df.empty:
    selected_exercise = st.selectbox("Choose exercise to visualize:", df["exercise"].unique())

    # Filter data
    exercise_df = df[df["exercise"] == selected_exercise].sort_values("timestamp")

    # Line chart for weight over time
    fig = px.line(exercise_df, x="timestamp", y="weight",
                  markers=True, title=f"Weight Progress: {selected_exercise}")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Log some workouts to see charts!")

# Optionally close connection (safe in Streamlit app)
# conn.close()
