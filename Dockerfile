FROM python:3.12-alpine AS build

RUN apk add --no-cache curl ca-certificates

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY pyknit ./pyknit
RUN pip wheel --no-deps --no-cache-dir --wheel-dir /wheel .

WORKDIR /site
COPY demos ./
COPY build/ /tmp/build/
RUN rm -rf README.md Makefile _assets/japanese-symbols && \
    mkdir -p _wheel _assets/pyodide _assets/wheels && \
    cp /wheel/pyknit-*.whl _wheel/ && \
    if [ -d /tmp/build/pyodide ]; then cp -a /tmp/build/pyodide/. _assets/pyodide/; fi && \
    if [ -d /tmp/build/wheels ]; then cp -a /tmp/build/wheels/. _assets/wheels/; fi && \
    PYODIDE=https://cdn.jsdelivr.net/pyodide/v0.24.1/full && \
    for f in pyodide.mjs pyodide.asm.js pyodide.asm.wasm pyodide-lock.json \
             python_stdlib.zip micropip-0.5.0-py3-none-any.whl \
             packaging-23.1-py3-none-any.whl; do \
        if [ ! -f "_assets/pyodide/$f" ]; then \
            curl -fsSL -o "_assets/pyodide/$f" "$PYODIDE/$f"; \
        fi; \
    done && \
    for f in typing_extensions-4.7.1-py3-none-any.whl \
             pydantic-1.10.7-py3-none-any.whl \
             Pillow-10.0.0-cp311-cp311-emscripten_3_1_45_wasm32.whl; do \
        if [ ! -f "_assets/wheels/$f" ]; then \
            curl -fsSL -o "_assets/wheels/$f" "$PYODIDE/$f"; \
        fi; \
    done

FROM nginxinc/nginx-unprivileged:alpine-slim AS runtime

COPY --from=build /site/ /usr/share/nginx/html/
COPY demos/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080