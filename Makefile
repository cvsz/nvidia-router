# Makefile — NVIDIA Free-Model Router
#
# Usage:
#   make setup          # create venv + install dependencies
#   make test           # run the test suite
#   make run            # run nvidia.py (chat example)
#   make serve          # run the OpenAI-compatible proxy
#   make lint           # ruff check + format check
#   make format         # ruff format
#   make clean          # remove venv and caches
#   make all            # setup + lint + test
#   make build          # default build (setup + lint + test + exe)
#   make build:gui      # build GUI executable (PyInstaller)
#   make build:tui      # build TUI package
#   make build:web      # build web deployment package
#   make build:desktops # build desktop application packages (.desktop + launcher)
#   make build:dev      # development build with dev tools
#   make build:prod     # production-optimized build (PyInstaller onefile)
#   make build:ent      # enterprise build with all features
#   make build:exe      # build native CLI executable using PyInstaller
#   make build:exe:win  # build Windows .exe (requires Wine)
#   make build:android  # build Android package (requires Buildozer)
#   make build:ios      # build iOS package (requires BeeWare/Kivy, macOS)
#   make build:zcloud   # build zcloud CLI entry point
#   make gui            # launch zcloud GUI
#   make install:zcloud # install zcloud to $(PREFIX)/bin
#   make uninstall:zcloud # remove zcloud from $(PREFIX)/bin

.PHONY: all setup test run serve lint format clean help venv install-deps build build\:all build\:web build\:desktops build\:dev build\:prod build\:ent build\:exe build\:exe\:win build\:gui build\:tui build\:android build\:ios build\:zcloud install\:zcloud uninstall\:zcloud zcloud gui docker\:build docker\:run

PYTHON ?= python3
VENV := .venv
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip
REQUIREMENTS := requests pytest ruff
PREFIX ?= /usr/local
DIST := dist
BUILD := build

# --------------------------------------------------------------------------- #
# Targets
# --------------------------------------------------------------------------- #

all: setup lint test

help: ## Show this help
	@echo "NVIDIA Free-Model Router — Make targets:"
	@echo
	@echo "Core targets:"
	@echo "  make setup        create virtualenv and install dependencies"
	@echo "  make install      install/upgrade dependencies (requires existing venv)"
	@echo "  make test         run the pytest suite"
	@echo "  make lint         ruff check + ruff format --check"
	@echo "  make format       ruff format (in place)"
	@echo "  make clean        remove .venv, build/, dist/ and Python caches"
	@echo "  make all          setup + lint + test"
	@echo
	@echo "Run targets:"
	@echo "  make run          run nvidia.py chat (requires NVIDIA_API_KEYS)"
	@echo "  make serve        run the OpenAI-compatible proxy (requires keys)"
	@echo "  make gui          launch zcloud GUI"
	@echo
	@echo "Model/Provider targets:"
	@echo "  make models       list catalog models with free/paid/provider metadata"
	@echo "  make models-free  list only free models"
	@echo "  make models-paid  list only paid models"
	@echo "  make providers    list configured providers with API key counts and base URLs"
	@echo "  make discover     auto-discover models from NVIDIA API and update models.json"
	@echo
	@echo "Build targets:"
	@echo "  make build        default build (setup + lint + test + exe)"
	@echo "  make build:all    build all variants (exe + gui + web + desktops + dev + prod + ent)"
	@echo "  make build:exe    build native CLI executable using PyInstaller"
	@echo "  make build:exe:win build Windows .exe (requires Wine)"
	@echo "  make build:gui    build GUI executable using PyInstaller"
	@echo "  make build:tui    build TUI package"
	@echo "  make build:web    build web deployment package"
	@echo "  make build:desktops build desktop application packages (.desktop files)"
	@echo "  make build:dev    development build with dev tools"
	@echo "  make build:prod   production-optimized build (PyInstaller onefile)"
	@echo "  make build:ent    enterprise build with all features"
	@echo "  make build:android build Android package (requires Buildozer)"
	@echo "  make build:ios    build iOS package (requires BeeWare/Kivy, macOS)"
	@echo
	@echo "zcloud targets:"
	@echo "  make build:zcloud  build zcloud CLI entry point"
	@echo "  make install:zcloud install zcloud to $(PREFIX)/bin"
	@echo "  make uninstall:zcloud remove zcloud from $(PREFIX)/bin"
	@echo "  make zcloud        alias for build:zcloud"
	@echo
	@echo "Docker targets:"
	@echo "  make docker:build   build Docker image"
	@echo "  make docker:run     run Docker container"
	@echo "  make docker:up      alias for docker:run"

