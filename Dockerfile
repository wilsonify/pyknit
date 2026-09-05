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
    mkdir -p _wheel _assets/pyscript _assets/pyodide _assets/wheels && \
    cp /wheel/pyknit-*.whl _wheel/ && \
    printf '%s\n' '"""Gauge conversion demo bootstrap (generated in image)."""' \
        'from pyknit.pyscript._demos import gauge_conversion_page  # noqa: F401  # auto-bootstraps' \
        > _assets/gauge-conversion.py && \
    if [ -d /tmp/build/pyscript ]; then cp -a /tmp/build/pyscript/. _assets/pyscript/; fi && \
    if [ -d /tmp/build/pyodide ]; then cp -a /tmp/build/pyodide/. _assets/pyodide/; fi && \
    if [ -d /tmp/build/wheels ]; then cp -a /tmp/build/wheels/. _assets/wheels/; fi && \
    PYODIDE=https://cdn.jsdelivr.net/pyodide/v0.24.1/full && \
    PYSCRIPT=https://pyscript.net/releases/2024.10.1 && \
    for f in core.css core.js core.js.map core-DHft4mQJ.js \
             core-DHft4mQJ.js.map \
             toml-CvAfdf9_.js toml-DiUM0_qs.js \
             zip-Bf48tRr5.js \
             deprecations-manager-BDRw2fed.js \
             donkey-c355Wa24.js \
             error-CdZsd8BO.js \
             py-editor-BRZBRs2T.js \
             py-terminal-D_z3jMz-.js; do \
        if [ ! -f "_assets/pyscript/$f" ]; then \
            curl -fsSL -o "_assets/pyscript/$f" "$PYSCRIPT/$f"; \
        fi; \
    done && \
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