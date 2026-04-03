Run these commands locally to create DB tables for the new models:

python manage.py makemigrations app
python manage.py migrate

Create superuser to access admin:

python manage.py createsuperuser

Start server:

python manage.py runserver
