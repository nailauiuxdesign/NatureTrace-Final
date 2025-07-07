# utils/azure_vision.py

import streamlit as st
import requests
import json
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

def get_azure_image_analysis(image_data) -> Dict:
    """
    Analyze image using Azure Computer Vision API
    
    Args:
        image_data: Image file data (bytes or file-like object)
    
    Returns:
        Dict with analysis results including animal detection, categories, and confidence
    """
    try:
        # Get Azure credentials from Streamlit secrets
        endpoint = st.secrets.get("AZURE_COMPUTER_VISION_ENDPOINT")
        key = st.secrets.get("AZURE_COMPUTER_VISION_KEY")
        
        if not endpoint or not key:
            return {
                'success': False,
                'error': 'Azure Computer Vision credentials not found in secrets',
                'animals': [],
                'categories': [],
                'confidence': 0.0
            }
        
        # Ensure endpoint has correct format
        if not endpoint.endswith('/'):
            endpoint += '/'
        
        # Azure Computer Vision analyze endpoint (v3.2 is working)
        analyze_url = f"{endpoint}vision/v3.2/analyze"
        
        # Parameters for analysis (v3.2 format, without celebrity recognition)
        params = {
            'visualFeatures': 'Categories,Description,Objects,Tags',
            'language': 'en'
        }
        
        # Headers for v3.2 API
        headers = {
            'Ocp-Apim-Subscription-Key': key,
            'Content-Type': 'application/octet-stream'
        }
        
        # Prepare image data
        if hasattr(image_data, 'read'):
            # If it's a file-like object, read the bytes
            image_bytes = image_data.read()
            # Reset file pointer if possible
            if hasattr(image_data, 'seek'):
                image_data.seek(0)
        else:
            # Assume it's already bytes
            image_bytes = image_data
        
        # Make API request
        logger.info("Sending image to Azure Computer Vision for analysis...")
        response = requests.post(analyze_url, headers=headers, params=params, data=image_bytes)
        
        if response.status_code == 200:
            result = response.json()
            
            # Extract animal-related information
            animals_found = []
            categories = []
            all_tags = []
            max_confidence = 0.0
            
            # Process categories (v3.2 format)
            if 'categories' in result:
                for category in result['categories']:
                    categories.append({
                        'name': category.get('name', ''),
                        'confidence': category.get('score', 0.0)
                    })
                    
                    # Check if category indicates animal
                    cat_name = category.get('name', '').lower()
                    if any(animal_word in cat_name for animal_word in ['animal', 'bird', 'mammal', 'reptile', 'fish', 'insect']):
                        max_confidence = max(max_confidence, category.get('score', 0.0))
            
            # Process tags for animal detection (v3.2 format)
            if 'tags' in result:
                for tag in result['tags']:
                    tag_name = tag.get('name', '').lower()
                    confidence = tag.get('confidence', 0.0)
                    all_tags.append({'name': tag_name, 'confidence': confidence})
                    
                    # Check if tag indicates specific animal
                    animal_keywords = [
                        'dog', 'cat', 'bird', 'lion', 'tiger', 'elephant', 'bear', 'wolf', 
                        'eagle', 'hawk', 'owl', 'parrot', 'snake', 'lizard', 'turtle', 
                        'fish', 'shark', 'whale', 'dolphin', 'butterfly', 'bee', 'spider',
                        'horse', 'cow', 'sheep', 'goat', 'pig', 'chicken', 'duck', 'rabbit',
                        'fox', 'deer', 'moose', 'squirrel', 'mouse', 'rat', 'frog', 'toad'
                    ]
                    
                    if any(keyword in tag_name for keyword in animal_keywords):
                        animals_found.append({
                            'name': tag_name.title(),
                            'confidence': confidence,
                            'source': 'azure_tag'
                        })
                        max_confidence = max(max_confidence, confidence)
            
            # Process objects for animal detection (v3.2 format)
            if 'objects' in result:
                for obj in result['objects']:
                    obj_name = obj.get('object', '').lower()
                    confidence = obj.get('confidence', 0.0)
                    
                    # Check if object is an animal
                    if any(animal_word in obj_name for animal_word in ['animal', 'bird', 'mammal', 'pet']):
                        animals_found.append({
                            'name': obj_name.title(),
                            'confidence': confidence,
                            'source': 'azure_object'
                        })
                        max_confidence = max(max_confidence, confidence)
            
            # Process description for animal mentions (v3.2 format)
            if 'description' in result and 'captions' in result['description']:
                for caption in result['description']['captions']:
                    caption_text = caption.get('text', '').lower()
                    confidence = caption.get('confidence', 0.0)
                    
                    # Look for animal mentions in description
                    animal_words = ['animal', 'bird', 'dog', 'cat', 'wild', 'pet', 'creature', 'wildlife']
                    if any(word in caption_text for word in animal_words):
                        # Extract potential animal names from description
                        description_animals = extract_animals_from_text(caption_text)
                        for animal in description_animals:
                            animals_found.append({
                                'name': animal.title(),
                                'confidence': confidence,
                                'source': 'azure_description'
                            })
                            max_confidence = max(max_confidence, confidence)
            
            # Remove duplicates and sort by confidence
            unique_animals = []
            seen_names = set()
            for animal in animals_found:
                name_lower = animal['name'].lower()
                if name_lower not in seen_names:
                    unique_animals.append(animal)
                    seen_names.add(name_lower)
            
            unique_animals.sort(key=lambda x: x['confidence'], reverse=True)
            
            logger.info(f"Azure analysis completed. Found {len(unique_animals)} potential animals with max confidence {max_confidence:.2f}")
            
            return {
                'success': True,
                'animals': unique_animals[:5],  # Top 5 most confident
                'categories': categories,
                'all_tags': all_tags,
                'confidence': max_confidence,
                'raw_result': result
            }
            
        else:
            error_msg = f"Azure API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'animals': [],
                'categories': [],
                'confidence': 0.0
            }
            
    except Exception as e:
        error_msg = f"Azure Computer Vision analysis failed: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'error': error_msg,
            'animals': [],
            'categories': [],
            'confidence': 0.0
        }

