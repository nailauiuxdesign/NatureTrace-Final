# app.py

import streamlit as st
import pandas as pd
import logging
from urllib.parse import parse_qs
from utils.image_utils import process_images, is_duplicate_image
from utils.data_utils import save_to_snowflake, fetch_dashboard_data, update_animal_sound_enhanced
from utils.map_utils import (
    get_animal_habitat_map, get_interactive_map_with_controls,
    get_comprehensive_animal_map, get_category_statistics_map,
    get_simple_colored_map, get_actual_locations_map,
    get_location_enhanced_habitat_map
)
from utils.llama_utils import generate_animal_facts, generate_description
from utils.sound_utils import (
    test_multiple_sound_sources, fetch_clean_animal_sound,
    prioritize_inaturalist_for_mammals
)
from utils.enhanced_image_processing import (
    enhanced_image_recognition, create_user_choice_interface,
    test_enhanced_recognition_pipeline
)
from utils.azure_vision import test_azure_connection
from utils.category_utils import convert_category_name

# Configure logging
logger = logging.getLogger(__name__)

def show_upload_page():
    st.title("➕ Upload New Animals")
    st.markdown("Upload up to 5 animal images to identify them and explore their world.")
    
    # Enhanced features notification
    st.info("""
    🌟 **Enhanced Upload Features:**
    - 🔍 **Advanced AI Recognition** - Current AI model + Azure Computer Vision analysis
    - 🤖 **Intelligent Comparison** - Groq AI compares and validates results
    - 🎯 **Smart Conflict Resolution** - Choose between different AI predictions when they differ
    - 📍 **Smart Location Detection** - Fetches GPS coordinates from iNaturalist, Wikipedia, or AI
    - 🔊 **Sound Integration** - Automatically finds animal sounds
    - 🗺️ **Interactive Maps** - View animals on real-world location maps
    """)
    
    # Test connection buttons in expandable section
    with st.expander("🔧 Test Enhanced Recognition Components", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Test Azure Computer Vision"):
                azure_test = test_azure_connection()
                if azure_test['success']:
                    st.success("✅ Azure Computer Vision connection successful")
                    st.info(f"Endpoint: {azure_test['endpoint']}")
                else:
                    st.error(f"❌ Azure connection failed: {azure_test['error']}")
        
        with col2:
            if st.button("Test Enhanced Pipeline"):
                test_enhanced_recognition_pipeline()

    uploaded_files = st.file_uploader("Upload Animal Images", accept_multiple_files=True, type=["jpg", "jpeg", "png"])

    if uploaded_files:
        st.subheader("🔍 Enhanced Animal Recognition")
        
        # Process all images with enhanced recognition
        processed_animals = []
        duplicate_animals = []
        recognition_results = []
        
        # Progress bar for processing
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"🔍 Processing {uploaded_file.name} ({idx+1}/{len(uploaded_files)})...")
            progress = (idx + 0.5) / len(uploaded_files)
            progress_bar.progress(progress)
            
            # Enhanced recognition pipeline
            recognition_result = enhanced_image_recognition(uploaded_file)
            recognition_results.append(recognition_result)
            
            if recognition_result.get('is_duplicate'):
                duplicate_animals.append({
                    'file': uploaded_file,
                    'name': uploaded_file.name
                })
            elif recognition_result.get('success'):
                processed_animals.append(recognition_result)
            
            progress = (idx + 1) / len(uploaded_files)
            progress_bar.progress(progress)
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
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
        
        # Display enhanced recognition results
        if processed_animals:
            st.subheader("🤖 Enhanced Recognition Results")
            
            for idx, recognition_result in enumerate(processed_animals):
                animal_file = recognition_result['file_object']
                recommendation = recognition_result.get('recommendation', 'single_choice')
                
                # Create container for each animal
                with st.container():
                    st.markdown("---")
                    
                    # Main layout: image on left, results on right
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        # Display image
                        st.image(animal_file, width=150, caption=f"📷 {animal_file.name}")
                        
                        # Show recognition confidence
                        confidence = recognition_result.get('confidence_score', 0.8)
                        st.metric("🎯 Confidence", f"{confidence:.1%}")
                    
                    with col2:
                        # Display recognition results based on recommendation type
                        if recommendation == 'confirmed':
                            # Single confirmed result
                            final_pred = recognition_result['final_prediction']
                            
                            st.success(f"✅ **Confirmed Identification: {final_pred['name']}**")
                            st.write(f"**Type:** *{final_pred['type']}*")
                            st.write(f"**Description:** {final_pred['description']}")
                            
                            # Show analysis summary
                            analysis = recognition_result.get('analysis_summary', {})
                            if analysis.get('azure_predictions', 0) > 0:
                                st.info(f"🔍 AI model prediction confirmed by Azure Computer Vision analysis")
                        
                        elif recommendation == 'azure_preferred':
                            # Azure result preferred
                            final_pred = recognition_result['final_prediction']
                            
                            st.info(f"🔍 **Azure Computer Vision Result: {final_pred['name']}**")
                            st.write(f"**Type:** *{final_pred['type']}*")
                            st.write(f"**Description:** {final_pred['description']}")
                            st.write(f"**AI Model also suggested:** {recognition_result['ai_result']['name']}")
                            
                        else:
                            # User choice required
                            st.warning("🤔 **Multiple identifications found - Please choose:**")
                            
                            # Show analysis details
                            ai_pred = recognition_result['ai_result']['name']
                            azure_preds = len(recognition_result['azure_result'].get('animals', []))
                            groq_confidence = recognition_result['groq_analysis'].get('confidence', 50)
                            
                            st.write(f"**AI Model:** {ai_pred}")
                            if azure_preds > 0:
                                azure_top = recognition_result['azure_result']['animals'][0]['name']
                                st.write(f"**Azure Computer Vision:** {azure_top} (+{azure_preds-1} others)")
                            st.write(f"**Groq Analysis Confidence:** {groq_confidence}%")
                            
                            # Create user choice interface
                            user_choice = create_user_choice_interface(recognition_result)
                            
                            if user_choice:
                                st.success(f"✅ **Selected: {user_choice['name']}**")
                                recognition_result['final_choice'] = user_choice
                            else:
                                recognition_result['final_choice'] = None
                                st.info("👆 Please make a selection above to continue")
                    
                    # Add to dashboard button (only show if final choice is made)
                    if recognition_result.get('final_choice'):
                        final_choice = recognition_result['final_choice']
                        
                        # Generate additional data
                        facts = generate_animal_facts(final_choice['name'])
                        map_html = get_animal_habitat_map(final_choice['name'])
                        
                        # Store for dashboard addition
                        recognition_result['facts'] = facts
                        recognition_result['map_html'] = map_html
                        
                        # Add to dashboard button
                        button_key = f"enhanced_dashboard_btn_{idx}_{hash(animal_file.name)}"
                        
                        if st.button("➕ Add to Dashboard", 
                                   key=button_key,
                                   use_container_width=True):
                            
                            # Create progress indicators
                            add_progress_bar = st.progress(0)
                            add_status_text = st.empty()
                            
                            try:
                                # Step 1: Adding to database
                                add_status_text.text(f"📝 Adding {final_choice['name']} to database...")
                                add_progress_bar.progress(20)
                                
                                # Step 2: Fetching location data
                                add_status_text.text(f"🌍 Fetching location data for {final_choice['name']}...")
                                add_progress_bar.progress(40)
                                
                                # Add animal to database with enhanced location and sound fetching
                                result = save_to_snowflake(
                                    filename=animal_file.name,
                                    name=final_choice['name'],
                                    description=final_choice['description'],
                                    facts=facts,
                                    category=final_choice['type'],
                                    fetch_sound=True,
                                    fetch_location=True
                                )
                                
                                add_progress_bar.progress(80)
                                add_status_text.text(f"🔊 Finalizing sound data...")
                                
                                add_progress_bar.progress(100)
                                add_status_text.text(f"✅ Complete!");
                                
                                if result and result.get('success'):
                                    # Show comprehensive success message with details
                                    st.success(f"🎉 {final_choice['name']} successfully added to your collection!")
                                    
                                    # Create expandable details section
                                    with st.expander("📊 View Addition Details", expanded=True):
                                        detail_col1, detail_col2, detail_col3 = st.columns(3)
                                        
                                        with detail_col1:
                                            st.subheader("🤖 Recognition")
                                            st.write(f"**Source:** {final_choice['source']}")
                                            st.write(f"**Confidence:** {final_choice.get('confidence', 0.9):.1%}")
                                            if recommendation != 'single_choice':
                                                st.write(f"**Method:** Enhanced AI comparison")
                                        
                                        with detail_col2:
                                            st.subheader("📍 Location Data")
                                            location_result = result.get('location_result', {})
                                            if location_result.get('success'):
                                                location_source = location_result.get('source', 'Unknown')
                                                location_name = location_result.get('location', 'Unknown location')
                                                st.success(f"✅ Found via {location_source}")
                                                st.write(f"**Location:** {location_name}")
                                                
                                                # Show source-specific icon
                                                source_icons = {
                                                    'iNaturalist': '🔬',
                                                    'Wikipedia': '📚', 
                                                    'Groq AI': '🤖'
                                                }
                                                icon = source_icons.get(location_source, '📍')
                                                st.write(f"{icon} **Source:** {location_source}")
                                            else:
                                                st.warning("⚠️ Location data not available")
                                                st.write("This animal can still be viewed on maps using habitat estimates.")
                                        
                                        with detail_col3:
                                            st.subheader("🔊 Sound Data")
                                            sound_result = result.get('sound_result', {})
                                            if sound_result and sound_result.get('success'):
                                                st.success("✅ Sound added successfully!")
                                                st.write("**Status:** Ready to play")
                                            else:
                                                st.info("🔄 Sound processing...")
                                                st.write("**Status:** Will be available on profile page")
                                    
                                    st.info("🏠 **Next Steps:** Visit the Home dashboard to see your animal with enhanced location mapping!")
                                    
                                    # Clear progress indicators
                                    add_progress_bar.empty()
                                    add_status_text.empty()
                                    
                                else:
                                    add_progress_bar.empty()
                                    add_status_text.empty()
                                    st.error(f"❌ Failed to add {final_choice['name']} to dashboard")
                                    
                            except Exception as e:
                                add_progress_bar.empty()
                                add_status_text.empty()
                                st.error(f"❌ Error adding {final_choice['name']}: {str(e)}")
                                logger.error(f"Enhanced upload error for {final_choice['name']}: {e}")
                
        elif not duplicate_animals:
            st.info("No animals recognized from the uploaded images.")
        
        # Show processing summary
        if recognition_results:
            st.markdown("---")
            st.subheader("📊 Processing Summary")
            
            total_processed = len([r for r in recognition_results if r.get('success')])
            total_duplicates = len(duplicate_animals)
            azure_analyzed = len([r for r in recognition_results if r.get('azure_result', {}).get('success')])
            user_choices = len([r for r in recognition_results if r.get('recommendation') == 'user_choice'])
            
            summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
            
            with summary_col1:
                st.metric("📷 Images Processed", total_processed)
            with summary_col2:
                st.metric("🔍 Azure Analyzed", azure_analyzed)
            with summary_col3:
                st.metric("🤔 User Choices", user_choices)
            with summary_col4:
                st.metric("🚫 Duplicates", total_duplicates)

