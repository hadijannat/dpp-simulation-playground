# Contributing

Thank you for contributing to DPP Simulation Playground.

## Development Setup

1. Clone the repository.
2. Start infrastructure with `make up`.
3. Run the frontend: `cd frontend && npm install && npm run dev`.
4. Run a backend service locally with `uvicorn app.main:app --reload`.

## Code Style
- Python: Ruff for linting and formatting, mypy for type checking.
- TypeScript: ESLint + Prettier.
- Commits: Conventional commits (`feat:`, `fix:`, `docs:`, `chore:`).

## Pull Requests
- Ensure tests pass (`make test`).
- Update docs when relevant.
