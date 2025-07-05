# app.py

import streamlit as st
from utils.image_utils import process_images, is_duplicate_image
from utils.data_utils import save_to_snowflake, fetch_dashboard_data
from utils.map_utils import get_animal_habitat_map
from utils.llama_utils import get_fun_fact, generate_description
import base64

st.set_page_config(page_title="Animal Insight", layout="wide")

# Sidebar navigation
page = st.sidebar.radio("Go to", ["Upload Images", "Animal Dashboard"])

if page == "Upload Images":
    st.title("🦁 Animal Insight - Discover & Explore")
    st.markdown("Upload up to 5 animal images to identify them and explore their world.")

    uploaded_files = st.file_uploader("Upload Animal Images", accept_multiple_files=True, type=["jpg", "jpeg", "png"])

    if uploaded_files:
        st.subheader("Recognized Animals")
        for uploaded_file in uploaded_files:
            if is_duplicate_image(uploaded_file):
                st.warning(f"{uploaded_file.name} has already been uploaded.")
                continue

            animal_name, animal_type, animal_desc = process_images(uploaded_file)
            sound_url = f"https://huggingface.co/spaces/NailaRajpoot/NatureTrace/resolve/main/assets/sounds/{animal_name.lower()}.mp3"
            map_html = get_animal_habitat_map(animal_name)
            facts = get_fun_fact(animal_name)

            col1, col2 = st.columns([1, 2])

            with col1:
                st.image(uploaded_file, caption=animal_name, use_container_width=True)
                if sound_url:
                    st.audio(sound_url, format="audio/mp3")
                st.button("Add to Dashboard", key=animal_name, on_click=lambda: save_to_snowflake(
                    filename=uploaded_file.name,
                    name=animal_name,
                    description=animal_desc,
                    facts=facts,
                    sound_url=sound_url
                ))

            with col2:
                st.markdown(f"### {animal_name}")
                st.markdown(animal_desc)
                st.markdown(f"**Fun Fact**: {facts}")
                st.components.v1.html(map_html, height=250)

elif page == "Animal Dashboard":
    st.title("📊 Animal Dashboard")
    df = fetch_dashboard_data()

    if df.empty:
        st.info("No data available yet. Upload animals to populate the dashboard.")
    else:
        st.dataframe(df, use_container_width=True)
        st.bar_chart(df['name'].value_counts())
