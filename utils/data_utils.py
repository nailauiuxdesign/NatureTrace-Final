import streamlit as st
from utils.image_utils import process_images, is_duplicate_image
from utils.llama_utils import generate_animal_facts
from utils.data_utils import save_to_snowflake, fetch_dashboard_data
from utils.sound_utils import generate_animal_sound
import os
from PIL import Image

st.set_page_config(layout="wide", page_title="Animal Insight | NatureTrace")


# Sidebar navigation
st.sidebar.title("🌿 Animal Insight")
page = st.sidebar.radio("Go to", ["Home", "Dashboard"])

if "uploaded_images" not in st.session_state:
    st.session_state.uploaded_images = {}

uploaded_images = st.session_state.uploaded_images
snowflake_ready = st.secrets.get("snowflake_account") is not None

def display_image_preview(img):
    st.image(img, use_container_width=True)

def handle_upload():
    uploaded_files = st.file_uploader("Upload up to 5 animal images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    if uploaded_files:
        if len(uploaded_images) + len(uploaded_files) > 5:
            st.warning("You can upload a maximum of 5 images.")
            return

        for file in uploaded_files:
            image = Image.open(file)
            if is_duplicate_image(image, uploaded_images):
                st.warning(f"❗ Duplicate image detected: {file.name}")
                continue

            animal_info = process_images(image)
            facts = generate_animal_facts(animal_info['name'])
            sound_url = generate_animal_sound(animal_info['name'])

            uploaded_images[file.name] = {
                "image": image,
                "name": animal_info['name'],
                "description": animal_info['description'],
                "facts": facts,
                "sound": sound_url,
                "added": False
            }

if page == "Home":
    st.title("🧠 Animal Insight — Discover & Explore")
    col1, col2 = st.columns([1, 1.5])

    with col1:
        handle_upload()

    with col2:
        if uploaded_images:
            st.subheader("Recognized Animals")
            for filename, data in uploaded_images.items():
                st.markdown(f"### {data['name']}")
                st.image(data['image'], use_container_width=False, width=250)
                st.write(data['description'])
                st.markdown(f"**Fun Fact**: {data['facts']}")
                if data['sound']:
                    st.audio(data['sound'], format='audio/mp3')

                if not data.get("added") and st.button(f"Add to Dashboard: {data['name']}", key=filename):
                    if snowflake_ready:
                        save_to_snowflake(filename, data)
                        data["added"] = True
                        st.success(f"✅ {data['name']} added to dashboard!")
                    else:
                        st.warning("❄️ Snowflake is not configured. Please check secrets.toml")
        else:
            st.info("Upload images to see animal details.")

elif page == "Dashboard":
    st.title("📊 Animal Dashboard")
    if not snowflake_ready:
        st.warning("Snowflake not configured. Please check secrets.toml")
    else:
        chart_data = fetch_dashboard_data()

        if chart_data:
            for chart in chart_data:
                st.plotly_chart(chart)
        else:
            st.info("No data found in Snowflake. Upload animals on Home page first.")
