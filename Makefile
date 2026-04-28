.DEFAULT_GOAL := help

PYTHON := uv run python

.PHONY: help install validate lint pages check

help: ## Show available targets
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ { printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

install: ## Install all dependencies with uv
	uv sync

validate: ## Validate SKILL.md frontmatter and structure
	$(PYTHON) scripts/validate_skills.py

lint: ## Lint SKILL.md markdown formatting
	$(PYTHON) -m pymarkdown --config .pymarkdown.json scan README.md CONTRIBUTING.md skills/

pages: ## Generate docs/index.html from all SKILL.md files
	$(PYTHON) scripts/generate_skills_page.py

check: validate lint pages ## Run all validations (validate + lint + pages)
