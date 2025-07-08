#!/usr/bin/env python3
"""
Test script for YOLOv8 integration in image_utils.py
"""

import os
import sys
from PIL import Image
import requests
from io import BytesIO

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_yolo_model_loading():
    """Test if YOLOv8 model loads correctly"""
    print("🔄 Testing YOLOv8 model loading...")
    
    try:
        from ultralytics import YOLO
        model = YOLO('yolov8l.pt')
        print("✅ YOLOv8 model loaded successfully!")
        return model
    except Exception as e:
        print(f"❌ Failed to load YOLOv8 model: {e}")
        return None

def test_animal_detection():
    """Test animal detection with sample images"""
    print("\n🔄 Testing animal detection...")
    
    try:
        from utils.image_utils import detect_animals_with_yolo, process_images
        
        # Test with a sample animal image (download from internet)
        test_images = [
            ("https://upload.wikimedia.org/wikipedia/commons/thumb/7/73/Lion_waiting_in_Namibia.jpg/320px-Lion_waiting_in_Namibia.jpg", "lion"),
            ("https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/American_Beaver.jpg/320px-American_Beaver.jpg", "animal"),
            ("https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Papio_anubis_%28Serengeti%2C_2009%29.jpg/320px-Papio_anubis_%28Serengeti%2C_2009%29.jpg", "monkey")
        ]
        
        for i, (url, expected_type) in enumerate(test_images):
            try:
                print(f"\n🐾 Testing image {i+1}: {expected_type}")
                
                # Download image with proper User-Agent
                headers = {
                    'User-Agent': 'NatureTrace/1.0 (flora.jiang1990@gmail.com)'
                }
                response = requests.get(url, timeout=10, headers=headers)
                response.raise_for_status()  # Raise an exception for bad status codes
                image = Image.open(BytesIO(response.content))
                image = image.convert('RGB')  # Ensure RGB format
                
                # Test YOLOv8 detection
                detected_animals, confidences, bboxes = detect_animals_with_yolo(image)
                
                if detected_animals and confidences:
                    best_animal = detected_animals[0]
                    best_confidence = confidences[0]
                    print(f"✅ YOLOv8 detected: {best_animal} (confidence: {best_confidence:.2%})")
                    if len(detected_animals) > 1:
                        print(f"   Other detections: {detected_animals[1:]} with confidences {[f'{c:.1%}' for c in confidences[1:]]}")
                else:
                    print("⚠️ YOLOv8 did not detect any animals")
                
                # Test full process_images function
                print("🔄 Testing full process_images function...")
                animal_name, animal_type, description = process_images(image)
                print(f"📋 Result: {animal_name} ({animal_type})")
                print(f"📝 Description: {description}")
                
            except Exception as e:
                print(f"❌ Error testing image {i+1}: {e}")
                
    except Exception as e:
        print(f"❌ Error in animal detection test: {e}")

def test_fallback_functionality():
    """Test fallback functionality when YOLOv8 fails"""
    print("\n🔄 Testing fallback functionality...")
    
    try:
        from utils.image_utils import fallback_animal_detection
        
        # Create a simple test image
        test_image = Image.new('RGB', (640, 480), color='green')
        
        animal_name, animal_type, description = fallback_animal_detection(test_image, "test_lion.jpg")
        print(f"📋 Fallback result: {animal_name} ({animal_type})")
        print(f"📝 Description: {description}")
        
    except Exception as e:
        print(f"❌ Error testing fallback: {e}")

def main():
    """Run all tests"""
    print("🧪 YOLOv8 Integration Test Suite")
    print("=" * 50)
    
    # Test 1: Model loading
    model = test_yolo_model_loading()
    
    if model:
        # Test 2: Animal detection
        test_animal_detection()
    else:
        print("⚠️ Skipping animal detection tests due to model loading failure")
    
    # Test 3: Fallback functionality
    test_fallback_functionality()
    
    print("\n🏁 Test suite completed!")
    print("\n💡 Tips:")
    print("- Make sure you have good internet connection for downloading YOLOv8 model")
    print("- The first run will download yolov8s.pt (~20MB)")
    print("- Test with real animal images for best results")

if __name__ == "__main__":
    main()
