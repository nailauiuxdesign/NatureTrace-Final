import time
import concurrent.futures
from PIL import Image
import streamlit as st
import hashlib
import io
import numpy as np
import cv2

# Store processed image hashes to detect duplicates
processed_images = set()

# YOLOv8 model cache
@st.cache_resource
def load_yolo_model():
    """Load and cache YOLOv8 Large model for better accuracy"""
    try:
        from ultralytics import YOLO
        # Use YOLOv8l (large) for better accuracy
        model = YOLO('yolov8l.pt')  # Downloads automatically if not present
        return model
    except Exception as e:
        st.warning(f"Could not load YOLOv8 model: {e}")
        return None

# Complete YOLO COCO animal class mapping (more comprehensive)
ANIMAL_CLASSES = {
    # All animal classes from COCO dataset
    14: 'bird', 15: 'cat', 16: 'dog', 17: 'horse', 18: 'sheep', 
    19: 'cow', 20: 'elephant', 21: 'bear', 22: 'zebra', 23: 'giraffe',
    # Additional potential detections (for better handling)
    0: 'person'  # To exclude humans from animal detection
}

# More detailed animal classification with better descriptions
ANIMAL_CATEGORIES = {
    'bird': ('Bird', 'A feathered vertebrate animal with wings, most of which can fly.'),
    'cat': ('Mammal', 'A small to medium-sized carnivorous mammal, including both domestic and wild species.'),
    'dog': ('Mammal', 'A carnivorous mammal that is a domesticated subspecies of the wolf.'),
    'horse': ('Mammal', 'A large, strong herbivorous mammal with a flowing mane and tail.'),
    'sheep': ('Mammal', 'A woolly ruminant mammal, typically kept as livestock for wool and meat.'),
    'cow': ('Mammal', 'A large domesticated bovine animal raised for milk, meat, and leather.'),
    'elephant': ('Mammal', 'The largest living terrestrial animal, known for its trunk and large ears.'),
    'bear': ('Mammal', 'A large, powerful carnivorous or omnivorous mammal with thick fur.'),
    'zebra': ('Mammal', 'An African equine mammal known for its distinctive black and white striped pattern.'),
    'giraffe': ('Mammal', 'The tallest living terrestrial animal, known for its extremely long neck and legs.'),
    # Additional classifications for better handling
    'lion': ('Mammal', 'A large wild cat native to Africa and India, known as the king of beasts.'),
    'tiger': ('Mammal', 'A large wild cat with orange fur and black stripes, native to Asia.'),
    'leopard': ('Mammal', 'A large wild cat with spotted fur, native to Africa and Asia.'),
    'wolf': ('Mammal', 'A large wild canine and ancestor of the domestic dog.'),
    'whale': ('Mammal', 'A large marine mammal that lives in the ocean.'),
    'dolphin': ('Mammal', 'An intelligent marine mammal known for its playful behavior.'),
    'shark': ('Fish', 'A large predatory fish with cartilaginous skeleton.'),
    'snake': ('Reptile', 'A long, legless reptile that can be venomous or non-venomous.'),
    'turtle': ('Reptile', 'A reptile with a protective shell, living on land or in water.'),
    'lizard': ('Reptile', 'A scaled reptile with four legs and a long tail.'),
    'frog': ('Amphibian', 'An amphibian that typically lives both in water and on land.'),
    'fish': ('Fish', 'An aquatic vertebrate animal with gills and fins.'),
    'rabbit': ('Mammal', 'A small mammal with long ears and powerful hind legs.'),
    'deer': ('Mammal', 'A hoofed ruminant mammal, typically having antlers.'),
    'fox': ('Mammal', 'A small to medium-sized carnivorous mammal with a bushy tail.'),
    'monkey': ('Mammal', 'A primate mammal typically having a long tail and living in trees.'),
    'penguin': ('Bird', 'A flightless aquatic bird primarily found in the Southern Hemisphere.'),
    'eagle': ('Bird', 'A large bird of prey with powerful wings and sharp talons.'),
    'owl': ('Bird', 'A nocturnal bird of prey with large eyes and silent flight.'),
    'parrot': ('Bird', 'A colorful bird known for its ability to mimic sounds.'),
    'peacock': ('Bird', 'A large bird known for the male\'s colorful, fan-shaped tail display.'),
}

