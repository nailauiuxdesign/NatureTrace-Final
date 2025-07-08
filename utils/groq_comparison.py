# utils/groq_comparison.py

import streamlit as st
from groq import Groq
import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

def get_groq_animal_comparison(ai_prediction: str, azure_predictions: List[Dict], image_context: str = "") -> Dict:
    """
    Use Groq AI to compare and analyze animal predictions from different sources
    
    Args:
        ai_prediction: Animal name from current AI model
        azure_predictions: List of animal predictions from Azure Computer Vision
        image_context: Optional context about the image
    
    Returns:
        Dict with Groq's analysis and recommendations
    """
    try:
        # Initialize Groq client
        groq_api_key = st.secrets.get("groq_api_key")
        if not groq_api_key:
            return {
                'success': False,
                'error': 'Groq API key not found in secrets',
                'recommendation': 'use_ai',
                'confidence': 0.0
            }
        
        client = Groq(api_key=groq_api_key)
        
        # Prepare Azure predictions text
        azure_text = "No specific animals detected"
        if azure_predictions:
            azure_text = ", ".join([
                f"{pred['name']} (confidence: {pred['confidence']:.2f})" 
                for pred in azure_predictions[:3]  # Top 3 predictions
            ])
        
        # Create prompt for Groq
        prompt = f"""
You are an expert zoologist and AI system evaluator. Please analyze these animal identification results:

**Current AI Model Prediction:** {ai_prediction}

**Azure Computer Vision Predictions:** {azure_text}

**Image Context:** {image_context if image_context else "No additional context provided"}

Please analyze these predictions and provide:
1. Are the predictions referring to the same animal or very similar animals?
2. Which prediction is most likely correct?
3. What is your confidence level (0-100)?
4. Brief reasoning for your assessment

Respond in JSON format:
{{
    "same_animal": true/false,
    "most_likely_correct": "ai_prediction" or "azure_prediction" or "uncertain",
    "confidence": 0-100,
    "reasoning": "brief explanation",
    "recommendation": "use_ai" or "use_azure" or "user_choice",
    "similarity_score": 0.0-1.0
}}

Be concise and focus on biological accuracy. Consider that the AI model might be more specific while Azure might be more general.
"""
        
        # Make Groq API call
        logger.info("Sending comparison request to Groq...")
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert zoologist who helps compare animal identification results from different AI systems. Always respond in valid JSON format."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama3-8b-8192",  # Fast model for quick responses
            temperature=0.3,  # Low temperature for consistent, factual responses
            max_tokens=500
        )
        
        response_text = chat_completion.choices[0].message.content.strip()
        
        # Parse JSON response
        try:
            # Clean the response in case there are markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].strip()
            
            result = json.loads(response_text)
            
            # Validate and normalize response
            result['success'] = True
            result['same_animal'] = result.get('same_animal', False)
            result['confidence'] = max(0, min(100, result.get('confidence', 50)))
            result['similarity_score'] = max(0.0, min(1.0, result.get('similarity_score', 0.5)))
            result['most_likely_correct'] = result.get('most_likely_correct', 'uncertain')
            result['recommendation'] = result.get('recommendation', 'user_choice')
            result['reasoning'] = result.get('reasoning', 'Analysis completed')
            
            logger.info(f"Groq comparison completed: {result['recommendation']} (confidence: {result['confidence']}%)")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Groq response as JSON: {e}")
            logger.error(f"Raw response: {response_text}")
            
            # Fallback analysis based on simple text matching
            return create_fallback_comparison(ai_prediction, azure_predictions)
            
    except Exception as e:
        logger.error(f"Groq comparison failed: {e}")
        return create_fallback_comparison(ai_prediction, azure_predictions)

def create_fallback_comparison(ai_prediction: str, azure_predictions: List[Dict]) -> Dict:
    """
    Create a fallback comparison when Groq API fails
    
    Args:
        ai_prediction: AI model prediction
        azure_predictions: Azure predictions
    
    Returns:
        Dict with basic comparison results
    """
    if not azure_predictions:
        return {
            'success': True,
            'same_animal': False,
            'most_likely_correct': 'ai_prediction',
            'confidence': 80,
            'reasoning': 'Azure found no specific animals, using AI model prediction',
            'recommendation': 'use_ai',
            'similarity_score': 0.0
        }
    
    # Simple string matching
    ai_lower = ai_prediction.lower()
    best_match_score = 0.0
    
    for azure_pred in azure_predictions:
        azure_lower = azure_pred['name'].lower()
        
        # Check for exact match
        if ai_lower == azure_lower:
            best_match_score = 1.0
            break
        
        # Check for partial match
        if ai_lower in azure_lower or azure_lower in ai_lower:
            best_match_score = max(best_match_score, 0.8)
        
        # Check for word overlap
        ai_words = set(ai_lower.split())
        azure_words = set(azure_lower.split())
        if ai_words.intersection(azure_words):
            overlap_score = len(ai_words.intersection(azure_words)) / len(ai_words.union(azure_words))
            best_match_score = max(best_match_score, overlap_score)
    
    same_animal = best_match_score >= 0.7
    
    if same_animal:
        recommendation = 'use_ai'
        reasoning = f'AI and Azure predictions are similar (match score: {best_match_score:.1%})'
        confidence = 85
    else:
        recommendation = 'user_choice'
        reasoning = f'AI and Azure predictions differ significantly (match score: {best_match_score:.1%})'
        confidence = 60
    
    return {
        'success': True,
        'same_animal': same_animal,
        'most_likely_correct': 'uncertain' if not same_animal else 'ai_prediction',
        'confidence': confidence,
        'reasoning': reasoning,
        'recommendation': recommendation,
        'similarity_score': best_match_score
    }

def get_animal_classification_confidence(prediction: str, context: str = "") -> Dict:
    """
    Use Groq to assess the confidence and accuracy of an animal classification
    
    Args:
        prediction: Animal name prediction
        context: Additional context about the classification
    
    Returns:
        Dict with confidence assessment
    """
    try:
        groq_api_key = st.secrets.get("groq_api_key")
        if not groq_api_key:
            return {'success': False, 'confidence': 50, 'reasoning': 'Groq API not available'}
        
        client = Groq(api_key=groq_api_key)
        
        prompt = f"""
As an expert zoologist, please assess the animal classification: "{prediction}"

Context: {context if context else "No additional context"}

Provide your assessment in JSON format:
{{
    "confidence": 0-100,
    "is_specific": true/false,
    "is_accurate": true/false,
    "classification_level": "species/genus/family/order/class",
    "suggestions": ["alternative name if applicable"],
    "reasoning": "brief explanation"
}}

Focus on biological accuracy and specificity.
"""
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert zoologist who assesses animal classifications. Always respond in valid JSON format."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama3-8b-8192",
            temperature=0.2,
            max_tokens=300
        )
        
        response_text = chat_completion.choices[0].message.content.strip()
        
        # Parse response
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].strip()
        
        result = json.loads(response_text)
        result['success'] = True
        
        return result
        
    except Exception as e:
        logger.error(f"Groq classification confidence assessment failed: {e}")
        return {
            'success': False,
            'confidence': 75,
            'is_specific': True,
            'is_accurate': True,
            'classification_level': 'species',
            'suggestions': [],
            'reasoning': 'Assessment unavailable, assuming reasonable accuracy'
        }
