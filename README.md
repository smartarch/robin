# Robin: A tool for automated literature mapping
This document describes <b>Robin</b> architecture and it provides use-cases where the tool can be helpful. <b>Robin</b> helps research teams to conduct literature mapping, which is important part of research methodology. Technically, <b>Robin</b> helps research team members to collectively conduct a literature mapping study by create dependent and independent publication lists. This document is consist of four sections:

* [Installation](#Installation)
* [Overall Architecture](#Overall-Architecture)
* [User Management](#User-Management)
* [Managing Mappings](#Managing-Mappings)
* [Making Queries](#Making-Queries)
* [Working With Lists](#Working-With-Lists)
* [Deploying](#Deploying)


## Installation
<b>Robin</b> is written in `python-django` which is a python package, and can be installed in the local library. To skip the installation section and use a docker, refer to the [Docker](/contianer). This section covers the following sections:

* Virtual Environment Setup and Package Installation
* Migrating The Database
* Creating Admin User
* Connecting to GitHub
* Connecting to IEEE and Scopus APIs

### Virtual Environment Setup 

We recommend using a `python-virtual-environement`, which can be used as the source of packages required for this project. To create the virtual environment, first make sure that `python-dev` is installed.

On Linux
```commandline
sudo apt-get update
sudo apt-get install python3 python3-dev python3-venv
```

On windows
```commandline
pip install virtualenv
```

If above command throws an error, then it means the pip is not installed, and it needs to be downloaded from the official website https://docs.python.org/3/installing/index.html#basic-usage

After installation of `venv` the following command on both Linux and Windows can be used to start a virtual environment.

```commandline
python3 -m venv env
```

If faced an issue while creating the virtual environment, refer to https://docs.python.org/3/library/venv.html. 

If the environment is correctly created, it needs to be activated. 

On `Linux` use:
```commandline
source env/bin/activate
```

On `Windows` use:
```commandline
env\Scripts\activate
```

After activating the virtual environment, the command line should look like this:
```
(env) /path_to_robin/
```

Now, to install the packages, the list of packages is in `requirments.txt`, and by using `pip` they can be installed on the virtual environment.
```commandline
pip install -r requirements.txt
```
### Migrating The Database
The next step is to start a database instance (which in this case is `SQLite`). To do so, use the following command while being on the `robin` folder:
```commandline
cd interface
python manage.py migrate
```

From this point, all the given commands will need to be done while in `interface` folder. To check if there is any issue with the project, run the following command
```commandline
python manage.py check
```
### Creating Admin User
If no issues were reported, proceed and create a super-user. A super-user is an admin with all privileges. To create such user, run the following command and enter requested information.

```commandline
python manage.py createsuperuser
```

Now, it is time to run the server. To start the server, run the following command:
```commandline
python manage.py runserver
```

Now open http://127.0.0.1:8000/admin, which is the `admin` page of the tool.

### Connecting to GitHub
In order to use `login-via-github`, two main steps should be taken. 
- Create an oAuth app on GitHub
- Create a social account on Robin




## Overall Architecture



## User Management

## Managing Mappings

## Making Queries

## Working With Lists

## Deploying