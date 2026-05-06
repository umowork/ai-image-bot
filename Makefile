# Makefile — общий шаблон для проектов портфолио
# Копируется в каждый проект из _shared/Makefile.template

PROJECT_NAME := $(notdir $(CURDIR))
PYTHON := python3
DOCKER_COMPOSE := docker-compose

.PHONY: all lint test build run clean install help

all: lint test

lint:
	ruff check . --ignore E501

test:
	python3 -m pytest tests/ -v --tb=short

build:
	docker-compose -f docker-compose.yml build

run:
	docker-compose -f docker-compose.yml up -d

down:
	docker-compose -f docker-compose.yml down

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .ruff_cache

install:
	pip install -r requirements.txt
	@if [ -f requirements-test.txt ]; then pip install -r requirements-test.txt; fi

help:
	@echo "Usage:"
	@echo "  make lint     — Run ruff"
	@echo "  make test     — Run pytest"
	@echo "  make build    — docker-compose build"
	@echo "  make run      — docker-compose up -d"
	@echo "  make down     — docker-compose down"
	@echo "  make clean    — Clean caches"
	@echo "  make install  — pip install -r requirements.txt"
