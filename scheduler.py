import streamlit as st
import datetime
from utils import load_schedule, save_schedule  # Make sure these are per-user


def scheduler_ui(selected_persona):
    user_email = st.session_state.user_data["Email"]

    if "scheduled_posts" not in st.session_state:
        st.session_state.scheduled_posts = load_schedule(user_email)

    st.subheader("📅 Schedule Your Content")

    with st.form("schedule_form"):
        post_date = st.date_input("Post Date", datetime.date.today())
        post_time = st.time_input("Post Time", datetime.datetime.now().time())
        content_idea = st.text_area(
            "What are you posting?", placeholder="Describe the scene, tease, or idea...")

        submitted = st.form_submit_button("📌 Schedule it")
        if submitted:
            new_post = {
                "datetime": f"{post_date} {post_time}",
                "idea": content_idea,
                "persona": selected_persona,
                "channel": "OnlyFans Post"
            }
            st.session_state.scheduled_posts.append(new_post)
            save_schedule(user_email, st.session_state.scheduled_posts)
            st.success("Scheduled!")

    if st.session_state.scheduled_posts:
        st.subheader("📋 Upcoming Posts")
        for post in sorted(st.session_state.scheduled_posts, key=lambda x: x["datetime"]):
            st.markdown(f"**{post['datetime']}** — {post['idea']}")
