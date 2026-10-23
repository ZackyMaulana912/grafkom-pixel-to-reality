# Module 1 -- Digital Representation, Colour & Memory
# POSIX make. On Windows use Git Bash / WSL, or run the `python ...` lines by hand.
# Use this module's own virtualenv so library versions match requirements.txt.
# Create it once: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
PY ?= .venv/bin/python

.PHONY: all data test report figures clean

all: data test report

## generate the deterministic synthetic heritage image set -> data/
data:
	$(PY) make_data.py --out data

## run every from-scratch unit's self-test + its reference match
test:
	$(PY) tests.py

## build report/budget.md + report/report.html + the downscale artifacts
report: data
	$(PY) gamma_resize_bug.py --fix --out report/
	$(PY) resample.py --image data/relief.ppm --factor 2 --methods naive-box,linear-box --out report/
	$(PY) format_compare.py --image data/crop_hifreq.ppm --out report/
	$(PY) format_compare.py --image data/crop_smooth.ppm --out report/
	$(PY) report.py
	@echo "open report/report.html"

## optional slide figures (not needed to compile the module)
figures:
	$(PY) ../../figures/make_figures_m1.py

clean:
	rm -rf data report _tmp_selftest.* __pycache__