def show_home_page():
    st.title("📊 Animal Dashboard & Interactive Map")
    
    try:
        df = fetch_dashboard_data()
    except Exception as e:
        st.error(f"Error fetching dashboard data: {str(e)}")
        st.info("Please check your database connection or try uploading some animals first.")
        return

    if df.empty:
        st.info("No data available yet. Upload animals to populate the dashboard.")
        return
    else:
        # Check column names (handle both NAME and name)
        name_col = 'NAME' if 'NAME' in df.columns else 'name'
        category_col = 'CATEGORY' if 'CATEGORY' in df.columns else 'category'
        animal_names = df[name_col].tolist()
        
        # Get available categories
        categories = ["All Categories"]
        if category_col in df.columns:
            categories.extend(sorted(df[category_col].dropna().unique()))
        
        # Category selector for map filtering,comment,
        st.markdown('### <i class="fas fa-globe"></i> Global Animal Habitat Map', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            selected_category = st.selectbox(
                "🎯 Filter by Category:",
                options=categories,
                index=0,
                help="Select a specific category to focus the map, or choose 'All Categories' to see everything"
            )
        
        with col2:
            show_stats = st.checkbox("📊 Show Statistics", value=True)
        
        with col3:
            map_height = st.select_slider(
                "🔧 Map Size:",
                options=["Compact", "Standard", "Large"],
                value="Standard"
            )
        
        # Show statistics overview if enabled
        if show_stats and selected_category == "All Categories":
            stats_map_html = get_category_statistics_map(df)
            st.components.v1.html(stats_map_html, height=500)
        
        # Show main comprehensive map
        with st.spinner("🌍 Loading interactive habitat map..."):
            map_filter = None if selected_category == "All Categories" else selected_category
            
            # Check if we have location data and use appropriate map
            lat_col = 'LATITUDE' if 'LATITUDE' in df.columns else 'latitude'
            lng_col = 'LONGITUDE' if 'LONGITUDE' in df.columns else 'longitude'
            
            has_location_data = (lat_col in df.columns and lng_col in df.columns and 
                               not df[lat_col].isna().all() and not df[lng_col].isna().all())
            
            if has_location_data:
                # Use actual GPS locations map
                try:
                    actual_locations_map_html = get_actual_locations_map(df, selected_category=map_filter)
                    height_mapping = {"Compact": 650, "Standard": 750, "Large": 850}
                    map_display_height = height_mapping[map_height]
                    
                    st.components.v1.html(actual_locations_map_html, height=map_display_height)
                    
                    # Show location statistics
                    valid_locations = df.dropna(subset=[lat_col, lng_col])
                    if selected_category != "All Categories":
                        category_col = 'CATEGORY' if 'CATEGORY' in df.columns else 'category'
                        if category_col in df.columns:
                            valid_locations = valid_locations[valid_locations[category_col] == selected_category]
                    
                except Exception as e:
                    st.warning("🔄 GPS map unavailable, loading habitat overview...")
                    # Fallback to habitat-based map
                    comprehensive_map_html = get_comprehensive_animal_map(df, selected_category=map_filter)
                    height_mapping = {"Compact": 650, "Standard": 750, "Large": 850}
                    map_display_height = height_mapping[map_height]
                    
                    if comprehensive_map_html and "Error" not in comprehensive_map_html:
                        st.components.v1.html(comprehensive_map_html, height=map_display_height)
                        st.info("📍 Showing habitat-based overview (GPS data loading failed)")
                    else:
                        st.error("Could not generate map. Please check your internet connection.")
            else:
                # Use habitat-based map as fallback
                try:
                    comprehensive_map_html = get_comprehensive_animal_map(df, selected_category=map_filter)
                    height_mapping = {"Compact": 650, "Standard": 750, "Large": 850}
                    map_display_height = height_mapping[map_height]
                    
                    if comprehensive_map_html and "Error" not in comprehensive_map_html:
                        st.components.v1.html(comprehensive_map_html, height=map_display_height)
                        st.info("📍 Showing habitat overview. Upload more data with GPS coordinates to see precise locations!")
                    else:
                        raise Exception("Habitat map failed")
                        
                except Exception as e:
                    # Final fallback to simple map
                    st.warning("🔄 Loading simplified map view...")
                    fallback_map_html = get_simple_colored_map(df, selected_category=map_filter)
                    height_mapping = {"Compact": 500, "Standard": 650, "Large": 800}
                    map_display_height = height_mapping[map_height]
                    
                    if fallback_map_html:
                        st.components.v1.html(fallback_map_html, height=map_display_height)
                        st.info("📍 Showing simplified habitat overview.")
                    else:
                        st.error("Could not generate map. Please check your internet connection.")
        
        # Add map interaction info
        if selected_category != "All Categories":
            filtered_count = len(df[df[category_col] == selected_category]) if category_col in df.columns else 0
            st.info(f"🔍 **Filtered View:** Showing habitats for {filtered_count} {selected_category.lower()} animals. Switch to 'All Categories' to see the full map.")
        
        st.markdown("---")
        
        # Animal Dashboard Section
        st.markdown('### <i class="fas fa-paw"></i> Your Animal Collection', unsafe_allow_html=True)
        
        # Layout options
        col1, col2 = st.columns([3, 1])
        with col1:
            view_mode = st.radio(
                "📋 Display Mode:",
                options=["Category Tabs", "Grid View", "List View"],
                horizontal=True,
                index=0
            )
        
        with col2:
            if st.button("🔄 Refresh Data"):
                st.rerun()
        
        # Filter animals based on selected category
        display_df = df if selected_category == "All Categories" else df[df[category_col] == selected_category] if category_col in df.columns else df
        
        # Check if we have any data to display
        if display_df.empty:
            st.info(f"No animals found in category: {selected_category}")
            return
            
        # Display content based on view mode
        if view_mode == "Category Tabs":
            # Group animals by category
            if category_col in df.columns:
                all_categories = df[category_col].dropna().unique()
                
                # Create tabs for each category
                if len(all_categories) > 0:
                    # Use imported convert_category_name function
                    tabs = st.tabs([f"{convert_category_name(cat)} ({len(df[df[category_col] == cat])})" for cat in sorted(all_categories)])
                    
                    # Category tabs
                    for i, category in enumerate(sorted(all_categories)):
                        with tabs[i]:
                            st.subheader(f"{convert_category_name(category)}")
                            category_animals = df[df[category_col] == category]
                            
                            # Create animal cards in columns
                            cols = st.columns(3)
                            for idx, (_, animal) in enumerate(category_animals.iterrows()):
                                with cols[idx % 3]:
                                    animal_name = animal.get(name_col, 'Unknown')
                                    animal_category = animal.get(category_col, 'Other')
                                    
                                    # Create animal card
                                    with st.container():
                                        st.markdown(f"### {animal_name}")
                                        
                                        # Display image if available
                                        if 'INATURAL_PIC' in animal and pd.notna(animal['INATURAL_PIC']):
                                            try:
                                                st.image(animal['INATURAL_PIC'], width=290)
                                            except:
                                                st.write("📷 Image not available")
                                        else:
                                            st.write("📷 No image available")
                                        
                                        # Show species if available
                                        if 'SPECIES' in animal and pd.notna(animal['SPECIES']):
                                            st.write(f"**Species:** {animal['SPECIES']}")
                                        
                                        # View button
                                        if st.button(f"View Profile", key=f"tab_{category}_{animal_name}_{idx}", use_container_width=True):
                                            st.session_state.selected_animal = animal_name
                                            st.session_state.animal_data = animal.to_dict()
                                            st.query_params["page"] = "profile"
                                            st.query_params["animal"] = animal_name
                                            st.rerun()
                else:
                    st.info("No categories found in the data.")

        elif view_mode == "Grid View":
            # Grid layout for all animals
            st.subheader(f"Grid View - {len(display_df)} Animals" + (f" ({selected_category})" if selected_category != "All Categories" else ""))
            
            cols = st.columns(4)
            for idx, (_, animal) in enumerate(display_df.iterrows()):
                with cols[idx % 4]:
                    animal_name = animal.get(name_col, 'Unknown')
                    animal_category = animal.get(category_col, 'Other')
                    
                    # Color coding with updated English categories
                    category_colors = {
                        'Birds': '#FF6B6B',
                        'Mammals': '#4ECDC4',
                        'Reptiles': '#45B7D1',
                        'Amphibians': '#96CEB4',
                        'Ray-Finned Fish': '#FECA57',
                        'Cartilaginous Fish': '#45B7D1',
                        'Insects': '#FF9FF3',
                        'Arachnids': '#54A0FF',
                        'Crustaceans': '#FFB6C1',
                        'Mollusks': '#DDA0DD',
                        'Animals': '#9C88FF',
                        'Other': '#9C88FF'
                    }
                    # Convert category to English before getting color
                    english_category = convert_category_name(animal_category)
                    card_color = category_colors.get(animal_category, '#9C88FF')
                    
                    with st.container():
                        st.markdown(f"""
                        <div style="border: 2px solid {card_color}; border-radius: 10px; padding: 10px; text-align: center; margin-bottom: 15px;">
                            <div style="background: {card_color}; color: white; margin: -10px -10px 10px -10px; padding: 8px; border-radius: 8px 8px 0 0;">
                                <strong>{english_category}</strong>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown(f"**{animal_name}**")
                        
                        if 'INATURAL_PIC' in animal and pd.notna(animal['INATURAL_PIC']):
                            try:
                                st.image(animal['INATURAL_PIC'], width=290)
                            except:
                                st.write("📷 Image not available")
                        else:
                            st.write("📷 No image available")

                        if st.button(f"View", key=f"grid_{animal_name}_{idx}", use_container_width=True):
                            st.session_state.selected_animal = animal_name
                            st.session_state.animal_data = animal.to_dict()
                            st.query_params["page"] = "profile"
                            st.query_params["animal"] = animal_name
                            st.rerun()

        else:  # List View
            st.subheader(f"List View - {len(display_df)} Animals" + (f" ({selected_category})" if selected_category != "All Categories" else ""))
            
            for idx, (_, animal) in enumerate(display_df.iterrows()):
                animal_name = animal.get(name_col, 'Unknown')
                animal_category = animal.get(category_col, 'Other')
                
                # Color coding for list items
                category_colors = {
                    'Bird': '#FF6B6B',
                    'Mammal': '#4ECDC4',
                    'Reptile': '#45B7D1',
                    'Amphibian': '#96CEB4',
                    'Fish': '#FECA57',
                    'Insect': '#FF9FF3',
                    'Arachnid': '#54A0FF',
                    'Other': '#9C88FF'
                }
                card_color = category_colors.get(animal_category, '#9C88FF')
                
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    st.markdown(f"""
                    <div style="display: flex; align-items: center;">
                        <div style="width: 20px; height: 20px; background-color: {card_color}; border-radius: 50%; margin-right: 15px; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>
                        <strong style="font-size: 1.1em;">{animal_name}</strong>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.write(f"**Category:** {convert_category_name(animal_category)}")
                
                with col3:
                    if 'SPECIES' in animal and pd.notna(animal['SPECIES']):
                        st.write(f"**Species:** {animal['SPECIES']}")
                
                with col4:
                    if st.button(f"View", key=f"list_{animal_name}_{idx}"):
                        st.session_state.selected_animal = animal_name
                        st.session_state.animal_data = animal.to_dict()
                        st.query_params["page"] = "profile"
                        st.query_params["animal"] = animal_name
                        st.rerun()
                
                st.markdown("---")

def show_profile_page():
    st.title("🐾 Animal Profile")
    
    # Auto-load animal data from URL if available
    query_params = st.query_params
    if 'animal' in query_params and query_params['animal']:
        url_animal = query_params['animal']
        if (not st.session_state.get('selected_animal') or 
            st.session_state.get('selected_animal') != url_animal):
            # Load animal data from database based on URL parameter
            try:
                df = fetch_dashboard_data()
                if not df.empty:
                    name_col = 'NAME' if 'NAME' in df.columns else 'name'
                    if name_col in df.columns:
                        animal_row = df[df[name_col].str.lower() == url_animal.lower()]
                        if not animal_row.empty:
                            st.session_state.selected_animal = url_animal
                            st.session_state.animal_data = animal_row.iloc[0].to_dict()
                    else:
                        st.warning("No name column found in database.")
            except Exception as e:
                st.error(f"Error loading animal data: {str(e)}")
    
    # Check if an animal is selected
    if 'selected_animal' not in st.session_state or not st.session_state.selected_animal:
        st.info("🔍 No animal selected. Please go to the Home Dashboard and select an animal to view its profile.")
        st.markdown("### How to view an animal profile:")
        st.markdown("1. Go to **🏠 Home (Dashboard)**")
        st.markdown("2. Click **View Profile** on any animal card")
        st.markdown("3. Return to this page to see the profile details")
    else:
        animal_name = st.session_state.selected_animal
        animal_data = st.session_state.get('animal_data', {})
        
        # Navigation buttons
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("← Back to Home Dashboard"):
                st.query_params.clear()
                st.session_state.current_page = "Home"
                st.rerun()
        with col2:
            if st.button("🔄 Clear Selection"):
                st.session_state.selected_animal = None
                st.session_state.animal_data = {}
                st.query_params.clear()
                st.rerun()
        
        st.markdown(f"## 🦁 {animal_name}")
        
        # Show shareable URL
        with st.expander("🔗 Share this Animal Profile", expanded=False):
            profile_url = f"?page=profile&animal={animal_name.replace(' ', '%20')}"
            st.code(profile_url, language="text")
            st.info("💡 Copy this URL to share this animal's profile directly!")
        
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
            
            # Location Information
            lat_col = 'LATITUDE' if 'LATITUDE' in animal_data else 'latitude'
            lng_col = 'LONGITUDE' if 'LONGITUDE' in animal_data else 'longitude'
            place_col = 'PLACE_GUESS' if 'PLACE_GUESS' in animal_data else 'place_guess'
            
            if lat_col in animal_data and lng_col in animal_data:
                latitude = animal_data.get(lat_col)
                longitude = animal_data.get(lng_col)
                place_guess = animal_data.get(place_col, '')
                
                if pd.notna(latitude) and pd.notna(longitude):
                    st.subheader("📍 Location Information")
                    if place_guess and pd.notna(place_guess):
                        st.write(f"**Location:** {place_guess}")
                    st.write(f"**Coordinates:** {latitude:.4f}, {longitude:.4f}")
                    
                    # Add a button to show this animal's location on map
                    if st.button("🗺️ Show Location on Map"):
                        with st.spinner(f"Loading {animal_name} location map..."):
                            location_map = get_location_enhanced_habitat_map(animal_name, 
                                          pd.DataFrame([animal_data]) if animal_data else None)
                            if location_map:
                                st.components.v1.html(location_map, height=400)
            
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
                                # Save the processed/clean URL with enhanced tracking
                                update_result = update_animal_sound_enhanced(
                                    animal_name=animal_name,
                                    sound_url=result['processed_url'],
                                    source=result.get('source', 'Unknown'),
                                    processed=result.get('speech_removed', False)
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

def show_map_page():
    st.title("🗺️ Animal Locations")
    st.markdown("Explore where different animals have been spotted and their natural habitats.")
    
    map_type = st.selectbox(
        "Select Map Type",
        ["Actual Locations", "Habitat Map", "Category Statistics", "Interactive Map", "Comprehensive Map"]
    )
    
    if map_type == "Actual Locations":
        get_actual_locations_map()
    elif map_type == "Habitat Map":
        get_animal_habitat_map()
    elif map_type == "Category Statistics":
        get_category_statistics_map()
    elif map_type == "Interactive Map":
        get_interactive_map_with_controls()
    else:
        get_comprehensive_animal_map()

def show_analytics_page():
    st.title("📊 Analytics Dashboard")
    st.markdown("View insights and statistics about recorded animals.")
    
    # Fetch dashboard data
    try:
        data = fetch_dashboard_data()
    except Exception as e:
        st.error(f"Error fetching dashboard data: {str(e)}")
        st.info("Please check your database connection or try uploading some animals first.")
        return
    
    if data.empty:
        st.info("No data available yet. Upload animals to populate the analytics dashboard.")
        return
    
    # Check column names (handle both uppercase and lowercase)
    name_col = 'NAME' if 'NAME' in data.columns else 'name'
    category_col = 'CATEGORY' if 'CATEGORY' in data.columns else 'category'
    species_col = 'SPECIES' if 'SPECIES' in data.columns else 'species'
    date_col = 'DATE' if 'DATE' in data.columns else 'date'
    
    # Display overall statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Animals", len(data))
    
    with col2:
        if species_col in data.columns:
            unique_species = data[species_col].dropna().nunique()
            st.metric("Unique Species", unique_species)
        else:
            st.metric("Unique Species", "N/A")
    
    with col3:
        if category_col in data.columns:
            unique_categories = data[category_col].dropna().nunique()
            st.metric("Categories", unique_categories)
        else:
            st.metric("Categories", "N/A")
    
    # Category distribution
    if category_col in data.columns:
        st.subheader("Category Distribution")
        category_counts = data[category_col].value_counts()
        if not category_counts.empty:
            st.bar_chart(category_counts)
        else:
            st.info("No category data available to display.")
    else:
        st.warning("No category column found in the data.")
    
    # Species distribution
    if species_col in data.columns:
        st.subheader("Species Distribution")
        species_counts = data[species_col].dropna().value_counts().head(10)  # Top 10 species
        if not species_counts.empty:
            st.bar_chart(species_counts)
        else:
            st.info("No species data available to display.")
    
    # Data quality overview
    st.subheader("📋 Data Overview")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Available Columns:**")
        available_cols = list(data.columns)
        for col in available_cols:
            non_null_count = data[col].count()
            total_count = len(data)
            percentage = (non_null_count / total_count) * 100 if total_count > 0 else 0
            st.write(f"- **{col}:** {non_null_count}/{total_count} ({percentage:.1f}% complete)")
    
    with col2:
        st.write("**Data Summary:**")
        if name_col in data.columns:
            st.write(f"**Animals:** {data[name_col].nunique()} unique names")
        
        # Check for image data
        image_col = 'INATURAL_PIC' if 'INATURAL_PIC' in data.columns else 'image'
        if image_col in data.columns:
            images_count = data[image_col].dropna().count()
            st.write(f"**Images:** {images_count} animals with images")
        
        # Check for location data
        lat_col = 'LATITUDE' if 'LATITUDE' in data.columns else 'latitude'
        lng_col = 'LONGITUDE' if 'LONGITUDE' in data.columns else 'longitude'
        if lat_col in data.columns and lng_col in data.columns:
            location_count = data.dropna(subset=[lat_col, lng_col]).shape[0]
            st.write(f"**Locations:** {location_count} animals with GPS coordinates")
        
        # Check for sound data
        sound_col = 'SOUND_URL' if 'SOUND_URL' in data.columns else 'sound_url'
        if sound_col in data.columns:
            sounds_count = data[sound_col].dropna().count()
            st.write(f"**Sounds:** {sounds_count} animals with audio")
    
    # Recent additions (if date column exists)
    if date_col in data.columns:
        st.subheader("📅 Recent Activity")
        try:
            # Convert date column to datetime if it's not already
            data[date_col] = pd.to_datetime(data[date_col], errors='coerce')
            recent_data = data.dropna(subset=[date_col]).sort_values(date_col, ascending=False).head(5)
            
            if not recent_data.empty:
                st.write("**Last 5 Animals Added:**")
                for _, animal in recent_data.iterrows():
                    animal_name = animal.get(name_col, 'Unknown')
                    animal_date = animal[date_col].strftime('%Y-%m-%d') if pd.notna(animal[date_col]) else 'Unknown date'
                    animal_category = animal.get(category_col, 'Unknown category')
                    st.write(f"- **{animal_name}** ({animal_category}) - {animal_date}")
            else:
                st.info("No recent activity data available.")
        except Exception as e:
            st.warning(f"Could not process date information: {str(e)}")
    else:
        st.info("No date column found for tracking recent activity.")

def main():
    st.set_page_config(page_title="NatureTrace - Animal Discovery Platform", layout="wide")

    # Initialize session state for page navigation
    if 'page' not in st.session_state:
        st.session_state.page = 'Home'

    # Add custom CSS
    st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        .nav-helper {
            background-color: #f0f2f6;
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 24px;
            border-left: 4px solid #1f77b4;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
    </style>
    """, unsafe_allow_html=True)

    # Sidebar navigation
    with st.sidebar:
        st.title("🦁 NatureTrace")
        st.markdown("---")
        
        # Navigation buttons
        pages = {
            "Home": "🏠",
            "Upload": "➕",
            "Profile": "🐾",
            "Map": "🗺️",
            "Analytics": "📊"
        }
        
        for page_name, icon in pages.items():
            if st.button(f"{icon} {page_name}", use_container_width=True):
                st.session_state.page = page_name
                st.rerun()
        
        st.markdown("---")
        st.markdown("### About")
        st.info("""
        🌟 **NatureTrace**
        Discover and track wildlife with AI-powered recognition and interactive mapping.
        """)

    # Display the selected page
    if st.session_state.page == "Upload":
        show_upload_page()
    elif st.session_state.page == "Profile":
        show_profile_page()
    elif st.session_state.page == "Map":
        show_map_page()
    elif st.session_state.page == "Analytics":
        show_analytics_page()
    else:  # Home is the default
        show_home_page()

if __name__ == "__main__":
    main()