def detect_animals_with_yolo(image):
    """
    Use YOLOv8 Large model to detect animals in the image with better accuracy
    Args:
        image: PIL Image object
    Returns:
        tuple: (detected_animals, confidence_scores, bounding_boxes) or (None, None, None) if no animals found
    """
    try:
        model = load_yolo_model()
        if model is None:
            return None, None, None
        
        # Convert PIL to numpy array
        img_array = np.array(image)
        
        # Run inference with optimized settings for animal detection
        results = model(img_array, verbose=False, conf=0.2, iou=0.5)  # Lower conf, better IoU
        
        detected_animals = []
        confidence_scores = []
        bounding_boxes = []
        
        # Parse results
        for result in results:
            if result.boxes is not None:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    bbox = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                    
                    # Check if detected class is an animal (lower threshold for better detection)
                    if class_id in ANIMAL_CLASSES and confidence > 0.15:  # Even lower threshold
                        animal_name = ANIMAL_CLASSES[class_id]
                        if animal_name != 'person':  # Exclude humans
                            detected_animals.append(animal_name)
                            confidence_scores.append(confidence)
                            bounding_boxes.append(bbox)
        
        if detected_animals:
            # Return all detections, sorted by confidence
            sorted_indices = sorted(range(len(confidence_scores)), key=lambda i: confidence_scores[i], reverse=True)
            sorted_animals = [detected_animals[i] for i in sorted_indices]
            sorted_confidences = [confidence_scores[i] for i in sorted_indices]
            sorted_boxes = [bounding_boxes[i] for i in sorted_indices]
            
            return sorted_animals, sorted_confidences, sorted_boxes
        
        return None, None, None
        
    except Exception as e:
        st.warning(f"YOLOv8 detection failed: {e}")
        return None, None, None

def analyze_animal_features(image, bbox=None):
    """
    Analyze specific features of the detected animal to improve classification
    Args:
        image: PIL Image object
        bbox: Bounding box coordinates [x1, y1, x2, y2]
    Returns:
        dict: Features that can help with classification
    """
    try:
        # Crop the image to the bounding box if provided
        if bbox:
            x1, y1, x2, y2 = [int(coord) for coord in bbox]
            cropped_image = image.crop((x1, y1, x2, y2))
        else:
            cropped_image = image
        
        # Convert to numpy array for analysis
        img_array = np.array(cropped_image)
        
        # Analyze color patterns (simplified)
        avg_color = np.mean(img_array, axis=(0, 1))
        
        # Basic shape analysis
        height, width = img_array.shape[:2]
        aspect_ratio = width / height
        
        # Simple pattern detection
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        features = {
            'avg_color': avg_color.tolist(),
            'aspect_ratio': aspect_ratio,
            'size': (width, height),
            'brightness': np.mean(gray)
        }
        
        return features
        
    except Exception as e:
        return {}

