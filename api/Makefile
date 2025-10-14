.PHONY: migrate migrate-create migrate-up migrate-down migrate-history

migrate:
	python migrate.py

migrate-create:
	@read -p "Migration name: " name; \
	alembic revision -m "$$name"

migrate-up:
	alembic upgrade head

migrate-down:
	alembic downgrade -1

migrate-history:
	alembic history --verbose