setup: venv install-deps ## Create venv and install dependencies

venv: ## Create the virtual environment if missing
	@if [ ! -d "$(VENV)" ]; then \
		echo "==> Creating virtual environment at $(VENV)"; \
		$(PYTHON) -m venv $(VENV); \
	else \
		echo "==> Virtual environment already exists at $(VENV)"; \
	fi

install-deps: ## Install / upgrade pip and project dependencies
	@echo "==> Upgrading pip"
	$(VENV_PIP) install --upgrade pip
	@echo "==> Installing dependencies: $(REQUIREMENTS)"
	$(VENV_PIP) install $(REQUIREMENTS)

test: ## Run the test suite
	@echo "==> Running tests"
	$(VENV_PYTHON) -m pytest test_nvidia.py -v

models: ## List catalog models with free/paid/provider metadata
	@echo "==> Listing catalog models"
	$(VENV_PYTHON) nvidia.py models

models-free: ## List only free models
	@echo "==> Listing free models"
	$(VENV_PYTHON) nvidia.py models --free

models-paid: ## List only paid models
	@echo "==> Listing paid models"
	$(VENV_PYTHON) nvidia.py models --paid

discover: ## Auto-discover models from NVIDIA API and update models.json (requires NVIDIA_API_KEYS)
	@echo "==> Discovering models from NVIDIA API"
	$(VENV_PYTHON) nvidia.py discover

models-update: discover ## Alias for discover (update the models catalog)

providers: ## List configured providers with API key counts and base URLs
	@echo "==> Listing configured providers"
	$(VENV_PYTHON) nvidia.py providers

run: ## Run nvidia.py chat example (set NVIDIA_API_KEYS first)
	@echo "==> Running nvidia.py chat"
	$(VENV_PYTHON) nvidia.py chat "write a regex for emails"

serve: ## Run the OpenAI-compatible proxy on :8000 (set keys + token first)
	@echo "==> Starting proxy on http://127.0.0.1:8000/v1"
	$(VENV_PYTHON) nvidia.py serve --port 8000

lint: ## Run ruff check and ruff format --check
	@echo "==> Linting with ruff"
	$(VENV_PYTHON) -m ruff check nvidia.py test_nvidia.py zcloud-gui.py zcloud-tui.py
	$(VENV_PYTHON) -m ruff format --check nvidia.py test_nvidia.py zcloud-gui.py zcloud-tui.py

format: ## Format code with ruff
	@echo "==> Formatting with ruff"
	$(VENV_PYTHON) -m ruff format nvidia.py test_nvidia.py zcloud-gui.py

clean: ## Remove virtualenv, build artifacts, dist, and Python caches
	@echo "==> Cleaning"
	rm -rf $(VENV) $(DIST) $(BUILD) __pycache__ .pytest_cache .ruff_cache
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
	find . -name "*.pyc" -delete
	find . -name "test_*_tmp.json" -delete
	find . -name "test_*_dirty.json" -delete
	find . -name "test_*_corrupt.json" -delete
	rm -rf test_proxy_stats

# --------------------------------------------------------------------------- #
# Build targets — REAL BUILDS (not just copies)
# --------------------------------------------------------------------------- #

build: setup lint test ## Default build: setup + lint + test + native executable
	@echo "==> Building default variant"
	$(MAKE) build\:exe
	@echo "==> Build complete"

build\:all: build ## Build all variants
	@echo "==> Building all variants"
	$(MAKE) build\:exe
	$(MAKE) build\:gui
	$(MAKE) build\:web
	$(MAKE) build\:desktops
	$(MAKE) build\:dev
	$(MAKE) build\:prod
	$(MAKE) build\:ent
	@echo "==> All variants built"

