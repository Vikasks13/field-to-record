"""
ASR subpackage for offline edge speech recognition with vocabulary biasing.
"""

from field_to_record.asr.engine import OfflineClinicalASR
from field_to_record.asr.prompt_biasing import get_conditioned_prompt, EMS_CLINICAL_PROMPT

__all__ = ["OfflineClinicalASR", "get_conditioned_prompt", "EMS_CLINICAL_PROMPT"]
