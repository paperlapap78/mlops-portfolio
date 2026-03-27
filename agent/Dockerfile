# ── Stage 1: builder ──────────────────────────────────────────────────────────
# Installs all production dependencies into a known location.
# We do this in a separate stage so the final image doesn't contain pip,
# setuptools, or build cache — keeping the runtime image lean and clean.
FROM python:3.11-slim AS builder

WORKDIR /build

# hatch-vcs reads the version from git tags, but Docker builds have no .git directory.
# Pass the version in at build time; CI supplies the real tag, local builds fall back to 0.0.0.
ARG SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0

# Copy only the packaging manifest first.
# Docker layer-caches this step — a code change in src/ won't re-run pip install.
COPY pyproject.toml .

# Install production dependencies only (no [dev] extras — no pytest, mypy, ruff in prod)
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir .


# ── Stage 2: runtime ──────────────────────────────────────────────────────────
# Minimal image: only the installed packages and application source code.
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed Python packages from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source code
COPY src/ src/

# Tell Python where to find the agent package
ENV PYTHONPATH=/app/src

# Run as non-root — security best practice for containerised workloads
# (EKS pods should never run as root unless explicitly required)
USER nobody

EXPOSE 8000

# Single worker: avoids OTel TracerProvider conflicts across forked processes.
# Concurrency comes from uvicorn's async event loop, which is sufficient for
# the I/O-bound workloads this app performs (Bedrock API calls, OpenSearch queries).
CMD ["uvicorn", "agent.infrastructure.api.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1"]
