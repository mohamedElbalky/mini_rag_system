from google import genai
from typing import AsyncGenerator
from django.conf import settings
from google.genai.types import Content, Part
import logging

logger = logging.getLogger(__name__)


class LLMHandler:
    """
    Handle LLM interactions with streaming support using google-genai
    Optimized to use the dedicated system_instruction parameter.
    """

    def __init__(self):
        # Initialize the GenAI client using the API key from Django settings
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = "gemini-2.5-flash"
        self.max_tokens = 1000
        # Define the system instruction as a class attribute or constant
        self.system_instruction = (
            "You are a helpful assistant that answers questions based on the provided context. "
            "If the context doesn't contain relevant information, say so and provide a general answer. "
            "Always be concise and accurate."
        )

    async def stream_response(self, query: str, context: str = "") -> AsyncGenerator[str, None]:
        """
        Stream LLM response, passing the context and system instruction separately.
        """
        try:
            # 1. Prepare only the context and user query
            contents = self._prepare_contents(query, context)

            # 2. Stream response from Gemini, passing the system instruction in the config
            stream = self.client.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=genai.types.GenerateContentConfig(
                    max_output_tokens=self.max_tokens,
                    temperature=0.7,
                    # ⭐ KEY CHANGE: Use the dedicated system_instruction parameter
                    system_instruction=self.system_instruction,
                )
            )

            # Iterate over the stream and yield text chunks
            for chunk in stream:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            # Catching the base Exception for logging
            logger.error(f"Error streaming LLM response: {str(e)}")
            yield f"Error: {str(e)}"

    def _prepare_contents(self, query: str, context: str = "") -> list[Content]:
        """
        Prepare messages (Contents) for LLM. 
        This method now only prepares the user-facing prompt (query + context).
        """
        
        # We no longer include the system instruction here
        if context:
            # Combine the context and the user's question clearly
            user_prompt = f"Context:\n{context}\n\nQuestion: {query}"
        else:
            # If no context is retrieved, just send the query
            user_prompt = query

        # We construct a list of Content objects for a single-turn request
        return [
            Content(
                role="user", 
                parts=[Part(text=user_prompt)]
            )
        ]
