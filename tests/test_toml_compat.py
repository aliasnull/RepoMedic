from repomedic.core.toml_compat import loads, _parse_minimal_toml

def test_toml_compat_loads_standard_pyproject():
    content = """
    [build-system]
    requires = ["setuptools>=61.0.0", "wheel"]
    build-backend = "setuptools.build_meta"

    [project]
    name = "repomedic"
    version = "0.1.0"
    description = "Repo diagnostics toolkit"
    requires-python = ">=3.10"
    dependencies = [
        "typing_extensions>=4.0; python_version < '3.11'",
    ]

    [project.optional-dependencies]
    dev = [
        "pytest>=7.0",
    ]
    """
    data = loads(content)
    assert data["project"]["name"] == "repomedic"
    assert data["project"]["requires-python"] == ">=3.10"
    assert "setuptools>=61.0.0" in data["build-system"]["requires"]
    assert "pytest>=7.0" in data["project"]["optional-dependencies"]["dev"]

def test_minimal_toml_fallback_parser():
    content = """
    # This is a comment
    [package]
    name = "test-pkg"
    enabled = true
    count = 42

    [package.meta]
    authors = ["Alice", "Bob"]
    """
    data = _parse_minimal_toml(content)
    assert data["package"]["name"] == "test-pkg"
    assert data["package"]["enabled"] is True
    assert data["package"]["count"] == 42
    assert data["package"]["meta"]["authors"] == ["Alice", "Bob"]

def test_toml_compat_fallback_when_tomllib_is_none(monkeypatch):
    import repomedic.core.toml_compat as tc
    monkeypatch.setattr(tc, "tomllib", None)
    
    content = """
    [project]
    name = "pure-py310"
    version = "1.0.0"
    dependencies = ["requests>=2.0.0"]
    """
    data = tc.loads(content)
    assert data["project"]["name"] == "pure-py310"
    assert data["project"]["dependencies"] == ["requests>=2.0.0"]

