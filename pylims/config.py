"""Configuration parameters."""
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Production database with schema; initially copy of misc/template_db.sqlite3
database = {
    'engine': 'sqlite3',
    'name': os.path.join(base_dir, 'db.sqlite3')
}

# Unit test database with schema; initially copy of misc/template_db.sqlite3
# Pylims unit tests reset the tables and sequences but they don't execute DDL.
test_database = {
    'engine': 'sqlite3',
    'name': os.path.join(base_dir, 'test_db.sqlite3')
}

# Log file for unexpected errors; typically errors during transactions.
logfile = os.path.join(base_dir, 'pylims.log')

# Log file for unit testing in case we need it.
test_logfile = os.path.join(base_dir, 'test_pylims.log')
