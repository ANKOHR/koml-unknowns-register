import pytest
from koml_unknowns_register.fixtures import generate

@pytest.fixture
def fixture_dir(tmp_path):
    generate(tmp_path / "input")
    return tmp_path / "input"
