.PHONY: help clean build

PLUGIN_ID := plugin.video.crunchyroll
BUILD_DIR := build
DIST_DIR := dist
PLUGIN_BUILD_DIR := $(BUILD_DIR)/$(PLUGIN_ID)

# Files and directories to include in the plugin
INCLUDE_FILES := addon.xml default.py LICENSE.txt changelog.txt
INCLUDE_DIRS := resources

# Files and directories to exclude
EXCLUDE_PATTERNS := .git .gitignore .ruff_cache .pytest_cache .idea __pycache__ \
                    *.pyo *.pyc *.egg-info \
                    tests pytest.ini pyproject.toml uv.lock \
                    api-new docs tools scripts \
                    build dist Makefile

help:
	@echo "Kodi Plugin Builder"
	@echo ""
	@echo "Usage:"
	@echo "  make build      - Build the plugin zip file"
	@echo "  make clean      - Remove build and dist directories"
	@echo "  make help       - Show this help message"

clean:
	@echo "Cleaning build directories..."
	@rm -rf $(BUILD_DIR) $(DIST_DIR)

build: clean
	@echo "Building $(PLUGIN_ID) plugin..."
	@mkdir -p $(PLUGIN_BUILD_DIR)

	# Copy included files
	@for file in $(INCLUDE_FILES); do \
		if [ -f "$$file" ]; then \
			cp "$$file" $(PLUGIN_BUILD_DIR)/; \
			echo "  ✓ $$file"; \
		fi \
	done

	# Copy included directories
	@for dir in $(INCLUDE_DIRS); do \
		if [ -d "$$dir" ]; then \
			cp -r "$$dir" $(PLUGIN_BUILD_DIR)/; \
			echo "  ✓ $$dir/"; \
		fi \
	done

	# Clean up excluded patterns from copied directories
	@find $(PLUGIN_BUILD_DIR) -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find $(PLUGIN_BUILD_DIR) -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@find $(PLUGIN_BUILD_DIR) -type f -name "*.pyo" -delete 2>/dev/null || true
	@find $(PLUGIN_BUILD_DIR) -type f -name "*.pyc" -delete 2>/dev/null || true
	@find $(PLUGIN_BUILD_DIR) -type f -name "Thumbs.db" -delete 2>/dev/null || true
	@find $(PLUGIN_BUILD_DIR) -type f -name ".env" -delete 2>/dev/null || true

	# Create zip file
	@mkdir -p $(DIST_DIR)
	@cd $(BUILD_DIR) && zip -r ../$(DIST_DIR)/$(PLUGIN_ID).zip $(PLUGIN_ID) -q
	@echo "  ✓ Created $(DIST_DIR)/$(PLUGIN_ID).zip"

	# Show final structure
	@echo ""
	@echo "Plugin structure:"
	@unzip -l $(DIST_DIR)/$(PLUGIN_ID).zip | head -20
	@echo ""
	@echo "Build complete! Plugin is ready at: $(DIST_DIR)/$(PLUGIN_ID).zip"
