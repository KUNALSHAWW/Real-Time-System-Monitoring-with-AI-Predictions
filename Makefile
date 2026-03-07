.PHONY: test lint audit clean

test:
	pytest -q --tb=short

lint:
	flake8 backend/ agent/ ml_engine/ data_pipeline/ tests/ --max-line-length=120 --ignore=E501,W503 || true

audit:
	pip-audit || true
	cd react-frontend && npm audit --audit-level=high || true

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -f test.db 2>/dev/null || true
