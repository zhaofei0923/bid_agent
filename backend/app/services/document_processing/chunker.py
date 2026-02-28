"""Text chunker — RecursiveCharacterTextSplitter strategy.

Splits documents into overlapping chunks for embedding and retrieval.
"""

from dataclasses import dataclass, field


@dataclass
class ChunkMetadata:
    """Metadata attached to each chunk."""

    section_id: str = ""
    section_type: str = ""
    page_number: int = 1
    source_document: str = ""


@dataclass
class TextChunk:
    """A single text chunk with position and metadata."""

    content: str
    chunk_index: int
    char_start: int
    char_end: int
    metadata: ChunkMetadata = field(default_factory=ChunkMetadata)


class DocumentChunker:
    """Recursive character text splitter with configurable overlap.

    Default configuration: 1000 chars per chunk, 200 overlap.
    Uses a hierarchy of separators: paragraph → line → sentence → word.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 100,
        separators: list[str] | None = None,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.separators = separators or ["\n\n", "\n", ". ", " "]

    def chunk_text(
        self,
        text: str,
        metadata: ChunkMetadata | None = None,
    ) -> list[TextChunk]:
        """Split text into overlapping chunks.

        Args:
            text: Full text to split.
            metadata: Base metadata to copy to each chunk.

        Returns:
            List of TextChunk objects.
        """
        if not text or not text.strip():
            return []

        meta = metadata or ChunkMetadata()
        splits = self._recursive_split(text, self.separators)

        chunks: list[TextChunk] = []
        current_text = ""
        current_start = 0
        char_pos = 0

        for split in splits:
            if len(current_text) + len(split) > self.chunk_size and current_text:
                if len(current_text.strip()) >= self.min_chunk_size:
                    chunks.append(
                        TextChunk(
                            content=current_text.strip(),
                            chunk_index=len(chunks),
                            char_start=current_start,
                            char_end=char_pos,
                            metadata=meta,
                        )
                    )

                # Overlap: retain tail of current chunk
                overlap = current_text[-self.chunk_overlap :] if self.chunk_overlap else ""
                current_text = overlap + split
                current_start = char_pos - len(overlap)
            else:
                current_text += split

            char_pos += len(split)

        # Final chunk
        if current_text.strip() and len(current_text.strip()) >= self.min_chunk_size:
            chunks.append(
                TextChunk(
                    content=current_text.strip(),
                    chunk_index=len(chunks),
                    char_start=current_start,
                    char_end=char_pos,
                    metadata=meta,
                )
            )

        return chunks

    def _recursive_split(self, text: str, separators: list[str]) -> list[str]:
        """Recursively split text using separator hierarchy."""
        if not separators:
            return [text]

        sep = separators[0]
        parts = text.split(sep)

        result: list[str] = []
        for i, part in enumerate(parts):
            # Re-append separator to fragments (except last)
            fragment = part + (sep if i < len(parts) - 1 else "")

            if len(fragment) > self.chunk_size and len(separators) > 1:
                result.extend(self._recursive_split(fragment, separators[1:]))
            else:
                result.append(fragment)

        return result
