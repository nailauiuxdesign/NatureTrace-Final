# app.py

import streamlit as st
import pandas as pd
from utils.image_utils import process_images, is_duplicate_image
from utils.data_utils import save_to_snowflake, fetch_dashboard_data
from utils.map_utils import get_animal_habitat_map
from utils.llama_utils import generate_animal_facts, generate_description
from dashboard_sound_integration import dashboard_sound_manager, streamlit_sound_management_ui

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
                auto_sound = st.checkbox("🔊 Auto-fetch sound", value=True, key=f"sound_check_{idx}")
                
                if st.button("➕ Add to Dashboard", 
                           key=button_key,
                           use_container_width=True):
                    with st.spinner(f"Adding {animal['name']} to dashboard..."):
                        # Use the enhanced function with automatic sound fetching
                        result = dashboard_sound_manager.add_animal_with_sound(
                            filename=animal['file'].name,
                            name=animal['name'],
                            description=animal['description'],
                            facts=animal['facts'],
                            category=animal['type'],
                            auto_fetch_sound=auto_sound
                        )
                    
                    if result["success"]:
                        st.success(f"✅ {animal['name']} added to dashboard!")
                        
                        # Show sound status
                        if auto_sound and result["sound_result"]:
                            if result["sound_result"]["success"]:
                                st.info(f"🔊 Sound found: {result['sound_result']['source']}")
                                # Play the sound
                                st.audio(result["sound_result"]["sound_url"])
                            else:
                                st.warning(f"⚠️ No sound found: {result['sound_result']['message']}")
                    else:
                        st.error(f"❌ Failed to add {animal['name']} to dashboard")
            
            with col2:
                # Animal info - clean and simple
                st.markdown(f"### 🦁 {animal['name']}")
                st.markdown(f"**Type:** *{animal['type']}*")
                st.markdown(f"**Description:** {animal['description']}")
                st.markdown(f"**Fun Fact:** {animal['facts']}")
            
            st.markdown("---")  # Add separator between animals

elif page == "Animal Dashboard":
    st.title("📊 Animal Dashboard")
    
    # Add sound management UI
    streamlit_sound_management_ui()
    
    st.markdown("---")  # Separator
    
    df = fetch_dashboard_data()

    if df.empty:
        st.info("No data available yet. Upload animals to populate the dashboard.")
    else:
        # Check column names (handle both NAME and name)
        name_col = 'NAME' if 'NAME' in df.columns else 'name'
        category_col = 'CATEGORY' if 'CATEGORY' in df.columns else 'category'
        
        # Group animals by category
        if category_col in df.columns:
            categories = df[category_col].dropna().unique()
            
            # Create tabs for each category
            if len(categories) > 0:
                tabs = st.tabs([f"🦁 {cat}" for cat in categories] + ["📊 All Data"])
                
                # Category tabs
                for i, category in enumerate(categories):
                    with tabs[i]:
                        st.subheader(f"{category} Animals")
                        category_animals = df[df[category_col] == category]
                        
                        # Create animal cards in columns
                        cols = st.columns(3)
                        for idx, (_, animal) in enumerate(category_animals.iterrows()):
                            with cols[idx % 3]:
                                animal_name = animal.get(name_col, 'Unknown')
                                
                                # Animal card
                                with st.container():
                                    st.markdown(f"### 🐾 {animal_name}")
                                    
                                    # Show image if available
                                    if 'INATURAL_PIC' in animal and pd.notna(animal['INATURAL_PIC']):
                                        try:
                                            st.image(animal['INATURAL_PIC'], width=200)
                                        except:
                                            st.write("📷 Image not available")
                                    
                                    # Basic info
                                    if 'DESCRIPTION' in animal and pd.notna(animal['DESCRIPTION']):
                                        st.write(f"**Description:** {animal['DESCRIPTION'][:100]}...")
                                    
                                    # View profile button
                                    if st.button(f"View Profile", key=f"profile_{animal_name}_{idx}"):
                                        st.session_state.selected_animal = animal_name
                                        st.session_state.animal_data = animal
                                        st.session_state.show_profile = True
                                        st.rerun()
                
                # All data tab
                with tabs[-1]:
                    st.subheader("All Animals Data")
                    st.dataframe(df, use_container_width=True)
                    
                    # Statistics
                    col1, col2 = st.columns(2)
                    with col1:
                        st.bar_chart(df[name_col].value_counts().head(10))
                    with col2:
                        if category_col in df.columns:
                            st.bar_chart(df[category_col].value_counts())
            else:
                # No categories, show all animals
                st.subheader("All Animals")
                cols = st.columns(3)
                for idx, (_, animal) in enumerate(df.iterrows()):
                    with cols[idx % 3]:
                        animal_name = animal.get(name_col, 'Unknown')
                        
                        with st.container():
                            st.markdown(f"### 🐾 {animal_name}")
                            
                            if 'INATURAL_PIC' in animal and pd.notna(animal['INATURAL_PIC']):
                                try:
                                    st.image(animal['INATURAL_PIC'], width=200)
                                except:
                                    st.write("📷 Image not available")
                            
                            if st.button(f"View Profile", key=f"profile_{animal_name}_{idx}"):
                                st.session_state.selected_animal = animal_name
                                st.session_state.animal_data = animal
                                st.session_state.show_profile = True
                                st.rerun()
        else:
            # Fallback to simple view
            st.dataframe(df, use_container_width=True)
            st.bar_chart(df[name_col].value_counts())

