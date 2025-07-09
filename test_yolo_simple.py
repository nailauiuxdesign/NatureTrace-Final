#!/usr/bin/env python3
"""
Simple YOLOv8 test with generated test images
"""

import os
import sys
from PIL import Image, ImageDraw
import numpy as np

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_test_image():
    """Create a simple test image"""
    # Create a simple colored image
    img = Image.new('RGB', (640, 480), color='lightblue')
    draw = ImageDraw.Draw(img)
    
    # Draw a simple animal-like shape (circle for body, smaller circle for head)
    draw.ellipse([200, 200, 400, 350], fill='brown', outline='black', width=3)  # Body
    draw.ellipse([300, 150, 380, 220], fill='brown', outline='black', width=2)  # Head
    draw.ellipse([320, 170, 330, 180], fill='black')  # Eye 1
    draw.ellipse([350, 170, 360, 180], fill='black')  # Eye 2
    
    return img

def test_yolo_with_simple_image():
    """Test YOLOv8 with a simple test image"""
    print("🧪 Testing YOLOv8 with simple test image...")
    
    try:
        from utils.image_utils import detect_animals_with_yolo, process_images
        
        # Create test image
        test_image = create_test_image()
        
        print("🔄 Testing YOLOv8 detection...")
        detected_animal, confidence = detect_animals_with_yolo(test_image)
        
        if detected_animal and confidence:
            print(f"✅ YOLOv8 detected: {detected_animal} (confidence: {confidence:.2%})")
        else:
            print("⚠️ YOLOv8 did not detect any animals in test image")
        
        print("🔄 Testing full process_images function...")
        animal_name, animal_type, description = process_images(test_image)
        print(f"📋 Result: {animal_name} ({animal_type})")
        print(f"📝 Description: {description}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_model_basic_functionality():
    """Test basic YOLOv8 model functionality"""
    print("\n🔄 Testing basic YOLOv8 functionality...")
    
    try:
        from ultralytics import YOLO
        
        # Load model
        model = YOLO('yolov8s.pt')
        print("✅ Model loaded successfully")
        
        # Create a simple test image
        test_array = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Run inference
        results = model(test_array, verbose=False)
        print(f"✅ Inference completed. Found {len(results)} result(s)")
        
        # Check if any detections
        for result in results:
            if result.boxes is not None:
                print(f"📊 Detected {len(result.boxes)} objects")
                for i, box in enumerate(result.boxes):
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    print(f"  - Object {i+1}: Class {class_id}, Confidence: {confidence:.2%}")
            else:
                print("No objects detected")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing basic functionality: {e}")
        return False

def main():
    """Run simplified tests"""
    print("🧪 Simplified YOLOv8 Test Suite")
    print("=" * 40)
    
    # Test 1: Basic model functionality
    basic_test = test_model_basic_functionality()
    
    # Test 2: Test with simple image
    if basic_test:
        test_yolo_with_simple_image()
    else:
        print("⚠️ Skipping image tests due to basic functionality failure")
    
    print("\n🏁 Simplified test completed!")
    print("\n📝 Note: YOLOv8 is primarily trained on common objects.")
    print("   For best results, test with real photos of animals.")

if __name__ == "__main__":
    main()
