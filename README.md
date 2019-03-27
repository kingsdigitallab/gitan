## Features

* create a local database of django models found across several github repositories
* web page to browse and search those models with direct link to github source code

![screenshot](https://raw.githubusercontent.com/kingsdigitallab/gitan/master/doc/django-model-explorer.png)

## Requirements

* Python 3
* pipenv
* A personal github access token

## Installation

Open a terminal, clone the repo and change into the repo directory:

```
cp local_settings_template.py local_settings.py
# set you github key in local_settings.py
pipenv sync
```

## Download and process metadata

```
pipenv shell
python gitan.py download
python gitan.py parse
```

## Browse metadata

```
python gitan.py runserver 8080
# point your browser to localhost:8080
# ctrl+C to stop the server
```
