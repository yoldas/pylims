# pylims

# Instructions

The application is written in Python. It needs Python version 3.6 or above.
It has only one testing dependency, for measuring the code coverage.

## Running

(Optional) Create virtual environment.

    python3 -m venv sangerEnv
    cd sangerEnv
    source bin/activate

Install coverage.

    pip install coverage

Download pylims.

    git clone yoldas/pylims

Go to the directory of lims.py and run the script without any arguments to view 
the usage help.

    cd pylims 
    python3 lims.py

The application database db.sqlite3 is a copy of misc/template_db.sqlite3 . It 
is possible to start over by copying misc/template_db.sqlite3 to db.sqlite3 .

## Testing

Execute the following for the unit tests.

    python3 -m unittest discover -v tests

Execute the following for coverage.

    coverage run --source=pylims -m unittest discover -v tests
    coverage html
    open htmlcov/index.html

The unit testing database test_db.sqlite3 is a copy of misc/template_db.sqlite3. 
Unit tests do not execute DDL statements, but they truncate tables and reset
sequences of the testing database.

## Assumptions

Application will not issue barcodes for containers (tubes or plates), and it
will not require registering empty containers.

customer_sample_name contains two parts, customer and sample_name used by that
customer. They are separated by name_delimiter (hyphen), for example
customer1-sample1.

There are two types of tubes, sample tubes and lab tubes.

Source tubes are discarded after tube_transfer; re-using will not be allowed.

Samples can be tagged only once; re-tagging will not be allowed.

