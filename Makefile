.PHONY: build install uninstall clean

BINARY = dist/bench
INSTALL_PATH = /usr/local/bin/bench

build:
	poetry run pyinstaller --onefile cli/main.py --name bench \
		--add-data "models:models" \
		--collect-all sklearn \
		--collect-all joblib

install: build
	cp $(BINARY) $(INSTALL_PATH)
	@echo "Установлено: $(INSTALL_PATH)"

uninstall:
	rm -f $(INSTALL_PATH)
	@echo "Удалено: $(INSTALL_PATH)"

clean:
	rm -rf dist/ build/ bench.spec
