update-deps:
	pip install --upgrade pip-tools pip setuptools
	pip-compile --upgrade --build-isolation --generate-hashes --output-file requirements/main.txt requirements/main.in
	pip-compile --upgrade --build-isolation --generate-hashes --output-file requirements/dev.txt requirements/dev.in

init: get_js
	pip install --editable .
	pip install --upgrade -r requirements/main.txt -r requirements/dev.txt

update: update-debs init

test:
	pytest appliance_status

run_locally:
	FLASK_ENV=development flask run

get_js:
	cd ../appliance_status_js; yarn build; cp dist/* ../appliance_status_py/appliance_status/static

.PHONY: udpate-debs init update
