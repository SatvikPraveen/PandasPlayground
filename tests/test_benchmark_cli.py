from __future__ import annotations

import json

import pytest

from pandasplayground import __version__, benchmark, cli


def test_time_callable_and_comparison():
    t = benchmark.time_callable("noop", lambda: None, repeat=3, min_time=0.01)
    assert len(t.samples) == 3 and t.loops >= 1 and t.best <= t.median


def test_tiny_suite_runs_and_serialises(tmp_path):
    run = benchmark.run_suite(n_rows=2_000, repeat=2, apply_rows=200)
    assert {c.case for c in run.comparisons} >= {"groupby_category_keys", "vectorized_vs_apply", "read_csv_vs_parquet"}
    data = json.loads(run.write_json(tmp_path / "r.json").read_text())
    assert data["environment"]["packages"]["pandas"]
    md = run.to_markdown()
    assert "chained \\|" in md  # pipes are escaped so the table renders
    assert 0 < run.memory["reduction"] < 1


def test_cli_version(capsys):
    with pytest.raises(SystemExit):
        cli.main(["--version"])
    assert __version__ in capsys.readouterr().out


@pytest.mark.integration
def test_cli_validate_and_pipeline(tmp_path, capsys):
    assert cli.main(["validate"]) == 0
    assert "9/9 datasets passed" in capsys.readouterr().out
    out = tmp_path / "p.csv"
    assert cli.main(["pipeline", "--output", str(out)]) == 0
    assert out.exists() and out.with_suffix(".manifest.json").exists()


def test_cli_generate_refuses_bundled_data_dir(capsys):
    assert cli.main(["generate", "--out", str(cli.PATHS.data)]) == 2


def test_cli_generate_and_docs_check(tmp_path, capsys):
    assert cli.main(["generate", "--out", str(tmp_path / "g"), "--rows", "30"]) == 0
    stale = tmp_path / "dd.md"
    stale.write_text("old")
    assert cli.main(["docs", "data-dictionary", "--out", str(stale), "--check"]) == 1
    assert cli.main(["docs", "data-dictionary", "--out", str(stale)]) == 0
    assert cli.main(["docs", "data-dictionary", "--out", str(stale), "--check"]) == 0


def test_cli_info(capsys):
    assert cli.main(["info"]) == 0
    assert json.loads(capsys.readouterr().out)["version"] == __version__
