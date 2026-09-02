PYTHON ?= python3
PORT ?= 8000
BUILD_DIR := build
WHEEL_DIR := $(BUILD_DIR)/wheel
PYODIDE_DIR := $(BUILD_DIR)/pyodide
WHEELS_DIR := $(BUILD_DIR)/wheels
PYSCRIPT_DIR := $(BUILD_DIR)/pyscript
DOCKER ?= docker
IMAGE ?= pyknit-demos

.PHONY: help setup wheel favicon serve run clean docker-build docker-test docker-serve docker-server runtime-cache docker copy-pyscript-assets

help:
	@echo "PyKnit browser demo helpers"
	@echo ""
	@echo "Targets:"
	@echo "  make setup         Build local wheel, ensure favicon, copy pyscript assets"
	@echo "  make wheel         Build local wheel into build/wheel"
	@echo "  make runtime-cache Download Pyodide runtime files into build/"
	@echo "  make copy-pyscript-assets  Copy pyscript/pyodide assets to demos/_assets/"
	@echo "  make favicon       Create an empty demos/favicon.ico if missing"
	@echo "  make serve         Run http.server from demos/ (default port 8000)"
	@echo "  make run           setup + serve"
	@echo "  make clean         Remove build artifacts"
	@echo "  make docker-build  Build the minimal production image"
	@echo "  make docker-test   Run the end-to-end tests against the image"
	@echo "  make docker-serve  Run the image on port 8080"
	@echo "  make docker-server Alias for docker-serve"
	@echo "  make docker        docker-build + docker-test"
	@echo ""
	@echo "Variables:"
	@echo "  PORT=9000          Change server port"
	@echo "  PYTHON=python3.12  Override Python executable"
	@echo "  DOCKER=docker      Container engine"
	@echo "  IMAGE=pyknit-demos  Image name for docker targets"

setup: wheel favicon demo-assets copy-pyscript-assets

demo-assets:
	mkdir -p demos/_assets
	@printf '%s\n' \
	  '"""Gauge conversion demo bootstrap (recreated by make demo-assets)."""' \
	  'from pyknit.pyscript._demos import gauge_conversion_page  # noqa: F401  # auto-bootstraps' \
	  > demos/_assets/gauge-conversion.py

copy-pyscript-assets: runtime-cache
	mkdir -p demos/_assets/pyscript demos/_assets/pyodide demos/_assets/wheels demos/_wheel
	cp -a $(PYSCRIPT_DIR)/* demos/_assets/pyscript/
	cp -a $(PYODIDE_DIR)/* demos/_assets/pyodide/
	cp -a $(WHEELS_DIR)/* demos/_assets/wheels/
	cp -a $(WHEEL_DIR)/*.whl demos/_wheel/ 2>/dev/null || true

wheel:
	mkdir -p $(BUILD_DIR) $(WHEEL_DIR)
	$(PYTHON) -m pip wheel . -w $(WHEEL_DIR) --no-deps

runtime-cache: $(PYODIDE_DIR) $(WHEELS_DIR) $(PYSCRIPT_DIR)
	@PYODIDE=https://cdn.jsdelivr.net/pyodide/v0.24.1/full; \
	PYSCRIPT=https://pyscript.net/releases/2024.10.1; \
	for f in pyodide.mjs pyodide.asm.js pyodide.asm.wasm pyodide-lock.json \
	         python_stdlib.zip micropip-0.5.0-py3-none-any.whl \
	         packaging-23.1-py3-none-any.whl; do \
		curl -fsSL -o "$(PYODIDE_DIR)/$$f" "$$PYODIDE/$$f"; \
	done; \
	for f in typing_extensions-4.7.1-py3-none-any.whl \
	         pydantic-1.10.7-py3-none-any.whl \
	         Pillow-10.0.0-cp311-cp311-emscripten_3_1_45_wasm32.whl; do \
		curl -fsSL -o "$(WHEELS_DIR)/$$f" "$$PYODIDE/$$f"; \
	done; \
	for f in core.css core.js core.js.map core-DHft4mQJ.js \
	         core-DHft4mQJ.js.map \
	         toml-CvAfdf9_.js toml-DiUM0_qs.js \
	         zip-Bf48tRr5.js \
	         deprecations-manager-BDRw2fed.js \
	         donkey-c355Wa24.js \
	         error-CdZsd8BO.js \
	         py-editor-BRZBRs2T.js \
	         py-terminal-D_z3jMz-.js; do \
		curl -fsSL -o "$(PYSCRIPT_DIR)/$$f" "$$PYSCRIPT/$$f"; \
	done

$(PYODIDE_DIR):
	mkdir -p $(PYODIDE_DIR)

$(WHEELS_DIR):
	mkdir -p $(WHEELS_DIR)

$(PYSCRIPT_DIR):
	mkdir -p $(PYSCRIPT_DIR)

favicon:
	test -f demos/favicon.ico || : > demos/favicon.ico

serve: copy-pyscript-assets
	$(PYTHON) -m http.server $(PORT) --directory demos

run: setup serve

clean:
	rm -rf $(BUILD_DIR)

docker-build: runtime-cache
	$(DOCKER) build -t $(IMAGE):latest -f Dockerfile .

docker-test:
	$(PYTHON) -m pytest test/end-to-end -q

docker-serve:
	$(DOCKER) run --rm -p 8080:8080 $(IMAGE):latest

docker-server: docker-serve

docker: docker-build docker-test