# Animal Profile Page
if st.session_state.get('show_profile', False):
    animal_name = st.session_state.get('selected_animal', '')
    animal_data = st.session_state.get('animal_data', {})
    
    # Back button
    if st.button("← Back to Dashboard"):
        st.session_state.show_profile = False
        st.rerun()
    
    st.title(f"🐾 {animal_name} Profile")
    
    # Two columns layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Image
        if 'INATURAL_PIC' in animal_data and pd.notna(animal_data['INATURAL_PIC']):
            try:
                st.image(animal_data['INATURAL_PIC'], caption=animal_name, width=300)
            except:
                st.write("📷 Image not available")
        
        # Basic Information
        st.subheader("📋 Basic Information")
        if 'CATEGORY' in animal_data and pd.notna(animal_data['CATEGORY']):
            st.write(f"**Category:** {animal_data['CATEGORY']}")
        if 'SPECIES' in animal_data and pd.notna(animal_data['SPECIES']):
            st.write(f"**Species:** {animal_data['SPECIES']}")
        
        # Description
        if 'DESCRIPTION' in animal_data and pd.notna(animal_data['DESCRIPTION']):
            st.subheader("📝 Description")
            st.write(animal_data['DESCRIPTION'])
    
    with col2:
        # Sound Section
        st.subheader("🔊 Animal Sound")
        
        # Test sound sources
        if st.button("🎵 Find & Test Sound"):
            with st.spinner("Searching for animal sounds..."):
                from utils.sound_utils import test_multiple_sound_sources
                sound_results = test_multiple_sound_sources(animal_name)
                
                if sound_results.get('best_url'):
                    st.success(f"✅ Sound found from {sound_results['best_source']}")
                    
                    # Audio player
                    try:
                        st.audio(sound_results['best_url'])
                        st.write(f"**Source:** {sound_results['best_source']}")
                        
                        # Duration info
                        best_source_data = sound_results['sources'].get(sound_results['best_source'], {})
                        duration = best_source_data.get('duration_estimate_seconds')
                        if duration:
                            st.write(f"**Duration:** ~{duration} seconds")
                            if 2 <= duration <= 3:
                                st.success("🎯 Perfect duration for your requirement!")
                            elif duration < 2:
                                st.warning("⚠️ Shorter than 2 seconds")
                            elif duration > 10:
                                st.warning("⚠️ Longer than 10 seconds")
                        
                    except Exception as e:
                        st.error(f"Could not play audio: {e}")
                        st.write(f"**Direct URL:** {sound_results['best_url']}")
                else:
                    st.error("❌ No valid sound sources found")
                    
                    # Show what was tried
                    st.write("**Sources tested:**")
                    for source, data in sound_results.get('sources', {}).items():
                        status = "✅" if data.get('valid') else "❌"
                        error = data.get('error', 'Unknown error') if not data.get('valid') else 'Success'
                        st.write(f"- {source}: {status} {error}")
        
        # Fun Facts
        if 'FACTS' in animal_data and pd.notna(animal_data['FACTS']):
            st.subheader("🎯 Fun Facts")
            st.write(animal_data['FACTS'])
        
        # Summary
        if 'SUMMARY' in animal_data and pd.notna(animal_data['SUMMARY']):
            st.subheader("📖 Summary")
            st.write(animal_data['SUMMARY'])
        
        # External Links
        st.subheader("🔗 Learn More")
        if 'WIKIPEDIA_URL' in animal_data and pd.notna(animal_data['WIKIPEDIA_URL']):
            st.markdown(f"[📖 Wikipedia]({animal_data['WIKIPEDIA_URL']})")
        
        # Additional sound sources
        st.write("**Manual Sound Sources:**")
        st.write("- [Xeno-Canto](https://xeno-canto.org) (Bird sounds)")
        st.write("- [Internet Archive](https://archive.org) (Various animals)")
        st.write("- [Freesound](https://freesound.org) (Creative Commons sounds)")
