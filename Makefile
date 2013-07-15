.PHONY: dist clean

VERSION := $(shell python3 setup.py --version)

dist:
	python setup.py sdist
	mkdir -p dist/app-misc/python_apis_maarons
	cp python_apis_maarons.ebuild dist/app-misc/python_apis_maarons/python_apis_maarons-${VERSION}.ebuild

clean:
	find . -name '__pycache__' -exec rm -rf {} +
	rm -rf build dist MANIFEST
