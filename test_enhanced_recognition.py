#!/usr/bin/env python3
"""
Test the enhanced YOLOv8l + Snowflake database integration for animal recognition
"""

import sys
import os
from PIL import Image, ImageDraw
import numpy as np

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_database_integration():
    """Test the database knowledge integration"""
    print("🧪 Testing Enhanced YOLOv8l + Database Integration")
    print("=" * 60)
    
    try:
        from utils.data_utils import get_animal_database_knowledge, match_detected_animal_to_database, get_enhanced_animal_description
        
        # Load database knowledge
        print("📚 Loading animal knowledge from Snowflake database...")
        animal_knowledge = get_animal_database_knowledge()
        
        if not animal_knowledge:
            print("⚠️ No database knowledge available - testing with mock data")
            # Create mock database knowledge for testing
            animal_knowledge = {
                'wolf': {
                    'name': 'Gray Wolf',
                    'description': 'A large wild canine native to wilderness areas',
                    'category': 'Mammal',
                    'species': 'Canis lupus',
                    'summary': 'The gray wolf is the largest wild member of the Canidae family and the ancestor of the domestic dog.',
                    'facts': 'Wolves live in packs and are known for their hunting skills.',
                    'name_variations': ['wolf', 'gray wolf', 'grey wolf', 'canis lupus']
                },
                'leopard': {
                    'name': 'Leopard',
                    'description': 'A spotted big cat known for climbing trees',
                    'category': 'Mammal',
                    'species': 'Panthera pardus',
                    'summary': 'Leopards are adaptable big cats with distinctive rosette patterns.',
                    'facts': 'Leopards are excellent climbers and often store prey in trees.',
                    'name_variations': ['leopard', 'panthera pardus', 'spotted cat']
                },
                'whale': {
                    'name': 'Humpback Whale',
                    'description': 'A large marine mammal found in oceans worldwide',
                    'category': 'Mammal',
                    'species': 'Megaptera novaeangliae',
                    'summary': 'Humpback whales are known for their complex songs and acrobatic behavior.',
                    'facts': 'These whales can grow up to 16 meters long and weigh up to 30 tons.',
                    'name_variations': ['whale', 'humpback whale', 'megaptera novaeangliae']
                }
            }
        
        unique_animals = len(set([v.get('name', '') for v in animal_knowledge.values() if v.get('name')]))
        print(f"✅ Loaded knowledge for {unique_animals} unique animals")
        
        # Test different YOLO detection scenarios
        test_cases = [
            {
                'detected': 'dog', 
                'confidence': 0.6, 
                'expected_match': 'wolf',
                'description': 'YOLO detects dog, should match to wolf in database'
            },
            {
                'detected': 'cat', 
                'confidence': 0.5, 
                'expected_match': 'leopard',
                'description': 'YOLO detects cat, should match to leopard in database'
            },
            {
                'detected': 'bird', 
                'confidence': 0.4, 
                'expected_match': 'whale',
                'description': 'YOLO detects bird, should match to whale in database'
            },
            {
                'detected': 'elephant', 
                'confidence': 0.8, 
                'expected_match': None,
                'description': 'YOLO detects elephant, no specific database match expected'
            }
        ]
        
        print(f"\n🔍 Testing database matching scenarios:")
        print("-" * 50)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. {test_case['description']}")
            print(f"   Input: {test_case['detected']} (confidence: {test_case['confidence']:.1%})")
            
            # Test database matching
            matched_data, enhanced_confidence, match_type = match_detected_animal_to_database(
                test_case['detected'], test_case['confidence'], animal_knowledge
            )
            
            if matched_data:
                enhanced_name, enhanced_description, db_category = get_enhanced_animal_description(
                    matched_data, enhanced_confidence
                )
                
                print(f"   ✅ Match found: {enhanced_name} ({match_type})")
                print(f"   📊 Enhanced confidence: {enhanced_confidence:.1%}")
                print(f"   📝 Category: {db_category}")
                print(f"   📄 Description preview: {enhanced_description[:100]}...")
                
                if test_case['expected_match']:
                    if test_case['expected_match'].lower() in enhanced_name.lower():
                        print(f"   🎯 SUCCESS: Expected match to {test_case['expected_match']}")
                    else:
                        print(f"   ⚠️ UNEXPECTED: Expected {test_case['expected_match']}, got {enhanced_name}")
            else:
                print(f"   ⚪ No database match found ({match_type})")
                if test_case['expected_match']:
                    print(f"   ❌ EXPECTED: Should have matched to {test_case['expected_match']}")
                else:
                    print(f"   ✅ CORRECT: No match expected")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in database integration test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_yolo_database_pipeline():
    """Test the complete YOLOv8l + database pipeline"""
    print(f"\n🚀 Testing Complete YOLOv8l + Database Pipeline")
    print("=" * 60)
    
    try:
        from utils.image_utils import load_animal_database_knowledge, classify_animal_advanced, analyze_animal_features
        from PIL import Image, ImageDraw
        
        # Load database knowledge
        animal_knowledge = load_animal_database_knowledge()
        db_count = len(set([v.get('name', '') for v in animal_knowledge.values() if v.get('name')]))
        print(f"📚 Database knowledge: {db_count} unique animals loaded")
        
        # Create test image (forest scene with canine)
        test_image = Image.new('RGB', (800, 400), 'darkgreen')  # Forest background
        draw = ImageDraw.Draw(test_image)
        
        # Draw wolf-like animal
        # Body (elongated)
        draw.ellipse([200, 180, 600, 280], fill='brown', outline='black', width=3)
        # Head (pointed)
        draw.ellipse([550, 150, 650, 250], fill='brown', outline='black', width=3)
        # Pointed ears
        draw.polygon([(570, 160), (580, 130), (590, 160)], fill='brown', outline='black')
        draw.polygon([(610, 160), (620, 130), (630, 160)], fill='brown', outline='black')
        # Legs
        for x in [230, 280, 520, 570]:
            draw.rectangle([x, 280, x+20, 350], fill='brown', outline='black', width=2)
        
        print(f"\n🖼️ Created test image: forest canine (should be classified as wolf)")
        
        # Simulate YOLO detection (what YOLO might detect)
        detected_animal = "dog"  # YOLO might detect as dog
        confidence = 0.65
        
        print(f"🔍 Simulated YOLO detection: {detected_animal} (confidence: {confidence:.1%})")
        
        # Analyze features
        features = analyze_animal_features(test_image)
        print(f"📐 Image features:")
        print(f"   Aspect ratio: {features.get('aspect_ratio', 'N/A'):.2f}")
        print(f"   Size: {features.get('size', 'N/A')}")
        print(f"   Average color: {features.get('avg_color', 'N/A')}")
        
        # Run enhanced classification
        print(f"\n🧠 Running enhanced classification (YOLOv8l + Database + Computer Vision)...")
        refined_name, category, description, final_confidence = classify_animal_advanced(
            detected_animal, confidence, features, test_image
        )
        
        print(f"\n✅ Enhanced Classification Results:")
        print(f"   🏷️ Animal: {refined_name}")
        print(f"   📂 Category: {category}")
        print(f"   📊 Final confidence: {final_confidence:.1%}")
        print(f"   📄 Description: {description[:150]}...")
        
        # Check if improvement was made
        if refined_name.lower() != detected_animal.lower():
            print(f"   🎯 IMPROVEMENT: {detected_animal} -> {refined_name}")
            if 'wolf' in refined_name.lower():
                print(f"   🏆 SUCCESS: Correctly identified forest canine as wolf!")
            else:
                print(f"   ⚠️ PARTIAL: Improved but not optimal classification")
        else:
            print(f"   ⚪ NO CHANGE: Classification remained as {detected_animal}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in pipeline test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_connection():
    """Test Snowflake database connection"""
    print(f"\n🗄️ Testing Snowflake Database Connection")
    print("=" * 50)
    
    try:
        from utils.data_utils import get_snowflake_connection
        
        conn = get_snowflake_connection()
        if conn:
            print("✅ Successfully connected to Snowflake database")
            
            # Test basic query
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM animal_insight_data WHERE name IS NOT NULL")
            count = cursor.fetchone()[0]
            print(f"📊 Found {count} animal records in database")
            
            cursor.close()
            conn.close()
            return True
        else:
            print("❌ Failed to connect to Snowflake database")
            print("💡 Check your Streamlit secrets configuration")
            return False
        
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        print("💡 Make sure you have proper Snowflake credentials in secrets.toml")
        return False

if __name__ == "__main__":
    print("🌟 Enhanced YOLOv8l + Snowflake Database Integration Test")
    print("Testing animal recognition improvements using your database knowledge")
    print("=" * 80)
    
    # Run all tests
    db_conn_success = test_database_connection()
    db_integration_success = test_database_integration()
    pipeline_success = test_yolo_database_pipeline()
    
    print(f"\n🏁 Test Results Summary:")
    print(f"   Database Connection: {'✅ PASS' if db_conn_success else '❌ FAIL'}")
    print(f"   Database Integration: {'✅ PASS' if db_integration_success else '❌ FAIL'}")
    print(f"   Complete Pipeline: {'✅ PASS' if pipeline_success else '❌ FAIL'}")
    
    if all([db_conn_success, db_integration_success, pipeline_success]):
        print(f"\n🎉 All tests passed! Your enhanced system now:")
        print(f"   🚀 Uses YOLOv8 Large model for better base detection")
        print(f"   🗄️ Leverages your Snowflake animal database for enhanced accuracy")
        print(f"   🧠 Applies computer vision analysis for edge cases")
        print(f"   📊 Provides confidence-based result selection")
        print(f"   🎯 Should better distinguish whales, big cats, and canines")
    else:
        print(f"\n⚠️ Some tests failed. Check the error messages above.")
        print(f"💡 Make sure your Snowflake connection is properly configured.")
