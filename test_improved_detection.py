#!/usr/bin/env python3
"""
Test the improved YOLOv8 animal detection with real processing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw
from utils.image_utils import detect_animals_with_yolo, classify_animal_advanced, analyze_animal_features

def test_improved_detection():
    """Test the improved detection logic"""
    print("🧪 Testing Improved Animal Detection")
    print("=" * 50)
    
    # Create test images that represent the problem cases
    
    # Test 1: Create a whale-like image (should not be classified as bird)
    print("\n🐋 Test 1: Whale-like image (wide marine animal)")
    whale_img = Image.new('RGB', (800, 300), 'lightblue')  # Wide aspect ratio, blue background
    draw = ImageDraw.Draw(whale_img)
    # Draw whale-like shape
    draw.ellipse([100, 100, 700, 200], fill='darkblue', outline='black', width=3)
    draw.ellipse([650, 140, 720, 160], fill='darkblue', outline='black', width=2)  # tail
    
    # Test detection
    animals, confidences, bboxes = detect_animals_with_yolo(whale_img)
    if animals:
        features = analyze_animal_features(whale_img, bboxes[0] if bboxes else None)
        refined_name, category, description, final_confidence = classify_animal_advanced(
            animals[0], confidences[0], features, whale_img
        )
        print(f"   YOLO detected: {animals[0]} ({confidences[0]:.2f})")
        print(f"   Refined to: {refined_name} ({final_confidence:.2f})")
        print(f"   Features: aspect_ratio={features.get('aspect_ratio', 'N/A'):.2f}")
    else:
        print("   No animals detected")
    
    # Test 2: Create a big cat image (should distinguish between lion/leopard/tiger)
    print("\n🐅 Test 2: Big cat image (spotted pattern - should be leopard)")
    cat_img = Image.new('RGB', (600, 400), 'darkgreen')  # Forest background
    draw = ImageDraw.Draw(cat_img)
    # Draw cat-like shape with spots
    draw.ellipse([200, 200, 400, 300], fill='orange', outline='black', width=2)  # body
    draw.ellipse([350, 150, 450, 250], fill='orange', outline='black', width=2)  # head
    # Add spots for leopard pattern
    for x in range(220, 380, 30):
        for y in range(220, 280, 25):
            draw.ellipse([x, y, x+8, y+8], fill='black')
    
    animals, confidences, bboxes = detect_animals_with_yolo(cat_img)
    if animals:
        features = analyze_animal_features(cat_img, bboxes[0] if bboxes else None)
        refined_name, category, description, final_confidence = classify_animal_advanced(
            animals[0], confidences[0], features, cat_img
        )
        print(f"   YOLO detected: {animals[0]} ({confidences[0]:.2f})")
        print(f"   Refined to: {refined_name} ({final_confidence:.2f})")
        print(f"   Features: aspect_ratio={features.get('aspect_ratio', 'N/A'):.2f}")
    else:
        print("   No animals detected")
    
    # Test 3: Create a wolf-like image (should not be classified as dog or lion)
    print("\n🐺 Test 3: Wolf-like image (wild canine in forest)")
    wolf_img = Image.new('RGB', (500, 400), 'darkgreen')  # Forest background
    draw = ImageDraw.Draw(wolf_img)
    # Draw wolf-like shape
    draw.ellipse([150, 220, 350, 320], fill='gray', outline='black', width=2)  # body
    draw.ellipse([300, 180, 400, 280], fill='gray', outline='black', width=2)  # head
    # Pointed ears
    draw.polygon([(320, 190), (330, 160), (340, 190)], fill='gray', outline='black')
    draw.polygon([(360, 190), (370, 160), (380, 190)], fill='gray', outline='black')
    
    animals, confidences, bboxes = detect_animals_with_yolo(wolf_img)
    if animals:
        features = analyze_animal_features(wolf_img, bboxes[0] if bboxes else None)
        refined_name, category, description, final_confidence = classify_animal_advanced(
            animals[0], confidences[0], features, wolf_img
        )
        print(f"   YOLO detected: {animals[0]} ({confidences[0]:.2f})")
        print(f"   Refined to: {refined_name} ({final_confidence:.2f})")
        print(f"   Features: aspect_ratio={features.get('aspect_ratio', 'N/A'):.2f}")
    else:
        print("   No animals detected")
    
    print("\n🏁 Improved detection test completed!")
    print("💡 The classification now uses:")
    print("   - Image features (aspect ratio, colors)")
    print("   - Background analysis (water, forest)")
    print("   - Size and shape heuristics")
    print("   - Lower confidence thresholds for better detection")

if __name__ == "__main__":
    test_improved_detection()
