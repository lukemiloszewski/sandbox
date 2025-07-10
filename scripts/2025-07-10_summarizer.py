import logging
import os

import dotenv
import dspy
from dspy import Parallel as DSPyParallel

logger = logging.getLogger(__name__)


class ProduceGist(dspy.Signature):
    """Produce a one- or two-sentence gist of what this chunk is about, so we can assign it to a class."""

    toc_path: list[str] = dspy.InputField(
        desc="path down which this chunk has traveled so far in the Table of Contents"
    )
    chunk: str = dspy.InputField()
    gist: str = dspy.OutputField()


class ProduceHeaders(dspy.Signature):
    """Produce a list of headers (top-level Table of Contents) for structuring a report on *all* chunk contents.
    Make sure every chunk would belong to exactly one section."""

    toc_path: list[str] = dspy.InputField()
    chunk_summaries: str = dspy.InputField()
    headers: list[str] = dspy.OutputField()


class WriteSection(dspy.Signature):
    """Craft a Markdown section, given a path down the table of contents, which ends with this section's specific heading.
    Start the content right beneath that heading: use sub-headings of depth at least +1 relative to the ToC path.
    Your section's content is to be entirely derived from the given list of chunks. That content must be complete but very concise,
    with all necessary knowledge from the chunks reproduced and repetitions or irrelevant details omitted."""

    toc_path: list[str] = dspy.InputField()
    content_chunks: list[str] = dspy.InputField()
    section_content: str = dspy.OutputField()


def produce_gist(toc_path, chunks):
    parallelizer = DSPyParallel()
    produce_gist = dspy.ChainOfThought(ProduceGist)
    chunk_summaries = parallelizer(
        [(produce_gist, {"toc_path": toc_path, "chunk": chunk}) for chunk in chunks]
    )
    return [summary.gist for summary in chunk_summaries]


def produce_headers(toc_path, chunk_summaries):
    produce_headers = dspy.ChainOfThought(ProduceHeaders)
    return produce_headers(toc_path=toc_path, chunk_summaries=chunk_summaries).headers


def classify_chunks(toc_path, chunks, headers):
    parallelizer = DSPyParallel()
    classify = dspy.ChainOfThought(f"toc_path: list[str], chunk -> topic: Literal{headers}")
    topics = parallelizer([(classify, {"toc_path": toc_path, "chunk": chunk}) for chunk in chunks])
    return topics


def group_sections(topics, chunks, headers):
    sections = {topic: [] for topic in headers}
    for topic, chunk in zip(topics, chunks):
        sections[topic.topic].append(chunk)
    return sections


def summarize_sections(toc_path, sections):
    parallelizer = DSPyParallel()
    summarized_sections = parallelizer(
        [
            (massively_summarize, {"toc_path": toc_path + [topic], "chunks": section_chunks})
            for topic, section_chunks in sections.items()
        ]
    )
    return summarized_sections


def massively_summarize(
    toc_path: list | str,
    chunks: list[str],
):
    if len(chunks) < 5 or len(toc_path) >= 3:
        content = dspy.ChainOfThought(WriteSection)(
            toc_path=toc_path, content_chunks=chunks
        ).section_content
        if content is None:
            return f"{toc_path[-1]}\n\nNo content generated for this section."
        return f"{toc_path[-1]}\n\n{content}"

    chunk_summaries = produce_gist(toc_path, chunks)
    headers = produce_headers(toc_path, chunk_summaries)
    topics = classify_chunks(toc_path, chunks, headers)
    sections = group_sections(topics, chunks, headers)
    summarized_sections = summarize_sections(toc_path, sections)
    valid_sections = [section for section in summarized_sections if section is not None]
    if not valid_sections:
        return f"{toc_path[-1]}\n\nNo content generated for this section."

    return toc_path[-1] + "\n\n" + "\n\n".join(valid_sections)


if __name__ == "__main__":
    dotenv.load_dotenv()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY_91")

    dspy.settings.configure(lm=dspy.LM("openai/gpt-4o-mini", cache=False, api_key=OPENAI_API_KEY))

    with open("essay.txt", encoding="utf-8") as f:
        merged_content = f.read()

    chunk_size = 1000
    chunks = [merged_content[i : i + chunk_size] for i in range(0, len(merged_content), chunk_size)]

    summary = massively_summarize(toc_path=["# Weave Docs Summary"], chunks=chunks)

    with open("summary.md", "w") as f:
        f.write(summary)
