import re


def normalize_whitespace(text: str) -> str:
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[\t\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_inline_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_line(line: str) -> str:
    line = line.strip().strip("|•-*·")
    line = re.sub(r"\s+", " ", line)
    return line


def dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        key = item.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        output.append(item.strip())
    return output
