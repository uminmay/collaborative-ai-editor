from typing import Optional, Dict, Any
import httpx
import logging
from ..core.settings import settings

logger = logging.getLogger(__name__)

class GroqService:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = settings.GROQ_MODEL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def get_code_completion(self, context: str, cursor_position: int) -> Optional[str]:
        """
        Get code completion from Groq API
        """
        try:
            # Get surrounding context
            context_before = context[:cursor_position].split('\n')[-3:]
            context_after = context[cursor_position:].split('\n')[:2]
            
            prompt_context = '\n'.join(context_before + context_after)
            
            # Check for empty context
            if not prompt_context.strip():
                return ""
            
            payload = {
                "model": settings.GROQ_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": """You are a code completion assistant. Follow these rules:
1. Provide only raw code completions, no markdown or explanations
2. Continue from the exact cursor position, not from the line start
3. Don't repeat code that's already in the context
4. Keep completions concise and contextual
5. Don't add docstrings or comments
6. Make sure to add spaces between context and response when needed things like comma in imports etc.
7. If user has moved to newline, don't complete the line, only complete the current line.
8. Try to put one statement per completion, unless it's a multi-line statement."""
                    },
                    {
                        "role": "user",
                        "content": f"Complete this code from the cursor position:\n{prompt_context}"
                    }
                ],
                "temperature": settings.GROQ_TEMPERATURE,
                "max_completion_tokens": settings.GROQ_MAX_TOKENS,
                "stream": False
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=settings.GROQ_REQUEST_TIMEOUT
                )
                
                if response.status_code == 200:
                    completion = response.json()["choices"][0]["message"]["content"].strip()
                    # Remove any markdown code block markers if they exist
                    completion = completion.replace('```python', '').replace('```', '').strip()
                    return completion
                else:
                    logger.error(f"Groq API error: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting code completion: {e}")
            return None

    async def validate_api_key(self) -> bool:
        """Validate that the Groq API key is working"""
        try:
            test_prompt = "def test_function():"
            result = await self.get_code_completion(test_prompt, len(test_prompt))
            return result is not None
        except Exception as e:
            logger.error(f"API key validation error: {e}")
            return False

# Create global instance
groq_service = GroqService()