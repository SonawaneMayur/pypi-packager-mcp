import pytest
from pathlib import Path
import tempfile
from src.pypi_packager_mcp.server import setup_package_structure, PackageRequest


def test_package_structure_creation():
    """Test package structure creation"""
    with tempfile.TemporaryDirectory() as tmpdir:
        request = PackageRequest(
            source_path="dummy_path",
            package_name="test_package",
            version="1.0.0"
        )

        package_dir = setup_package_structure(tmpdir, request)

        assert package_dir.exists()
        assert (package_dir / "pyproject.toml").exists()
        assert (package_dir / "README.md").exists()
        assert (package_dir / "src" / "test_package" / "__init__.py").exists()


def test_package_request_validation():
    """Test PackageRequest model validation"""
    request = PackageRequest(
        source_path="/path/to/source",
        package_name="my-package",
        version="1.0.0"
    )

    assert request.source_path == "/path/to/source"
    assert request.package_name == "my-package"
    assert request.version == "1.0.0"
    assert request.repository == "pypi"  # default value
