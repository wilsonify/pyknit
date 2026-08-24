PYTHON ?= python3
PORT ?= 8000
BUILD_DIR := build
WHEEL_DIR := $(BUILD_DIR)/wheel
PYODIDE_DIR := $(BUILD_DIR)/pyodide
WHEELS_DIR := $(BUILD_DIR)/wheels
DOCKER ?= docker
IMAGE ?= pyknit-demos

.PHONY: help setup wheel favicon serve run clean docker-build docker-test docker-serve docker-server runtime-cache docker

help:
	@echo "PyKnit browser demo helpers"
	@echo ""
	@echo "Targets:"
	@echo "  make setup         Build local wheel and ensure favicon exists"
	@echo "  make wheel         Build local wheel into build/wheel"
	@echo "  make runtime-cache Download Pyodide runtime files into build/"
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

setup: wheel favicon

wheel:
	mkdir -p $(BUILD_DIR) $(WHEEL_DIR)
	$(PYTHON) -m pip wheel . -w $(WHEEL_DIR) --no-deps

runtime-cache: $(PYODIDE_DIR) $(WHEELS_DIR)
	@PYODIDE=https://cdn.jsdelivr.net/pyodide/v0.24.1/full; \
	for f in pyodide.mjs pyodide.asm.js pyodide.asm.wasm pyodide-lock.json \
	         python_stdlib.zip micropip-0.5.0-py3-none-any.whl \
	         packaging-23.1-py3-none-any.whl; do \
		curl -fsSL -o "$(PYODIDE_DIR)/$$f" "$$PYODIDE/$$f"; \
	done; \
	for f in typing_extensions-4.7.1-py3-none-any.whl \
	         pydantic-1.10.7-py3-none-any.whl \
	         Pillow-10.0.0-cp311-cp311-emscripten_3_1_45_wasm32.whl; do \
		curl -fsSL -o "$(WHEELS_DIR)/$$f" "$$PYODIDE/$$f"; \
	done

$(PYODIDE_DIR):
	mkdir -p $(PYODIDE_DIR)

$(WHEELS_DIR):
	mkdir -p $(WHEELS_DIR)

favicon:
	test -f demos/favicon.ico || : > demos/favicon.ico

serve:
	$(PYTHON) -m http.server $(PORT) --directory demos

run: setup serve

clean:
	rm -rf $(BUILD_DIR)

docker-build:
	$(DOCKER) build -t $(IMAGE):latest -f Dockerfile .

docker-test:
	$(PYTHON) -m pytest test/end-to-end -q

docker-serve:
	$(DOCKER) run --rm -p 8080:8080 $(IMAGE):latest

docker-server: docker-serve

docker: docker-build docker-test