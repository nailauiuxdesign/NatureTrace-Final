# app.py

import streamlit as st
import pandas as pd
from utils.image_utils import process_images, is_duplicate_image
from utils.data_utils import save_to_snowflake, fetch_dashboard_data, update_animal_sound_url
from utils.map_utils import get_animal_habitat_map, get_interactive_map_with_controls
from utils.llama_utils import generate_animal_facts, generate_description
from utils.sound_utils import test_multiple_sound_sources, fetch_clean_animal_sound, prioritize_inaturalist_for_mammals

st.set_page_config(page_title="Animal Insight", layout="wide")

# Initialize session state for navigation
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Upload Images"

# Sidebar navigation
page = st.sidebar.radio("Go to", ["Upload Images", "Animal Dashboard", "Animal Profile"], 
                       index=["Upload Images", "Animal Dashboard", "Animal Profile"].index(st.session_state.current_page) if st.session_state.current_page in ["Upload Images", "Animal Dashboard", "Animal Profile"] else 0)

# Update current page in session state
st.session_state.current_page = page

if page == "Upload Images":
    st.title("🦁 Animal Insight - Discover & Explore")
    st.markdown("Upload up to 5 animal images to identify them and explore their world.")

    uploaded_files = st.file_uploader("Upload Animal Images", accept_multiple_files=True, type=["jpg", "jpeg", "png"])

    if uploaded_files:
        st.subheader("🔍 Recognized Animals")
        
        # Process all images first
        processed_animals = []
        duplicate_animals = []
        
        for uploaded_file in uploaded_files:
            # Check if it's a duplicate first
            is_duplicate = is_duplicate_image(uploaded_file)
            
            if is_duplicate:
                # Store duplicate info for modal display
                duplicate_animals.append({
                    'file': uploaded_file,
                    'name': uploaded_file.name
                })
            else:
                # Process non-duplicate images
                animal_name, animal_type, animal_desc = process_images(uploaded_file)
                sound_url = f"https://huggingface.co/spaces/NailaRajpoot/NatureTrace/resolve/main/assets/sounds/{animal_name.lower()}.mp3"
                map_html = get_animal_habitat_map(animal_name)
                facts = generate_animal_facts(animal_name)
                
                # Store processed animal data (non-duplicates only)
                processed_animals.append({
                    'file': uploaded_file,
                    'name': animal_name,
                    'type': animal_type,
                    'description': animal_desc,
                    'facts': facts,
                    'sound_url': sound_url,
                    'map_html': map_html
                })
        
        # Show duplicate modal if there are duplicates
        if duplicate_animals:
            st.error("🚫 Duplicate Images Detected!")
            with st.expander("📋 View Duplicate Images", expanded=True):
                st.warning(f"Found {len(duplicate_animals)} duplicate image(s) that already exist in the database:")
                for dup in duplicate_animals:
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.image(dup['file'], width=150)
                    with col2:
                        st.write(f"**File:** {dup['name']}")
                        st.write("❌ This image is already in the database and will not be processed again.")
                st.info("💡 Only new, unique images will be shown below for processing.")
        
        # Display all results - 1 image per row (only non-duplicates)
        if processed_animals:
            st.subheader("🔍 Recognized Animals")
            for idx, animal in enumerate(processed_animals):
                # Create two columns: image on left, content on right
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    # Uniform small image with fixed dimensions
                    st.image(animal['file'], width=150, caption=animal['name'])
                    
                    # Add to dashboard button with unique key
                    button_key = f"dashboard_btn_{idx}_{hash(animal['file'].name)}"
                    
                    if st.button("➕ Add to Dashboard", 
                               key=button_key,
                               use_container_width=True):
                        with st.spinner(f"Adding {animal['name']} to dashboard..."):
                            # Add animal to database first
                            result = save_to_snowflake(
                                filename=animal['file'].name,
                                name=animal['name'],
                                description=animal['description'],
                                facts=animal['facts'],
                                category=animal['type']
                            )
                            
                            if result:
                                # Automatically fetch and add sound
                                with st.spinner(f"Fetching sound for {animal['name']}..."):
                                    sound_result = update_animal_sound_url(animal_name=animal['name'])
                                    if sound_result and sound_result.get('success'):
                                        st.success(f"✅ {animal['name']} added to dashboard with sound!")
                                    else:
                                        st.success(f"✅ {animal['name']} added to dashboard!")
                                        st.info("🔊 Sound will be available on profile page")
                            else:
                                st.error(f"❌ Failed to add {animal['name']} to dashboard")
                
                with col2:
                    # Animal info - clean and simple
                    st.markdown(f"### 🦁 {animal['name']}")
                    st.markdown(f"**Type:** *{animal['type']}*")
                    st.markdown(f"**Description:** {animal['description']}")
                    st.markdown(f"**Fun Fact:** {animal['facts']}")
                
                st.markdown("---")  # Add separator between animals
        elif not duplicate_animals:
            st.info("No animals recognized from the uploaded images.")

