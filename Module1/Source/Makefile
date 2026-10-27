# Module 1 -- Digital Representation, Colour & Memory
# POSIX make. On Windows use Git Bash / WSL, or run the `python ...` lines by hand.
# Use this module's own virtualenv so library versions match requirements.txt.
# Create it once: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
PY ?= .venv/bin/python

.PHONY: all data photos photos-small test report png figures clean

all: data test report

## synthetic image set, then my own photos -> data/ + data/manifest.csv
data:
	$(PY) make_data.py --out data
	$(PY) import_photos.py --src photos/small --out data

## only my photos: photos/small/*.jpg -> data/*.ppm + manifest rows
photos:
	$(PY) import_photos.py --src photos/small --out data

## rebuild photos/small from the full-resolution originals (not in git, see photos/README.md)
photos-small:
	$(PY) prepare_photos.py

## run every from-scratch unit's self-test + its reference match
test:
	$(PY) tests.py

## build report/budget.md + report/report.html + the downscale artifacts
report: data
	$(PY) gamma_resize_bug.py --fix --out report/
	$(PY) resample.py --image data/relief.ppm --factor 2 --methods naive-box,linear-box --out report/
	$(PY) format_compare.py --image data/crop_dinding.ppm --out report/
	$(PY) format_compare.py --image data/crop_surai.ppm --out report/
	$(PY) downscale_compare.py --out report/
	$(PY) dither.py --out report/
	$(PY) aliasing_demo.py --out report/
	$(PY) cvd.py --legend --out report/
	$(PY) report.py
	@echo "open report/report.html"

## report images -> ../docs/img/*.png for the README (GitHub cannot show .ppm)
png:
	$(PY) export_png.py --src report --out ../docs/img

## Studi Pendahuluan diagrams (own venv, needs matplotlib; not needed to compile the module)
figures:
	figures/.venv/bin/python figures/make_figures.py

clean:
	rm -rf data report _tmp_selftest.* __pycache__
