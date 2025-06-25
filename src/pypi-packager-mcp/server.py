from fastmcp import FastMCP
from pydantic import BaseModel, Field
import subprocess
import shutil
import os
import tempfile
from pathlib import Path
from typing import List, Optional

# Initialize FastMCP server
mcp = FastMCP("Advanced PyPI Packager",
              instructions="Converts Python code to production-ready PyPI packages")


class PackageRequest(BaseModel):
    source_path: str = Field(..., description="Path to Python file or directory")
    package_name: str = Field(..., description="Name for PyPI package")
    version: str = Field(..., description="Package version (semantic format)")
    pypi_token: Optional[str] = Field(None, description="PyPI API token for upload")
    repository: str = Field("pypi", description="'pypi' or 'testpypi'")
    run_tests: bool = Field(True, description="Run pytest if tests exist")
    lint_code: bool = Field(True, description="Run Ruff linter")
    min_python: str = Field("3.8", description="Minimum Python version")


class PackageResponse(BaseModel):
    status: str
    build_log: List[str]
    dist_files: List[str]
    errors: List[str] = []
    pypi_url: Optional[str] = None


@mcp.tool()
def create_pypi_package(request: PackageRequest) -> PackageResponse:
    """Converts Python code to PyPI package with quality checks and upload"""
    build_log = []
    errors = []
    dist_files = []
    pypi_url = None

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            # 1. Create package structure
            build_log.append("📦 Creating package structure...")
            package_dir = setup_package_structure(tmpdir, request)

            # 2. Linting
            if request.lint_code:
                build_log.append("🔍 Running linter...")
                lint_result = run_ruff_lint(package_dir)
                build_log.extend(lint_result['logs'])
                if lint_result['errors']:
                    errors.extend(lint_result['errors'])

            # 3. Testing
            if request.run_tests:
                build_log.append("🧪 Running tests...")
                test_result = run_pytest(package_dir)
                build_log.extend(test_result['logs'])
                if test_result['errors']:
                    errors.extend(test_result['errors'])

            # 4. Build package
            build_log.append("🏗️ Building package...")
            build_result = build_package(package_dir)
            build_log.extend(build_result['logs'])
            dist_files = build_result['dist_files']

            # 5. Upload to PyPI
            if request.pypi_token and not errors:
                build_log.append("🚀 Uploading to PyPI...")
                upload_result = upload_package(package_dir, request)
                build_log.extend(upload_result['logs'])
                pypi_url = upload_result.get('pypi_url')
                if upload_result.get('errors'):
                    errors.extend(upload_result['errors'])

            status = "success" if not errors else "partial_success"

        except Exception as e:
            errors.append(f"Critical error: {str(e)}")
            status = "error"

    return PackageResponse(
        status=status,
        build_log=build_log,
        dist_files=dist_files,
        errors=errors,
        pypi_url=pypi_url
    )


def setup_package_structure(tmpdir: str, request: PackageRequest) -> Path:
    """Create standard PyPI package structure"""
    package_dir = Path(tmpdir) / request.package_name
    src_dir = package_dir / "src" / request.package_name
    src_dir.mkdir(parents=True, exist_ok=True)

    # Copy source files
    source_path = Path(request.source_path)
    if source_path.is_dir():
        shutil.copytree(source_path, src_dir, dirs_exist_ok=True)
    else:
        shutil.copy(source_path, src_dir / source_path.name)

    # Create __init__.py if missing
    if not (src_dir / "__init__.py").exists():
        (src_dir / "__init__.py").write_text(f'__version__ = "{request.version}"\n')

    # Create pyproject.toml
    pyproject_content = f"""[build-system]
        requires = ["setuptools>=61.0"]
        build-backend = "setuptools.build_meta"
        
        [project]
        name = "{request.package_name}"
        version = "{request.version}"
        description = "Auto-generated PyPI package via MCP"
        requires-python = ">={request.min_python}"
        authors = [
            {{name = "MCP Packager", email = "mcp@example.com"}}
        ]
        
        [tool.ruff]
        line-length = 120
        select = ["E", "F", "W", "I"]
        """
    (package_dir / "pyproject.toml").write_text(pyproject_content)

    # Create README
    readme_content = f"""# {request.package_name}

            Automatically packaged via MCP server.
            
            ## Installation
            
            pip install {request.package_name}
                
            
            ## Usage
            
            import {request.package_name}
    
            Your usage instructions here
    """
    (package_dir / "README.md").write_text(readme_content)

    return package_dir


