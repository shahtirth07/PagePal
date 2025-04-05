# backend/list_google_models.py
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables (specifically GOOGLE_API_KEY)
load_dotenv()

api_key = os.getenv("Google_Api_key")

if not api_key:
    print("Error: GOOGLE_API_KEY not found in .env file.")
    print("Please make sure your Google API key is set in backend/.env")
else:
    try:
        genai.configure(api_key=api_key)
        print("Available Google Generative AI Models supporting 'generateContent':")
        print("-" * 60)
        
        count = 0
        # Iterate through models and print those supporting the needed method
        for m in genai.list_models():
            # 'generateContent' is the method used by Chat models
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
                count += 1
        
        if count == 0:
            print("\nNo models found supporting 'generateContent'.")
            print("Please check:")
            print("1. Your GOOGLE_API_KEY is correct.")
            print("2. The necessary AI APIs (Vertex AI / Generative Language) are enabled in your GCP project.")
            print("3. Billing is enabled for your GCP project.")
            print("4. Your API key has the correct permissions.")
        else:
             print("-" * 60)
             print(f"Found {count} model(s). Use one of the names listed above in your app.py.")

    except Exception as e:
        print(f"\nAn error occurred while trying to list models:")
        print(e)
        print("\nPlease double-check your GOOGLE_API_KEY and Google Cloud project setup.")

