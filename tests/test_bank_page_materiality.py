"""Unit guards: a published date is reused only for identical code records."""
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "site"))
from bank_page_materiality import date_for_code, load_published_catalog, MAX_CATALOG_BYTES


def catalog(date, *, bic="RLNWATWWXXX"):
    return {
        "country": "AT", "relation": "OFFICIAL_LIST",
        "effective_date": date,
        "codes": {"32600": {"n": "Synthetic Bank", "b": [bic]},
                  "99901": {"n": "Unchanged Bank", "b": ["TESTATWWXXX"]}},
    }


def test_date_tracks_exact_material_change_only():
    published = catalog("2026-11-03")
    current = catalog("2026-11-11", bic="RLNWATWW600")
    assert date_for_code(current, published, "99901") == "2026-11-03"
    assert date_for_code(current, published, "32600") == "2026-11-11"
    assert date_for_code(current, published, "new-code") == "2026-11-11"
    assert date_for_code(current, None, "99901") == "2026-11-11"
    assert published["codes"]["32600"]["b"] == ["RLNWATWWXXX"]
    assert current["codes"]["32600"]["b"] == ["RLNWATWW600"]


def test_baseline_loader_is_strict_and_never_falls_back_silently(tmp_path):
    target = tmp_path / "AT.json"
    valid = catalog("2026-11-03")
    target.write_text(json.dumps(valid), encoding="utf-8")
    assert load_published_catalog(tmp_path, "AT") == valid
    with pytest.raises(ValueError, match="country"):
        load_published_catalog(tmp_path, "../AT")
    for key, value in [
        ("country", "OTHER"), ("relation", "UNVERIFIED"),
        ("effective_date", "2026-02-30"),
        ("effective_date", "2026-11-11oops"), ("codes", []),
    ]:
        candidate = {**valid, key: value}
        target.write_text(json.dumps(candidate), encoding="utf-8")
        with pytest.raises(ValueError):
            load_published_catalog(tmp_path, "AT")
    target.write_bytes(b"x" * (MAX_CATALOG_BYTES + 1))
    with pytest.raises(ValueError, match="limit"):
        load_published_catalog(tmp_path, "AT")


def test_symlink_is_not_accepted_as_verified_baseline(tmp_path):
    genuine = tmp_path / "genuine.json"
    genuine.write_text(json.dumps(catalog("2026-11-03")), encoding="utf-8")
    link = tmp_path / "AT.json"
    link.symlink_to(genuine)
    with pytest.raises(ValueError, match="regular file"):
        load_published_catalog(tmp_path, "AT")
