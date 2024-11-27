import datetime
import os
import pathlib

from typing import List

import dotenv
import requests

from rich.pretty import pprint

dotenv.load_dotenv()

# authentication

RAINDROP_API_KEY = os.getenv("RAINDROP_API_KEY", None)

if not RAINDROP_API_KEY:
    raise ValueError("RAINDROP_API_KEY not found in the environment variables.")

# constants

ROOT_PATH = pathlib.Path(__file__).parent
OUTPUT_PATH = ROOT_PATH / "_outputs"
CURRENT_DATE = datetime.datetime.now().strftime("%Y-%m-%d")


def fetch_data(search_query: str = None) -> dict:
    base_url = "https://api.raindrop.io/rest/v1/raindrops/0"

    if search_query:
        base_url += f"?search={search_query}"

    response = requests.get(
        base_url, headers={"Authorization": "Bearer " + RAINDROP_API_KEY}
    )
    return response.json()


def parse_response(data: dict) -> List[dict]:
    items = data.get("items", [])
    extracted_data = []
    for item in items:
        link = item.get("link", "No link provided")
        title = item.get("title", "No title provided")
        created = item.get("created", "No creation date provided")
        extracted_data.append({"link": link, "title": title, "created": created})
    return extracted_data


def create_markdown(items):
    markdown_content = "# Extracted Links and Titles\n\n"
    for item in items:
        markdown_content += f"- **Title:** {item['title']}\n  - **Link:** {item['link']}\n  - **Created:** {item['created']}\n"

    with open(OUTPUT_PATH / f"{CURRENT_DATE}_extracted_links.md", "w") as file:
        file.write(markdown_content)

    return None


if __name__ == "__main__":
    input_search_query = "created:>2024-04-10"

    api_response = fetch_data(input_search_query)
    parsed_data = parse_response(api_response)
    pprint(parsed_data)
    create_markdown(parsed_data)
