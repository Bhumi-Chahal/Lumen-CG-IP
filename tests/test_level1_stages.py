from pathlib import Path

def test_project_dependencies_and_package_layout():
    root=Path(__file__).resolve().parents[1]
    assert "pygame" in (root/"requirements.txt").read_text()
    for name in ("content","engine","systems"):
        assert (root/"src"/name/"__init__.py").is_file()
