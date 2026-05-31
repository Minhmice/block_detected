.PHONY: setup setup-dev dev doctor

FORCE ?=

# First-time dev install (Python 3.11 venv, no PyAudio)
setup:
	./scripts/setup_dev.sh $(if $(FORCE),--force,)

# Reinstall Python + npm deps into existing venv
setup-dev:
	./scripts/setup_dev.sh
	@echo "Dependencies refreshed."

# Start FastAPI :8000 + Next.js :3000
dev:
	npm run dev:all

# Print venv python version and key env checks
doctor:
	@test -d .venv || (echo "No .venv — run: make setup" && exit 1)
	@echo "Python: $$(.venv/bin/python --version)"
	@echo "Venv:   $$(.venv/bin/python -c 'import sys; print(sys.executable)')"
	@test -f .env && echo ".env:   present" || echo ".env:   MISSING (run make setup)"
	@test -f frontend/.env.local && echo "frontend/.env.local: present" || echo "frontend/.env.local: MISSING"
	@.venv/bin/python -c "import fastapi, cv2, numpy; print('fastapi/cv2/numpy: OK')" 2>/dev/null || echo "Python deps: run make setup-dev"
	@command -v node >/dev/null && echo "node:   $$(node --version)" || echo "node:   not found"