build\:exe: setup lint test ## Build native CLI executable using PyInstaller
	@echo "==> Building native CLI executable"
	@mkdir -p $(DIST)/exe
	$(VENV_PYTHON) -m PyInstaller \
		--noconfirm \
		--clean \
		--onefile \
		--icon nvidia.ico \
		--name nvidia-router \
		--distpath $(DIST)/exe \
		--workpath $(BUILD)/pyinstaller \
		--specpath $(BUILD)/pyinstaller \
		nvidia.py
	cp nvidia.ico nvidia.png make_icon.py models.json provider.json $(DIST)/exe/
	@echo "==> Native executable ready: $(DIST)/exe/nvidia-router"
	@echo "==> Data files: $(DIST)/exe/models.json, $(DIST)/exe/provider.json, $(DIST)/exe/nvidia.ico, $(DIST)/exe/nvidia.png"

build\:exe\:win: setup lint test ## Build Windows .exe (requires Wine for cross-compilation)
	@echo "==> Building Windows .exe"
	@mkdir -p $(DIST)/exe/win
	@if command -v wine >/dev/null 2>&1; then \
		$(VENV_PYTHON) -m PyInstaller \
			--noconfirm \
			--clean \
			--onefile \
			--icon nvidia.ico \
			--name nvidia-router \
			--distpath $(DIST)/exe/win \
			--workpath $(BUILD)/pyinstaller-win \
			--specpath $(BUILD)/pyinstaller-win \
			nvidia.py; \
		cp nvidia.ico nvidia.png make_icon.py models.json provider.json $(DIST)/exe/win/; \
		echo "==> Windows .exe ready: $(DIST)/exe/win/nvidia-router.exe"; \
	else \
		echo "==> Wine not found. Install wine to cross-compile Windows .exe."; \
		echo "==>   sudo apt install wine"; \
		echo "==>   Then run: make build:exe:win"; \
	fi

build\:gui: setup lint test ## Build GUI executable using PyInstaller
	@echo "==> Building GUI executable"
	@mkdir -p $(DIST)/gui
	$(VENV_PYTHON) -m PyInstaller \
		--noconfirm \
		--clean \
		--onefile \
		--windowed \
		--icon nvidia.ico \
		--name zcloud-gui \
		--distpath $(DIST)/gui \
		--workpath $(BUILD)/pyinstaller-gui \
		--specpath $(BUILD)/pyinstaller-gui \
		--add-data "$(CURDIR)/models.json:." \
		--add-data "$(CURDIR)/provider.json:." \
		--add-data "$(CURDIR)/nvidia.ico:." \
		--add-data "$(CURDIR)/nvidia.png:." \
		zcloud-gui.py
	cp nvidia.ico nvidia.png make_icon.py models.json provider.json $(DIST)/gui/
	@echo "==> GUI executable ready: $(DIST)/gui/zcloud-gui"

build\:tui: setup lint test ## Build TUI package with textual
	@echo "==> Building TUI package"
	@mkdir -p $(DIST)/tui
	$(VENV_PIP) install textual rich
	$(VENV_PYTHON) -m py_compile nvidia.py test_nvidia.py
	cp nvidia.ico nvidia.png make_icon.py nvidia.py models.json provider.json zcloud $(DIST)/tui/
	chmod +x $(DIST)/tui/zcloud
	@echo "==> TUI package ready in $(DIST)/tui/"
	@echo "==> Run: $(DIST)/tui/zcloud providers"

build\:web: setup lint test ## Build web deployment package
	@echo "==> Building web deployment package"
	@mkdir -p $(DIST)/web
	$(VENV_PYTHON) -m py_compile nvidia.py test_nvidia.py zcloud-gui.py
	cp nvidia.ico nvidia.png make_icon.py nvidia.py zcloud-gui.py models.json provider.json $(DIST)/web/
	printf 'requests==2.34.2\npytest==9.2.0\nruff==0.17.5\n' > $(DIST)/web/requirements.txt
	@echo "==> Web package ready in $(DIST)/web/"
	@echo "==> Run: cd $(DIST)/web && python nvidia.py serve --port 8000"

