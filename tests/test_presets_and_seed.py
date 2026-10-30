"""Unit tests for presets, custom configs, and deterministic seeding."""

from company_name.generator import WordGenerator
from company_name.presets import create_config_from_dict, get_preset, load_custom_config


def test_seed_reproducibility():
    gen1 = WordGenerator(preset_name="balanced", seed=42)
    gen2 = WordGenerator(preset_name="balanced", seed=42)

    res1 = gen1.generate(count=10)
    res2 = gen2.generate(count=10)

    spellings1 = [r.spelling for r in res1]
    spellings2 = [r.spelling for r in res2]

    assert spellings1 == spellings2
    assert [r.respelling for r in res1] == [r.respelling for r in res2]
    assert [r.ipa for r in res1] == [r.ipa for r in res2]
    assert [r.score for r in res1] == [r.score for r in res2]


def test_presets_loading():
    for name in ["balanced", "soft", "crisp", "tolkien", "elvish"]:
        config = get_preset(name)
        assert config.name in {"balanced", "soft", "crisp", "tolkien"}
        assert len(config.consonant_weights) > 0
        assert len(config.vowel_weights) > 0


def test_custom_toml_config():
    config = load_custom_config("example_custom.toml")
    assert config.name == "custom"
    assert config.cluster_probability == 0.10
    assert config.consonant_weights["l"] == 6.0


def test_config_allow_reduplication_is_honoured():
    config = create_config_from_dict("custom", {"allow_reduplication": True})
    gen = WordGenerator(config=config)
    assert gen.filter.allow_reduplication


def test_generator_constraints_filtering():
    gen = WordGenerator(preset_name="balanced", seed=101)

    # starts_with constraint
    res_start = gen.generate(count=5, starts_with="Lu")
    for r in res_start:
        assert r.spelling.lower().startswith("lu")

    # ends_with constraint
    res_end = gen.generate(count=5, ends_with="ra")
    for r in res_end:
        assert r.spelling.lower().endswith("ra")
