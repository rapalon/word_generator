"""Presets and configuration loading for word generation."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
import tomllib


@dataclass
class GeneratorConfig:
    name: str = "balanced"
    syllable_distribution: dict[int, float] = field(
        default_factory=lambda: {1: 0.025, 2: 0.50, 3: 0.45, 4: 0.025}
    )
    consonant_weights: dict[str, float] = field(
        default_factory=lambda: {
            "l": 3.5, "m": 3.2, "n": 3.2, "r": 3.0,
            "s": 2.2, "v": 2.0, "d": 2.0, "b": 2.0, "k": 2.0, "t": 2.0,
            "p": 1.2, "g": 1.1, "f": 1.1, "z": 0.9, "h": 0.9, "y": 0.9, "w": 0.8,
            "x": 0.05,
        }
    )
    cluster_weights: dict[str, float] = field(
        default_factory=lambda: {
            "bl": 1.0, "br": 1.0, "cl": 0.9, "cr": 0.9, "dr": 0.9,
            "fl": 0.9, "fr": 0.9, "gl": 0.8, "gr": 0.8, "pl": 1.0,
            "pr": 1.0, "tr": 0.9, "st": 0.8, "sl": 0.8,
        }
    )
    cluster_probability: float = 0.20  # Max 1 cluster per word
    vowel_weights: dict[str, float] = field(
        default_factory=lambda: {
            "AE": 1.8, "EH": 2.0, "IH": 2.0, "AA": 2.2, "AH": 1.2,
            "IY": 2.5, "EY": 2.5, "OW": 2.8, "UW": 2.0, "AX": 1.0,
        }
    )
    open_syllable_target_min: float = 0.70
    min_length: int = 4
    max_length: int = 9
    require_memorability: bool = True  # At least 1 plosive & 1 sonorant
    allow_reduplication: bool = False


BALANCED_CONFIG = GeneratorConfig(name="balanced")

SOFT_CONFIG = GeneratorConfig(
    name="soft",
    syllable_distribution={1: 0.02, 2: 0.53, 3: 0.43, 4: 0.02},
    consonant_weights={
        "l": 5.0, "m": 4.8, "n": 4.5, "r": 4.0, "b": 3.5,
        "v": 2.5, "w": 2.0, "y": 2.0, "d": 1.5,
        "s": 1.0, "h": 1.0, "f": 0.8, "g": 0.6,
        "p": 0.5, "k": 0.4, "t": 0.4, "z": 0.3, "x": 0.01,
    },
    cluster_weights={
        "bl": 1.2, "br": 1.0, "fl": 1.0, "fr": 0.8, "gl": 0.8, "sl": 1.0,
        "cl": 0.3, "cr": 0.3, "dr": 0.4, "pl": 0.6, "pr": 0.6, "tr": 0.3, "st": 0.3, "gr": 0.5,
    },
    cluster_probability=0.15,
    vowel_weights={
        "OW": 4.5, "UW": 3.5, "AA": 3.2, "AX": 2.5,
        "AE": 1.5, "IY": 1.8, "EY": 2.0, "EH": 1.0, "IH": 0.8, "AH": 1.2,
    },
)

CRISP_CONFIG = GeneratorConfig(
    name="crisp",
    syllable_distribution={1: 0.05, 2: 0.55, 3: 0.38, 4: 0.02},
    consonant_weights={
        "k": 4.5, "t": 4.2, "p": 3.8, "s": 3.5, "z": 2.8,
        "d": 2.5, "b": 2.2, "v": 1.8, "f": 1.8, "g": 1.8,
        "l": 1.5, "r": 1.5, "n": 1.2, "m": 1.0, "h": 0.8, "y": 0.8, "w": 0.5,
        "x": 0.2,
    },
    cluster_weights={
        "st": 1.5, "tr": 1.4, "cl": 1.3, "cr": 1.3, "pr": 1.3, "pl": 1.2,
        "dr": 1.0, "fl": 0.9, "fr": 0.9, "sl": 0.8, "bl": 0.7, "br": 0.7, "gl": 0.6, "gr": 0.6,
    },
    cluster_probability=0.25,
    vowel_weights={
        "IY": 4.0, "EY": 3.8, "IH": 3.2, "EH": 3.0, "AE": 2.5,
        "OW": 1.5, "UW": 1.0, "AA": 1.2, "AH": 0.8, "AX": 0.8,
    },
)

TOLKIEN_CONFIG = GeneratorConfig(
    name="tolkien",
    syllable_distribution={1: 0.02, 2: 0.42, 3: 0.50, 4: 0.06},
    consonant_weights={
        "l": 5.8, "r": 5.2, "n": 4.8, "m": 3.8,
        "d": 3.0, "t": 2.8, "s": 2.8, "v": 2.6,
        "g": 2.2, "b": 2.0, "w": 1.8, "y": 1.8,
        "k": 1.6, "f": 1.4, "p": 1.4, "h": 1.2,
        "z": 0.1, "x": 0.01,
    },
    cluster_weights={
        "gl": 1.5, "gr": 1.4, "fl": 1.4, "fr": 1.3,
        "br": 1.3, "dr": 1.2, "cl": 1.2, "cr": 1.1,
        "tr": 1.2, "pl": 1.1, "sl": 1.1, "st": 1.0,
        "bl": 1.0, "pr": 1.0,
    },
    cluster_probability=0.22,
    vowel_weights={
        "AE": 3.8, "EH": 3.5, "IY": 3.2, "OW": 3.0,
        "AA": 2.6, "UW": 2.2, "EY": 2.0, "AX": 1.6,
        "IH": 1.2, "AH": 0.8,
    },
    open_syllable_target_min=0.72,
    min_length=4,
    max_length=9,
    require_memorability=True,
)

PRESETS: dict[str, GeneratorConfig] = {
    "balanced": BALANCED_CONFIG,
    "soft": SOFT_CONFIG,
    "crisp": CRISP_CONFIG,
    "tolkien": TOLKIEN_CONFIG,
    "elvish": TOLKIEN_CONFIG,
}


def load_custom_config(path: str | Path) -> GeneratorConfig:
    """Load a custom preset configuration from a JSON or TOML file."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")

    content = file_path.read_text(encoding="utf-8")
    if file_path.suffix.lower() == ".json":
        data = json.loads(content)
    elif file_path.suffix.lower() in {".toml", ".tml"}:
        data = tomllib.loads(content)
    else:
        # Try JSON first, then TOML
        try:
            data = json.loads(content)
        except Exception:
            data = tomllib.loads(content)

    return create_config_from_dict("custom", data)


