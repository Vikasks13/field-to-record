"""
GBNF (GGML BNF Grammar) specification for small language models (llama.cpp / Qwen-2.5-SLM).
Forces token-by-token generation strictly into a valid JSON schema for medication
and procedure slot-filling with 0% JSON syntax error rate.
"""

GBNF_CLINICAL_SCHEMA = r"""
root ::= "{" ws "\"medications\":" ws medication-list "," ws "\"procedures\":" ws procedure-list "," ws "\"observations\":" ws observation-list "}"

medication-list ::= "[" ws (medication ("," ws medication)*)? ws "]"
medication ::= "{" ws "\"drug_name\":" ws string "," ws "\"dosage_value\":" ws number "," ws "\"dosage_unit\":" ws string "," ws "\"route\":" ws string ("," ws "\"time\":" ws string)? "}"

procedure-list ::= "[" ws (procedure ("," ws procedure)*)? ws "]"
procedure ::= "{" ws "\"procedure_name\":" ws string ("," ws "\"anatomical_site\":" ws string)? ("," ws "\"success\":" ws boolean)? "}"

observation-list ::= "[" ws (observation ("," ws observation)*)? ws "]"
observation ::= "{" ws "\"code\":" ws string "," ws "\"value\":" ws number "," ws "\"unit\":" ws string "}"

string ::= "\"" ([^"\\\x00-\x1F] | "\\" (["\\/bfnrt] | "u" [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F]))* "\""
number ::= ("-"? ([0-9] | [1-9] [0-9]*)) ("." [0-9]+)?
boolean ::= "true" | "false"
ws ::= [ \t\n\r]*
"""


def get_gbnf_grammar() -> str:
    """Returns raw GBNF grammar string for llama.cpp / SLM execution."""
    return GBNF_CLINICAL_SCHEMA.strip()
