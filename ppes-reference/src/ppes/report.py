"""Book-style report generator."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Section:
    title: str
    body: str = ""
    data: dict[str, float] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


@dataclass
class Report:
    title: str
    author: str
    sections: list[Section] = field(default_factory=list)

    def add(self, title: str, **kw):
        self.sections.append(Section(title, **kw))

    def to_text(self) -> str:
        out = [self.title, "=" * len(self.title), ""]
        for s in self.sections:
            out.append(s.title)
            out.append("-" * len(s.title))
            if s.body:
                out.append(s.body)
            for k, v in s.data.items():
                out.append(f"  {k:<30} {v:.6g}")
            for note in s.notes:
                out.append(f"  * {note}")
            out.append("")
        return "\n".join(out)