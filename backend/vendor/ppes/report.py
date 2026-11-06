"""Report generator."""
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

    def add(self, title, **kw):
        self.sections.append(Section(title, **kw))

    def to_text(self):
        out = [self.title, "="*len(self.title), ""]
        for s in self.sections:
            out.append(s.title); out.append("-"*len(s.title))
            if s.body: out.append(s.body)
            for k, v in s.data.items():
                out.append(f"  {k:<30} {v:.6g}")
            for n in s.notes: out.append(f"  * {n}")
            out.append("")
        return "\n".join(out)

    def to_docx(self, path):
        from docx import Document
        doc = Document()
        doc.add_heading(self.title, level=0)
        doc.add_paragraph(f"Author: {self.author}")
        for s in self.sections:
            doc.add_heading(s.title, level=1)
            if s.body: doc.add_paragraph(s.body)
            if s.data:
                t = doc.add_table(rows=1, cols=2)
                h = t.rows[0].cells
                h[0].text = "Parameter"; h[1].text = "Value"
                for k, v in s.data.items():
                    r = t.add_row().cells
                    r[0].text = k; r[1].text = f"{v:.6g}"
            for n in s.notes:
                doc.add_paragraph(n, style="List Bullet")
        doc.save(path)

    def to_pdf(self, path):
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import (SimpleDocTemplate, Paragraph,
                                        Spacer, Table, TableStyle)
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        st = getSampleStyleSheet()
        story = [Paragraph(self.title, st["Title"]),
                 Paragraph(f"Author: {self.author}", st["Normal"]),
                 Spacer(1, 12)]
        for s in self.sections:
            story.append(Paragraph(s.title, st["Heading1"]))
            if s.body: story.append(Paragraph(s.body, st["Normal"]))
            if s.data:
                data = [["Parameter", "Value"]] + [
                    [k, f"{v:.6g}"] for k, v in s.data.items()]
                t = Table(data)
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
                    ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
                ]))
                story.append(t)
            for n in s.notes:
                story.append(Paragraph(f"* {n}", st["Normal"]))
            story.append(Spacer(1, 12))
        SimpleDocTemplate(path, pagesize=A4).build(story)
