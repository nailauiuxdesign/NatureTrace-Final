# app.py

import streamlit as st
from utils.image_utils import process_images, is_duplicate_image
from utils.data_utils import save_to_snowflake, fetch_dashboard_data
from utils.map_utils import get_animal_habitat_map
from utils.llama_utils import generate_animal_facts, generate_description
import base64
import time

st.set_page_config(page_title="Animal Insight", layout="wide")

# Sidebar navigation
page = st.sidebar.radio("Go to", ["Upload Images", "Animal Dashboard"])

if page == "Upload Images":
    st.title("🦁 Animal Insight - Discover & Explore")
    st.markdown("Upload up to 5 animal images to identify them and explore their world.")

    uploaded_files = st.file_uploader("Upload Animal Images", accept_multiple_files=True, type=["jpg", "jpeg", "png"])

    if uploaded_files:
        st.subheader("🔍 Recognized Animals")
        
        # Process all images first
        processed_animals = []
        
        for uploaded_file in uploaded_files:
            # Check if it's a duplicate first
            is_duplicate = is_duplicate_image(uploaded_file)
            
            # Always process the image, even if it's a duplicate
            animal_name, animal_type, animal_desc = process_images(uploaded_file)
            sound_url = f"https://huggingface.co/spaces/NailaRajpoot/NatureTrace/resolve/main/assets/sounds/{animal_name.lower()}.mp3"
            map_html = get_animal_habitat_map(animal_name)
            facts = generate_animal_facts(animal_name)
            
            # Show toast notification for duplicates
            if is_duplicate:
                st.toast(f"🔄 {uploaded_file.name} has already been added to dashboard", icon="ℹ️")
            
            # Store processed animal data (including duplicates for display)
            processed_animals.append({
                'file': uploaded_file,
                'name': animal_name,
                'type': animal_type,
                'description': animal_desc,
                'facts': facts,
                'sound_url': sound_url,
                'map_html': map_html,
                'is_duplicate': is_duplicate
            })
        
        # Display all results - 1 image per row
        for idx, animal in enumerate(processed_animals):
            # Create two columns: image on left, content on right
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # Uniform image with fixed dimensions
                st.image(animal['file'], width=200)
                
                # Add to dashboard button with unique key
                button_key = f"dashboard_btn_{idx}_{hash(animal['file'].name)}"
                if st.button("➕ Add to Dashboard", 
                           key=button_key,
                           use_container_width=True):
                    save_to_snowflake(
                        filename=animal['file'].name,
                        name=animal['name'],
                        description=animal['description'],
                        facts=animal['facts'],
                        sound_url=animal['sound_url']
                    )
                    st.success(f"✅ {animal['name']} added to dashboard!")
            
            with col2:
                # Animal info - clean and simple
                st.markdown(f"### 🦁 {animal['name']}")
                st.markdown(f"**Type:** *{animal['type']}*")
                st.markdown(f"**Description:** {animal['description']}")
                st.markdown(f"**Fun Fact:** {animal['facts']}")
            
            st.markdown("---")  # Add separator between animals

elif page == "Animal Dashboard":
    st.title("📊 Animal Dashboard")
    df = fetch_dashboard_data()

    if df.empty:
        st.info("No data available yet. Upload animals to populate the dashboard.")
    else:
        st.dataframe(df, use_container_width=True)
        st.bar_chart(df['name'].value_counts())
