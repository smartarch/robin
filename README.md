# robin
Research Observatory Instrument


### Create a Local Database File
To manage the publications on a local server, the first step is to create a database. By default, Django uses `SQLite3`. For other type of database please refer to: https://docs.djangoproject.com/en/4.2/ref/databases/

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


### Working With Django Models
For Django a model is a python class that represents a table in the database. To understand fully on Django models, please refer to https://docs.djangoproject.com/en/4.2/topics/db/models/ . We provide a simple example to work with Django Model to populate the `Country` table in the database. 

First, we show how to add one single country in Django provided shell.
```commandline
cd interface
python manage.py shell
```
```python
from publication.models import Country      # Country is a class in models.py
new_country = Country(name= "Czechia", other_forms= "Czech Republic;CZ")          # to create a new country
new_country.save()                          # save the object in the the database
```
If the server is running, the added country can be seen in http://127.0.0.1:8000/admin/publication/country/.
Note that the name of `country` is unique, and if we try the above line again, it will throw an exception.
To remove the country using the shell, we can try the following:

```python
added_country = Country.objects.get(name="Czechia")
added_country.delete()
```

Now we try to add all the countries from list of countries as a csv file `country_names.csv` from 
https://github.com/lukes/ISO-3166-Countries-with-Regional-Codes/blob/master/all/all.csv.
```python
from publication.models import Country
with open("country_names.csv", "r") as country_names:
    for line in country_names.readlines():
    country_name, other_forms = line.strip("\"").strip().split(",",1)
    new_country = Country (name=country_name, other_forms=other_forms)
    new_country.save()

```

Since the list of countries is not often changed (at least at the time of this publication), we can keep the country list to the populated one. Please be aware that some publication affiliation countries use different names such as "USA" instead of "United States". 

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

