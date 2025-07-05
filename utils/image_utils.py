# utils/image_utils.py
from PIL import Image
import imagehash
import torch
from torchvision import transforms
from transformers import DetrImageProcessor, DetrForObjectDetection

# Load pre-trained DETR model from Hugging Face
processor = DetrImageProcessor.from_pretrained("facebook/detr-resnet-50")
model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50")
model.eval()

def process_images(image):
    """
    Processes an image and returns the most confident object name and dummy description.
    """
    transform = transforms.ToTensor()
    inputs = processor(images=image, return_tensors="pt")

    with torch.no_grad():
        outputs = model(**inputs)

    # Get the top predicted label
    logits = outputs.logits.softmax(-1)[0, :, :-1]  # skip the last class (no object)
    top_idx = logits.max(1).values.argmax().item()
    label = model.config.id2label[outputs.logits[0][top_idx].argmax().item()]

    return {
        "name": label.title(),
        "description": f"This is likely a {label.lower()}. Learn more about its habitat and behavior."
    }

def is_duplicate_image(new_image, existing_images):
    """
    Check whether new_image is a duplicate using perceptual hashing.
    """
    new_hash = imagehash.average_hash(new_image)
    for data in existing_images.values():
        existing_hash = imagehash.average_hash(data['image'])
        if new_hash - existing_hash < 5:  # hamming distance threshold
            return True
    return False