def extract_animals_from_text(text: str) -> List[str]:
    """
    Extract potential animal names from text description
    
    Args:
        text: Text to analyze
    
    Returns:
        List of potential animal names
    """
    # Common animal names that might appear in descriptions
    common_animals = [
        'dog', 'cat', 'bird', 'lion', 'tiger', 'elephant', 'bear', 'wolf', 
        'eagle', 'hawk', 'owl', 'parrot', 'penguin', 'flamingo', 'peacock',
        'snake', 'lizard', 'turtle', 'crocodile', 'alligator', 'iguana',
        'fish', 'shark', 'whale', 'dolphin', 'octopus', 'jellyfish',
        'butterfly', 'bee', 'spider', 'ant', 'dragonfly', 'moth',
        'horse', 'cow', 'sheep', 'goat', 'pig', 'chicken', 'duck', 'rabbit',
        'fox', 'deer', 'moose', 'squirrel', 'mouse', 'rat', 'hamster',
        'frog', 'toad', 'salamander', 'monkey', 'gorilla', 'chimpanzee',
        'zebra', 'giraffe', 'hippopotamus', 'rhinoceros', 'kangaroo'
    ]
    
    found_animals = []
    text_lower = text.lower()
    
    for animal in common_animals:
        if animal in text_lower:
            found_animals.append(animal)
    
    return found_animals

