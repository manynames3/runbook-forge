FROM python:3.12-slim

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace

COPY pyproject.toml README.md ./
COPY src ./src
COPY fixtures ./fixtures
COPY reports/.gitkeep ./reports/.gitkeep
COPY runbooks/.gitkeep ./runbooks/.gitkeep

RUN python -m pip install --upgrade pip \
    && python -m pip install -e ".[dev]"

CMD ["runbook-forge", "demo"]
