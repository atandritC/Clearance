import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass
class ParsedDocument:
    document_id: str
    title: str
    department: str
    access_level: str
    version: str
    status: str
    effective_date: date
    body: str


def parse_knowledge_base(path: Path) -> list[ParsedDocument]:
    markdown = path.read_text(encoding="utf-8")

    sections = re.split(r"(?=^### DOC-)", markdown, flags=re.MULTILINE)
    documents = []

    for section in sections:
        lines = section.splitlines()

        if not lines or not lines[0].startswith("### DOC-"):
            continue

        section_heading = re.search(r"^## ", section, flags=re.MULTILINE)
        if section_heading:
            section = section[: section_heading.start()]
            lines = section.splitlines()

        heading_parts = lines[0].split(" — ", maxsplit=1)
        if len(heading_parts) != 2:
            raise ValueError(f"Could not read document title: {lines[0]}")

        title = heading_parts[1].removesuffix(" (superseded)")

        fields = {}
        body_start = None

        for line_number, line in enumerate(lines[1:], start=1):
            if line.startswith("- ") and ": " in line:
                key, value = line[2:].split(": ", maxsplit=1)
                fields[key] = value
            elif line.strip():
                body_start = line_number
                break

        required_fields = [
            "document_id",
            "department",
            "access_level",
            "version",
            "status",
            "effective_date",
        ]

        missing_fields = [field for field in required_fields if field not in fields]
        if missing_fields:
            raise ValueError(f"{lines[0]} is missing: {', '.join(missing_fields)}")

        body = "\n".join(lines[body_start:]).strip() if body_start else ""
        body = re.sub(r"\n---\s*$", "", body).strip()

        documents.append(
            ParsedDocument(
                document_id=fields["document_id"],
                title=title,
                department=fields["department"],
                access_level=fields["access_level"],
                version=fields["version"],
                status=fields["status"],
                effective_date=date.fromisoformat(fields["effective_date"]),
                body=body,
            )
        )

    return documents