def compare_recognition_results(ai_result: Dict, azure_result: Dict, animal_name: str) -> Dict:
    """
    Compare AI model result with Azure Computer Vision result using similarity analysis
    
    Args:
        ai_result: Result from current AI model (name, type, description)
        azure_result: Result from Azure Computer Vision
        animal_name: Animal name from current AI model
    
    Returns:
        Dict with comparison results and recommendations
    """
    try:
        # Extract Azure's top animal predictions
        azure_animals = azure_result.get('animals', [])
        azure_top_animal = azure_animals[0] if azure_animals else None
        
        # Normalize names for comparison
        ai_name_lower = animal_name.lower().strip()
        
        # Check for direct matches or high similarity
        similarity_score = 0.0
        matching_azure_animal = None
        
        for azure_animal in azure_animals:
            azure_name_lower = azure_animal['name'].lower().strip()
            
            # Direct match
            if ai_name_lower == azure_name_lower:
                similarity_score = 1.0
                matching_azure_animal = azure_animal
                break
            
            # Partial match (one name contains the other)
            if ai_name_lower in azure_name_lower or azure_name_lower in ai_name_lower:
                similarity_score = max(similarity_score, 0.8)
                if similarity_score == 0.8:
                    matching_azure_animal = azure_animal
            
            # Check for common animal type/category matches
            ai_words = set(ai_name_lower.split())
            azure_words = set(azure_name_lower.split())
            common_words = ai_words.intersection(azure_words)
            
            if common_words:
                word_similarity = len(common_words) / max(len(ai_words), len(azure_words))
                if word_similarity > similarity_score:
                    similarity_score = word_similarity
                    matching_azure_animal = azure_animal
        
        # Determine if results are similar enough
        is_similar = similarity_score >= 0.7  # 70% similarity threshold
        
        result = {
            'is_similar': is_similar,
            'similarity_score': similarity_score,
            'ai_prediction': {
                'name': animal_name,
                'type': ai_result.get('type', 'Unknown'),
                'description': ai_result.get('description', ''),
                'confidence': 0.9  # Assume high confidence for current AI model
            },
            'azure_prediction': None,
            'recommendation': 'ai_only'  # Default recommendation
        }
        
        if azure_top_animal:
            result['azure_prediction'] = {
                'name': azure_top_animal['name'],
                'confidence': azure_top_animal['confidence'],
                'source': azure_top_animal.get('source', 'azure')
            }
            
            if is_similar:
                # Results are similar - use AI result but mention Azure confirmation
                result['recommendation'] = 'confirmed'
                result['message'] = f"AI prediction '{animal_name}' confirmed by Azure Computer Vision (similarity: {similarity_score:.1%})"
            else:
                # Results differ - let user choose
                result['recommendation'] = 'user_choice'
                result['message'] = f"Different predictions found. Please choose the correct identification."
        else:
            # Azure found no animals
            result['recommendation'] = 'ai_only'
            result['message'] = f"Azure Computer Vision did not detect specific animals. Using AI model prediction: '{animal_name}'"
        
        return result
        
    except Exception as e:
        logger.error(f"Error comparing recognition results: {e}")
        return {
            'is_similar': False,
            'similarity_score': 0.0,
            'ai_prediction': {
                'name': animal_name,
                'type': ai_result.get('type', 'Unknown'),
                'description': ai_result.get('description', ''),
                'confidence': 0.9
            },
            'azure_prediction': None,
            'recommendation': 'ai_only',
            'message': f"Comparison failed. Using AI model prediction: '{animal_name}'"
        }

def test_azure_connection() -> Dict:
    """
    Test Azure Computer Vision API connection
    
    Returns:
        Dict with connection test results
    """
    try:
        endpoint = st.secrets.get("AZURE_COMPUTER_VISION_ENDPOINT")
        key = st.secrets.get("AZURE_COMPUTER_VISION_KEY")
        
        if not endpoint or not key:
            return {
                'success': False,
                'error': 'Azure credentials not found in secrets.toml'
            }
        
        # Test endpoint accessibility
        test_url = f"{endpoint.rstrip('/')}/vision/v3.2/"
        headers = {'Ocp-Apim-Subscription-Key': key}
        
        response = requests.get(test_url, headers=headers, timeout=10)
        
        return {
            'success': True,
            'endpoint': endpoint,
            'status_code': response.status_code,
            'message': 'Azure Computer Vision API connection successful'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Azure connection test failed: {str(e)}'
        }
