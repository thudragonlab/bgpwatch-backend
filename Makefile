build:
	gunicorn -c ./config/gunicorn_config.py app:app

requirement:
	  pipreqs ./ --encoding=utf8 --force  --savepath requirements

public_doc:
	  npx @redocly/cli build-docs config/openapi.json -o src/templates/redoc-static.html

