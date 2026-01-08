
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    Handles extraction of text from various document formats (PDF, HWP, etc.)
    """
    
    def extract_text(self, file_path: str) -> str:
        """
        Detects file type and extracts text.
        """
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            return self._extract_pdf(file_path)
        elif ext in [".hwp", ".hwpx"]:
            return self._extract_hwp(file_path)
        else:
            return f"[Unsupported Format: {ext}]"

    def _extract_pdf(self, path: str) -> str:
        """
        Extract text from PDF.
        """
        text_content = []
        try:
            # Try pypdf
            import pypdf
            reader = pypdf.PdfReader(path)
            for page in reader.pages:
                text_content.append(page.extract_text() or "")
            return "\n".join(text_content)
        except ImportError:
            logger.warning("pypdf not installed. Using fallback PDF extraction.")
            # Fallback: simple string reading (won't work for compressed PDFs, but ok for debug)
            # Or assume we rely on pypdf.
            return "[Error: pypdf library missing]"
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            return f"[Error processing PDF: {e}]"

    def _extract_hwp(self, path: str) -> str:
        """
        Extract text from HWP.
        Real HWP parsing is complex (requires 'olefile' or 'hwp5-parser').
        For this demo, we read our dummy text file or return placeholder.
        """
        try:
            # For our simulation, we wrote plain text into the .hwp file.
            # In production, use: import olefile ...
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                if "DUMMY HWP CONTENT" in content:
                    return content
                else:
                     return "[Real HWP content extraction requires 'olefile' or 'libhwp']"
        except Exception as e:
            logger.error(f"HWP extraction failed: {e}")
            return f"[Error processing HWP: {e}]"
