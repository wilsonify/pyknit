PYTHON ?= python3
PORT ?= 8000
WHEEL_DIR := _wheel

.PHONY: help setup wheel favicon serve run clean

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
	@echo ""
	@echo "Variables:"
	@echo "  PORT=9000          Change server port"
	@echo "  PYTHON=python3.12  Override Python executable"

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