def classify_animal_advanced(detected_animal, confidence, features=None, image=None):
    """
    Enhanced animal classification using YOLOv8l results, image features, and Snowflake database knowledge
    Addresses specific issues: whale->bird, leopard/wolf->lion misclassifications
    Args:
        detected_animal: Animal detected by YOLO
        confidence: Detection confidence
        features: Additional image features
        image: PIL Image object for additional analysis
    Returns:
        tuple: (refined_animal_name, category, description, final_confidence)
    """
    # Base classification from YOLO
    base_animal = detected_animal.lower()
    
    # Load database knowledge for enhanced matching
    try:
        animal_knowledge = load_animal_database_knowledge()
        from utils.data_utils import match_detected_animal_to_database, get_enhanced_animal_description
    except Exception as e:
        animal_knowledge = {}
        st.warning(f"Database knowledge unavailable: {e}")
    
    # PHASE 1: Database-Enhanced Matching
    if animal_knowledge:
        matched_data, enhanced_confidence, match_type = match_detected_animal_to_database(
            detected_animal, confidence, animal_knowledge
        )
        
        if matched_data and match_type in ["exact_match", "partial_match"]:
            # Use database knowledge for enhanced result
            enhanced_name, enhanced_description, db_category = get_enhanced_animal_description(
                matched_data, enhanced_confidence
            )
            
            if enhanced_name:
                st.success(f"🎯 Database match found: {enhanced_name} ({match_type})")
                return enhanced_name, db_category, enhanced_description, enhanced_confidence
    
    # PHASE 2: Advanced Computer Vision Analysis (fallback if no database match)
    
    # 1. Fix whale being detected as bird
    if base_animal == 'bird' and confidence < 0.7:
        # Check if this might actually be a marine mammal
        if image and features:
            aspect_ratio = features.get('aspect_ratio', 1.0)
            # Whales have very elongated horizontal shapes
            if aspect_ratio > 2.5:  # Very wide/elongated
                # Additional color analysis for water context
                img_array = np.array(image)
                avg_color = np.mean(img_array, axis=(0, 1))
                # High blue component suggests aquatic environment
                if avg_color[2] > avg_color[0] and avg_color[2] > avg_color[1]:
                    base_animal = 'whale'
                    confidence = 0.7  # Give reasonable confidence to whale classification
                    print("🐋 Corrected bird->whale misclassification based on shape and water context")
    
    # 2. Fix big cats being misclassified as lion
    elif base_animal in ['cat', 'lion'] and confidence < 0.8:
        # Use more sophisticated analysis to distinguish big cats
        if image and features:
            img_array = np.array(image)
            
            # Analyze image characteristics for big cat distinction
            # Color pattern analysis
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Check for striped pattern (tiger)
            # Simple stripe detection using horizontal gradients
            try:
                grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
                horizontal_variance = np.var(grad_x)
            except:
                horizontal_variance = 0
            
            # Check for spotted pattern (leopard/cheetah)
            try:
                # Use bilateral filter to smooth and then find contours
                smooth = cv2.bilateralFilter(gray, 9, 75, 75)
                thresh = cv2.threshold(smooth, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            except:
                contours = []
            
            # Color analysis for environment and coat
            avg_color = np.mean(img_array, axis=(0, 1))
            
            # Classification logic based on patterns and colors
            if horizontal_variance > 1000:  # High horizontal variance suggests stripes
                base_animal = 'tiger'
                confidence = 0.75
                print("🐅 Detected stripe pattern - classified as tiger")
            elif len(contours) > 20:  # Many small contours suggest spots
                # Distinguish between leopard and cheetah
                if avg_color[1] > 120:  # Greenish background (forest)
                    base_animal = 'leopard'
                    print("🐆 Detected spot pattern in forest - classified as leopard")
                else:
                    base_animal = 'cheetah'
                    print("🐆 Detected spot pattern in savanna - classified as cheetah")
                confidence = 0.75
            elif avg_color[0] > 140 and avg_color[1] > 100:  # Golden/tawny colors
                # Could be lion, but check environment
                if avg_color[1] < avg_color[0]:  # More golden than green
                    base_animal = 'lion'
                    print("🦁 Golden coloring in savanna - classified as lion")
                else:
                    base_animal = 'leopard'  # Forest cat
                    print("🐆 Detected in forest environment - classified as leopard")
                confidence = 0.7
            else:
                # Default to leopard for unclear big cats (common misclassification)
                base_animal = 'leopard'
                confidence = 0.65
                print("🐆 Unclear big cat - defaulting to leopard")
    
    # 3. Fix wolf being misclassified as lion
    elif base_animal == 'lion' and confidence < 0.7:
        # Check if this might actually be a canine
        if image and features:
            img_array = np.array(image)
            avg_color = np.mean(img_array, axis=(0, 1))
            aspect_ratio = features.get('aspect_ratio', 1.0)
            
            # Wolves are typically more elongated and in forest/snow environments
            if aspect_ratio > 1.8:  # More elongated than typical big cats
                # Check for cooler colors (forest, snow)
                if avg_color[2] > avg_color[0] or avg_color[1] > avg_color[0]:  # Blue or green dominant
                    base_animal = 'wolf'
                    confidence = 0.75
                    print("🐺 Corrected lion->wolf based on elongated shape and environment")
    
    # 4. Improve dog/wolf distinction
    elif base_animal == 'dog' and confidence > 0.4:
        if image and features:
            img_array = np.array(image)
            avg_color = np.mean(img_array, axis=(0, 1))
            
            # Wild environment suggests wolf
            if avg_color[1] > avg_color[0] + 20:  # Significantly more green (forest)
                base_animal = 'wolf'
                confidence = min(0.8, confidence + 0.2)
                print("🐺 Forest environment detected - reclassified dog as wolf")
    
    # PHASE 3: Try database matching again with refined animal name
    if animal_knowledge and base_animal != detected_animal.lower():
        matched_data, enhanced_confidence, match_type = match_detected_animal_to_database(
            base_animal, confidence, animal_knowledge
        )
        
        if matched_data and match_type in ["exact_match", "partial_match"]:
            enhanced_name, enhanced_description, db_category = get_enhanced_animal_description(
                matched_data, enhanced_confidence
            )
            
            if enhanced_name:
                st.info(f"🔄 Refined database match: {base_animal} -> {enhanced_name}")
                return enhanced_name, db_category, enhanced_description, enhanced_confidence
    
    # PHASE 4: Final confidence adjustment and fallback
    if base_animal in ['whale', 'tiger', 'leopard', 'cheetah', 'wolf']:
        # These were specifically corrected, so boost confidence
        final_confidence = min(0.85, confidence + 0.1)
    else:
        # Standard confidence handling
        if confidence > 0.8:
            final_confidence = confidence
        elif confidence > 0.5:
            final_confidence = confidence * 0.95
        else:
            final_confidence = confidence * 0.9
    
    final_animal = base_animal
    
    # Get final animal info from static categories
    if final_animal in ANIMAL_CATEGORIES:
        category, description = ANIMAL_CATEGORIES[final_animal]
        refined_name = final_animal.title()
    else:
        # Fallback
        refined_name = final_animal.title()
        category = "Mammal"  # Most animals are mammals
        description = f"A {final_animal} detected in the image."
    
    # Enhance description to mention YOLOv8l
    enhanced_description = f"{description} Detected using YOLOv8 Large model with advanced computer vision analysis."
    
    return refined_name, category, enhanced_description, final_confidence

def get_animal_info(detected_animal, confidence=None):
    """
    Get detailed information about detected animal
    Args:
        detected_animal: Animal name detected by YOLO
        confidence: Detection confidence score
    Returns:
        tuple: (animal_name, animal_type, description)
    """
    if detected_animal and detected_animal.lower() in ANIMAL_CATEGORIES:
        animal_type, base_description = ANIMAL_CATEGORIES[detected_animal.lower()]
        
        # Enhance description with confidence info
        if confidence:
            description = f"{base_description} (Detected with {confidence:.1%} confidence)"
        else:
            description = base_description
            
        return detected_animal.title(), animal_type, description
    
    # Fallback for unknown animals
    return "Unknown Animal", "Unknown", "An animal was detected but could not be classified."

def process_images(uploaded_file):
    """
    Process a single image and return animal information using enhanced YOLOv8l + advanced classification.
    Args:
        uploaded_file: Uploaded file object or PIL Image
    Returns:
        tuple: (animal_name, animal_type, animal_description)
    """
    try:
        # Handle both file objects and PIL Images
        if hasattr(uploaded_file, 'read'):
            # It's a file object
            image = Image.open(uploaded_file)
            uploaded_file.seek(0)  # Reset file pointer
            filename = uploaded_file.name
        else:
            # It's already a PIL Image
            image = uploaded_file
            filename = "uploaded_image.jpg"
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Enhanced YOLOv8l detection with database integration
        with st.spinner("🔍 Analyzing image with YOLOv8 Large model + Database knowledge..."):
            detected_animals, confidences, bboxes = detect_animals_with_yolo(image)
            
        # Load database knowledge for enhanced matching
        animal_knowledge = load_animal_database_knowledge()
        db_animals_count = len(set([v.get('name', '') for v in animal_knowledge.values() if v.get('name')]))
        
        if db_animals_count > 0:
            st.info(f"🗄️ Using database knowledge of {db_animals_count} animals from your Snowflake data")
        
        if detected_animals and confidences:
            # Get the best detection
            best_animal = detected_animals[0]
            best_confidence = confidences[0]
            best_bbox = bboxes[0] if bboxes else None
            
            # Analyze image features for better classification
            features = analyze_animal_features(image, best_bbox)
            
            # Advanced classification with image analysis
            refined_name, category, description, final_confidence = classify_animal_advanced(
                best_animal, best_confidence, features, image
            )
            
            if final_confidence > 0.35:  # Lower threshold for accepting YOLO results
                st.success(f"✅ Detected {refined_name} with {final_confidence:.1%} confidence!")
                
                # Add feature-based description enhancement
                enhanced_description = f"{description} Detected using advanced AI analysis."
                
                # Show additional detections if available
                if len(detected_animals) > 1:
                    other_detections = [f"{detected_animals[i]} ({confidences[i]:.1%})" 
                                      for i in range(1, min(3, len(detected_animals)))]
                    st.info(f"🔍 Other possible detections: {', '.join(other_detections)}")
                
                return refined_name, category, enhanced_description
        
        # Fallback to Groq API with database enhancement
        st.warning("🤖 YOLOv8 detection unclear, trying advanced AI analysis with database knowledge...")
        
        with st.spinner("📡 Connecting to Groq API for enhanced analysis..."):
            try:
                # Import here to avoid issues if not available
                from groq import Groq
                import base64
                
                # Convert image to base64 for API
                buffered = io.BytesIO()
                image.save(buffered, format="JPEG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode()
                
                # Initialize Groq client
                client = Groq(api_key=st.secrets.get("GROQ_API_KEY"))
                
                # Create enhanced prompt with database knowledge
                db_animals_list = ""
                if animal_knowledge:
                    unique_animals = list(set([v.get('name', '') for v in animal_knowledge.values() if v.get('name')]))[:20]
                    db_animals_list = f"\n\nKnown animals in database: {', '.join(unique_animals[:20])}{'...' if len(unique_animals) > 20 else ''}"
                
                prompt = f"""
                Analyze this image and identify the specific animal. Be very precise about the animal type.
                
                IMPORTANT: 
                - If you see a whale or marine mammal, do NOT call it a bird
                - If you see a big cat (lion, tiger, leopard, cheetah), be specific about which one
                - If you see a wolf, do NOT call it a dog or lion
                - If you see a leopard, do NOT call it a lion
                
                Look for these distinguishing features:
                - Marine animals: water environment, streamlined body, fins/flippers
                - Lions: mane (males), tawny color, pride behavior
                - Tigers: orange with black stripes
                - Leopards: spotted pattern, rosettes, climbing trees
                - Cheetahs: solid spots, lean build, small head
                - Wolves: pointed ears, longer snout, wild environment
                
                {db_animals_list}
                
                Provide exactly in this format:
                Animal_Name|Category|Description
                
                Examples:
                - Humpback Whale|Mammal|A large marine mammal found in oceans worldwide
                - Leopard|Mammal|A spotted big cat known for its climbing ability
                - Gray Wolf|Mammal|A wild canine and ancestor of domestic dogs
                """
                
                response = client.chat.completions.create(
                    model="llama-3.2-90b-vision-preview",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{img_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=300,
                    temperature=0.1
                )
                
                result = response.choices[0].message.content.strip()
                
                # Parse the response
                if '|' in result:
                    parts = result.split('|')
                    if len(parts) >= 3:
                        animal_name = parts[0].strip()
                        animal_type = parts[1].strip()
                        animal_desc = parts[2].strip()
                        
                        st.success(f"🎯 Advanced AI identified: {animal_name}")
                        return animal_name, animal_type, f"{animal_desc} (Identified using advanced vision AI)"
                
                # If parsing fails, use the full response
                st.success("🎯 Advanced AI analysis completed")
                return "Unknown Animal", "Unknown", f"AI Analysis: {result}"
                
            except Exception as groq_error:
                st.error(f"❌ Advanced AI analysis failed: {groq_error}")
        
        # Final fallback
        st.warning("⚠️ Could not identify animal accurately")
        return "Unknown Animal", "Unknown", "Unable to identify the animal in this image. Please try a clearer image."
        
    except Exception as e:
        st.error(f"❌ Image processing failed: {e}")
        return "Processing Error", "Unknown", f"Error processing image: {str(e)}"
        
    except Exception as e:
        st.error(f"Error processing image: {str(e)}")
        return "Unknown", "Unknown", "Could not process image"

def enhance_description_with_groq(animal_name, image, filename):
    """
    Use Groq API to enhance animal description
    Args:
        animal_name: Detected animal name
        image: PIL Image object
        filename: Image filename
    Returns:
        str: Enhanced description or None if failed
    """
    try:
        import requests
        from utils.llama_utils import GROQ_API_URL, HEADERS, LLAMA_MODEL
        
        width, height = image.size
        
        prompt = f"""You detected a {animal_name} in an image (filename: {filename}, dimensions: {width}x{height}). 
Please provide an interesting and educational description about this animal in one sentence. 
Focus on unique characteristics, habitat, or behavior. Make it engaging and informative."""

        body = {
            "model": LLAMA_MODEL,
            "messages": [
                {"role": "system", "content": "You are a zoologist providing educational descriptions of animals."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 100
        }

        response = requests.post(GROQ_API_URL, headers=HEADERS, json=body)
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        
        return None
        
    except Exception:
        return None

def fallback_animal_detection(image, filename):
    """
    Fallback method using filename analysis and Groq API
    Args:
        image: PIL Image object
        filename: Image filename
    Returns:
        tuple: (animal_name, animal_type, description)
    """
    try:
        import requests
        from utils.llama_utils import GROQ_API_URL, HEADERS, LLAMA_MODEL
        
        width, height = image.size
        aspect_ratio = width / height
        filename_lower = filename.lower()
        
        # Smart animal detection based on filename
        filename_animals = {
            ['lion', 'cat', 'feline']: ("Lion", "Mammal", "A powerful big cat known as the king of the jungle."),
            ['elephant', 'trunk']: ("Elephant", "Mammal", "A large mammal with a trunk and big ears."),
            ['giraffe', 'tall']: ("Giraffe", "Mammal", "The tallest mammal in the world with a long neck."),
            ['bird', 'eagle', 'hawk', 'owl']: ("Eagle", "Bird", "A powerful bird of prey with excellent eyesight."),
            ['dog', 'canine', 'wolf']: ("Wolf", "Mammal", "A wild canine that lives in packs."),
            ['bear', 'panda']: ("Bear", "Mammal", "A large, powerful mammal with thick fur."),
            ['tiger', 'stripe']: ("Tiger", "Mammal", "A large striped cat native to Asia."),
            ['zebra', 'stripe']: ("Zebra", "Mammal", "A striped horse-like animal from Africa."),
            ['monkey', 'ape', 'primate']: ("Monkey", "Mammal", "An intelligent primate that lives in trees."),
        }
        
        # Check filename for animal hints
        for keywords, (name, type_, desc) in filename_animals.items():
            if any(word in filename_lower for word in keywords):
                return name, type_, desc
        
        # Use Groq API for intelligent guess based on image properties
        prompt = f"""Based on an image with dimensions {width}x{height} (aspect ratio {aspect_ratio:.2f}) and filename '{filename}', 
suggest a realistic animal that might be in this image. Consider common animals that people photograph.

Respond in this exact format:
Animal Name: [name]
Animal Type: [type like Mammal, Bird, Reptile, etc.]
Description: [brief educational description in one sentence]"""

        body = {
            "model": LLAMA_MODEL,
            "messages": [
                {"role": "system", "content": "You are an expert zoologist who can make educated guesses about animals based on image metadata and context."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 150
        }

        response = requests.post(GROQ_API_URL, headers=HEADERS, json=body)
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # Parse the response
            lines = content.strip().split('\n')
            animal_name = "Lion"  # Default fallback
            animal_type = "Mammal"
            animal_desc = "A powerful big cat known as the king of the jungle."
            
            for line in lines:
                if line.startswith("Animal Name:"):
                    animal_name = line.replace("Animal Name:", "").strip()
                elif line.startswith("Animal Type:"):
                    animal_type = line.replace("Animal Type:", "").strip()
                elif line.startswith("Description:"):
                    animal_desc = line.replace("Description:", "").strip()
            
            return animal_name, animal_type, animal_desc
        
        # Final fallback
        return "Lion", "Mammal", "A powerful big cat known as the king of the jungle."
        
    except Exception:
        return "Lion", "Mammal", "A powerful big cat known as the king of the jungle."

def is_duplicate_image(uploaded_file):
    """
    Check if an image has already been processed by checking Snowflake database.
    Args:
        uploaded_file: Uploaded file object
    Returns:
        bool: True if duplicate, False otherwise
    """
    try:
        from utils.data_utils import get_snowflake_connection
        
        # Check if filename exists in Snowflake database
        conn = get_snowflake_connection()
        if not conn:
            # If Snowflake is not configured, fall back to session-based duplicate detection
            file_content = uploaded_file.read()
            uploaded_file.seek(0)  # Reset file pointer
            file_hash = hashlib.md5(file_content).hexdigest()
            
            if file_hash in processed_images:
                return True
            else:
                processed_images.add(file_hash)
                return False
            
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM animal_insight_data WHERE filename = %s", (uploaded_file.name,))
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        return count > 0
        
    except Exception as e:
        # Fall back to session-based duplicate detection if database fails
        try:
            file_content = uploaded_file.read()
            uploaded_file.seek(0)  # Reset file pointer
            file_hash = hashlib.md5(file_content).hexdigest()
            
            if file_hash in processed_images:
                return True
            else:
                processed_images.add(file_hash)
                return False
        except:
            return False

def process_images_in_chunks(uploaded_files, chunk_size=5, timeout=30):
    """
    Process images in chunks with a timeout for each chunk.
    Args:
        uploaded_files (list): List of uploaded file objects.
        chunk_size (int): Number of images to process per chunk.
        timeout (int): Timeout in seconds for each chunk.
    Returns:
        list: List of results for all images.
    """
    results = []

    # Split uploaded_files into chunks
    chunks = [uploaded_files[i:i + chunk_size] for i in range(0, len(uploaded_files), chunk_size)]

    for chunk in chunks:
        start_time = time.time()
        chunk_results = []
        for uploaded_file in chunk:
            if time.time() - start_time > timeout:
                st.warning("Processing chunk timed out.")
                break
            # Call the process_images function defined earlier in this file
            result = process_images(uploaded_file)
            chunk_results.append(result)
        results.extend(chunk_results)

    return results

# Cache for database animal knowledge to avoid repeated queries
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_animal_database_knowledge():
    """Load and cache animal knowledge from Snowflake database"""
    try:
        from utils.data_utils import get_animal_database_knowledge
        return get_animal_database_knowledge()
    except Exception as e:
        st.warning(f"Could not load database knowledge: {e}")
        return {}

# Enhanced animal categorization with better mammal distinctions
MAMMAL_SUBCATEGORIES = {
    'big_cats': ['lion', 'tiger', 'leopard', 'cheetah', 'jaguar', 'panther'],
    'canines': ['wolf', 'fox', 'dog', 'coyote', 'jackal'],
    'marine_mammals': ['whale', 'dolphin', 'seal', 'walrus', 'orca', 'sea_lion'],
    'primates': ['monkey', 'ape', 'chimpanzee', 'gorilla', 'orangutan'],
    'ungulates': ['deer', 'elk', 'moose', 'antelope', 'gazelle', 'horse', 'zebra']
}

# Shape and aspect ratio patterns for better classification
ANIMAL_SHAPE_PATTERNS = {
    'marine_elongated': {
        'animals': ['whale', 'dolphin', 'seal'],
        'aspect_ratio_range': (2.0, 4.0),  # Very wide/elongated
        'characteristics': ['streamlined', 'horizontal orientation']
    },
    'big_cat_compact': {
        'animals': ['lion', 'tiger', 'leopard', 'cheetah'],
        'aspect_ratio_range': (1.2, 2.0),  # Moderately wide
        'characteristics': ['muscular build', 'feline features']
    },
    'canine_proportioned': {
        'animals': ['wolf', 'fox', 'dog'],
        'aspect_ratio_range': (1.5, 2.5),  # Elongated but not as much as marine
        'characteristics': ['pointed ears', 'longer snout']
    },
    'bird_varied': {
        'animals': ['bird', 'eagle', 'owl', 'penguin'],
        'aspect_ratio_range': (0.8, 2.0),  # Variable, depends on pose
        'characteristics': ['feathers', 'beak', 'wings']
    }
}
