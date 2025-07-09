# test_speech_removal.py
import streamlit as st
from utils.sound_utils import fetch_clean_animal_sound, prioritize_inaturalist_for_mammals, test_multiple_sound_sources
from utils.audio_processor import AUDIO_PROCESSING_AVAILABLE

def test_speech_removal():
    """Test speech removal functionality for animal sounds"""
    st.title("🎵 Animal Sound Speech Removal Test")
    
    if not AUDIO_PROCESSING_AVAILABLE:
        st.error("❌ Audio processing libraries not available!")
        st.write("Please install: `pip install pydub SpeechRecognition pyaudio`")
        return
    
    st.success("✅ Audio processing libraries available!")
    
    # Test with animals that often have human narration
    test_animals = [
        ("Bobcat", "mammal"),
        ("American Robin", "bird"),
        ("Great Horned Owl", "bird"),
        ("Gray Wolf", "mammal"),
        ("Mountain Lion", "mammal")
    ]
    
    selected_animal = st.selectbox(
        "Select an animal to test:",
        options=[f"{name} ({type_})" for name, type_ in test_animals],
        index=0
    )
    
    if selected_animal:
        animal_name, animal_type = selected_animal.split(" (")
        animal_type = animal_type.rstrip(")")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Test Standard Sources"):
                with st.spinner(f"Testing standard sources for {animal_name}..."):
                    results = test_multiple_sound_sources(animal_name, animal_type)
                    
                    if results.get('best_url'):
                        st.success(f"✅ Found sound from {results['best_source']}")
                        st.audio(results['best_url'])
                        
                        # Show source analysis
                        st.write("**Source Analysis:**")
                        for source, data in results.get('sources', {}).items():
                            status = "✅" if data.get('valid') else "❌"
                            st.write(f"- {source}: {status}")
                    else:
                        st.error("❌ No sounds found")
        
        with col2:
            if st.button("🧹 Test with Speech Removal"):
                with st.spinner(f"Testing speech removal for {animal_name}..."):
                    # Test prioritized iNaturalist for mammals
                    if animal_type == "mammal":
                        clean_url = prioritize_inaturalist_for_mammals(animal_name, animal_type)
                        if clean_url:
                            st.success(f"✅ Clean sound from prioritized iNaturalist")
                            st.audio(clean_url)
                        else:
                            st.info("Testing with speech removal...")
                    
                    # Test full speech removal process
                    result = fetch_clean_animal_sound(animal_name, animal_type)
                    
                    if result.get('success'):
                        st.success(f"✅ {result['message']}")
                        
                        # Show analysis if available
                        if result.get('analysis'):
                            analysis = result['analysis']
                            st.write("**Audio Analysis:**")
                            st.write(f"- Total Duration: {analysis['total_duration']:.1f}s")
                            st.write(f"- Speech Content: {analysis['speech_ratio']:.1%}")
                            st.write(f"- Animal Content: {analysis['animal_ratio']:.1%}")
                            st.write(f"- Quality Score: {analysis['quality_score']:.0f}/100")
                            
                            if analysis['recommended']:
                                st.success("High quality animal sound!")
                            else:
                                st.warning("⚠️ May contain significant human speech")
                        
                        # Play the processed audio
                        if result.get('processed_url'):
                            st.audio(result['processed_url'])
                            
                            if result.get('speech_removed'):
                                st.info("🧹 Speech has been removed from this audio")
                            else:
                                st.info("Original audio (minimal speech detected)")
                        
                        # Show original for comparison if different
                        if (result.get('original_url') != result.get('processed_url') and 
                            result.get('speech_removed')):
                            st.write("**Original (with speech):**")
                            st.audio(result['original_url'])
                    else:
                        st.error(f"❌ {result.get('message', 'Unknown error')}")
        
        # Additional info
        st.markdown("---")
        st.markdown("### 📋 How it works:")
        st.markdown("""
        1. **Source Priority**: For mammals like Bobcat, iNaturalist is prioritized over Macaulay Library
        2. **Speech Detection**: Uses Google Speech Recognition to identify human narration
        3. **Segment Analysis**: Splits audio on silence and analyzes each segment
        4. **Smart Removal**: Removes segments containing human speech indicators like:
           - "This is...", "Here we have...", "You can hear..."
           - Technical terms like "recorded at", "Macaulay Library"
           - Multiple clear words (likely narration)
        5. **Quality Preservation**: Keeps pure animal sounds and natural environment audio
        """)

if __name__ == "__main__":
    test_speech_removal()
