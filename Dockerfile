# Image for running FaraX in development with Docker Compose (see compose.yaml).
FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:0.13 /uv /uvx /bin/

# The package version normally comes from git tags (setuptools-scm), but .git isn't
# copied into the image. Pass the real version with
# `--build-arg FARAX_VERSION=$(git describe --tags)` if it matters.
ARG FARAX_VERSION=0.0.0
ENV SETUPTOOLS_SCM_PRETEND_VERSION_FOR_FARAX=${FARAX_VERSION}

# Keep the virtual environment outside /app so the source code mount in Compose doesn't
# hide it, and don't write bytecode into the mounted source tree.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/opt/venv/bin:$PATH

WORKDIR /app

# Install the dependencies first, so this layer is reused until the lock file changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

# Install the project itself, without editable mode.
COPY . .
RUN uv sync --locked --no-dev --no-editable

# Run as an unprivileged user. The File Store directory is created here so the named
# volume mounted over it is writable by that user.
ARG UID=1000
RUN useradd --uid ${UID} --no-create-home farax \
    && mkdir -p /data/media \
    && chown farax /data/media
USER farax

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
