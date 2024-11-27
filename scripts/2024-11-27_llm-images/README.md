# README

## Tokens

- https://simonwillison.net/2023/Jun/8/gpt-tokenizers/
- https://tiktokenizer.vercel.app/

Encodings:

- which encodings do tiktoken / openai support
  - https://github.com/openai/tiktoken/blob/main/tiktoken/model.py

## Image Tokens

Calculating tokens from images:

- tiktoken doesn't have support for tokenising images
  - https://github.com/openai/tiktoken/issues/250
- this library tries to solve that problem - https://github.com/pamelafox/openai-messages-token-helper
  - takes the pricing logic presented here https://platform.openai.com/docs/guides/vision#calculating-costs and wraps it into a package
    - requires base64-encoded images
  - there is also this thread with calculation logic https://community.openai.com/t/how-do-i-calculate-image-tokens-in-gpt4-vision/492318/2

Calculating token costs:

- https://help.openai.com/en/articles/7127956-how-much-does-gpt-4-cost
  - costs differ between prompt tokens and sampled tokens
- https://platform.openai.com/docs/guides/vision#calculating-costs

Dev:

- Mime types
  - https://docs.python.org/3/library/mimetypes.html
- Base64 encoding
  - https://docs.python.org/3/library/base64.html
- OpenAI API
  - utilities
    - use the `stop` and `max_tokens` parameters to avoid running out of tokens
  - inputs
    - either a link to the image or the base64
    - add the image as part of the `user` context
    - specify image fidelity
      - high
        - 512x512 tiles, represented as 170 tokens each
        - first scaled to 2048x2048 (if needed)
        - second scaled so that shortest side is 768px long
        - finally count number of 512x512 tiles the image can be divided into
      - low
        - 512x512 tile, represented as 85 tokens

## Image Embeddings

- option one is to generate a text caption of the image and embed that (although this is lossy)
- option two is to directly embed the image using pre-trained models (ie CLIP-based)

Examples:

- https://huggingface.co/blog/image-similarity
- https://cookbook.openai.com/examples/custom_image_embedding_search
