PYTHON ?= python3
PORT ?= 8000
WHEEL_DIR := _wheel
DOCKER ?= docker
IMAGE ?= pyknit-demos

.PHONY: help setup wheel favicon serve run clean docker-build docker-test docker-serve docker

help:
	@echo "PyKnit browser demo helpers"
	@echo ""
	@echo "Targets:"
	@echo "  make setup         Build local wheel and ensure favicon exists"
	@echo "  make wheel         Build local wheel into demos/_wheel"
	@echo "  make favicon       Create an empty demos/favicon.ico if missing"
	@echo "  make serve         Run http.server from demos/ (default port 8000)"
	@echo "  make run           setup + serve"
	@echo "  make clean         Remove built wheel artifacts"
	@echo "  make docker-build  Build the minimal production image"
	@echo "  make docker-test   Run the end-to-end tests against the image"
	@echo "  make docker-serve  Run the image on port 8080"
	@echo "  make docker        docker-build + docker-test"
	@echo ""
	@echo "Variables:"
	@echo "  PORT=9000          Change server port"
	@echo "  PYTHON=python3.12  Override Python executable"
	@echo "  DOCKER=docker      Container engine"
	@echo "  IMAGE=pyknit-demos  Image name for docker targets"

setup: wheel favicon

wheel:
	mkdir -p $(WHEEL_DIR)
	cd .. && $(PYTHON) -m pip wheel . -w demos/$(WHEEL_DIR) --no-deps

favicon:
	test -f favicon.ico || : > favicon.ico

serve:
	cd .. && $(PYTHON) -m http.server $(PORT) --directory demos

run: setup serve

clean:
	rm -f $(WHEEL_DIR)/pyknit-*.whl

docker-build:
	cd .. && $(DOCKER) build -t $(IMAGE):latest -f demos/Dockerfile .

docker-test:
	cd .. && $(PYTHON) -m pytest test/end-to-end -q

docker-serve:
	$(DOCKER) run --rm -p 8080:8080 $(IMAGE):latest

docker: docker-build docker-test