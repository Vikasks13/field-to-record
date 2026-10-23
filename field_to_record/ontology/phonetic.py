"""
Phonetic matching and string edit-distance algorithms.
Implements:
1. Double Metaphone (primary and alternate phonetic encodings).
2. Damerau-Levenshtein distance with transposition support.
Allows matching noisy edge ASR transcripts against medical lexicons with threshold <= 2.
"""

from typing import Tuple, List, Optional


def damerau_levenshtein_distance(s1: str, s2: str) -> int:
    """
    Computes Damerau-Levenshtein distance between two strings,
    supporting insertions, deletions, substitutions, and adjacent transpositions.
    """
    d = {}
    len1, len2 = len(s1), len(s2)
    for i in range(-1, len1 + 1):
        d[(i, -1)] = i + 1
    for j in range(-1, len2 + 1):
        d[(-1, j)] = j + 1

    for i in range(len1):
        for j in range(len2):
            cost = 0 if s1[i] == s2[j] else 1
            d[(i, j)] = min(
                d[(i - 1, j)] + 1,        # deletion
                d[(i, j - 1)] + 1,        # insertion
                d[(i - 1, j - 1)] + cost  # substitution
            )
            if i > 0 and j > 0 and s1[i] == s2[j - 1] and s1[i - 1] == s2[j]:
                d[(i, j)] = min(d[(i, j)], d[(i - 2, j - 2)] + 1)  # transposition

    return d[(len1 - 1, len2 - 1)]


def double_metaphone(name: str) -> Tuple[str, str]:
    """
    Simplified pure-Python Double Metaphone phonetic encoder.
    Produces primary and secondary phonetic keys for medical drug names.
    """
    if not name:
        return ("", "")

    clean = name.upper().strip()
    primary = []
    secondary = []

    i = 0
    length = len(clean)

    # Initial letter edge cases
    if clean.startswith(("GN", "KN", "PN", "WR", "PS")):
        i = 1

    while i < length:
        ch = clean[i]

        if ch in ("A", "E", "I", "O", "U", "Y"):
            if i == 0:
                primary.append("A")
                secondary.append("A")
            i += 1
        elif ch == "B":
            primary.append("P")
            secondary.append("P")
            i += 2 if (i + 1 < length and clean[i + 1] == "B") else 1
        elif ch == "C":
            # Soft C
            if i + 1 < length and clean[i + 1] in ("E", "I", "Y"):
                primary.append("S")
                secondary.append("S")
                i += 2
            elif i + 1 < length and clean[i + 1] == "H":
                primary.append("X")
                secondary.append("K")
                i += 2
            else:
                primary.append("K")
                secondary.append("K")
                i += 2 if (i + 1 < length and clean[i + 1] == "K") else 1
        elif ch == "D":
            primary.append("T")
            secondary.append("T")
            i += 2 if (i + 1 < length and clean[i + 1] == "D") else 1
        elif ch in ("F", "V"):
            primary.append("F")
            secondary.append("F")
            i += 2 if (i + 1 < length and clean[i + 1] in ("F", "V")) else 1
        elif ch == "G":
            if i + 1 < length and clean[i + 1] in ("E", "I", "Y"):
                primary.append("J")
                secondary.append("K")
            else:
                primary.append("K")
                secondary.append("K")
            i += 2 if (i + 1 < length and clean[i + 1] == "G") else 1
        elif ch == "H":
            if i + 1 < length and clean[i + 1] in ("A", "E", "I", "O", "U", "Y"):
                primary.append("H")
                secondary.append("H")
            i += 1
        elif ch in ("J", "K", "Q"):
            primary.append("K")
            secondary.append("K")
            i += 1
        elif ch == "L":
            primary.append("L")
            secondary.append("L")
            i += 2 if (i + 1 < length and clean[i + 1] == "L") else 1
        elif ch == "M":
            primary.append("M")
            secondary.append("M")
            i += 2 if (i + 1 < length and clean[i + 1] == "M") else 1
        elif ch == "N":
            primary.append("N")
            secondary.append("N")
            i += 2 if (i + 1 < length and clean[i + 1] == "N") else 1
        elif ch == "P":
            if i + 1 < length and clean[i + 1] == "H":
                primary.append("F")
                secondary.append("F")
                i += 2
            else:
                primary.append("P")
                secondary.append("P")
                i += 2 if (i + 1 < length and clean[i + 1] == "P") else 1
        elif ch == "R":
            primary.append("R")
            secondary.append("R")
            i += 2 if (i + 1 < length and clean[i + 1] == "R") else 1
        elif ch == "S":
            if i + 1 < length and clean[i + 1] == "H":
                primary.append("X")
                secondary.append("X")
                i += 2
            else:
                primary.append("S")
                secondary.append("S")
                i += 2 if (i + 1 < length and clean[i + 1] == "S") else 1
        elif ch == "T":
            if i + 1 < length and clean[i + 1] == "H":
                primary.append("0")  # theta sound
                secondary.append("T")
                i += 2
            else:
                primary.append("T")
                secondary.append("T")
                i += 2 if (i + 1 < length and clean[i + 1] == "T") else 1
        elif ch == "W":
            if i == 0 and i + 1 < length and clean[i + 1] in ("A", "E", "I", "O", "U"):
                primary.append("A")
                secondary.append("F")
            i += 1
        elif ch == "X":
            primary.append("K")
            primary.append("S")
            secondary.append("K")
            secondary.append("S")
            i += 1
        elif ch == "Z":
            primary.append("S")
            secondary.append("S")
            i += 1
        else:
            i += 1

    return ("".join(primary)[:8], "".join(secondary)[:8])


def find_best_phonetic_match(target: str, candidates: List[str], max_dist: int = 2) -> Optional[str]:
    """
    Finds the closest candidate using Double Metaphone and Damerau-Levenshtein distance.
    Returns None if no candidate matches within max_dist.
    """
    t_clean = target.lower().strip()
    # Exact match first
    for c in candidates:
        if c.lower() == t_clean:
            return c

    # Edit distance on raw string
    best_candidate = None
    min_dist = max_dist + 1

    for c in candidates:
        dist = damerau_levenshtein_distance(t_clean, c.lower())
        if dist < min_dist:
            min_dist = dist
            best_candidate = c

    if best_candidate and min_dist <= max_dist:
        return best_candidate

    # Phonetic matching via Metaphone
    t_pri, t_sec = double_metaphone(t_clean)
    for c in candidates:
        c_pri, c_sec = double_metaphone(c)
        if (t_pri and (t_pri == c_pri or t_pri == c_sec)) or (t_sec and (t_sec == c_pri or t_sec == c_sec)):
            # Verify string edit distance is reasonable (<= 3)
            if damerau_levenshtein_distance(t_clean, c.lower()) <= 3:
                return c

    return None
