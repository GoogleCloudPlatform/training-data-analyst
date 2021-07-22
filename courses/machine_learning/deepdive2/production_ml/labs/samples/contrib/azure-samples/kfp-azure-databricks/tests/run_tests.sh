pip install --upgrade ..
pip install coverage
coverage run -m unittest discover --verbose
coverage report