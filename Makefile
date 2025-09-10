VENV=.venv
PY=$(VENV)/bin/python
PIP=$(VENV)/bin/pip

.PHONY: help venv install normalize validate html test check app

help:
	@echo "Targets: venv, install, normalize, validate, html, test, check, app"

venv:
	@test -d $(VENV) || python3 -m venv $(VENV)

install: venv
	$(PIP) install --upgrade pip
	$(PIP) install -r webapp/requirements.txt

normalize: install
	$(PY) scripts/normalize_v0_2_examples.py v0.3.0/xml/*.xml

validate: install
	$(PY) scripts/validate_v0_2.py v0.3.0/xml/BAM-F017.xml v0.3.0/xsd/drmd.xsd
	$(PY) scripts/validate_v0_2.py v0.3.0/xml/BAM-M375a.xml v0.3.0/xsd/drmd.xsd

html: install
	mkdir -p v0.3.0/html
	$(PY) scripts/xml2html.py v0.3.0/xml/BAM-F017.xml v0.3.0/xsl/drmd.xsl v0.3.0/html/BAM-F017.html
	$(PY) scripts/xml2html.py v0.3.0/xml/BAM-M375a.xml v0.3.0/xsl/drmd.xsl v0.3.0/html/BAM-M375a.html

test: install
	$(PY) -m unittest tests/test_v0_2_0.py -v

check: normalize validate html test

# Run Streamlit app (headless). Use Ctrl+C to stop when running interactively.
app: install
	$(VENV)/bin/streamlit run webapp/app.py --server.headless true --server.port 8501

.PHONY: docker-build docker-run
docker-build:
	docker build -t drmd-app:latest .

docker-run:
	docker run --rm -p 8501:8501 \
	  -e DRMD_XSD_PATH=/app/v0.3.0/xsd/drmd.xsd \
	  -e DRMD_XSL_PATH=/app/v0.3.0/xsl/drmd.xsl \
	  -e QUDT_TTL_PATH=/app/imports/qudt.ttl \
	  drmd-app:latest
