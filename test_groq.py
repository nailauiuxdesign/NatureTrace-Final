import groq
import os

def test_groq_setup():
    try:
        # Check if GROQ_API_KEY is set
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            print("⚠️ GROQ_API_KEY environment variable is not set.")
            print("\nTo use Groq, you need to:")
            print("1. Get an API key from https://console.groq.com")
            print("2. Set the environment variable GROQ_API_KEY with your key")
            print("\nOn Windows, you can set it using:")
            print("set GROQ_API_KEY=your_api_key_here")
            return False
        
        # Initialize Groq client
        client = groq.Groq(api_key=api_key)
        print("✅ Groq package installed successfully!")
        print("✅ API key is set!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing Groq setup: {str(e)}")
        return False

if __name__ == "__main__":
    test_groq_setup()