build\:desktops: setup lint test ## Build desktop application packages (.desktop files)
	@echo "==> Building desktop application packages"
	@mkdir -p $(DIST)/desktops
	$(VENV_PYTHON) -m py_compile nvidia.py test_nvidia.py zcloud-gui.py
	cp nvidia.ico nvidia.png make_icon.py nvidia.py zcloud-gui.py models.json provider.json zcloud $(DIST)/desktops/
	chmod +x $(DIST)/desktops/zcloud
	@printf '[Desktop Entry]\nName=zcloud\nComment=NVIDIA Free-Model Router\nExec=zcloud %%f\nIcon=zcloud\nTerminal=false\nType=Application\nCategories=Network;Chat;\n' > $(DIST)/desktops/zcloud.desktop
	@echo "==> Desktop package ready in $(DIST)/desktops/"
	@echo "==> Desktop entry: $(DIST)/desktops/zcloud.desktop"

build\:dev: setup lint test ## Development build with dev tools
	@echo "==> Building development variant"
	$(VENV_PIP) install --upgrade pytest ruff
	$(VENV_PYTHON) -m py_compile nvidia.py test_nvidia.py zcloud-gui.py
	@mkdir -p $(DIST)/dev
	cp nvidia.ico nvidia.png make_icon.py nvidia.py zcloud-gui.py test_nvidia.py models.json provider.json zcloud $(DIST)/dev/
	chmod +x $(DIST)/dev/zcloud
	@echo "==> Dev build ready in $(DIST)/dev/"
	@echo "==> Run: $(DIST)/dev/zcloud providers"

build\:prod: setup lint test ## Production-optimized build (PyInstaller onefile)
	@echo "==> Building production variant"
	@mkdir -p $(DIST)/prod
	$(VENV_PYTHON) -m PyInstaller \
		--noconfirm \
		--clean \
		--onefile \
		--icon nvidia.ico \
		--name nvidia-router \
		--distpath $(DIST)/prod \
		--workpath $(BUILD)/pyinstaller-prod \
		--specpath $(BUILD)/pyinstaller-prod \
		nvidia.py
	cp nvidia.ico nvidia.png make_icon.py models.json provider.json $(DIST)/prod/
	@echo "==> Production executable ready: $(DIST)/prod/nvidia-router"

build\:ent: setup lint test ## Enterprise build with all features
	@echo "==> Building enterprise variant"
	@mkdir -p $(DIST)/ent
	$(VENV_PYTHON) -m PyInstaller \
		--noconfirm \
		--clean \
		--onefile \
		--windowed \
		--icon nvidia.ico \
		--name zcloud-enterprise \
		--distpath $(DIST)/ent \
		--workpath $(BUILD)/pyinstaller-ent \
		--specpath $(BUILD)/pyinstaller-ent \
		--add-data "$(CURDIR)/models.json:." \
		--add-data "$(CURDIR)/provider.json:." \
		--add-data "$(CURDIR)/nvidia.ico:." \
		--add-data "$(CURDIR)/nvidia.png:." \
		zcloud-gui.py
	cp nvidia.ico nvidia.png make_icon.py nvidia.py zcloud-gui.py models.json provider.json zcloud $(DIST)/ent/
	chmod +x $(DIST)/ent/zcloud
	@echo "==> Enterprise package ready in $(DIST)/ent/"
	@echo "==> GUI: $(DIST)/ent/zcloud-enterprise"
	@echo "==> CLI: $(DIST)/ent/zcloud"

build\:android: setup lint test ## Build Android package (requires Buildozer)
	@echo "==> Building Android package"
	@mkdir -p $(DIST)/android
	$(VENV_PYTHON) -m py_compile nvidia.py test_nvidia.py zcloud-gui.py
	cp nvidia.ico nvidia.png make_icon.py nvidia.py zcloud-gui.py models.json provider.json zcloud $(DIST)/android/
	chmod +x $(DIST)/android/zcloud
	@printf '[app]\ntitle = zcloud\npackage.name = zcloud\npackage.domain = com.nvidia.router\nsource.dir = .\nsource.include_exts = py,png,jpg,kv,atlas\nversion = 1.0\nrequirements = python3,kivy,requests\nosx.python_version = 3\nosx.kivy_version = 2.1.0\nandroid.archs = arm64-v8a\nandroid.api = 31\nandroid.minapi = 24\n' > $(DIST)/android/buildozer.spec
	@echo "==> Android package ready in $(DIST)/android/"
	@echo "==> To build APK: cd $(DIST)/android && buildozer android debug"