def create_config_from_dict(name: str, data: dict[str, Any]) -> GeneratorConfig:
    """Create a GeneratorConfig from a dictionary, using balanced defaults for missing keys."""
    base = GeneratorConfig(name=name)

    if "syllable_distribution" in data:
        base.syllable_distribution = {
            int(k): float(v)
            for k, v in data["syllable_distribution"].items()
            if str(k).isdigit()
        }
    if "consonant_weights" in data:
        base.consonant_weights = {
            str(k): float(v) for k, v in data["consonant_weights"].items()
        }
    if "cluster_weights" in data:
        base.cluster_weights = {
            str(k): float(v) for k, v in data["cluster_weights"].items()
        }
    if "cluster_probability" in data:
        base.cluster_probability = float(data["cluster_probability"])
    if "vowel_weights" in data:
        base.vowel_weights = {
            str(k): float(v) for k, v in data["vowel_weights"].items()
        }
    if "open_syllable_target_min" in data:
        base.open_syllable_target_min = float(data["open_syllable_target_min"])
    if "min_length" in data:
        base.min_length = int(data["min_length"])
    if "max_length" in data:
        base.max_length = int(data["max_length"])
    if "require_memorability" in data:
        base.require_memorability = bool(data["require_memorability"])
    if "allow_reduplication" in data:
        base.allow_reduplication = bool(data["allow_reduplication"])

    return base


def get_preset(name: str, custom_path: Optional[str | Path] = None) -> GeneratorConfig:
    """Get preset by name ('balanced', 'soft', 'crisp', 'tolkien'/'elvish', or 'custom')."""
    preset_key = name.lower()
    if preset_key == "custom":
        if not custom_path:
            raise ValueError("custom_path must be provided when preset is 'custom'")
        return load_custom_config(custom_path)
    if preset_key in PRESETS:
        return PRESETS[preset_key]
    raise ValueError(f"Unknown preset '{name}'. Choose from: balanced, soft, crisp, tolkien, elvish, custom.")
