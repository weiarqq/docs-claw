import pytest

from docs_claw.paths import safe_id


def test_safe_id_accepts_lowercase_ids():
    assert safe_id("ryzenai") == "ryzenai"
    assert safe_id("amd_docs-2026") == "amd_docs-2026"


@pytest.mark.parametrize("value", ["../x", "RyzenAI", "docs/site", "", "a.b"])
def test_safe_id_rejects_unsafe_ids(value):
    with pytest.raises(ValueError):
        safe_id(value)
