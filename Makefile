.PHONY: test validate

test:
	python -m unittest discover -s tests -v

validate: test
	python -m veka international-audit --output /tmp/veka-international-audit.json
	python -m veka lexical-risk --target mi --target ne --top 10 --candidates 3
