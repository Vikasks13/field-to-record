"""
Reports subpackage for SBAR and SOAP handover note generation.
"""

from field_to_record.reports.sbar import SBARReportGenerator
from field_to_record.reports.soap import SOAPReportGenerator

__all__ = ["SBARReportGenerator", "SOAPReportGenerator"]
