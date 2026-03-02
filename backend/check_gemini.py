import os
from google import genai

# 1. Configuration - Use your newest key here
# Try hardcoding it first to eliminate environment variable issues
TEST_KEY = "xxx" 

def test_gemini_connection():
    print("--- Gemini API Connectivity Test ---")
    print(f"Testing Key: {TEST_KEY[:10]}...")

    try:
        # Initialize the modern Client
        client = genai.Client(api_key=TEST_KEY.strip())
        
        print("Sending test request to gemini-3-pro...")
        
        # Simple test generation
        response = client.models.generate_content(
            model="gemini-3.1-pro-preview",
            contents="Hello! If you can read this, the API key is working. Give me a 5-word security tip."
        )
        
        print("\n✅ SUCCESS!")
        print(f"AI Response: {response.text}")
        
    except Exception as e:
        print("\n❌ FAILED")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        
        if "API_KEY_INVALID" in str(e):
            print("\nSUGGESTION: The key is formatted correctly but Google doesn't recognize it.")
            print("1. Check if the key was deleted in AI Studio.")
            print("2. Ensure 'Generative Language API' is enabled in Google Cloud Console.")

def list_all_available_models():
    client = genai.Client(api_key=TEST_KEY.strip())
    print("--- 🔍 Scanning for ALL Accessible Gemini Models ---")
    
    try:
        # In the 2026 SDK, we use this to get the base Google models
        # instead of just your "owned" models.
        models = client.models.list()
        
        found = False
        for model in models:
            # We look for the newest 3.x and 2.x models
            if "gemini" in model.name:
                print(f"✅ Found: {model.name}")
                found = True
        
        if not found:
            print("❌ No base models found. Trying 2.5 Pro check...")
            # Fallback test: manually try to call the most stable Pro
            try:
                res = client.models.generate_content(
                    model="gemini-2.5-pro",
                    contents="test"
                )
                print("💡 gemini-2.5-pro is ACTIVE and working.")
            except:
                print("❌ gemini-2.5-pro is also unreachable.")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    #test_gemini_connection()
    #list_all_available_models()
    test_gemini_connection()