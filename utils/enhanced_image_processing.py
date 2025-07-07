# utils/enhanced_image_processing.py

import streamlit as st
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple
from utils.image_utils import process_images, is_duplicate_image
from utils.azure_vision import get_azure_image_analysis, compare_recognition_results
from utils.groq_comparison import get_groq_animal_comparison, get_animal_classification_confidence

logger = logging.getLogger(__name__)

def enhanced_image_recognition(uploaded_file) -> Dict:
    """
    Enhanced image recognition pipeline that combines current AI model with Azure Computer Vision
    and uses Groq for intelligent comparison and conflict resolution
    
    Args:
        uploaded_file: Streamlit uploaded file object
    
    Returns:
        Dict with comprehensive recognition results
    """
    try:
        # Step 1: Check for duplicates
        logger.info(f"Processing image: {uploaded_file.name}")
        
        is_duplicate = is_duplicate_image(uploaded_file)
        if is_duplicate:
            return {
                'success': False,
                'is_duplicate': True,
                'message': f"Image {uploaded_file.name} already exists in database",
                'filename': uploaded_file.name
            }
        
        # Step 2: Current AI model recognition
        logger.info("Running current AI model analysis...")
        ai_animal_name, ai_animal_type, ai_description = process_images(uploaded_file)
        
        ai_result = {
            'name': ai_animal_name,
            'type': ai_animal_type,
            'description': ai_description,
            'source': 'current_ai_model'
        }
        
        # Step 3: Azure Computer Vision analysis
        logger.info("Running Azure Computer Vision analysis...")
        
        # Reset file pointer for Azure analysis
        if hasattr(uploaded_file, 'seek'):
            uploaded_file.seek(0)
        
        azure_result = get_azure_image_analysis(uploaded_file)
        
        # Step 4: Groq comparison and conflict resolution
        logger.info("Using Groq to compare and analyze results...")
        
        azure_animals = azure_result.get('animals', [])
        image_context = f"Image filename: {uploaded_file.name}, AI description: {ai_description}"
        
        groq_comparison = get_groq_animal_comparison(
            ai_prediction=ai_animal_name,
            azure_predictions=azure_animals,
            image_context=image_context
        )
        
        # Step 5: Determine final recommendation
        final_result = process_recognition_results(
            ai_result=ai_result,
            azure_result=azure_result,
            groq_comparison=groq_comparison,
            uploaded_file=uploaded_file
        )
        
        logger.info(f"Enhanced recognition completed for {uploaded_file.name}: {final_result['recommendation']}")
        
        return final_result
        
    except Exception as e:
        logger.error(f"Enhanced image recognition failed for {uploaded_file.name}: {e}")
        return {
            'success': False,
            'is_duplicate': False,
            'error': str(e),
            'message': f"Recognition failed for {uploaded_file.name}",
            'filename': uploaded_file.name
        }

