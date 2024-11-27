import base64
import mimetypes
import os
from urllib.parse import urlparse

import dotenv
import requests
import tiktoken
from openai_messages_token_helper import count_tokens_for_image
from pathlib import Path


dotenv.load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def calculate_token_count_from_text(
    text: str, encoding_name: str = "cl100k_base"
) -> int:
    tokens = _generate_tokens(text, encoding_name)
    return len(tokens)


def calculate_token_count_from_image(image_path: str) -> int:
    base64_image = _encode_image(image_path)
    tokens = count_tokens_for_image(base64_image)
    return tokens


def _generate_tokens(text, encoding_name: str = "cl100k_base") -> list:
    encoding = tiktoken.get_encoding(encoding_name)
    tokens = encoding.encode(text)
    return tokens


def _encode_image(image_source: str) -> str:
    is_url = bool(urlparse(image_source).scheme)

    if is_url:
        try:
            response = requests.get(image_source, timeout=10)
            response.raise_for_status()

            mime_type = response.headers.get("content-type", "image/jpeg")
            encoded = base64.b64encode(response.content).decode("utf-8")

        except requests.RequestException as e:
            raise ValueError(f"Failed to fetch image from URL: {str(e)}")
    else:
        image_path = Path(__file__).parent / image_source
        if not image_path.exists():
            raise ValueError(f"Image file not found: {image_source}")

        mime_type = mimetypes.guess_type(image_path)[0]
        if not mime_type:
            mime_type = "image/jpeg"

        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode("utf-8")

    rv = f"data:{mime_type};base64,{encoded}"
    return rv


if __name__ == "__main__":
    input_text = "A quick brown fox jumps over the lazy dog."
    tokens = calculate_token_count_from_text(input_text)
    print(f"Number of tokens in the text: {tokens}")

    input_image = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
    tokens = calculate_token_count_from_image(input_image)
    print(f"Number of tokens in the image: {tokens}")
