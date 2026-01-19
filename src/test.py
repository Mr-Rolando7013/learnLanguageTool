import os
from dotenv import load_dotenv
from pathlib import Path

# Explicitly point to your .env file
env_path = Path(__file__).resolve().parents[1] / ".env"
print("Looking for .env at:", env_path)

load_dotenv(env_path)

# Check the variable
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    print("✅ OPENAI_API_KEY is set:", api_key[:5] + "…")  # only show first 5 chars
else:
    print("❌ OPENAI_API_KEY is NOT set")