# Makefile для чат-бота анализа постов
# Использование: make <команда>

PYTHON_VERSION = 3.12.3
VENV_DIR = venv
PROJECT_DIR = $(shell pwd)
SERVER_DIR = $(PROJECT_DIR)/server
APP_DIR = $(PROJECT_DIR)/app

# Определяем Python
PYTHON = $(VENV_DIR)/bin/python
PIP = $(VENV_DIR)/bin/pip

# Цвета для вывода
GREEN = \033[0;32m
YELLOW = \033[0;33m
RED = \033[0;31m
NC = \033[0m # No Color

# Определяем пакетный менеджер
PKG_MANAGER := $(shell if command -v apt-get >/dev/null 2>&1; then echo "apt"; elif command -v dnf >/dev/null 2>&1; then echo "dnf"; elif command -v yum >/dev/null 2>&1; then echo "yum"; elif command -v pacman >/dev/null 2>&1; then echo "pacman"; elif command -v brew >/dev/null 2>&1; then echo "brew"; else echo "unknown"; fi)

.PHONY: help install install-system install-python venv deps server frontend run clean logs check

# Помощь по командам
help:
	@echo "$(GREEN)Доступные команды:$(NC)"
	@echo "  $(YELLOW)make install$(NC)        - Полная установка (система + Python + venv + зависимости)"
	@echo "  $(YELLOW)make install-system$(NC) - Установка системных зависимостей (требует sudo)"
	@echo "  $(YELLOW)make install-python$(NC) - Установка Python $(PYTHON_VERSION) через pyenv"
	@echo "  $(YELLOW)make venv$(NC)           - Создание виртуального окружения"
	@echo "  $(YELLOW)make deps$(NC)           - Установка зависимостей Python"
	@echo "  $(YELLOW)make server$(NC)         - Запуск FastAPI сервера (порт 8000)"
	@echo "  $(YELLOW)make frontend$(NC)       - Запуск Streamlit фронтенда (порт 8501)"
	@echo "  $(YELLOW)make run$(NC)            - Запуск сервера и фронтенда одновременно"
	@echo "  $(YELLOW)make check$(NC)          - Проверка установки"
	@echo "  $(YELLOW)make clean$(NC)          - Удаление виртуального окружения"
	@echo "  $(YELLOW)make stop$(NC)           - Остановка всех процессов"

# Полная установка
install: install-system install-python venv deps
	@echo "$(GREEN)✅ Установка завершена!$(NC)"
	@echo "Запустите: $(YELLOW)make run$(NC)"

# Установка системных зависимостей для сборки Python
install-system:
	@echo "$(YELLOW)📦 Установка системных зависимостей...$(NC)"
	@echo "Обнаружен пакетный менеджер: $(PKG_MANAGER)"
ifeq ($(PKG_MANAGER),apt)
	@sudo apt-get update
	@sudo apt-get install -y \
		build-essential \
		curl \
		git \
		libssl-dev \
		zlib1g-dev \
		libbz2-dev \
		libreadline-dev \
		libsqlite3-dev \
		libncursesw5-dev \
		xz-utils \
		tk-dev \
		libxml2-dev \
		libxmlsec1-dev \
		libffi-dev \
		liblzma-dev \
		wget \
		ca-certificates
else ifeq ($(PKG_MANAGER),dnf)
	@sudo dnf groupinstall -y "Development Tools"
	@sudo dnf install -y \
		curl \
		git \
		openssl-devel \
		zlib-devel \
		bzip2-devel \
		readline-devel \
		sqlite-devel \
		ncurses-devel \
		xz-devel \
		tk-devel \
		libxml2-devel \
		xmlsec1-devel \
		libffi-devel \
		wget \
		ca-certificates
else ifeq ($(PKG_MANAGER),yum)
	@sudo yum groupinstall -y "Development Tools"
	@sudo yum install -y \
		curl \
		git \
		openssl-devel \
		zlib-devel \
		bzip2-devel \
		readline-devel \
		sqlite-devel \
		ncurses-devel \
		xz-devel \
		tk-devel \
		libxml2-devel \
		xmlsec1-devel \
		libffi-devel \
		wget \
		ca-certificates
else ifeq ($(PKG_MANAGER),pacman)
	@sudo pacman -Syu --noconfirm
	@sudo pacman -S --noconfirm \
		base-devel \
		curl \
		git \
		openssl \
		zlib \
		bzip2 \
		readline \
		sqlite \
		ncurses \
		xz \
		tk \
		libxml2 \
		libffi \
		wget \
		ca-certificates
else ifeq ($(PKG_MANAGER),brew)
	@brew update
	@brew install \
		openssl \
		readline \
		sqlite3 \
		xz \
		zlib \
		tcl-tk \
		curl \
		git \
		wget
else
	@echo "$(RED)❌ Неизвестный пакетный менеджер. Установите вручную:$(NC)"
	@echo "  - build-essential / Development Tools"
	@echo "  - curl, git, wget"
	@echo "  - openssl, zlib, bzip2, readline, sqlite, ncurses"
	@echo "  - xz, tk, libxml2, libffi"
	@exit 1
endif
	@echo "$(GREEN)✅ Системные зависимости установлены$(NC)"

# Установка Python через pyenv
install-python:
	@echo "$(YELLOW)📦 Проверка/установка Python $(PYTHON_VERSION)...$(NC)"
	@command -v curl >/dev/null 2>&1 || { echo "$(RED)❌ curl не найден. Запустите: make install-system$(NC)"; exit 1; }
	@command -v git >/dev/null 2>&1 || { echo "$(RED)❌ git не найден. Запустите: make install-system$(NC)"; exit 1; }
	@if ! command -v pyenv >/dev/null 2>&1; then \
		echo "$(YELLOW)Установка pyenv...$(NC)"; \
		curl -fsSL https://pyenv.run | bash; \
		echo ''; \
		echo 'export PYENV_ROOT="$$HOME/.pyenv"' >> ~/.bashrc; \
		echo '[[ -d $$PYENV_ROOT/bin ]] && export PATH="$$PYENV_ROOT/bin:$$PATH"' >> ~/.bashrc; \
		echo 'eval "$$(pyenv init -)"' >> ~/.bashrc; \
		echo "$(GREEN)✅ pyenv установлен$(NC)"; \
		echo "$(YELLOW)⚠️  Перезапустите терминал или выполните: source ~/.bashrc$(NC)"; \
		echo "$(YELLOW)   Затем снова запустите: make install-python$(NC)"; \
		exit 0; \
	fi
	@export PYENV_ROOT="$$HOME/.pyenv" && \
	export PATH="$$PYENV_ROOT/bin:$$PATH" && \
	eval "$$(pyenv init -)" && \
	if ! pyenv versions 2>/dev/null | grep -q $(PYTHON_VERSION); then \
		echo "$(YELLOW)Установка Python $(PYTHON_VERSION) (это может занять несколько минут)...$(NC)"; \
		pyenv install $(PYTHON_VERSION); \
	else \
		echo "$(GREEN)Python $(PYTHON_VERSION) уже установлен$(NC)"; \
	fi && \
	pyenv local $(PYTHON_VERSION)
	@echo "$(GREEN)✅ Python $(PYTHON_VERSION) готов$(NC)"

# Создание виртуального окружения
venv:
	@echo "$(YELLOW)🔧 Создание виртуального окружения...$(NC)"
	@if [ ! -d "$(VENV_DIR)" ]; then \
		python3 -m venv $(VENV_DIR); \
		echo "$(GREEN)✅ Виртуальное окружение создано$(NC)"; \
	else \
		echo "$(GREEN)Виртуальное окружение уже существует$(NC)"; \
	fi

# Установка зависимостей
deps: venv
	@echo "$(YELLOW)📚 Установка зависимостей...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) install \
		fastapi \
		uvicorn \
		openai \
		langchain \
		langchain-core \
		requests \
		streamlit \
		pydantic \
		pandas \
		dotenv
	@echo "$(GREEN)✅ Зависимости установлены$(NC)"

# Запуск FastAPI сервера
server: check-venv
	@echo "$(GREEN)🚀 Запуск FastAPI сервера на порту 8000...$(NC)"
	@cd $(SERVER_DIR) && $(PROJECT_DIR)/$(VENV_DIR)/bin/uvicorn backend:app --reload --port 8000

# Запуск Streamlit фронтенда
frontend: check-venv
	@echo "$(GREEN)🌐 Запуск Streamlit на порту 8501...$(NC)"
	@$(VENV_DIR)/bin/streamlit run $(APP_DIR)/chat.py --server.port 8501

# Запуск сервера и фронтенда одновременно (в фоне)
run: check-venv stop
	@echo "$(GREEN)🚀 Запуск приложения...$(NC)"
	@cd $(SERVER_DIR) && $(PROJECT_DIR)/$(VENV_DIR)/bin/uvicorn backend:app --host 0.0.0.0 --port 8000 &
	@sleep 2
	@$(VENV_DIR)/bin/streamlit run $(APP_DIR)/chat.py --server.port 8501 --server.address 0.0.0.0 &
	@sleep 2
	@echo "$(GREEN)🔄 Запуск autoupdate с периодичностью 2 часа...$(NC)"
	@while true; do \
		echo "$$(date): Запуск autoupdate.py..."; \
		cd $(SERVER_DIR) && $(PROJECT_DIR)/$(PYTHON) autoupdate.py; \
		echo "$$(date): Следующий запуск через 2 часа"; \
		sleep 7200; \
	done &
	@echo "$(GREEN)✅ Приложение запущено!$(NC)"
	@echo "  📡 Сервер: http://localhost:8000"
	@echo "  🌐 Фронтенд: http://localhost:8501"
	@echo "  🔄 Autoupdate: каждые 2 часа"
	@echo ""
	@echo "Для остановки: $(YELLOW)make stop$(NC)"

# Проверка виртуального окружения
check-venv:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "$(RED)❌ Виртуальное окружение не найдено. Запустите: make install$(NC)"; \
		exit 1; \
	fi

# Проверка установки
check:
	@echo "$(YELLOW)🔍 Проверка установки...$(NC)"
	@echo "Python версия:"
	@$(PYTHON) --version 2>/dev/null || echo "$(RED)Python не найден в venv$(NC)"
	@echo ""
	@echo "Установленные пакеты:"
	@$(PIP) list 2>/dev/null | grep -E "(fastapi|uvicorn|openai|streamlit|langchain|pandas)" || echo "$(RED)Пакеты не установлены$(NC)"

# Остановка всех процессов
stop:
	@echo "$(YELLOW)⏹️ Остановка процессов...$(NC)"
	@-kill $$(lsof -ti:8000) 2>/dev/null || true
	@-kill $$(lsof -ti:8501) 2>/dev/null || true
	@-pkill -f "autoupdate.py" 2>/dev/null || true
	@-pkill -f "sleep 7200" 2>/dev/null || true
	@echo "$(GREEN)✅ Процессы остановлены$(NC)"

# Очистка
clean: stop
	@echo "$(YELLOW)🧹 Удаление виртуального окружения...$(NC)"
	@rm -rf $(VENV_DIR)
	@rm -f .python-version
	@echo "$(GREEN)✅ Очистка завершена$(NC)"

# Загрузка данных из CSV
load-data: check-venv
	@echo "$(YELLOW)📊 Загрузка данных из CSV...$(NC)"
	@cd $(SERVER_DIR) && $(PROJECT_DIR)/$(PYTHON) insert_data.py
	@echo "$(GREEN)✅ Данные загружены$(NC)"
