import os

API_URL = os.getenv("API_URL", "http://api:4000")
MODEL_OPTIONS = ["gpt-oss:120b", "mistral", "llama2", "codellama", "neural-chat"]
SEARCH_TYPES = ["semantic", "hybrid", "keyword"]