FROM python:3.12-alpine AS build

RUN apk add --no-cache ca-certificates

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY pyknit ./pyknit
RUN pip wheel --no-deps --no-cache-dir --wheel-dir /wheel .

WORKDIR /site
COPY demos ./
COPY build/ /tmp/build/
RUN set -eux; \
    rm -rf README.md Makefile favicon.ico; \
    mkdir -p wheels pyscript pyodide; \
    test -s /tmp/build/pyscript/core.js; \
    test -s /tmp/build/pyscript/core.css; \
    test -s /tmp/build/pyodide/pyodide.mjs; \
    test -s /tmp/build/pyodide/pyodide.asm.js; \
    test -s /tmp/build/pyodide/pyodide.asm.wasm; \
    test -s /tmp/build/pyodide/pyodide-lock.json; \
    test -s /tmp/build/pyodide/python_stdlib.zip; \
    test -s /tmp/build/wheels/Pillow-10.0.0-cp311-cp311-emscripten_3_1_45_wasm32.whl; \
    test -s /tmp/build/wheels/pydantic-1.10.7-py3-none-any.whl; \
    test -s /tmp/build/wheels/typing_extensions-4.7.1-py3-none-any.whl; \
    find /tmp/build/wheels -maxdepth 1 -type f -name 'pyknit-*.whl' -size +0c | grep -q .; \
    cp /wheel/pyknit-*.whl wheels/; \
    cp -a /tmp/build/pyscript/. pyscript/; \
    cp -a /tmp/build/pyodide/. pyodide/; \
    cp -a /tmp/build/wheels/. wheels/; \
    if [ -d _wheel ]; then cp -a _wheel/. wheels/; fi; \
    printf '%s\n' '"""Gauge conversion demo bootstrap (generated in image)."""' \
        'from pyknit.pyscript._demos import gauge_conversion_page  # noqa: F401  # auto-bootstraps' \
        > gauge-conversion.py; \
    cp _assets/common.css .; \
    cp _assets/sock.jpg .; \
    cp _assets/sweater.jpg .; \
    find . -name '*.html' -exec sed -i \
        -e 's|/_assets/pyodide/|/pyodide/|g' \
        -e 's|/_assets/pyscript/|/pyscript/|g' \
        -e 's|/_assets/wheels/|/wheels/|g' \
        -e 's|/_wheel/|/wheels/|g' \
        -e 's|/_assets/common\.css|/common.css|g' \
        -e 's|/_assets/gauge-conversion\.py|/gauge-conversion.py|g' \
        -e 's|_assets/sock\.jpg|sock.jpg|g' \
        -e 's|_assets/sweater\.jpg|sweater.jpg|g' \
        {} +; \
    rm -rf _assets _wheel

FROM nginxinc/nginx-unprivileged:alpine-slim AS runtime

COPY --from=build /site/ /usr/share/nginx/html/
COPY demos/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080
