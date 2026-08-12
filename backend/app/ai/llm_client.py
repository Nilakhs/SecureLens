import os
import json
import logging
from dotenv import load_dotenv

# Import the official google-genai SDK
try:
    from google import genai
    from google.genai import types
    from google.genai.errors import APIError
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False

logger = logging.getLogger(__name__)

# Load env variables (useful when running standalone scripts)
load_dotenv()


class LLMError(Exception):
    """Base exception for all LLM Client errors."""
    pass


class LLMUnavailableError(LLMError):
    """Raised when the LLM service is not configured or cannot be reached."""
    pass


class LLMTimeoutError(LLMError):
    """Raised when the LLM request times out."""
    pass


class LLMRateLimitError(LLMError):
    """Raised when hitting API rate limits or quota limits."""
    pass


class LLMInvalidResponseError(LLMError):
    """Raised when the response is not valid JSON or doesn't match the schema."""
    pass


class LLMClient:
    """
    Abstraciton layer for LLM API calls.
    Keeps the rest of the application decoupled from the specific provider.
    """

    @staticmethod
    def get_client():
        """Initializes and returns the Google GenAI Client if available and configured."""
        if not SDK_AVAILABLE:
            raise LLMUnavailableError("google-genai SDK is not installed in the environment.")

        api_key = os.getenv("AI_API_KEY")
        if not api_key:
            raise LLMUnavailableError("AI_API_KEY environment variable is not set in backend/.env.")

        try:
            # Create standard GenAI client
            return genai.Client(api_key=api_key)
        except Exception as e:
            logger.error(f"LLMClient: Failed to initialize Gemini Client: {e}")
            raise LLMUnavailableError(f"Failed to initialize Gemini Client: {e}")

    @classmethod
    def complete(cls, prompt: str, system_instruction: str) -> dict:
        """
        Sends the prompt to the Gemini API, requesting a structured JSON response.

        Args:
            prompt: The user prompt containing the code/finding details.
            system_instruction: The system prompt guiding the output format.

        Returns:
            dict containing the parsed JSON response.

        Raises:
            LLMError subclasses on failure.
        """
        # Resolve model from env or use default flash model
        model = os.getenv("AI_MODEL", "gemini-2.5-flash")
        timeout_val = os.getenv("AI_TIMEOUT_SECONDS", "30")
        try:
            timeout = float(timeout_val)
        except ValueError:
            timeout = 30.0

        client = cls.get_client()

        try:
            logger.info(f"LLMClient: Sending request to model {model} (timeout={timeout}s)...")

            # Call the models API
            # Note: client.models.generate_content supports config options
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                )
            )

            if not response or not response.text:
                raise LLMInvalidResponseError("LLM returned an empty or missing response text.")

            # Attempt to parse the response text as JSON
            try:
                data = json.loads(response.text)
                return data
            except json.JSONDecodeError as jde:
                logger.error(f"LLMClient: Failed to parse response text as JSON: {response.text}")
                raise LLMInvalidResponseError(f"LLM response was not valid JSON: {jde}")

        except APIError as ae:
            # Handle standard Google API Errors
            status_code = ae.code
            message = str(ae)
            logger.error(f"LLMClient: Google API Error: Code={status_code}, Message={message}")

            if status_code == 429:
                raise LLMRateLimitError("Gemini API rate limit exceeded. Please try again later.")
            elif status_code == 408 or "timeout" in message.lower():
                raise LLMTimeoutError("Gemini API request timed out.")
            elif status_code in (401, 403):
                raise LLMUnavailableError("Invalid or unauthorized Gemini API key.")
            else:
                raise LLMError(f"Gemini API returned code {status_code}: {message}")

        except Exception as e:
            # Fallback for unexpected exceptions or timeouts
            err_msg = str(e)
            logger.error(f"LLMClient: Unexpected error during complete call: {err_msg}")

            if "timeout" in err_msg.lower() or "deadline exceeded" in err_msg.lower():
                raise LLMTimeoutError("The request to the LLM timed out.")
            raise LLMError(f"An unexpected error occurred while calling the LLM: {err_msg}")
