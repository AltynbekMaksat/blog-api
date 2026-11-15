# Blog API

A Django-based blog management system with Django REST Framework and a customized Django Unfold administration panel.

## Technologies

- Python 3.14
- Django 6.1.1
- Django REST Framework
- SQLite
- Django Unfold
- Faker
- Ruff

## Project Structure

```text
blog-api/
├── apps/
│   ├── auths/
│   └── blog/
├── docs/
│   └── screenshots/
├── logs/
├── requirements/
│   ├── base.txt
│   └── dev.txt
├── settings/
├── templates/
├── .gitignore
├── db.sqlite3
├── manage.py
└── README.md
```

ORM Queries

The project contains 50 Django ORM queries implemented in apps/blog/queries.py.

Running the queries

Run all read-only queries (1–39 and 45–50):

python manage.py queries

Run a specific query:

python manage.py queries --number 31

Display generated SQL:

python manage.py queries --number 6 --sql

Seed data

Populate the database with test data:

python manage.py seed --clear

Data-changing queries

Queries 40–44 are excluded from the default execution because they modify database records.

Run them individually:

python manage.py queries --number 40 
python manage.py queries --number 41
python manage.py queries --number 42
python manage.py queries --number 43
python manage.py queries --number 44

The command displays the query number, function name, number of SQL queries, and results.