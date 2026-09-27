"""Headless smoke tests: every dashboard page must render without raising."""

from __future__ import annotations

import pytest

from .conftest import ROOT

pytest.importorskip("streamlit")
pytest.importorskip("plotly")
from streamlit.testing.v1 import AppTest  # noqa: E402

pytestmark = pytest.mark.integration

PAGES = [ROOT / "STREAMLIT_App.py", *sorted((ROOT / "pages").glob("*.py"))]


@pytest.mark.parametrize("page", PAGES, ids=[p.name for p in PAGES])
def test_page_renders(page, monkeypatch):
    monkeypatch.chdir(ROOT)
    at = AppTest.from_file(str(page), default_timeout=120).run()
    assert not at.exception, [e.value for e in at.exception]
