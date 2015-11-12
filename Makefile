.PHONY: all test clean_coverage doc doc_coverage clean pep8 pyflakes check

all:
	@echo 'test           run the unit tests'
	@echo 'pep8           check pep8 compliance'
	@echo 'pyflakes       check for unused imports (requires pyflakes)'
	@echo 'check          make sure you are ready to commit'
	@echo 'clean          cleanup the source tree'

doc_coverage:
	@echo 'Running docstring coverage...'
	@docstring-coverage burpui

test: clean_coverage
	@echo 'Running all tests...'
	@nosetests --with-coverage --cover-package=burpui test/test_burpui.py

doc:
	@echo 'Generating documentation...'
	@cd docs && make html

clean:
	@find . -type d -name "__pycache__" -exec rm -rf "{}" \; || true
	@find . -type f -name "*.pyc" -delete || true
	@rm -rf build dist burp_ui.egg-info docs/_build || true

clean_coverage:
	@rm -f .coverage

pep8:
	@echo 'Checking pep8 compliance...'
	@pep8 --ignore=E501 burpui

pyflakes:
	@echo 'Running pyflakes...'
	@pyflakes burpui

check: pep8 pyflakes doc_coverage test
