import logging
import os

import dotenv
import dspy
from dspy import Parallel as DSPyParallel

logger = logging.getLogger(__name__)


class GenerateSummary(dspy.Signature):
    """Generate a concise summary of a chunk's content for classification purposes."""

    chunk: str = dspy.InputField()
    gist: str = dspy.OutputField()


class GenerateHeaders(dspy.Signature):
    """Generate top-level headers for organizing chunks into a structured report."""

    chunk_summaries: str = dspy.InputField()
    headers: list[str] = dspy.OutputField()


class GenerateHeaderSection(dspy.Signature):
    """Generate a complete markdown section for a given header from relevant chunks."""

    content_chunks: list[str] = dspy.InputField()
    section_content: str = dspy.OutputField()


def generate_chunk_summary(chunks):
    parallelizer = DSPyParallel()
    generate_chunk_summary = dspy.ChainOfThought(GenerateSummary)
    chunk_summaries = parallelizer(
        [(generate_chunk_summary, {"chunk": chunk}) for chunk in chunks]
    )
    return [summary.gist for summary in chunk_summaries]


def generate_headers(chunk_summaries):
    generate_headers = dspy.ChainOfThought(GenerateHeaders)
    return generate_headers(chunk_summaries=chunk_summaries).headers


def classify_chunks(chunks, headers):
    parallelizer = DSPyParallel()
    classify = dspy.ChainOfThought(f"chunk -> topic: Literal{headers}")
    topics = parallelizer([(classify, {"chunk": chunk}) for chunk in chunks])
    return topics


def group_sections(topics, chunks, headers):
    sections = {topic: [] for topic in headers}
    for topic, chunk in zip(topics, chunks):
        sections[topic.topic].append(chunk)
    return sections


def massively_summarize(chunks: list[str]):
    if len(chunks) < 5:
        content = dspy.ChainOfThought(GenerateHeaderSection)(
            content_chunks=chunks
        ).section_content
        if content is None:
            return f"No content generated for this section."
        return f"\n\n{content}"

    chunk_summaries = generate_chunk_summary(chunks)
    headers = generate_headers(chunk_summaries)
    topics = classify_chunks(chunks, headers)
    sections = group_sections(topics, chunks, headers)

    valid_sections = [section for section in sections if section is not None]
    if not valid_sections:
        return f"No content generated for this section."

    rv = "\n\n".join(valid_sections)
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

    summary = massively_summarize(chunks=chunks)

    with open("summary.md", "w") as f:
        f.write(summary)
