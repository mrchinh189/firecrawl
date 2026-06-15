.PHONY: help install test fixtures run web-dev web-build docker clean
help:                ## Danh sách lệnh
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-12s\033[0m %s\n",$$1,$$2}'
install:             ## Cài dependencies Python
	pip3 install -r requirements.txt
fixtures:            ## Sinh dữ liệu mẫu offline
	python3 fixtures/make_fixtures.py
test:                ## Chạy toàn bộ test
	python3 -m pytest -q
run: fixtures        ## Chạy pipeline -> HTML + DOCX + Telegram (dry-run nếu thiếu khóa)
	python3 run_pipeline.py
web-dev:             ## Dev server dashboard (http://localhost:3000)
	cd web && npm install && npm run dev
web-build:           ## Build production web
	cd web && npm install && npm run build
docker:              ## Self-host bằng docker-compose
	docker compose up -d --build
clean:               ## Xóa artifacts
	rm -rf data/*.html data/*.docx data/*.png .pytest_cache web/.next
