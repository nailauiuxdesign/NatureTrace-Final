# test_animal_sounds.py
import streamlit as st
import pandas as pd
from utils.data_utils import fetch_dashboard_data
from utils.sound_utils import test_multiple_sound_sources, validate_sound_url, generate_animal_sound
import time
import json

def main():
    st.title("Animal Sound Testing Suite")
    st.markdown("Testing sound functionality for all animals in the database")
    
    # Fetch animals from database
    df = fetch_dashboard_data()
    
    if df.empty:
        st.error("No animals found in database")
        return
    
    # Get unique animals
    if 'NAME' in df.columns:
        animals = df['NAME'].dropna().unique()
    elif 'name' in df.columns:
        animals = df['name'].dropna().unique()
    else:
        st.error("No NAME column found in database")
        return
    
    st.success(f"Found {len(animals)} unique animals to test")
    
    # Test options
    test_mode = st.radio(
        "Select test mode:",
        ["Quick Test (existing URLs)", "Comprehensive Test (all sources)", "Individual Animal Test"]
    )
    
    if test_mode == "Individual Animal Test":
        selected_animal = st.selectbox("Select animal to test:", animals)
        if st.button("Test Selected Animal"):
            test_individual_animal(selected_animal)
    
    elif test_mode == "Quick Test (existing URLs)":
        if st.button("Run Quick Test"):
            run_quick_test(df)
    
    elif test_mode == "Comprehensive Test (all sources)":
        if st.button("Run Comprehensive Test"):
            run_comprehensive_test(animals)

def test_individual_animal(animal_name):
    """Test a single animal comprehensively with enhanced functionality"""
    st.subheader(f"🔍 Testing: {animal_name}")
    
    # Try to determine animal type from database
    animal_type = "unknown"
    try:
        from utils.data_utils import get_snowflake_connection
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT animal_type FROM animal_insight_data WHERE UPPER(name) = UPPER(%s)", (animal_name,))
        result = cursor.fetchone()
        if result:
            animal_type = result[0] or "unknown"
        cursor.close()
        conn.close()
    except:
        pass
    
    st.info(f"🏷️ Animal type: {animal_type}")
    
    with st.spinner("Testing all sound sources with enhanced quality filtering..."):
        results = test_multiple_sound_sources(animal_name, animal_type)
    
    # Display results
    st.write("**Test Results:**")
    
    if results["best_url"]:
        st.success(f"✅ Best source: {results['best_source']}")
        st.write(f"**URL:** {results['best_url']}")
        
        # Show audio player
        try:
            st.audio(results["best_url"])
        except:
            st.warning("Could not create audio player (URL might not be directly playable)")
    else:
        st.error("❌ No valid sound sources found")
        
        # Show attempted URLs for debugging
        st.write("**Attempted URLs:**")
        for source, data in results["sources"].items():
            attempted_url = data.get('url', 'No URL generated')
            raw_url = data.get('raw_url', '')
            error = data.get('error', 'Unknown error')
            
            st.write(f"**{source.title()}:**")
            if attempted_url != 'No URL generated':
                st.write(f"  - Final URL: `{attempted_url}`")
            if raw_url:
                st.write(f"  - Raw API URL: `{raw_url}`")
            st.write(f"  - Error: {error}")
            st.write("")
    
    # Detailed source breakdown
    st.write("**Source Details:**")
    for source, data in results["sources"].items():
        with st.expander(f"{source.title()} Results"):
            if data.get("valid"):
                st.success("✅ Valid")
                url = data.get('url', 'N/A')
                st.write(f"**URL:** {url}")
                st.write(f"File Size: {data.get('file_size_mb', 'Unknown')} MB")
                st.write(f"Duration Estimate: {data.get('duration_estimate_seconds', 'Unknown')} seconds")
                st.write(f"Content Type: {data.get('content_type', 'Unknown')}")
                
                # Check if it meets 2-3 second requirement
                duration = data.get('duration_estimate_seconds')
                if duration:
                    if 2 <= duration <= 3:
                        st.success("Perfect duration (2-3 seconds)")
                    elif duration < 2:
                        st.warning("⚠️ Too short (less than 2 seconds)")
                    elif duration > 10:
                        st.warning("⚠️ Too long (more than 10 seconds)")
                    else:
                        st.info("ℹ️ Acceptable duration")
                
                # Save to database button
                if st.button(f"💾 Save {source.title()} URL to Database", key=f"save_{source}_{animal_name}"):
                    from utils.sound_utils import save_sound_url_to_database
                    if save_sound_url_to_database(animal_name, url, source):
                        st.success(f"✅ Saved {source.title()} URL to database!")
                    else:
                        st.error("❌ Failed to save URL to database")
                        
            else:
                st.error(f"❌ Invalid: {data.get('error', 'Unknown error')}")
                # Show raw URL for debugging if available
                raw_url = data.get('raw_url', '')
                if raw_url:
                    st.write(f"**Raw URL from API:** {raw_url}")

