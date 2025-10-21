import os

import dotenv
import dspy
from dspy import Parallel as DSPyParallel


class GenerateChunkSummary(dspy.Signature):
    """
    Generate a concise summary of the given text chunk.
    
    Instructions:
    - Focus on the main ideas, key points, and essential information
    - Be direct and precise - avoid unnecessary elaboration or context
    - Only include information present in the original text
    """

    chunk: str = dspy.InputField(desc="Text chunk to be summarized")
    summary: str = dspy.OutputField(desc="Concise summary capturing the main points of the chunk")


class GenerateAttributes(dspy.Signature):
    """
    Extract high-level organizational attributes from a collection of content summaries.
    
    Instructions:
    - Identify overarching themes, topics, or categories that emerge from the summaries
    - Create attributes that can serve as organizational headers or classifiers
    - Focus on recurring concepts, subject matters, or logical groupings
    """

    chunk_summaries: str = dspy.InputField(desc="Collection of individual chunk summaries to analyze")
    headers: list[str] = dspy.OutputField(desc="List of high-level attributes/themes for organizing content")


class GenerateOverallSummary(dspy.Signature):
    """
    Create a comprehensive overview that synthesizes the extracted attributes and individual summaries.
    
    Instructions:
    - Combine insights from both the attributes and the summaries
    - Create a coherent narrative that ties together all the processed information
    - Be comprehensive yet concise - aim for a substantial but digestible overview
    """

    attributes: list[str] = dspy.InputField(desc="High-level organizational attributes extracted from the content")
    summaries: list[str] = dspy.InputField(desc="Individual summaries of content chunks")
    overall_summary: str = dspy.OutputField(desc="Comprehensive synthesis of attributes and summaries")


def generate_chunk_summaries(chunks):
    parallelizer = DSPyParallel()
    generate_chunk_summaries = dspy.ChainOfThought(GenerateChunkSummary)
    chunk_summaries = parallelizer(
        [(generate_chunk_summaries, {"chunk": chunk}) for chunk in chunks]
    )
    rv = [summary.summary for summary in chunk_summaries]
    return rv


def generate_attributes(chunk_summaries):
    generate_attributes = dspy.ChainOfThought(GenerateAttributes)
    summaries_text = "\n\n---\n\n".join(chunk_summaries)
    rv = generate_attributes(chunk_summaries=summaries_text).headers
    return rv


def generate_overall_summary(attributes, summaries):
    generate_overall = dspy.ChainOfThought(GenerateOverallSummary)
    rv = generate_overall(attributes=attributes, summaries=summaries).overall_summary
    return rv


def process_content(chunks: list[str]) -> dict:
    content_summaries = generate_chunk_summaries(chunks)
    content_attributes = generate_attributes(content_summaries)
    overall_summary = generate_overall_summary(content_attributes, content_summaries)

    rv = {
        "attributes": content_attributes,
        "summaries": content_summaries,
        "overall_summary": overall_summary,
    }
    return rv


def format_as_markdown(summary_data: dict) -> str:
    markdown_lines = []

    markdown_lines.append("## Key Attributes")
    markdown_lines.append("")
    for attribute in summary_data["attributes"]:
        markdown_lines.append(f"- {attribute}")
    markdown_lines.append("")

    markdown_lines.append("## Overall Summary")
    markdown_lines.append("")
    markdown_lines.append(summary_data["overall_summary"])
    markdown_lines.append("")

    return "\n".join(markdown_lines)


if __name__ == "__main__":
    dotenv.load_dotenv()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY_91")

    dspy.settings.configure(lm=dspy.LM("openai/gpt-4o-mini", cache=False, api_key=OPENAI_API_KEY))

    with open("input.txt", encoding="utf-8") as f:
        content = f.read()

    # if content is small, we can summarize it directly
    chunk_size = 5000
    chunks = [content[i : i + chunk_size] for i in range(0, len(content), chunk_size)]

    summary = process_content(chunks=chunks)
    summary_string = format_as_markdown(summary)

    with open("summary.md", "w") as f:
        f.write(summary_string)
