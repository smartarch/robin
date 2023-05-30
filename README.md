# robin
Research Observatory Instrument


### Create a Local Database File
To manage the publications on a local server, the first step is to create a database. By default, Django uses SQL-Elite. For other type of database please refer to: https://docs.djangoproject.com/en/4.2/ref/databases/

Robin uses the default djagno database, and to create it run the following command lines:
```commandline
cd interface
python manage.py makemigrations
python manage.py migrate
```

By migrating, the tables will be created in the database file, and the new database file will be visible. In order to view the table, we have enabled the Admin site, which is accessible by a super user, and the following command is to make one:

```commandline
cd interface
python manage.py createsuperuser
```

Once the superuser is created, run the server using the following command:
```commandline
cd interface
python manage.py runserver
```

Now, open provided link http://127.0.0.1:8000/admin/ (usually it is run on port 8000) and enter the username and password. Once entered the Admin panel, the tables of all apps are accessible.



### Enable Github Login
By the support of Django-allauth (https://django-allauth.readthedocs.io), we have provided login using Github. The login requires a oAuth key. Run the server if it is not already running, then perform the following steps:


* Register a new OAuth application at https://github.com/settings/applications/new
    - Set homepage to http://127.0.0.1:8000
    - Set Authorization callback URL to http://127.0.0.1:8000/accounts/github/login/callback/
* Open http://127.0.0.1:8000/admin/socialaccount/socialapp/add/
    - set Provider as Github
    - Provide a name for example 'github'
    - Client ID and Secret key are extracted from the github OAuth application
    - Key is optional
    - Move the available site to chosen site
    - Save
  
Now the team can access Robin using Github account from this link http://127.0.0.1:8000/accounts/github/login/  