def process_recognition_results(ai_result: Dict, azure_result: Dict, groq_comparison: Dict, uploaded_file) -> Dict:
    """
    Process and combine recognition results from all sources
    
    Args:
        ai_result: Current AI model results
        azure_result: Azure Computer Vision results
        groq_comparison: Groq comparison analysis
        uploaded_file: Original uploaded file
    
    Returns:
        Dict with processed results and recommendations
    """
    try:
        # Base result structure
        result = {
            'success': True,
            'is_duplicate': False,
            'filename': uploaded_file.name,
            'file_object': uploaded_file,
            'ai_result': ai_result,
            'azure_result': azure_result,
            'groq_analysis': groq_comparison,
            'recommendation': 'single_choice',  # Default
            'final_prediction': ai_result,
            'alternatives': [],
            'user_choice_required': False,
            'confidence_score': 0.8
        }
        
        # Analyze Groq recommendation
        groq_recommendation = groq_comparison.get('recommendation', 'user_choice')
        same_animal = groq_comparison.get('same_animal', False)
        confidence = groq_comparison.get('confidence', 50)
        
        azure_animals = azure_result.get('animals', [])
        
        if groq_recommendation == 'use_ai' or (same_animal and confidence >= 75):
            # AI prediction confirmed or strongly preferred
            result['recommendation'] = 'confirmed'
            result['final_prediction'] = ai_result
            result['confidence_score'] = min(0.95, confidence / 100.0)
            result['message'] = f"AI prediction '{ai_result['name']}' confirmed"
            
            if azure_animals:
                result['message'] += f" (Azure also detected: {azure_animals[0]['name']})"
        
        elif groq_recommendation == 'use_azure' and azure_animals:
            # Azure prediction preferred
            result['recommendation'] = 'azure_preferred'
            result['final_prediction'] = {
                'name': azure_animals[0]['name'],
                'type': categorize_animal(azure_animals[0]['name']),
                'description': f"Identified by Azure Computer Vision (confidence: {azure_animals[0]['confidence']:.2f})",
                'source': 'azure_computer_vision'
            }
            result['confidence_score'] = azure_animals[0]['confidence']
            result['message'] = f"Azure prediction '{azure_animals[0]['name']}' preferred over AI prediction"
        
        else:
            # Conflicting results - require user choice
            result['recommendation'] = 'user_choice'
            result['user_choice_required'] = True
            result['confidence_score'] = confidence / 100.0
            
            # Prepare options for user selection
            options = []
            
            # Option 1: AI prediction
            options.append({
                'source': 'AI Model',
                'name': ai_result['name'],
                'type': ai_result['type'],
                'description': ai_result['description'],
                'confidence': 'High',
                'details': 'Current AI model prediction'
            })
            
            # Option 2: Azure prediction (if available)
            if azure_animals:
                for i, azure_animal in enumerate(azure_animals[:2]):  # Top 2 Azure predictions
                    options.append({
                        'source': f'Azure Computer Vision #{i+1}',
                        'name': azure_animal['name'],
                        'type': categorize_animal(azure_animal['name']),
                        'description': f"Detected by Azure (confidence: {azure_animal['confidence']:.2f})",
                        'confidence': f"{azure_animal['confidence']:.1%}",
                        'details': f"Source: {azure_animal.get('source', 'azure')}"
                    })
            
            result['alternatives'] = options
            result['message'] = "Multiple predictions found. Please choose the most accurate identification."
        
        # Add additional metadata
        result['analysis_summary'] = {
            'ai_prediction': ai_result['name'],
            'azure_predictions': len(azure_animals),
            'groq_confidence': confidence,
            'similarity_score': groq_comparison.get('similarity_score', 0.0),
            'processing_successful': True
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing recognition results: {e}")
        return {
            'success': False,
            'is_duplicate': False,
            'error': str(e),
            'message': "Failed to process recognition results",
            'filename': uploaded_file.name if uploaded_file else 'unknown'
        }

def categorize_animal(animal_name: str) -> str:
    """
    Categorize an animal name into broad categories
    
    Args:
        animal_name: Name of the animal
    
    Returns:
        String category (Bird, Mammal, Reptile, etc.)
    """
    animal_lower = animal_name.lower()
    
    # Bird keywords
    bird_keywords = [
        'bird', 'eagle', 'hawk', 'owl', 'parrot', 'penguin', 'flamingo', 'peacock',
        'duck', 'goose', 'swan', 'chicken', 'turkey', 'pigeon', 'crow', 'raven',
        'sparrow', 'robin', 'cardinal', 'blue jay', 'woodpecker', 'hummingbird'
    ]
    
    # Mammal keywords
    mammal_keywords = [
        'mammal', 'dog', 'cat', 'lion', 'tiger', 'elephant', 'bear', 'wolf',
        'fox', 'deer', 'horse', 'cow', 'sheep', 'goat', 'pig', 'rabbit',
        'squirrel', 'mouse', 'rat', 'monkey', 'gorilla', 'zebra', 'giraffe'
    ]
    
    # Reptile keywords
    reptile_keywords = [
        'reptile', 'snake', 'lizard', 'turtle', 'tortoise', 'crocodile', 
        'alligator', 'iguana', 'gecko', 'chameleon'
    ]
    
    # Fish keywords
    fish_keywords = [
        'fish', 'shark', 'salmon', 'tuna', 'goldfish', 'bass', 'trout',
        'cod', 'swordfish', 'angel fish'
    ]
    
    # Amphibian keywords
    amphibian_keywords = [
        'amphibian', 'frog', 'toad', 'salamander', 'newt'
    ]
    
    # Insect keywords
    insect_keywords = [
        'insect', 'bug', 'butterfly', 'bee', 'ant', 'beetle', 'fly',
        'dragonfly', 'moth', 'mosquito', 'spider', 'wasp'
    ]
    
    # Check categories
    if any(keyword in animal_lower for keyword in bird_keywords):
        return 'Bird'
    elif any(keyword in animal_lower for keyword in mammal_keywords):
        return 'Mammal'
    elif any(keyword in animal_lower for keyword in reptile_keywords):
        return 'Reptile'
    elif any(keyword in animal_lower for keyword in fish_keywords):
        return 'Fish'
    elif any(keyword in animal_lower for keyword in amphibian_keywords):
        return 'Amphibian'
    elif any(keyword in animal_lower for keyword in insect_keywords):
        return 'Insect'
    else:
        return 'Other'

def create_user_choice_interface(recognition_result: Dict) -> Optional[Dict]:
    """
    Create Streamlit interface for user to choose between different recognition results
    
    Args:
        recognition_result: Result from enhanced_image_recognition
    
    Returns:
        Dict with user's final choice, or None if no choice made yet
    """
    if not recognition_result.get('user_choice_required', False):
        return recognition_result.get('final_prediction')
    
    alternatives = recognition_result.get('alternatives', [])
    if not alternatives:
        return recognition_result.get('final_prediction')
    
    st.warning("🤔 **Multiple animal identifications found!** Please choose the most accurate one:")
    
    # Create radio button options
    option_labels = []
    option_data = []
    
    for i, option in enumerate(alternatives):
        label = f"**{option['name']}** ({option['source']}) - Confidence: {option['confidence']}"
        option_labels.append(label)
        option_data.append(option)
    
    # Add "Other" option
    option_labels.append("**Other** (I'll type the correct animal name)")
    option_data.append({'source': 'user_input', 'name': 'other'})
    
    # User selection
    selected_index = st.radio(
        "Choose the correct animal identification:",
        range(len(option_labels)),
        format_func=lambda x: option_labels[x],
        key=f"animal_choice_{recognition_result['filename']}"
    )
    
    selected_option = option_data[selected_index]
    
    # Handle "Other" option
    if selected_option['name'] == 'other':
        custom_name = st.text_input(
            "Enter the correct animal name:",
            key=f"custom_animal_{recognition_result['filename']}"
        )
        
        if custom_name and custom_name.strip():
            return {
                'name': custom_name.strip(),
                'type': categorize_animal(custom_name.strip()),
                'description': f"User-provided identification: {custom_name.strip()}",
                'source': 'user_input',
                'confidence': 1.0
            }
        else:
            return None  # Wait for user input
    
    # Convert selected option to final prediction format
    return {
        'name': selected_option['name'],
        'type': selected_option.get('type', 'Other'),
        'description': selected_option.get('description', ''),
        'source': selected_option['source'],
        'confidence': 0.9 if selected_option['source'] == 'AI Model' else 
                     float(selected_option.get('confidence', '0.8').rstrip('%')) / 100
    }

def test_enhanced_recognition_pipeline():
    """
    Test function for the enhanced recognition pipeline
    """
    st.write("### 🧪 Enhanced Recognition Pipeline Test")
    
    # Test Azure connection
    from utils.azure_vision import test_azure_connection
    azure_test = test_azure_connection()
    
    if azure_test['success']:
        st.success("✅ Azure Computer Vision connection successful")
    else:
        st.error(f"❌ Azure connection failed: {azure_test['error']}")
    
    # Test Groq connection
    try:
        groq_api_key = st.secrets.get("groq_api_key")
        if groq_api_key:
            st.success("✅ Groq API key found")
        else:
            st.error("❌ Groq API key not found")
    except:
        st.error("❌ Failed to check Groq API key")
    
    st.info("🔧 **Enhanced Pipeline Features:**")
    st.write("- Current AI model + Azure Computer Vision analysis")
    st.write("- Groq-powered intelligent comparison")
    st.write("- Smart conflict resolution")
    st.write("- User choice for ambiguous cases")
    st.write("- Duplicate detection")
    st.write("- Confidence scoring")