elif page == "Animal Dashboard":
    st.title("📊 Animal Dashboard & Interactive Map")
    
    df = fetch_dashboard_data()

    if df.empty:
        st.info("No data available yet. Upload animals to populate the dashboard.")
    else:
        # Main layout: Dashboard on left, Map on right
        dashboard_col, map_col = st.columns([1.2, 0.8])
        
        # Check column names (handle both NAME and name)
        name_col = 'NAME' if 'NAME' in df.columns else 'name'
        category_col = 'CATEGORY' if 'CATEGORY' in df.columns else 'category'
        animal_names = df[name_col].tolist()
        
        # Initialize selected animal for map
        if 'selected_map_animal' not in st.session_state:
            st.session_state.selected_map_animal = animal_names[0] if animal_names else ""
        
        with dashboard_col:
            st.subheader("🐾 Your Animals")
            
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
                            
                            # Create animal cards in columns (2 columns to fit the layout)
                            cols = st.columns(2)
                            for idx, (_, animal) in enumerate(category_animals.iterrows()):
                                with cols[idx % 2]:
                                    animal_name = animal.get(name_col, 'Unknown')
                                    
                                    # Animal card with better styling
                                    with st.container():
                                        st.markdown(f"#### 🐾 {animal_name}")
                                        
                                        # Show image if available
                                        if 'INATURAL_PIC' in animal and pd.notna(animal['INATURAL_PIC']):
                                            try:
                                                st.image(animal['INATURAL_PIC'], width=150)
                                            except:
                                                st.write("📷 Image not available")
                                        
                                        # Basic info
                                        if 'DESCRIPTION' in animal and pd.notna(animal['DESCRIPTION']):
                                            st.write(f"**Description:** {animal['DESCRIPTION'][:80]}...")
                                        
                                        # Action buttons
                                        btn_col1, btn_col2 = st.columns(2)
                                        with btn_col1:
                                            if st.button(f"View Profile", key=f"profile_{animal_name}_{idx}"):
                                                st.session_state.selected_animal = animal_name
                                                st.session_state.animal_data = animal.to_dict()
                                                st.session_state.current_page = "Animal Profile"
                                                st.rerun()
                                        
                                        with btn_col2:
                                            if st.button(f"Show Map", key=f"map_{animal_name}_{idx}"):
                                                st.session_state.selected_map_animal = animal_name
                                                st.rerun()
                                    
                                    st.markdown("---")  # Separator between cards
                    
                    # All data tab
                    with tabs[-1]:
                        st.subheader("All Animals Data")
                        st.dataframe(df, use_container_width=True)
                        
                        # Statistics in smaller columns
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("**Animals by Name**")
                            st.bar_chart(df[name_col].value_counts().head(5))
                        with col2:
                            if category_col in df.columns:
                                st.write("**Animals by Category**")
                                st.bar_chart(df[category_col].value_counts())
                else:
                    # No categories, show all animals
                    st.subheader("All Animals")
                    cols = st.columns(2)
                    for idx, (_, animal) in enumerate(df.iterrows()):
                        with cols[idx % 2]:
                            animal_name = animal.get(name_col, 'Unknown')
                            
                            with st.container():
                                st.markdown(f"#### 🐾 {animal_name}")
                                
                                if 'INATURAL_PIC' in animal and pd.notna(animal['INATURAL_PIC']):
                                    try:
                                        st.image(animal['INATURAL_PIC'], width=150)
                                    except:
                                        st.write("📷 Image not available")
                                
                                # Action buttons
                                btn_col1, btn_col2 = st.columns(2)
                                with btn_col1:
                                    if st.button(f"View Profile", key=f"profile_{animal_name}_{idx}"):
                                        st.session_state.selected_animal = animal_name
                                        st.session_state.animal_data = animal.to_dict()
                                        st.session_state.current_page = "Animal Profile"
                                        st.rerun()
                                
                                with btn_col2:
                                    if st.button(f"Show Map", key=f"map_{animal_name}_{idx}"):
                                        st.session_state.selected_map_animal = animal_name
                                        st.rerun()
                            
                            st.markdown("---")
            else:
                # Fallback to simple view
                st.dataframe(df, use_container_width=True)
                st.bar_chart(df[name_col].value_counts())
        
        with map_col:
            st.subheader("🗺️ Habitat Map")
            
            # Animal selector for map
            selected_for_map = st.selectbox(
                "🔍 Select animal to view habitat:",
                options=animal_names,
                index=animal_names.index(st.session_state.selected_map_animal) if st.session_state.selected_map_animal in animal_names else 0,
                key="map_selector"
            )
            
            # Update session state when selection changes
            if selected_for_map != st.session_state.selected_map_animal:
                st.session_state.selected_map_animal = selected_for_map
            
            if selected_for_map:
                # Generate and display enhanced map
                with st.spinner("Loading habitat map..."):
                    map_html = get_interactive_map_with_controls(selected_for_map)
                    if map_html:
                        st.components.v1.html(map_html, height=500)
                    else:
                        st.error("Could not generate map for this animal.")
                        # Fallback to basic map
                        basic_map = get_animal_habitat_map(selected_for_map)
                        if basic_map:
                            st.components.v1.html(basic_map, height=400)
                        else:
                            st.error("No map data available for this animal.")
                
                # Show animal info below map
                animal_row = df[df[name_col] == selected_for_map].iloc[0]
                if 'DESCRIPTION' in animal_row and pd.notna(animal_row['DESCRIPTION']):
                    st.write(f"**About {selected_for_map}:**")
                    st.write(animal_row['DESCRIPTION'][:200] + "..." if len(str(animal_row['DESCRIPTION'])) > 200 else animal_row['DESCRIPTION'])
            else:
                st.info("Select an animal to view its habitat map.")

