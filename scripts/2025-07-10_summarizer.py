import json
import os

import dotenv
import dspy
from dspy import Parallel as DSPyParallel


class GenerateSummary(dspy.Signature):
    """Generate a concise summary of a chunk's content for classification purposes."""

    chunk: str = dspy.InputField()
    gist: str = dspy.OutputField()


class GenerateAttributes(dspy.Signature):
    """Generate top-level headers for organizing chunks into a structured report."""

    chunk_summaries: str = dspy.InputField()
    headers: list[str] = dspy.OutputField()


def generate_summaries(chunks):
    parallelizer = DSPyParallel()
    generate_summaries = dspy.ChainOfThought(GenerateSummary)
    chunk_summaries = parallelizer(
        [(generate_summaries, {"chunk": chunk}) for chunk in chunks]
    )
    rv = [summary.gist for summary in chunk_summaries]
    return rv


def generate_attributes(chunk_summaries):
    generate_attributes = dspy.ChainOfThought(GenerateAttributes)
    rv = generate_attributes(chunk_summaries=chunk_summaries).headers
    return rv


def process_content(chunks: list[str]) -> dict:
    content_summaries = generate_summaries(chunks)
    content_attributes = generate_attributes(content_summaries)

    rv = {
        "attributes": content_attributes,
        "summaries": content_summaries,
    }
    return rv


if __name__ == "__main__":
    dotenv.load_dotenv()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY_91")

    dspy.settings.configure(lm=dspy.LM("openai/gpt-4o-mini", cache=False, api_key=OPENAI_API_KEY))

    with open("f.txt", encoding="utf-8") as f:
        content = f.read()

    # if content is small, we can summarize it directly
    chunk_size = 1000
    chunks = [content[i : i + chunk_size] for i in range(0, len(content), chunk_size)]

    summary = process_content(chunks=chunks)
    summary_string = json.dumps(summary, indent=2, ensure_ascii=False)

    with open("summary.md", "w") as f:
        f.write(summary_string)
