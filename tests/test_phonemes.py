"""Unit tests for phoneme inventories and properties."""

from company_name.phonemes import (
    ALLOWED_CODAS,
    ALLOWED_ONSET_CLUSTERS,
    CONSONANTS,
    VOWELS,
    PhoneticClass,
    VowelQuality,
)


def test_consonant_inventory_rules():
    # Never use 'th', 'ng', 'zh' as onsets
    assert "th" not in CONSONANTS
    assert "ng" not in CONSONANTS
    assert "zh" not in CONSONANTS

    # 'x' is not allowed as onset, only as rare coda
    assert not CONSONANTS["x"].can_onset
    assert CONSONANTS["x"].can_coda

    # Check sonorants
    sonorants = [k for k, v in CONSONANTS.items() if v.phonetic_class == PhoneticClass.SONORANT]
    assert set(sonorants) == {"l", "m", "n", "r"}

    # Check plosives
    plosives = [k for k, v in CONSONANTS.items() if v.phonetic_class == PhoneticClass.PLOSIVE]
    assert set(plosives) == {"k", "t", "p", "b", "d", "g"}


def test_allowed_clusters_whitelist():
    expected_clusters = {
        "bl", "br", "cl", "cr", "dr", "fl", "fr", "gl", "gr", "pl", "pr", "tr", "st", "sl"
    }
    assert set(ALLOWED_ONSET_CLUSTERS.keys()) == expected_clusters
    for cluster in ALLOWED_ONSET_CLUSTERS.values():
        assert cluster.is_cluster
        assert cluster.can_onset
        assert not cluster.can_coda


def test_vowel_inventory():
    assert "AX" in VOWELS  # schwa
    assert VOWELS["AX"].quality == VowelQuality.SCHWA
    assert VOWELS["AX"].ipa == "ə"

    # Tense vowels
    assert VOWELS["IY"].quality == VowelQuality.LONG_TENSE
    assert VOWELS["EY"].quality == VowelQuality.LONG_TENSE
    assert VOWELS["OW"].quality == VowelQuality.LONG_TENSE
    assert VOWELS["UW"].quality == VowelQuality.LONG_TENSE

    # Lax vowels
    assert VOWELS["AE"].quality == VowelQuality.SHORT_LAX
    assert VOWELS["EH"].quality == VowelQuality.SHORT_LAX
    assert VOWELS["IH"].quality == VowelQuality.SHORT_LAX
    assert VOWELS["AA"].quality == VowelQuality.SHORT_LAX
    assert VOWELS["AH"].quality == VowelQuality.SHORT_LAX
