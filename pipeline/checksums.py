"""LEI check-digit validation, ISO 17442 / ISO 7064 MOD 97-10.

Arithmetic in code, policy in shapes: the pipeline computes validity and
asserts it into the graph; SHACL requires the recorded result.
"""

def lei_checksum_valid(lei: str) -> bool:
    """ISO 7064 MOD 97-10 over the base-36 expansion of the 20-char LEI."""
    lei = lei.strip().upper()
    if len(lei) != 20 or not lei.isalnum():
        return False
    try:
        expanded = "".join(str(int(c, 36)) for c in lei)
    except ValueError:
        return False
    return int(expanded) % 97 == 1


def lei_wellformed(lei: str) -> bool:
    """ISO 17442 shape: 18 alphanumerics + 2 decimal check digits."""
    lei = lei.strip().upper()
    return len(lei) == 20 and lei[:18].isalnum() and lei[18:].isdigit()


# Embedded test vectors: real LEIs (valid) and observed register defects.
_VALID = [
    "5493000MN7XN3BBKCE67",  # AP Skadesforsikring, the corrected form
    "213800B4ZY949VJYD671",  # Ergon Insurance Limited
    "529900J6X2TY517BIE79",  # SIGNAL IDUNA Biztosító
]
_INVALID = [
    "00000000000000000000",  # all zeros, filed in the EIOPA register
    "5493O00MN7XN3BBKCE67",  # letter O for zero, filed in the EIOPA register
    "529900TDXS505XDXWZ69",
    "549300X77HR0ZWZELM25",
    "5493000MN7XN3BBKCE6",   # truncated
]

def _selftest():
    for lei in _VALID:
        assert lei_checksum_valid(lei), lei
    for lei in _INVALID:
        assert not lei_checksum_valid(lei), lei

_selftest()
