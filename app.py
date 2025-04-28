import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from supabase import create_client, Client

# Supabase Params
url = "https://azusyrpyjvpsepgeaebo.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF6dXN5cnB5anZwc2VwZ2VhZWJvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU1MTIzOTQsImV4cCI6MjA2MTA4ODM5NH0.efHjfgIesIoH_otrit_gxP19jYGTzAgAXin7ivhiHrU"

supabase = create_client(url, key)

# Side Bar : Choose User
st.sidebar.header("👤 Who are you?")

response = supabase.table("workouts_v2").select("user").execute()

if response.data:
    df_users = pd.DataFrame(response.data)
    user_list = sorted(df_users["user"].dropna().unique().tolist())
else:
    user_list = []
    st.info("ℹ️ No users found yet. Add a workout to begin.")

# Sidebar: User selector
selected_user = st.sidebar.selectbox("Select your name", options=[""] + user_list)
new_user = st.sidebar.text_input("Or enter a new name:")

# Determine final user name
current_user = new_user.strip() if new_user else selected_user

#Navigation Bar
st.sidebar.title("🔹 Navigate")
page = st.sidebar.radio("Go to", ["🏋️ Log Workout", "📊 Workout Stats", "📈 Progress Charts", "🗂 Workout History", "🗑️ Delete Workout"])

# Backup and Restore button
# Admin Tools - Only for "mor"
if current_user.lower() == "mor":
    st.sidebar.markdown("---")
    st.sidebar.markdown("📁 **Admin Tools**")

    # 🔹 Download backup (CSV from Supabase)
    try:
        # Pull all workouts from Supabase
        response = supabase.table("workouts_v2").select("*").execute()

        if response.data:
            df_backup = pd.DataFrame(response.data)
            csv_backup = df_backup.to_csv(index=False).encode('utf-8')

            st.sidebar.download_button(
                label="⬇️ Download All Workouts Backup (CSV)",
                data=csv_backup,
                file_name="full_workouts_backup.csv",
                mime="text/csv",
            )
        else:
            st.sidebar.info("ℹ️ No data found to backup.")

    except Exception as e:
        st.sidebar.error(f"❌ Failed to fetch backup: {e}")

    st.sidebar.markdown("🔁 **Restore (Manual Upload)**")
    uploaded_file = st.sidebar.file_uploader("Upload backup CSV file", type=["csv"])

    if "restored" not in st.session_state:
        st.session_state.restored = False

    if uploaded_file is not None and not st.session_state.restored:
        try:
            df_restore = pd.read_csv(uploaded_file)

            # 🔥 Clear existing workouts
            supabase.table("workouts_v2").delete().neq("id", 0).execute()

            # Build list of rows
            rows_to_insert = []

            for _, row in df_restore.iterrows():
                rows_to_insert.append({
                    "user": row["user"],
                    "exercise": row["exercise"],
                    "weight": row["weight"],
                    "reps": row["reps"],
                    "sets": row["sets"],
                    "date": row["date"],
                })

            # Insert all workouts at once
            response = supabase.table("workouts_v2").insert(rows_to_insert).execute()

            if response.data:
                st.sidebar.success(f"✅ Backup restored! {len(rows_to_insert)} workouts loaded.")
                st.session_state.restored = True
                # ✅ No rerun — just show message
                st.sidebar.info("✅ Restore completed! Please refresh the page to see updated workouts.")
            else:
                st.sidebar.error("❌ Failed to restore backup.")

        except Exception as e:
            st.sidebar.error(f"❌ Restore error: {e}")

    # ✅ After restoring, if user refreshes manually (F5), the app will naturally pick up the new data

# If no user selected or entered, stop the app
if not current_user:
    st.warning("Please select or enter your name in the sidebar to continue.")
    st.stop()

st.title("🏋️ Strength Training Tracker")
st.subheader("Track your workouts and see your progress")

#Load and define df
response = supabase.table("workouts_v2") \
    .select("*") \
    .eq("user", current_user) \
    .order("date", desc=True) \
    .execute()

df = pd.DataFrame(response.data)

# 🔥 Drop 'id' column if it exists
if "id" in df.columns:
    df = df.drop(columns=["id"])

# Get list of previous exercises
previous_exercises = df["exercise"].unique().tolist() if not df.empty else []

# Initialize session state for form inputs if not already set
if "exercise_input" not in st.session_state:
    st.session_state.exercise_input = ""

if "weight_input" not in st.session_state:
    st.session_state.weight_input = 0.0

if "reps_input" not in st.session_state:
    st.session_state.reps_input = 1

if "sets_input" not in st.session_state:
    st.session_state.sets_input = 1

if "just_logged_workout" not in st.session_state:
    st.session_state.just_logged_workout = False

# 🔥 Reset fields if workout just logged
if st.session_state.just_logged_workout:
    st.session_state.exercise_input = ""
    st.session_state.weight_input = 0.0
    st.session_state.reps_input = 1
    st.session_state.sets_input = 1
    st.session_state.just_logged_workout = False
