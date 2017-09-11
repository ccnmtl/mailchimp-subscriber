VE ?= ./ve
FLAKE8 ?= $(VE)/bin/flake8
REQUIREMENTS ?= requirements.txt
SYS_PYTHON ?= python3
ENV_PYTHON ?= $(VE)/bin/python
PIP ?= $(VE)/bin/pip
PY_SENTINAL ?= $(VE)/sentinal
WHEEL_VERSION ?= 0.29.0
VIRTUALENV ?= virtualenv.py
SUPPORT_DIR ?= requirements/virtualenv_support/
SCRIPT_FILE ?= mailchimp-subscriber.py
TEST_FILES ?= *
MAX_COMPLEXITY ?= 10
PY_DIRS ?= *.py tests --exclude virtualenv.py

$(PY_SENTINAL): $(REQUIREMENTS) $(VIRTUALENV) $(SUPPORT_DIR)*
	rm -rf $(VE)
	$(SYS_PYTHON) $(VIRTUALENV) --extra-search-dir=$(SUPPORT_DIR) --never-download $(VE)
	$(PIP) install wheel==$(WHEEL_VERSION)
	$(PIP) install --use-wheel --no-deps --requirement $(REQUIREMENTS)
	$(SYS_PYTHON) $(VIRTUALENV) --relocatable $(VE)
	touch $@

flake8: $(PY_SENTINAL)
	$(FLAKE8) $(PY_DIRS) --max-complexity=$(MAX_COMPLEXITY)

run: $(PY_SENTINAL)
	$(ENV_PYTHON) $(SCRIPT_FILE)

test: $(PY_SENTINAL)
	$(VE)/bin/python -m tests/$(TEST_FILES)

clean:
	rm -rf ve

.PHONY: clean
