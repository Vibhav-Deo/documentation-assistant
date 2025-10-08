import json
import requests
from fastapi import HTTPException
from config import OLLAMA_API_URL

class AIService:
    def __init__(self):
        self.api_url = OLLAMA_API_URL
        self.system_prompts = {
            "default": "You are a helpful AI assistant.",
            "technical": "You are a technical documentation expert.",
            "support": "You are a customer support specialist."
        }
    
    def generate_response(self, prompt: str, model: str = "mistral", temperature: float = 0.7) -> str:
        """Generate AI response using Ollama"""
        try:
            payload = {
                "model": model, 
                "prompt": prompt,
                "options": {
                    "temperature": temperature,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1
                }
            }
            r = requests.post(
                self.api_url,
                json=payload,
                stream=True,
                timeout=60
            )
            r.raise_for_status()
            
            answer_parts = []
            for line in r.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode("utf-8"))
                        if "response" in data:
                            answer_parts.append(data["response"])
                    except json.JSONDecodeError:
                        continue
            
            return "".join(answer_parts).strip()
            
        except (requests.ConnectionError, requests.Timeout) as e:
            raise HTTPException(status_code=503, detail=f"Ollama service unavailable: {str(e)}")
        except requests.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Ollama API error: {str(e)}")
    
    def build_prompt(self, question: str, context: str = "", context_history: str = "") -> str:
        """Build enhanced prompt for AI model"""
        prompt_parts = [
            "You are a helpful AI assistant specialized in providing accurate, well-structured answers."
        ]
        
        if context_history:
            prompt_parts.append(f"\nPrevious conversation context:\n{context_history}")
        
        if context:
            prompt_parts.extend([
                "\nInstructions:",
                "- Answer based ONLY on the provided context",
                "- Be specific and cite relevant information",
                "- If the context doesn't contain the answer, say so clearly",
                "- Structure your response with clear sections if needed",
                "- Use bullet points or numbered lists for clarity when appropriate",
                f"\nContext:\n{context}",
                f"\nQuestion: {question}",
                "\nAnswer:"
            ])
        else:
            prompt_parts.extend([
                "\nInstructions:",
                "- Provide accurate, helpful information",
                "- Be concise but comprehensive",
                "- Structure your response clearly",
                "- If you're uncertain, acknowledge limitations",
                f"\nQuestion: {question}",
                "\nAnswer:"
            ])
        
        return "\n".join(prompt_parts)
    
    def get_system_prompt(self, prompt_type: str = "default") -> str:
        """Get system prompt based on use case"""
        return self.system_prompts.get(prompt_type, self.system_prompts["default"])
    
    def build_contextual_prompt(self, question: str, context: str = "", context_history: str = "", prompt_type: str = "default") -> str:
        """Build prompt with system context for specific use cases"""
        system_prompt = self.get_system_prompt(prompt_type)
        base_prompt = self.build_prompt(question, context, context_history)
        return f"{system_prompt}\n\n{base_prompt}"