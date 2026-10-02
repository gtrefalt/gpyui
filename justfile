set shell := ["bash", "-euo", "pipefail", "-c"]

tools := "env -u VIRTUAL_ENV UV_PROJECT_ENVIRONMENT=.venv-tools uv run --locked --only-group dev"

# List available development commands.
default:
    @just --list

# Install Python development tools without building the Rust extension.
tools:
    env -u VIRTUAL_ENV UV_PROJECT_ENVIRONMENT=.venv-tools uv sync --locked --only-group dev

# Install the pre-commit and pre-push Git hooks.
hooks: tools
    {{ tools }} lefthook install

# Run all Python lint, formatting and type checks.
check: lint format-check typecheck
    @just --fmt --check
    {{ tools }} lefthook validate

# Check Python code and native-extension type stubs with Ruff.
lint:
    {{ tools }} ruff check src examples scripts tests

# Check formatting without modifying files.
format-check:
    {{ tools }} ruff format --check src examples scripts tests

# Apply safe lint fixes and format Python files.
format:
    {{ tools }} ruff check --fix src examples scripts tests
    {{ tools }} ruff format src examples scripts tests

# Check the library, examples, scripts and tests with ty.
typecheck:
    {{ tools }} ty check

# Run Python and Rust bridge tests (requires the native build prerequisites).
test:
    env -u VIRTUAL_ENV UV_PROJECT_ENVIRONMENT=.venv uv run --locked pytest -q

# Run actual native-window interaction tests on a real or virtual display.
test-native:
    env -u VIRTUAL_ENV UV_PROJECT_ENVIRONMENT=.venv scripts/test-native.sh

# Check Rust formatting and linting.
rust-check:
    cargo fmt --check
    cargo clippy --locked -- -D warnings

# Build the extension and wheel in release mode.
build:
    env -u VIRTUAL_ENV UV_PROJECT_ENVIRONMENT=.venv uv build --wheel

# Verify generated references and build the documentation in strict mode.
docs-check:
    env -u VIRTUAL_ENV UV_PROJECT_ENVIRONMENT=.venv-docs uv run --locked --only-group docs python scripts/generate-docs.py --check
    env -u VIRTUAL_ENV UV_PROJECT_ENVIRONMENT=.venv-docs uv run --locked --only-group docs zensical build --strict --clean
    env -u VIRTUAL_ENV UV_PROJECT_ENVIRONMENT=.venv-docs uv run --locked --only-group docs python scripts/check-docs-site.py

# Regenerate component references and versioned preview URLs.
docs-generate:
    env -u VIRTUAL_ENV UV_PROJECT_ENVIRONMENT=.venv-docs uv run --locked --only-group docs python scripts/generate-docs.py

# Serve the documentation locally.
docs-serve:
    env -u VIRTUAL_ENV UV_PROJECT_ENVIRONMENT=.venv-docs uv run --locked --only-group docs zensical serve
