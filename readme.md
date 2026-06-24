<!-- if you want to run this project you need to install python 3.8  -->
after install run this commands


py -3.8 -m venv venv
venv\Scripts\activate
pip install django
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver