"""
CAD File Parser

Extracts metadata, text, and entities from CAD files (DWG/DXF).
Uses ezdxf library for parsing.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class CADMetadata:
    """Extracted CAD file metadata"""

    file_path: str
    file_type: str  # dwg, dxf
    drawing_number: Optional[str] = None
    version: Optional[str] = None
    title: Optional[str] = None
    scale: Optional[str] = None
    date: Optional[str] = None
    layers: list[str] = None
    blocks: list[str] = None
    text_content: list[str] = None
    entities_count: int = 0

    def __post_init__(self):
        if self.layers is None:
            self.layers = []
        if self.blocks is None:
            self.blocks = []
        if self.text_content is None:
            self.text_content = []


class CADParser:
    """
    Parse CAD files (DWG/DXF) and extract metadata.

    Features:
        - Title block extraction
        - Layer information
        - Text entity extraction
        - Block references
        - Dimension extraction (future)
    """

    def __init__(self):
        """Initialize CAD parser"""
        try:
            import ezdxf

            self.ezdxf = ezdxf
            logger.info("Initialized CAD parser with ezdxf")
        except ImportError as e:
            logger.error("Failed to import ezdxf", error=str(e))
            raise RuntimeError("ezdxf not installed. Run: pip install ezdxf") from e

    def parse_file(self, file_path: str) -> CADMetadata:
        """
        Parse CAD file and extract metadata.

        Args:
            file_path: Path to DWG or DXF file

        Returns:
            CADMetadata object
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"CAD file not found: {file_path}")

        file_type = path.suffix.lower().lstrip(".")

        if file_type not in ["dwg", "dxf"]:
            raise ValueError(f"Unsupported file type: {file_type}")

        logger.info("Parsing CAD file", file_path=file_path, file_type=file_type)

        try:
            # Read CAD file
            doc = self.ezdxf.readfile(file_path)

            # Extract metadata
            metadata = CADMetadata(file_path=str(path), file_type=file_type)

            # Extract layers
            metadata.layers = [layer.dxf.name for layer in doc.layers]

            # Extract blocks
            metadata.blocks = [block.name for block in doc.blocks]

            # Extract text entities
            text_entities = []
            for entity in doc.modelspace():
                if entity.dxftype() == "TEXT":
                    text_entities.append(entity.dxf.text)
                elif entity.dxftype() == "MTEXT":
                    text_entities.append(entity.text)

            metadata.text_content = text_entities
            metadata.entities_count = len(list(doc.modelspace()))

            # Try to extract title block info (heuristic)
            title_block_info = self._extract_title_block(text_entities)
            metadata.drawing_number = title_block_info.get("drawing_number")
            metadata.version = title_block_info.get("version")
            metadata.title = title_block_info.get("title")
            metadata.scale = title_block_info.get("scale")
            metadata.date = title_block_info.get("date")

            logger.info(
                "Parsed CAD file",
                layers=len(metadata.layers),
                blocks=len(metadata.blocks),
                text_entities=len(text_entities),
                total_entities=metadata.entities_count,
            )

            return metadata

        except Exception as e:
            logger.error("Failed to parse CAD file", error=str(e), file_path=file_path)
            raise

    def _extract_title_block(self, text_entities: list[str]) -> dict[str, str]:
        """
        Extract title block information from text entities (heuristic).

        Args:
            text_entities: List of text strings from CAD file

        Returns:
            Dictionary with title block fields
        """
        title_block = {}

        # Common patterns in title blocks
        patterns = {
            "drawing_number": ["DWG NO", "DRAWING NO", "SHEET", "NO."],
            "version": ["REV", "REVISION", "VERSION"],
            "title": ["TITLE", "PROJECT"],
            "scale": ["SCALE"],
            "date": ["DATE"],
        }

        for text in text_entities:
            text_upper = text.upper()

            # Check for drawing number (e.g., "A-101", "S-203")
            if any(char.isdigit() and "-" in text for char in text):
                if len(text) < 20 and not title_block.get("drawing_number"):
                    # Likely a drawing number
                    parts = text.split()
                    for part in parts:
                        if "-" in part and any(c.isdigit() for c in part):
                            title_block["drawing_number"] = part
                            break

            # Check for version/revision (e.g., "REV 3", "R3")
            for pattern in patterns["version"]:
                if pattern in text_upper:
                    # Extract revision identifier
                    words = text.split()
                    for i, word in enumerate(words):
                        if pattern in word.upper() and i + 1 < len(words):
                            title_block["version"] = words[i + 1]
                            break

            # Check for scale (e.g., '1/4" = 1\'-0"')
            if "SCALE" in text_upper or "=" in text:
                if any(char.isdigit() for char in text):
                    title_block["scale"] = text

            # Check for date (e.g., "11/14/2025")
            if "/" in text and any(char.isdigit() for char in text):
                if len(text) < 20:
                    title_block["date"] = text

        logger.debug("Extracted title block", title_block=title_block)
        return title_block

    def extract_to_text(self, metadata: CADMetadata) -> str:
        """
        Convert CAD metadata to text format for embedding.

        Args:
            metadata: CADMetadata object

        Returns:
            Formatted text string
        """
        lines = []

        # Header
        lines.append(f"CAD File: {Path(metadata.file_path).name}")
        lines.append(f"File Type: {metadata.file_type.upper()}")

        # Title block
        if metadata.drawing_number:
            lines.append(f"Drawing Number: {metadata.drawing_number}")
        if metadata.version:
            lines.append(f"Version: {metadata.version}")
        if metadata.title:
            lines.append(f"Title: {metadata.title}")
        if metadata.scale:
            lines.append(f"Scale: {metadata.scale}")
        if metadata.date:
            lines.append(f"Date: {metadata.date}")

        # Layers
        if metadata.layers:
            lines.append(f"\nLayers ({len(metadata.layers)}):")
            for layer in metadata.layers[:20]:  # Limit to first 20
                lines.append(f"  - {layer}")

        # Text content
        if metadata.text_content:
            lines.append(f"\nText Content ({len(metadata.text_content)} items):")
            for text in metadata.text_content[:50]:  # Limit to first 50
                if text.strip():
                    lines.append(f"  {text}")

        # Statistics
        lines.append(f"\nTotal Entities: {metadata.entities_count}")

        return "\n".join(lines)


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    # Example: Parse a DXF file
    parser = CADParser()

    # Note: This requires an actual DXF file to test
    # metadata = parser.parse_file("/path/to/drawing.dxf")
    # text = parser.extract_to_text(metadata)
    # print(text)

    print("CAD Parser initialized successfully")
    print("To use: parser.parse_file('path/to/drawing.dxf')")
