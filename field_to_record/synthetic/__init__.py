"""
Synthetic subpackage for zero-PHI benchmark scenarios and acoustic noise injection.
"""

from field_to_record.synthetic.generator import SyntheticScenarioGenerator
from field_to_record.synthetic.noise_injector import AcousticNoiseInjector

__all__ = ["SyntheticScenarioGenerator", "AcousticNoiseInjector"]