# Input form
if page == "🏋️ Log Workout":
    st.header("🏋️ Log a New Workout")
    # Your workout logging form here
    with st.form("log_workout"):
        # First row: Select exercise and Weight
        col1, col2 = st.columns([2, 1])  # Wider select, smaller weight

        with col1:
            if previous_exercises:
                st.caption("💡 Existing exercises (select from box) or input a new one:")
                chosen = st.selectbox(
                    "Pick from previous exercises or input a new exercise",
                    [""] + previous_exercises,
                    key="previous_exercise"
                )

                if chosen:
                    st.session_state.exercise_input = chosen

        with col2:
            # Compact weight input
            st.markdown('<div style="padding-top: 36px; width: 120px;">', unsafe_allow_html=True)
            weight = st.number_input(
                "Weight (kg)",
                min_value=0.0,
                step=0.5,
                key="weight_input"
            )
            st.markdown('</div>', unsafe_allow_html=True)

        # Second row: Exercise name input
        exercise = st.text_input(
            "Exercise Name",
            value=st.session_state.get("exercise_input", ""),
            key="exercise_input_real"
        )

        # Second row: Reps and Sets
        col3, col4 = st.columns(2)
        with col3:
            reps = st.number_input("Reps", min_value=1, step=1, key="reps_input")
        with col4:
            sets = st.number_input("Sets", min_value=1, step=1, key="sets_input")

        # Centered Log Workout button

        # Create a container
        button_container = st.container()

        # Inside the container: center the button
        with button_container:
            centered_button = st.columns(5)  # Three columns
            with centered_button[2]:  # Middle column
                submit = st.form_submit_button("Log Workout")

        if submit:
            try:
                final_exercise = exercise.strip()

                if not final_exercise:
                    st.warning("⚠️ Please enter a valid exercise name!")
                    st.stop()

                response = supabase.table("workouts_v2").insert({
                    "user": current_user,
                    "exercise": final_exercise,
                    "weight": st.session_state.weight_input,
                    "reps": st.session_state.reps_input,
                    "sets": st.session_state.sets_input,
                    "date": datetime.today().date().isoformat()
                }).execute()

                st.success(f"✅ Workout logged for {current_user}!")

                st.session_state.exercise_input = ""
                st.session_state.exercise_input_real = ""
                st.session_state.previous_exercise = ""
                st.session_state.weight_input = 0.0
                st.session_state.reps_input = 1
                st.session_state.sets_input = 1
                st.session_state.just_logged_workout = True
                st.rerun()

            except Exception as e:
                st.error(f"❌ Failed to log workout: {e}")
# Workout Stats
elif page == "📊 Workout Stats":
    if not df.empty :
        st.header("📊 Your Workout Stats")
        first_date = df["date"].min()
        last_date = df["date"].max()
        total_sessions = len(df)

        # Display metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("🏋️‍♂️ Total Sessions", total_sessions)
        col2.metric("📅 First Logged Workout", first_date)
        col3.metric("📅 Latest Logged Workout", last_date)

        # Group by exercise and get max weight
        best_lifts = df.groupby('exercise')['weight'].max().reset_index()

        st.subheader("🏆 Personal Records (Best Lifts)")
        st.dataframe(best_lifts)

#Progress Charts
elif page == "📈 Progress Charts":
    st.header("📈 Progress Charts")

    if not df.empty:
        selected_exercise = st.selectbox("Choose exercise to visualize:", df["exercise"].unique())

        exercise_df = df[df["exercise"] == selected_exercise].copy()
        exercise_df = exercise_df.sort_values("date")
        exercise_df["date_str"] = pd.to_datetime(exercise_df["date"]).dt.strftime('%Y-%m-%d')

        if not exercise_df.empty:
            last_session = exercise_df.iloc[-1]  # latest workout entry

            st.subheader("📝 Last Session for Selected Exercise")
            st.info(
                f"**Date:** {last_session['date']}  \n"
                f"**Weight:** {last_session['weight']} kg  \n"
                f"**Reps:** {last_session['reps']}  \n"
                f"**Sets:** {last_session['sets']}"
            )

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
                title=dict(x=0.5),
                xaxis=dict(type="category", tickangle=0)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No logged sessions for this exercise yet.")
    else:
        st.info("⚠️ No workouts logged yet. Start logging to see progress!")

#Workout History
elif page == "🗂 Workout History":
    st.header("🗂 Workout History")

    if df.empty:
        st.info("No workout data yet — log something to get started!")
    else:
        st.dataframe(df.sort_values("date", ascending=False))

#Delete Log
elif page == "🗑️ Delete Workout":
    st.header("🗑️ Delete a Workout")
    if not df.empty:

        user_entries = df.copy()

        user_entries["entry_label"] = user_entries.apply(
            lambda row: f"{row['id']} | {row['date']} | {row['exercise']} ({row['weight']}kg)", axis=1
        )

        selected_label = st.selectbox("Select workout to delete:", user_entries["entry_label"])
        confirm_delete = st.checkbox("Confirm deletion")

        if st.button("Delete Workout"):
            if confirm_delete:
                try:
                    entry_id = int(selected_label.split(" | ")[0])

                    # 🔥 Just execute delete
                    supabase.table("workouts_v2").delete().eq("id", entry_id).execute()

                    st.success("✅ Workout deleted successfully!")
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Deletion failed: {e}")

            else:
                st.warning("⚠️ Please confirm before deleting.")

# Optionally close connection (safe in Streamlit app)
# conn.close()
