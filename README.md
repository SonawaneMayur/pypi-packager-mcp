# PyPI Packager MCP Server

An advanced Model Context Protocol server for packaging Python code into production-ready PyPI packages with automated quality checks and secure publishing.

## Features

### Core Packaging Capabilities
- Automatic generation of standard `src/` layout using FastMCP tooling.  
- Dynamic generation of `pyproject.toml` and `README.md` files.

### Quality Assurance
- Linting with Ruff to enforce code style and quality.  
- Testing via pytest for automated test execution.  
- Build validation using the build library to create both source and wheel distributions.

### Security & Publishing
- Secure handling of PyPI tokens with Twine for authenticated uploads.  
- Support for publishing to PyPI or TestPyPI repositories.  
- Isolated package builds in temporary directories to prevent workspace pollution.

## Installation
python3 -m venv .venv    # Create virtual environment
source .venv/bin/activate  # Activate environment
pip install fastmcp build twine ruff pytest pydantic  # Install dependencies


## Usage

**Development Mode**  
fastmcp dev src/pypi_packager_mcp/server.py  # Start server with stdio transport


**Production Deployment**  
fastmcp run src/pypi_packager_mcp/server.py –transport streamable-http –host 0.0.0.0 –port 8000  # HTTP transport


## Tool API

Use the `create_pypi_package` tool with parameters described below.

| Parameter     | Type     | Required | Description                                                                                 |
|---------------|----------|----------|---------------------------------------------------------------------------------------------|
| source_path   | string   | Yes      | Path to a Python file or directory to package                                               |
| package_name  | string   | Yes      | Desired PyPI package name                                                                  |
| version       | string   | Yes      | Semantic version identifier (e.g., `"1.0.0"`)                                               |
| pypi_token    | string   | No       | PyPI API token for uploading distributions                                                  |
| repository    | string   | No       | Repository target (`"pypi"` or `"testpypi"`)                                                |
| run_tests     | boolean  | No       | Run pytest on tests directory if present (default: `true`)                                  |
| lint_code     | boolean  | No       | Run Ruff linter on source code (default: `true`)                                            |
| min_python    | string   | No       | Minimum required Python version (default: `"3.8"`)                                          |

### Example Request
{ “source_path”: “/path/to/my_module”, “package_name”: “awesome_tool”, “version”: “1.0.0”, “pypi_token”: “pypi-AgENdGV…”, “repository”: “pypi”, “run_tests”: true, “lint_code”: true, “min_python”: “3.9” }

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.  
For the full text of the MIT License, visit https://opensource.org/licenses/MIT [1].

---

https://pypi.org/project/fastmcp/  
https://pypi.org/project/build/  
https://pypi.org/project/twine/  
https://pypi.org/project/ruff/  
https://docs.pytest.org/en/stable/  
https://pydantic-docs.helpmanual.io/  
https://docs.python.org/3/library/venv.html  