elif page == "Animal Profile":
    st.title("🐾 Animal Profile")
    
    # Check if an animal is selected
    if 'selected_animal' not in st.session_state or not st.session_state.selected_animal:
        st.info("🔍 No animal selected. Please go to the Dashboard and select an animal to view its profile.")
        st.markdown("### How to view an animal profile:")
        st.markdown("1. Go to **Animal Dashboard**")
        st.markdown("2. Click **View Profile** on any animal card")
        st.markdown("3. Return to this page to see the profile details")
    else:
        animal_name = st.session_state.selected_animal
        animal_data = st.session_state.get('animal_data', {})
        
        # Navigation buttons
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("← Back to Dashboard"):
                st.session_state.current_page = "Animal Dashboard"
                st.rerun()
        with col2:
            if st.button("🔄 Clear Selection"):
                st.session_state.selected_animal = None
                st.session_state.animal_data = {}
                st.rerun()
        
        st.markdown(f"## 🦁 {animal_name}")
        
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
            
            # Check if sound already exists in database
            sound_url = animal_data.get('SOUND_URL')
            if sound_url and pd.notna(sound_url):
                st.success("✅ Sound available")
                try:
                    st.audio(sound_url)
                    if 'SOUND_SOURCE' in animal_data and pd.notna(animal_data['SOUND_SOURCE']):
                        st.write(f"**Source:** {animal_data['SOUND_SOURCE']}")
                except Exception as e:
                    st.error(f"Could not play audio: {e}")
                    st.write(f"**Direct URL:** {sound_url}")
            else:
                st.info("🔍 No sound found in database")
            
            # Find/Update sound button
            if st.button("🎵 Find/Update Sound"):
                with st.spinner("Searching for clean animal sounds..."):
                    # Use enhanced sound fetching with speech removal
                    result = fetch_clean_animal_sound(animal_name, animal_data.get('CATEGORY', 'unknown'))
                    
                    if result.get('success'):
                        st.success(f"✅ {result['message']}")
                        
                        # Show audio analysis if available
                        if result.get('analysis'):
                            analysis = result['analysis']
                            with st.expander("📊 Audio Quality Analysis", expanded=False):
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("Duration", f"{analysis['total_duration']:.1f}s")
                                    st.metric("Animal Content", f"{analysis['animal_ratio']:.1%}")
                                with col2:
                                    st.metric("Speech Content", f"{analysis['speech_ratio']:.1%}")
                                    st.metric("Quality Score", f"{analysis['quality_score']:.0f}/100")
                                
                                if analysis['recommended']:
                                    st.success("🎯 High quality animal sound!")
                                elif analysis['speech_ratio'] > 0.3:
                                    st.warning("⚠️ Contains human speech - processed to remove it")
                                else:
                                    st.info("✨ Clean natural sound")
                        
                        # Play the processed audio
                        if result.get('processed_url'):
                            st.audio(result['processed_url'])
                            st.write(f"**Source:** {result.get('source', 'Unknown')}")
                            
                            if result.get('speech_removed'):
                                st.success("🧹 Human speech removed from this recording")
                            else:
                                st.info("🔊 Original clean recording")
                            
                            # Show comparison if speech was removed
                            if (result.get('original_url') != result.get('processed_url') and 
                                result.get('speech_removed')):
                                with st.expander("🔀 Compare with Original", expanded=False):
                                    st.write("**Original (with human speech):**")
                                    st.audio(result['original_url'])
                                    st.write("**Processed (speech removed):**")
                                    st.audio(result['processed_url'])
                            
                            # Update database button
                            if st.button("💾 Save This Sound"):
                                with st.spinner("Updating database..."):
                                    # Save the processed/clean URL
                                    update_result = update_animal_sound_url(
                                        animal_name=animal_name,
                                        sound_url=result['processed_url'],
                                        source=f"{result.get('source', 'Unknown')} (processed)"
                                    )
                                    if update_result and update_result.get('success'):
                                        st.success("✅ Clean sound saved to database!")
                                        st.rerun()
                                    else:
                                        st.error("❌ Failed to save sound")
                    else:
                        st.error(f"❌ {result.get('message', 'No sounds found')}")
                        
                        # Fallback to original method
                        st.info("🔄 Trying alternative sources...")
                        sound_results = test_multiple_sound_sources(animal_name)
                        
                        if sound_results.get('best_url'):
                            st.warning("⚠️ Found sound but may contain human speech")
                            st.audio(sound_results['best_url'])
                            st.write(f"**Source:** {sound_results['best_source']}")
                        else:
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
