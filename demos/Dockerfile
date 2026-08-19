FROM python:3.12-alpine AS build

RUN apk add --no-cache curl ca-certificates

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY pyknit ./pyknit
RUN pip wheel --no-deps --no-cache-dir --wheel-dir /wheel .

WORKDIR /site
COPY demos ./
RUN rm -rf README.md Makefile _assets/japanese-symbols && \
    mkdir -p _wheel _assets/pyodide && \
    cp /wheel/pyknit-*.whl _wheel/ && \
    PYODIDE=https://cdn.jsdelivr.net/pyodide/v0.24.1/full && \
    for f in pyodide.mjs pyodide.asm.js pyodide.asm.wasm pyodide-lock.json \
             python_stdlib.zip micropip-0.5.0-py3-none-any.whl \
             packaging-23.1-py3-none-any.whl; do \
        curl -fsSL -o "_assets/pyodide/$f" "$PYODIDE/$f"; \
    done

FROM nginxinc/nginx-unprivileged:alpine-slim AS runtime

COPY --from=build /site/ /usr/share/nginx/html/
COPY demos/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080