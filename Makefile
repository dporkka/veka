.PHONY: test validate

PYTHON ?= python3

test:
	$(PYTHON) -m unittest discover -s tests -v

validate: test
	$(PYTHON) -m veka international-audit --output /tmp/veka-international-audit.json
	$(PYTHON) -m veka lexical-risk --target mi --target ne --top 10 --candidates 3
	$(PYTHON) -m veka communication-audit
	$(PYTHON) -m veka borrowing-audit
	$(PYTHON) -m veka conversation-score
	$(PYTHON) -m veka root-research > /dev/null
	$(PYTHON) -m veka root-sources > /dev/null