def run_quick_test(df):
    """Test existing sound URLs in database"""
    st.subheader("🚀 Quick Test Results")
    
    sound_col = None
    for col in ['SOUND_URL', 'sound_url']:
        if col in df.columns:
            sound_col = col
            break
    
    if not sound_col:
        st.error("No sound URL column found in database")
        return
    
    # Filter out empty URLs
    df_with_sounds = df[df[sound_col].notna() & (df[sound_col] != '')]
    
    if df_with_sounds.empty:
        st.warning("No sound URLs found in database")
        return
    
    st.write(f"Testing {len(df_with_sounds)} existing sound URLs...")
    
    results = []
    progress_bar = st.progress(0)
    
    for i, (idx, row) in enumerate(df_with_sounds.iterrows()):
        animal_name = row.get('NAME') or row.get('name', 'Unknown')
        sound_url = row[sound_col]
        
        # Update progress
        progress_bar.progress((i + 1) / len(df_with_sounds))
        
        # Test the URL
        validation = validate_sound_url(sound_url)
        
        results.append({
            'Animal': animal_name,
            'URL': sound_url,
            'Status': '✅ Valid' if validation['valid'] else f"❌ {validation.get('error', 'Invalid')}",
            'File Size (MB)': validation.get('file_size_mb', 'Unknown'),
            'Duration (sec)': validation.get('duration_estimate_seconds', 'Unknown'),
            'Content Type': validation.get('content_type', 'Unknown')
        })
    
    # Display results table
    results_df = pd.DataFrame(results)
    st.dataframe(results_df, use_container_width=True)
    
    # Summary statistics
    valid_count = sum(1 for r in results if '✅' in r['Status'])
    st.write(f"**Summary:** {valid_count}/{len(results)} URLs are valid ({valid_count/len(results)*100:.1f}%)")

def run_comprehensive_test(animals):
    """Test all animals against all sound sources"""
    st.subheader("🔬 Comprehensive Test Results")
    st.warning("This may take several minutes to complete...")
    
    # Limit to first 10 animals for demo
    test_animals = animals[:10] if len(animals) > 10 else animals
    st.write(f"Testing first {len(test_animals)} animals...")
    
    all_results = []
    progress_bar = st.progress(0)
    
    for idx, animal in enumerate(test_animals):
        st.write(f"Testing {animal}...")
        
        # Update progress
        progress_bar.progress((idx + 1) / len(test_animals))
        
        # Test all sources
        results = test_multiple_sound_sources(animal)
        
        # Compile results
        row = {
            'Animal': animal,
            'Best Source': results.get('best_source', 'None'),
            'Best URL': results.get('best_url', 'None'),
            'Hugging Face': '✅' if results['sources'].get('huggingface', {}).get('valid') else '❌',
            'Xeno-Canto': '✅' if results['sources'].get('xeno_canto', {}).get('valid') else '❌',
            'Internet Archive': '✅' if results['sources'].get('internet_archive', {}).get('valid') else '❌'
        }
        
        # Add duration info if available
        if results.get('best_url'):
            best_source_data = results['sources'].get(results['best_source'], {})
            duration = best_source_data.get('duration_estimate_seconds')
            if duration:
                if 2 <= duration <= 3:
                    row['Duration Status'] = 'Perfect (2-3s)'
                elif duration < 2:
                    row['Duration Status'] = '⚠️ Too short'
                elif duration > 10:
                    row['Duration Status'] = '⚠️ Too long'
                else:
                    row['Duration Status'] = 'ℹ️ Acceptable'
            else:
                row['Duration Status'] = '❓ Unknown'
        else:
            row['Duration Status'] = '❌ No sound'
        
        all_results.append(row)
        
        # Small delay to avoid overwhelming APIs
        time.sleep(0.5)
    
    # Display comprehensive results
    results_df = pd.DataFrame(all_results)
    st.dataframe(results_df, use_container_width=True)
    
    # Summary statistics
    animals_with_sounds = sum(1 for r in all_results if r['Best URL'] != 'None')
    perfect_duration = sum(1 for r in all_results if 'Perfect' in r.get('Duration Status', ''))
    
    st.write("**Summary:**")
    st.write(f"- Animals with valid sounds: {animals_with_sounds}/{len(all_results)}")
    st.write(f"- Animals with perfect duration (2-3s): {perfect_duration}/{len(all_results)}")
    
    # Source effectiveness
    hf_success = sum(1 for r in all_results if r['Hugging Face'] == '✅')
    xc_success = sum(1 for r in all_results if r['Xeno-Canto'] == '✅')
    ia_success = sum(1 for r in all_results if r['Internet Archive'] == '✅')
    
    st.write("**Source Effectiveness:**")
    st.write(f"- Hugging Face: {hf_success}/{len(all_results)} ({hf_success/len(all_results)*100:.1f}%)")
    st.write(f"- Xeno-Canto: {xc_success}/{len(all_results)} ({xc_success/len(all_results)*100:.1f}%)")
    st.write(f"- Internet Archive: {ia_success}/{len(all_results)} ({ia_success/len(all_results)*100:.1f}%)")

if __name__ == "__main__":
    main()
