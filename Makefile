.PHONY: build install uninstall clean

BINARY_DIR = dist/bench
INSTALL_PATH = /usr/local/bin/bench

build:
	poetry run pyinstaller --onedir cli/main.py --name bench \
		--add-data "models:models" \
		--collect-all sklearn \
		--collect-all joblib

install: build
	mkdir -p /usr/local/lib/bench
	cp -r $(BINARY_DIR)/. /usr/local/lib/bench/
	ln -sf /usr/local/lib/bench/bench $(INSTALL_PATH)
	@echo "Установлено: $(INSTALL_PATH)"

uninstall:
	rm -f $(INSTALL_PATH)
	rm -rf /usr/local/lib/bench
	@echo "Удалено: $(INSTALL_PATH)"

clean:
	rm -rf dist/ build/ bench.spec
