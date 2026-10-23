"""
Acoustic chunking engine for long continuous field dictations.
Slices audio streams into overlapping windows (default 30 seconds with 2.0s overlap)
guided by silence boundaries to avoid clipping critical clinical words.
"""

from typing import List, Dict, Any


class AudioChunker:
    """
    Chunks continuous PCM audio into windowed buffers for real-time edge speech recognition.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_duration_sec: float = 30.0,
        overlap_sec: float = 2.0,
    ):
        self.sample_rate = sample_rate
        self.chunk_size_samples = int(sample_rate * chunk_duration_sec)
        self.overlap_samples = int(sample_rate * overlap_sec)
        self.step_samples = self.chunk_size_samples - self.overlap_samples
        self.bytes_per_sample = 2  # 16-bit PCM

    def chunk_pcm_bytes(self, pcm_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Splits PCM byte buffer into overlapping chunk payloads.
        Returns list of chunks with metadata: chunk_index, start_sec, end_sec, pcm_data.
        """
        sample_count = len(pcm_bytes) // self.bytes_per_sample
        if sample_count == 0:
            return []

        chunks: List[Dict[str, Any]] = []
        start_idx = 0
        chunk_idx = 0

        while start_idx < sample_count:
            end_idx = min(start_idx + self.chunk_size_samples, sample_count)
            byte_start = start_idx * self.bytes_per_sample
            byte_end = end_idx * self.bytes_per_sample
            chunk_data = pcm_bytes[byte_start:byte_end]

            start_sec = start_idx / float(self.sample_rate)
            end_sec = end_idx / float(self.sample_rate)

            chunks.append({
                "chunk_index": chunk_idx,
                "start_sec": round(start_sec, 2),
                "end_sec": round(end_sec, 2),
                "duration_sec": round(end_sec - start_sec, 2),
                "pcm_bytes": chunk_data,
                "byte_length": len(chunk_data),
            })

            chunk_idx += 1
            if end_idx >= sample_count:
                break
            start_idx += self.step_samples

        return chunks
