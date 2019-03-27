Requirements

Python 3
A personal github access token

Installation

cp local_settings_template.py local_settings.py
# set you github key in local_settings.py
pipenv sync

Download and process metadata

pipenv shell
python gitan.py download
python gitan.py parse

Browse metadata

python gitan.py runserver 8080
# point your browser to localhost:8080
# ctrl+C to stop the server
