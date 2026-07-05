# integrity-bench

Поддерживаемые форматы: `txt`, `csv`, `json`, `zip`, `gzip`, `7z`, `png`, `jpeg`, `bmp`, `elf`, `pe`, `macho`, `mp4`, `mkv`, `avi`.

---

## Требования

- Python 3.13+
- [Poetry](https://python-poetry.org/)
- `7z` (для проверки 7z-архивов): `brew install p7zip`
- `djpeg` (для проверки JPEG): `brew install jpeg`

---

## Сборка и установка

```bash
# собрать бинарник
make build

# установить в /usr/local/bin/bench
sudo make install

# удалить
sudo make uninstall
```

После установки команда `bench` доступна из любой директории.

---

## Использование

### Анализ файлов

```bash
# один файл
bench detect path/to/file.jpg

# директория
bench detect path/to/folder/

# с выводом в CSV
bench detect path/to/folder/ --csv report.csv

# с детальной информацией по каждому детектору
bench detect path/to/folder/ --csv report.csv --verbose

# с проверкой по эталонным меткам
bench detect path/to/folder/ --ground-truth ground_truth.json
```

### Повреждение файлов

```bash
bench corrupt path/to/sample/ path/to/output/
```

Создаёт повреждённые копии файлов из `sample/` в `output/` и сохраняет `output/ground_truth.json` с метками.

---

## Вывод

```
  doc.txt                                   intact      1.0000  [txt]    8мс
! photo.bmp                                 corrupted   0.1200  [bmp]   12мс
! broken.jpeg                               uncertain   0.4500  [jpeg]  18мс

Итого: 3 файла, проблемных: 2 (corrupted: 1, uncertain: 1), среднее время: 13мс/файл
```

`!` — файл повреждён или не определён.  
`uncertain` — детекторы дали противоречивые сигналы (score от 0.3 до 0.7).

---

## Метки и пороги

| Метка | Score |
|---|---|
| `intact` | ≥ 0.7 |
| `uncertain` | 0.3 — 0.7 |
| `corrupted` | ≤ 0.3 |

---

## Архитектура

Стенд использует четыре детектора:

- **CrcDetector** — проверка встроенных контрольных сумм (`zip`, `gzip`, `png`)
- **StructuralDetector** — разбор структуры формата (`jpeg`, `7z`, исполняемые, видео)
- **StatisticalDetector** — анализ энтропии и её дисперсии по окнам
- **MlDetector** — Random Forest на статистических признаках (предобученные модели включены)

Итоговый score вычисляет агрегатор: если есть достоверный детектор — доверяет ему, иначе — взвешенное среднее.