def run_ruff_lint(package_dir: Path) -> dict:
    """Run Ruff linter on the package"""
    logs = []
    errors = []
    try:
        result = subprocess.run(
            ["ruff", "check", str(package_dir / "src")],
            capture_output=True,
            text=True,
            cwd=package_dir
        )
        if result.returncode == 0:
            logs.append("✅ Linting passed")
        else:
            logs.append(f"⚠️ Linting issues:\n{result.stdout}")
            if result.stderr:
                errors.append(f"Linting error: {result.stderr}")
    except Exception as e:
        errors.append(f"Linter error: {str(e)}")
    return {"logs": logs, "errors": errors}


def run_pytest(package_dir: Path) -> dict:
    """Run pytest on the package"""
    logs = []
    errors = []
    test_dir = package_dir / "tests"

    if not test_dir.exists():
        logs.append("ℹ️ No tests found - skipping")
        return {"logs": logs, "errors": errors}

    try:
        result = subprocess.run(
            ["pytest", str(test_dir), "-v"],
            capture_output=True,
            text=True,
            cwd=package_dir
        )
        logs.append(f"Test results:\n{result.stdout}")
        if result.returncode != 0:
            errors.append(f"Tests failed with exit code {result.returncode}")
    except Exception as e:
        errors.append(f"Test runner error: {str(e)}")
    return {"logs": logs, "errors": errors}


def build_package(package_dir: Path) -> dict:
    """Build the Python package"""
    logs = []
    dist_files = []
    try:
        result = subprocess.run(
            ["python", "-m", "build"],
            capture_output=True,
            text=True,
            cwd=package_dir
        )
        logs.append("Build output:\n" + result.stdout)
        if result.returncode == 0:
            dist_dir = package_dir / "dist"
            if dist_dir.exists():
                dist_files = [str(f) for f in dist_dir.iterdir()]
                logs.append(f"📦 Built packages: {', '.join([f.name for f in dist_dir.iterdir()])}")
        else:
            return {
                "logs": logs,
                "dist_files": [],
                "errors": [f"Build failed with code {result.returncode}: {result.stderr}"]
            }
    except Exception as e:
        return {
            "logs": logs,
            "dist_files": [],
            "errors": [f"Build error: {str(e)}"]
        }
    return {"logs": logs, "dist_files": dist_files, "errors": []}


def upload_package(package_dir: Path, request: PackageRequest) -> dict:
    """Upload package to PyPI"""
    logs = []
    try:
        dist_path = package_dir / "dist" / "*"
        result = subprocess.run(
            [
                "twine", "upload",
                "--repository", request.repository,
                "--username", "__token__",
                "--password", request.pypi_token,
                str(dist_path)
            ],
            capture_output=True,
            text=True,
            cwd=package_dir
        )
        logs.append("Upload output:\n" + result.stdout)
        if result.returncode == 0:
            pypi_url = f"https://pypi.org/project/{request.package_name}/{request.version}/"
            return {"logs": logs, "pypi_url": pypi_url, "errors": []}
        else:
            return {"logs": logs, "errors": [f"Upload failed: {result.stderr}"]}
    except Exception as e:
        return {"logs": logs, "errors": [f"Upload error: {str(e)}"]}


if __name__ == "__main__":
    mcp.run(transport="stdio")
