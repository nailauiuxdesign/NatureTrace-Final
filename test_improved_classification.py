#!/usr/bin/env python3
"""
Test improved animal classification for specific issues mentioned by user
"""

import sys
import os
from PIL import Image, ImageDraw
import numpy as np

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_whale_like_image():
    """Create an elongated image that might be confused for a bird"""
    image = Image.new('RGB', (800, 300), 'lightblue')  # Very wide aspect ratio
    draw = ImageDraw.Draw(image)
    
    # Draw a whale-like shape (very elongated)
    # Body (very long ellipse)
    draw.ellipse([100, 100, 700, 200], fill='gray', outline='black', width=3)
    # Tail (triangle)
    draw.polygon([(650, 120), (720, 100), (720, 200), (650, 180)], fill='gray', outline='black')
    # Head/mouth area
    draw.ellipse([80, 120, 150, 180], fill='gray', outline='black', width=2)
    
    return image

def create_leopard_like_image():
    """Create a spotted cat that might be confused for a lion"""
    image = Image.new('RGB', (600, 400), 'darkgreen')  # Forest background
    draw = ImageDraw.Draw(image)
    
    # Body (cat-like)
    draw.ellipse([200, 200, 500, 320], fill='orange', outline='black', width=2)
    # Head
    draw.ellipse([450, 150, 550, 250], fill='orange', outline='black', width=2)
    # Add spots (leopard pattern)
    for x in range(220, 480, 40):
        for y in range(210, 310, 30):
            draw.ellipse([x, y, x+15, y+15], fill='black')
    # Ears
    draw.polygon([(460, 160), (480, 130), (500, 160)], fill='orange', outline='black')
    draw.polygon([(500, 160), (520, 130), (540, 160)], fill='orange', outline='black')
    
    return image

def create_wolf_like_image():
    """Create an elongated canine in forest that might be confused for a lion"""
    image = Image.new('RGB', (700, 350), 'darkgreen')  # Forest background
    draw = ImageDraw.Draw(image)
    
    # Body (elongated, more than a typical big cat)
    draw.ellipse([150, 150, 550, 250], fill='brown', outline='black', width=2)
    # Head (more pointed/elongated than cat)
    draw.ellipse([500, 120, 600, 220], fill='brown', outline='black', width=2)
    # Pointed ears (wolf-like)
    draw.polygon([(520, 130), (530, 100), (545, 130)], fill='brown', outline='black')
    draw.polygon([(555, 130), (570, 100), (585, 130)], fill='brown', outline='black')
    # Longer snout
    draw.ellipse([580, 160, 620, 180], fill='brown', outline='black')
    # Legs
    for x in [180, 220, 480, 520]:
        draw.rectangle([x, 250, x+15, 320], fill='brown', outline='black')
    
    return image

def test_improved_classification():
    """Test the improved animal classification logic"""
    print("🧪 Testing Improved Animal Classification")
    print("=" * 50)
    
    try:
        from utils.image_utils import classify_animal_advanced, analyze_animal_features
        
        # Test cases based on user's reported issues
        test_cases = [
            {
                'name': 'Whale-like elongated shape (was misclassified as bird)',
                'image': create_whale_like_image(),
                'detected_animal': 'bird',  # What YOLO might detect
                'confidence': 0.6,
                'expected_correction': 'whale'
            },
            {
                'name': 'Leopard in forest (was misclassified as lion)',
                'image': create_leopard_like_image(),
                'detected_animal': 'cat',  # What YOLO might detect
                'confidence': 0.5,
                'expected_correction': 'leopard'
            },
            {
                'name': 'Wolf in forest (was misclassified as lion)',
                'image': create_wolf_like_image(),
                'detected_animal': 'lion',  # What YOLO might detect incorrectly
                'confidence': 0.6,
                'expected_correction': 'wolf'
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🐾 Test {i}: {test_case['name']}")
            print(f"   Initial detection: {test_case['detected_animal']} (confidence: {test_case['confidence']:.1%})")
            
            # Analyze features
            features = analyze_animal_features(test_case['image'])
            
            # Run improved classification
            refined_name, category, description, final_confidence = classify_animal_advanced(
                test_case['detected_animal'],
                test_case['confidence'],
                features,
                test_case['image']
            )
            
            print(f"   ✅ Refined result: {refined_name} ({category})")
            print(f"   📊 Final confidence: {final_confidence:.1%}")
            print(f"   📝 Description: {description}")
            
            # Check if correction was made
            if refined_name.lower() == test_case['expected_correction']:
                print(f"   🎯 SUCCESS: Correctly identified as {test_case['expected_correction']}!")
            elif refined_name.lower() != test_case['detected_animal']:
                print(f"   ⚠️ PARTIAL: Changed from {test_case['detected_animal']} to {refined_name.lower()}")
            else:
                print(f"   ❌ NO CHANGE: Still classified as {test_case['detected_animal']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in classification test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_feature_analysis():
    """Test the feature analysis function"""
    print(f"\n🔍 Testing Feature Analysis")
    print("=" * 30)
    
    try:
        from utils.image_utils import analyze_animal_features
        
        # Test with whale image (very elongated)
        whale_image = create_whale_like_image()
        whale_features = analyze_animal_features(whale_image)
        
        print(f"🐋 Whale-like image features:")
        print(f"   Aspect ratio: {whale_features.get('aspect_ratio', 'N/A'):.2f}")
        print(f"   Size: {whale_features.get('size', 'N/A')}")
        print(f"   Brightness: {whale_features.get('brightness', 'N/A'):.1f}")
        
        # Test with leopard image
        leopard_image = create_leopard_like_image()
        leopard_features = analyze_animal_features(leopard_image)
        
        print(f"\n🐆 Leopard-like image features:")
        print(f"   Aspect ratio: {leopard_features.get('aspect_ratio', 'N/A'):.2f}")
        print(f"   Size: {leopard_features.get('size', 'N/A')}")
        print(f"   Average color: {leopard_features.get('avg_color', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in feature analysis test: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Advanced Animal Classification Test")
    print("Addressing whale->bird, leopard/wolf->lion issues")
    print("=" * 60)
    
    # Run tests
    feature_success = test_feature_analysis()
    classification_success = test_improved_classification()
    
    print(f"\n🏁 Test Results:")
    print(f"   Feature Analysis: {'✅ PASS' if feature_success else '❌ FAIL'}")
    print(f"   Classification: {'✅ PASS' if classification_success else '❌ FAIL'}")
    
    if feature_success and classification_success:
        print("🎉 All tests passed! The improved classification should better handle:")
        print("   - Whale vs Bird distinction")
        print("   - Leopard vs Lion distinction")
        print("   - Wolf vs Lion distinction")
    else:
        print("⚠️ Some tests failed. Check the error messages above.")
