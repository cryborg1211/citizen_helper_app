import os
from google import genai

# Reusing the provided API Key
os.environ["GOOGLE_API_KEY"] = "AIzaSyAOy-oxZH4HNmiHcy7VDz8XxtEE2VATBHA" 

def list_gemma_models():
    """ 
    Connects to the Google API using the new Python SDK to list available Gemma models.
    Used for verifying model accessibility and correct model naming conventions.
    """
    print("Connecting to Google API to verify available models...")
    try:
        # Initialize client using the modern Google SDK
        client = genai.Client()
        
        print("\n=== CURRENTLY AVAILABLE GEMMA MODELS ON API ===")
        found = False
        
        # Iterate through all models hosted by Google
        for model in client.models.list():
            # Filter for models containing 'gemma' in their identifier
            if "gemini" in model.name.lower():
                print(f"👉 Recommended Model ID: '{model.name}'")
                found = True
                
        if not found:
            print("❌ No Gemma models were found for this API key.")
            
    except Exception as e:
        print(f"Error encountered during API connection: {e}")

if __name__ == "__main__":
    list_gemma_models()