build\:ios: setup lint test ## Build iOS package (requires BeeWare/Kivy, macOS only)
	@echo "==> Building iOS package"
	@mkdir -p $(DIST)/ios
	$(VENV_PYTHON) -m py_compile nvidia.py test_nvidia.py zcloud-gui.py
	cp nvidia.ico nvidia.png make_icon.py nvidia.py zcloud-gui.py models.json provider.json zcloud $(DIST)/ios/
	chmod +x $(DIST)/ios/zcloud
	@printf '// swift-tools-version:5.5\nimport PackageDescription\n\nlet package = Package(\n    name: "zcloud",\n    platforms: [.iOS(.v15)],\n    products: [\n        .executable(name: "zcloud", targets: ["zcloud"])\n    ],\n    targets: [\n        .executableTarget(\n            name: "zcloud",\n            dependencies: [],\n            path: "."\n        )\n    ]\n)\n' > $(DIST)/ios/Package.swift
	@echo "==> iOS package ready in $(DIST)/ios/"
	@echo "==> To build: cd $(DIST)/ios && swift build (macOS required)"

# --------------------------------------------------------------------------- #
# zcloud executable entry point
# --------------------------------------------------------------------------- #

build\:zcloud: setup lint test ## Build zcloud CLI entry point
	@echo "==> Building zcloud executable"
	@chmod +x zcloud
	@mkdir -p $(DIST)/bin
	cp zcloud $(DIST)/bin/zcloud
	cp nvidia.py $(DIST)/bin/nvidia.py
	cp models.json $(DIST)/bin/models.json
	cp provider.json $(DIST)/bin/provider.json
	cp nvidia.ico $(DIST)/bin/nvidia.ico
	cp nvidia.png $(DIST)/bin/nvidia.png
	cp make_icon.py $(DIST)/bin/make_icon.py
	@echo "==> zcloud ready: $(DIST)/bin/zcloud"

install\:zcloud: build\:zcloud ## Install zcloud to /usr/local/bin (or PREFIX)
	@echo "==> Installing zcloud to $(PREFIX)/bin"
	@mkdir -p "$(PREFIX)/bin"
	cp zcloud "$(PREFIX)/bin/zcloud"
	chmod +x "$(PREFIX)/bin/zcloud"
	@echo "==> Installed. Run: zcloud providers"

uninstall\:zcloud: ## Remove zcloud from $(PREFIX)/bin
	@echo "==> Removing zcloud from $(PREFIX)/bin"
	rm -f "$(PREFIX)/bin/zcloud"
	@echo "==> Removed"

zcloud: build\:zcloud ## Alias for build:zcloud
	@echo "==> zcloud executable at ./zcloud"

gui: ## Launch zcloud GUI
	@echo "==> Launching zcloud GUI"
	$(VENV_PYTHON) zcloud-gui.py

# --------------------------------------------------------------------------- #
# Docker targets
# --------------------------------------------------------------------------- #

docker\:build: ## Build Docker image
	@echo "==> Building Docker image"
	docker build -t nvidia-router:latest .
	docker tag nvidia-router:latest nvidia-router:$$(date +%Y%m%d)
	@echo "==> Docker image ready: nvidia-router:latest"

docker\:run: docker\:build ## Run Docker container (requires NVIDIA_API_KEYS)
	@echo "==> Running Docker container"
	@if [ -z "$(NVIDIA_API_KEYS)" ]; then \
		echo "Warning: NVIDIA_API_KEYS not set. Set it before running:"; \
		echo "  export NVIDIA_API_KEYS=\"nvapi-aaa,nvapi-bbb\""; \
	fi
	docker run --rm -d \
		--name nvidia-router \
		-p 8000:8000 \
		-e NVIDIA_API_KEYS="$$NVIDIA_API_KEYS" \
		-e NVIDIA_BASE_URL="$$NVIDIA_BASE_URL" \
		-e NVIDIA_RPM="$$NVIDIA_RPM" \
		-e NVIDIA_CACHE_TTL="$$NVIDIA_CACHE_TTL" \
		-e NVIDIA_TIMEOUT="$$NVIDIA_TIMEOUT" \
		-e NVIDIA_MAX_WAIT="$$NVIDIA_MAX_WAIT" \
		nvidia-router:latest \
		serve --host 0.0.0.0 --port 8000
	@echo "==> Container running at http://localhost:8000/v1"
	@echo "==> Test: curl http://localhost:8000/health"

docker\:up: docker\:run ## Alias for docker:run

