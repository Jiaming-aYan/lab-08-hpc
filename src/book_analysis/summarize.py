#!/usr/bin/env python3
"""Summarize one book and add its analysis to gutenberg.books.

Usage: summarize.py BOOK_LIST TASK_ID
"""

import logging
import os
import socket
import sys
import time
from datetime import datetime, timezone

import torch
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from transformers import pipeline

logger = logging.getLogger(__name__)
MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
GENRES = ["adventure", "romance", "horror", "science fiction", "mystery", "satire",
          "historical fiction", "children's story", "poetry", "drama"]
MAX_WORDS = 20000
PROMPT = ("{excerpt}\n\nThat was the beginning of a book. Summarize the story in three sentences. "
          "Then, on a new line, write 'Genre: ' and the genre that fits best, one of: {genres}. "
          "Write plain text, without Markdown.")


def read_book(path):
    """Return the text of a book without Project Gutenberg's header and license."""
    with open(path, encoding="utf-8", errors="replace") as book_file:
        text = book_file.read()
    start = text.find("*** START OF")
    end = text.find("*** END OF")
    begin = text.find("\n", start) + 1 if start != -1 else 0
    return text[begin:end if end != -1 else len(text)]


def summarize_book(text):
    """Return the model's three-sentence summary and a recognized genre."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info("Running %s on %s", MODEL, device)
    generator = pipeline("text-generation", model=MODEL, device=device, dtype=torch.bfloat16)
    excerpt = " ".join(text.split()[:MAX_WORDS])
    messages = [{"role": "user", "content": PROMPT.format(excerpt=excerpt, genres=", ".join(GENRES))}]
    answer = generator(messages, max_new_tokens=200, do_sample=False)[0]["generated_text"][-1]["content"]
    answer = answer.replace("*", "")
    summary, _, genre = answer.rpartition("Genre:")
    if not summary:
        summary, genre = answer, "unknown"
    summary = summary.strip().removeprefix("Summary:").strip()
    genre = genre.strip().strip(".").lower()
    return summary, genre if genre in GENRES else "unknown"


def upload_summary(key, summary, genre, job):
    """Update the existing book document with its analysis and this run."""
    client = MongoClient(
        os.environ["MONGODB_ATLAS_URL"],
        username=os.environ["MONGODB_ATLAS_USER"],
        password=os.environ["MONGODB_ATLAS_PWD"],
    )
    at = datetime.now(timezone.utc)
    try:
        result = client["gutenberg"]["books"].update_one(
            {"_id": key},
            {
                "$set": {"llm_analysis": {
                    "summary": summary, "genre": genre, "model": MODEL, "at": at,
                }},
                "$push": {"runs": {"host": socket.gethostname(), "at": at, "job": job}},
            },
        )
        if result.matched_count == 0:
            logger.warning("No MongoDB document found for %s", key)
    except PyMongoError as exc:
        logger.error("Cannot update MongoDB document for %s: %s", key, exc)
        raise
    finally:
        client.close()


def main():
    """Summarize the selected book and save the result in MongoDB."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if len(sys.argv) != 3:
        logger.error("Usage: summarize.py BOOK_LIST TASK_ID")
        sys.exit(1)
    try:
        task_id = int(sys.argv[2])
    except ValueError:
        logger.error("TASK_ID must be an integer")
        sys.exit(1)

    with open(sys.argv[1], encoding="utf-8") as list_file:
        paths = [line.strip() for line in list_file if line.strip() and line.strip() != "File path"]
    if not 1 <= task_id <= len(paths):
        logger.error("TASK_ID must be in the range 1-%d", len(paths))
        sys.exit(1)

    path = paths[task_id - 1]
    key = os.path.basename(path)
    logger.info("Task %d: %s", task_id, path)
    started = time.time()
    text = read_book(path)
    summary, genre = summarize_book(text)
    logger.info("%s: %s, %.1f s", key, genre, time.time() - started)

    array_job_id = os.environ.get("SLURM_ARRAY_JOB_ID")
    array_task_id = os.environ.get("SLURM_ARRAY_TASK_ID")
    job = f"{array_job_id}_{array_task_id}" if array_job_id and array_task_id else None
    upload_summary(key, summary, genre, job)
    print(f"Summarized {key} in {time.time() - started:.1f} s on {socket.gethostname()}")


if __name__ == "__main__":
    main()
