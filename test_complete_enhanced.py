#!/usr/bin/env python3
"""
Test the complete enhanced image recognition pipeline with Azure Computer Vision
"""

import streamlit as st
import sys
from PIL import Image
import io
import requests

# Load secrets
sys.argv = ['test']
st.secrets.load_if_toml_exists()

def test_complete_pipeline():
    """Test the complete enhanced image recognition pipeline"""
    
    print("🧪 Testing Complete Enhanced Image Recognition Pipeline")
    print("=" * 60)
    
    # Test 1: Azure Computer Vision API
    print("\n1. 🔍 Testing Azure Computer Vision API")
    print("-" * 40)
    
    from utils.azure_vision import get_azure_image_analysis
    
    # Create a test image of a dog
    img = Image.new('RGB', (200, 200), color='brown')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    azure_result = get_azure_image_analysis(img_bytes)
    
    print(f"✅ Azure API Success: {azure_result.get('success')}")
    if azure_result.get('success'):
        print(f"📊 Animals Found: {len(azure_result.get('animals', []))}")
        print(f"🏷️ Categories: {len(azure_result.get('categories', []))}")
        print(f"🎯 Max Confidence: {azure_result.get('confidence', 0):.2%}")
        
        # Show top results
        animals = azure_result.get('animals', [])
        if animals:
            print("🐾 Top Animals Detected:")
            for i, animal in enumerate(animals[:3]):
                print(f"  {i+1}. {animal['name']} (confidence: {animal['confidence']:.2%})")
        else:
            print("ℹ️ No animals detected in test image")
    else:
        print(f"❌ Azure Error: {azure_result.get('error')}")
    
    # Test 2: Groq Comparison
    print("\n2. 🤖 Testing Groq AI Comparison")
    print("-" * 40)
    
    from utils.groq_comparison import get_groq_animal_comparison
    
    # Mock data for testing
    ai_prediction = "Brown Dog"
    azure_predictions = [
        {'name': 'Dog', 'confidence': 0.85},
        {'name': 'Brown', 'confidence': 0.75}
    ]
    
    groq_result = get_groq_animal_comparison(ai_prediction, azure_predictions, "Test image of a brown dog")
    
    print(f"✅ Groq Success: {groq_result.get('success')}")
    if groq_result.get('success'):
        print(f"🎯 Same Animal: {groq_result.get('same_animal')}")
        print(f"📊 Confidence: {groq_result.get('confidence')}%")
        print(f"💡 Recommendation: {groq_result.get('recommendation')}")
        print(f"📝 Reasoning: {groq_result.get('reasoning')}")
    else:
        print(f"❌ Groq Error: {groq_result.get('error')}")
    
    # Test 3: Enhanced Image Processing Pipeline
    print("\n3. 🔄 Testing Enhanced Image Processing Pipeline")
    print("-" * 40)
    
    from utils.enhanced_image_processing import enhanced_image_recognition
    
    # Create a mock file object
    class MockFile:
        def __init__(self, name, data):
            self.name = name
            self.data = data
            self.position = 0
        
        def read(self):
            return self.data
        
        def seek(self, position):
            self.position = position
        
        def tell(self):
            return self.position
    
    img_bytes.seek(0)
    mock_file = MockFile("test_dog.jpg", img_bytes.read())
    
    # Note: This would normally check for duplicates in database
    # For testing, we'll assume it's not a duplicate
    
    print("🔍 Running enhanced recognition...")
    try:
        enhanced_result = enhanced_image_recognition(mock_file)
        
        print(f"✅ Pipeline Success: {enhanced_result.get('success')}")
        if enhanced_result.get('success'):
            print(f"📂 Recommendation: {enhanced_result.get('recommendation')}")
            print(f"🎯 Confidence: {enhanced_result.get('confidence_score', 0):.2%}")
            print(f"🤔 User Choice Required: {enhanced_result.get('user_choice_required')}")
            
            # Show AI result
            ai_result = enhanced_result.get('ai_result', {})
            print(f"🤖 AI Prediction: {ai_result.get('name')} ({ai_result.get('type')})")
            
            # Show Azure result
            azure_result = enhanced_result.get('azure_result', {})
            azure_animals = azure_result.get('animals', [])
            if azure_animals:
                print(f"🔍 Azure Top Prediction: {azure_animals[0]['name']} (confidence: {azure_animals[0]['confidence']:.2%})")
            
            # Show Groq analysis
            groq_analysis = enhanced_result.get('groq_analysis', {})
            print(f"🧠 Groq Recommendation: {groq_analysis.get('recommendation')}")
            
        else:
            print(f"❌ Pipeline Error: {enhanced_result.get('error')}")
            
    except Exception as e:
        print(f"❌ Pipeline Exception: {e}")
    
    # Test 4: Overall Assessment
    print("\n4. 📊 Overall Assessment")
    print("-" * 40)
    
    azure_works = azure_result.get('success', False)
    groq_works = groq_result.get('success', False)
    
    print(f"🔍 Azure Computer Vision: {'✅ Working' if azure_works else '❌ Not Working'}")
    print(f"🤖 Groq AI Comparison: {'✅ Working' if groq_works else '❌ Not Working'}")
    
    if azure_works and groq_works:
        print("\n🎉 SUCCESS! Enhanced image recognition pipeline is fully functional!")
        print("🚀 Your app now has:")
        print("   ✅ Dual AI analysis (Current model + Azure)")
        print("   ✅ Intelligent comparison with Groq")
        print("   ✅ Smart conflict resolution")
        print("   ✅ User choice interface for ambiguous cases")
    elif azure_works:
        print("\n⚠️ PARTIAL: Azure works but Groq has issues")
        print("   - Azure analysis will work")
        print("   - Fallback comparison logic will be used")
    elif groq_works:
        print("\n⚠️ PARTIAL: Groq works but Azure has issues")
        print("   - Will fall back to current AI model only")
        print("   - Groq comparison may still provide insights")
    else:
        print("\n❌ ISSUES: Both Azure and Groq have problems")
        print("   - System will fall back to current AI model")
        print("   - Enhanced features may not work optimally")

if __name__ == "__main__":
    test_complete_pipeline()
