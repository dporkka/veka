.PHONY: test validate

test:
	python -m unittest discover -s tests -v

validate: test
	python -m veka international-audit --output /tmp/veka-international-audit.json
