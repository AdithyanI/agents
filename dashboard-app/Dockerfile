# Agents control-plane dashboard for ASUS. Build context: a git archive of this
# repository at one revision (see scripts/deploy-linux-control-plane-dashboard.py).
FROM node:22-bookworm-slim AS build
WORKDIR /build
COPY dashboard-app/package.json dashboard-app/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY dashboard-app/ ./
RUN npm run build

FROM python:3.13-slim
ARG RELEASE_REVISION
LABEL io.agents-dashboard.service="dashboard" \
      org.opencontainers.image.revision="${RELEASE_REVISION}"
# PyYAML parses skill metadata; everything else is stdlib.
RUN pip install --no-cache-dir PyYAML==6.0.3
WORKDIR /app
COPY . /app/
COPY --from=build /build/dist /app/dashboard-dist
# The queue extracts sources with umask 0077; make the release readable by the runtime user.
RUN rm -rf /app/dashboard-app/node_modules && chmod -R a+rX /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 AGENTS_DASHBOARD_HOSTED=1 \
    RELEASE_REVISION=${RELEASE_REVISION}
USER 1000:1000
CMD ["sh", "-c", "exec python /app/scripts/control-plane-dashboard.py serve --root /app --dashboard-root /app/dashboard-dist --host 127.0.0.1 --port 8765 --release-sha \"$RELEASE_REVISION\" --no-input"]
