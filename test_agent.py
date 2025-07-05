# test_agent.py
import streamlit as st
from PIL import Image
from utils.image_utils import process_images
from utils.llama_utils import generate_animal_facts
from utils.sound_utils import generate_animal_sound


def test_image_recognition():
    st.subheader("🧪 Test: Image Recognition")
    image = Image.new("RGB", (224, 224), color=(255, 255, 255))
    result = process_images(image)
    st.write("Output:", result)


def test_llama_generation():
    st.subheader("🧪 Test: LLaMA Fact Generation")
    example_animal = "penguin"
    fact = generate_animal_facts(example_animal)
    st.write(f"Fun Fact for {example_animal}:", fact)


def test_sound_generation():
    st.subheader("🧪 Test: Animal Sound Description")
    example_animal = "elephant"
    sound = generate_animal_sound(example_animal)
    if sound:
        st.write(f"Simulated Sound for {example_animal}:", sound)
    else:
        st.error("Sound generation failed.")


if __name__ == "__main__":
    st.title("🧪 Blackbox Agent Test Suite")
    test_image_recognition()
    test_llama_generation()
    test_sound_generation()
