import re
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class DocumentMetadata:
    title: str
    document_type: str
    keywords: List[str]
    summary: str
    creation_date: datetime
    update_date: Optional[str]
    department: str
    author: str
    theme: str

@dataclass
class DocumentSection:
    number: str
    title: str
    content: str
    subsections: List['DocumentSection'] = None

class MarkdownDocumentParser:
    def __init__(self, file_path: str):
        """Initialize the parser with the markdown file path."""
        self.file_path = file_path
        self.content = self._read_file()
        self.metadata = None
        self.sections = []
        
    def _read_file(self) -> str:
        """Read the markdown file content."""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _extract_metadata_value(self, pattern: str, text: str) -> str:
        """Extract metadata value using regex pattern."""
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
        return ""

    def parse_metadata(self) -> DocumentMetadata:
        """Parse document metadata from the markdown content."""
        # Extract metadata section
        metadata_section = re.search(r'\*\*ΣΤΟΙΧΕΙΑ ΕΓΓΡΑΦΟΥ \[ΜΕΤΑΔΕΔΟΜΕΝΑ\]\*\*(.*?)(?=ΣΥΝΤΑΚΤΗΣ\*\*)',
                                   self.content, re.DOTALL)
        
        if not metadata_section:
            raise ValueError(f"Could not find metadata section, {self.file_path}")

        metadata_text = metadata_section.group(1)
        
        # Parse creation date
        date_str = self._extract_metadata_value(r'ΗΜΕΡΟΜΗΝΙΑ ΣΥΝΤΑΞΗΣ\*\*: ([^*\n]+)', metadata_text).strip()
        if date_str and date_str != '………':
            try:
                creation_date = datetime.strptime(date_str.strip(), '%d.%m.%Y')
            except ValueError:
                creation_date = None
        else:
            creation_date = None

        # Parse other metadata fields
        self.metadata = DocumentMetadata(
            title=self._extract_metadata_value(r'ΤΙΤΛΟΣ ΑΡΧΕΙΟΥ\*\*: ([^*\n]+)', metadata_text).strip('_'),
            document_type=self._extract_metadata_value(r'ΕΙΔΟΣ ΕΓΓΡΑΦΟΥ\*\*: ([^*\n]+)', metadata_text),
            keywords=[kw.strip() for kw in self._extract_metadata_value(r'KEY WORDS: \*\*([^*\n]+)', metadata_text).split(',')],
            summary=self._extract_metadata_value(r'ΠΕΡΙΛΗΨΗ: \*\*([^*\n]+)', metadata_text),
            creation_date=creation_date,
            update_date=self._extract_metadata_value(r'ΗΜΕΡΟΜΗΝΙΑ ΕΠΙΚΑΙΡΟΠΟΙΗΣΗΣ\*\*: ([^*\n]+)', metadata_text),
            department=self._extract_metadata_value(r'ΣΥΝΤΑΚΤΡΙΑ ΜΟΝΑΔΑ\*\*: ([^*\n]+)', metadata_text),
            author=self._extract_metadata_value(r'ΣΥΝΤΑΚΤΗΣ\*\*: ([^*\n]+)', metadata_text),
            theme=self._extract_metadata_value(r'ΘΕΜΑ\*\*: ([^*\n]+)', metadata_text)
        )
        
        return self.metadata

    def parse_sections(self) -> List[DocumentSection]:
        """Parse document sections from the markdown content."""
        # Find main sections
        section_pattern = r'\*\*\[(\d+)\]\. ([^\n]+)\*\*\s*(.*?)(?=\*\*\[\d+\]|\Z)'
        sections = []
        
        for match in re.finditer(section_pattern, self.content, re.DOTALL):
            section_num = match.group(1)
            section_title = match.group(2)
            section_content = match.group(3).strip()
            
            # Create section object
            section = DocumentSection(
                number=section_num,
                title=section_title,
                content=section_content
            )
            sections.append(section)
        
        self.sections = sections
        return sections

    def extract_rag_content(self) -> Dict:
        """Extract content in a format suitable for RAG system."""
        if not self.metadata:
            self.parse_metadata()
        if not self.sections:
            self.parse_sections()
            
        return {
            "metadata": {
                "title": self.metadata.title,
                "document_type": self.metadata.document_type,
                "theme": self.metadata.theme,
                "keywords": ",".join(self.metadata.keywords),
                "summary": self.metadata.summary,
                "creation_date": self.metadata.creation_date.isoformat() if self.metadata.creation_date else None,
                "update_date": self.metadata.update_date,
                "department": self.metadata.department,
                "author": self.metadata.author
            },
            "content": {
                "sections": [
                    {
                        "number": section.number,
                        "title": section.title,
                        "content": section.content,
                    }
                    for section in self.sections
                ],
                "full_text": self.content
            }
        }

    def extract_legal_references(self) -> List[Dict]:
        """Extract legal references from the document content."""
        legal_refs = []
        # Pattern for legal references like "άρθρο 19 παρ. 1 του Ν. 2889/2001"
        ref_pattern = r'(?:άρθρο|άρθρων)\s+(\d+)(?:\s+παρ\.\s+(\d+))?\s+(?:του\s+)?[Νν]\.\s*(\d+)/(\d+)'
        
        for match in re.finditer(ref_pattern, self.content):
            legal_refs.append({
                "article": match.group(1),
                "paragraph": match.group(2) if match.group(2) else None,
                "law_number": f"{match.group(3)}/{match.group(4)}"
            })
        
        return legal_refs