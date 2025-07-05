# utils/image_utils.py
import torch
from torchvision import transforms
from PIL import Image
import requests
import hashlib
import numpy as np
from transformers import DetrImageProcessor, DetrForObjectDetection

# Load HF model
processor = DetrImageProcessor.from_pretrained("facebook/detr-resnet-50")
model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50")

def process_images(image):
    transform = transforms.Compose([
        transforms.Resize((480, 480)),
        transforms.ToTensor(),
    ])
    inputs = processor(images=image, return_tensors="pt")
    outputs = model(**inputs)

    # Get predicted label
    logits = outputs.logits[0]
    probs = logits.softmax(dim=-1)
    top_prob, top_label = torch.max(probs, dim=-1)

    label_name = model.config.id2label[top_label.item()]
    description = f"This looks like a {label_name} with confidence {top_prob.item():.2f}"

    return {
        "name": label_name,
        "description": description
    }

def is_duplicate_image(image, uploaded_images):
    """Check if image is a duplicate using SHA256 hash"""
    img_hash = hashlib.sha256(np.array(image).tobytes()).hexdigest()
    for _, data in uploaded_images.items():
        existing_hash = hashlib.sha256(np.array(data['image']).tobytes()).hexdigest()
        if img_hash == existing_hash:
            return True
    return False
