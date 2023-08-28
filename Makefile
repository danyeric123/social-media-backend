format:
	pipenv run isort . && pipenv run yapf . -r -i --style google

deploy: format
	sls deploy 