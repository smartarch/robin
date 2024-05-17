# Robin: A tool for automated literature mapping

This document describes how to install **Robin**, and it provides use-cases where the tool can be helpful. **Robin** helps research teams to conduct literature mapping, which is important part of research methodology. Research team members can use **Robin** to collectively conduct a literature mapping study by create dependent and independent publication lists. This document is consist of the following sections:

* [Installation](#installation)

## Installation

**Robin** is written in Python (Django), and can be installed using the following steps:

1. [Virtual Environment Setup and Package Installation](#virtual-environment-setup)
2. [Migrating (Creating) the Database](#migrating-creating-the-database)
3. [Creating Admin User](#creating-admin-user)
4. [Starting Robin server](#starting-robin-server)
5. [Optional features](#optional-features)
   * [GitHub OAuth](#github-oauth)
   * [IEEE Xplore Search](#ieee-xplore-search)
   * [Scopus Search](#scopus-search)

### Virtual Environment Setup

We recommend using a Python virtual environment, which can be used as the source of packages required for this project. To create the virtual environment, first make sure that `python-dev` is installed.

On Linux

```bash
sudo apt-get update
sudo apt-get install python3 python3-dev python3-venv
```

On Windows

```bash
pip install virtualenv
```

If above command throws an error, then it means the `pip` is not installed, and it needs to be downloaded from the official website <https://docs.python.org/3/installing/index.html#basic-usage>

After installation of `venv` the following command on both Linux and Windows can be used to start a virtual environment.

```bash
python3 -m venv env
```

If faced an issue while creating the virtual environment, refer to <https://docs.python.org/3/library/venv.html>.

If the environment is correctly created, it needs to be activated.

On Linux use:

```bash
source env/bin/activate
```

On Windows use:

```bat
env\Scripts\activate
```

After activating the virtual environment, the command line should look like this:

```bash
(env) /path_to_robin/
```

Now, to install the packages (list of packages is in `requirments.txt`), use `pip` in the virtual environment.

```bash
pip install -r requirements.txt
```

### Migrating (Creating) The Database

The next step is to start a database instance (which in this case is `SQLite`). To do so, use the following command while being on the `robin` folder:

```bash
cd interface
python manage.py migrate
```

From this point, all the given commands will need to be done while in `interface` folder. To check if there is any issue with the project, run the following command

```bash
python manage.py check
```

### Creating Admin User

If no issues were reported, proceed and create a super-user. A super-user is an admin with all privileges. To create such user, run the following command and enter requested information.

```bash
python manage.py createsuperuser
```

### Starting Robin server

Now, it is time to run the server. To start the server, run the following command in the `interface` folder:

```bash
python manage.py runserver
```

Now open <http://127.0.0.1:8000/>, where the Robin app should be accessible (as shown in the following screenshot).

![home page shown with login access](readme_contents/public_page.png)

To open the administration of the tool, go to <http://127.0.0.1:8000/admin>.

### Optional Features

#### GitHub OAuth

In order to enable login via GitHub, two main steps should be taken.

* Create an OAuth app on GitHub, which can be done using <https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app>

* Create a social account on Robin. If the local server is running, simply login to admin section for social accounts (<http://127.0.0.1:8000/admin/socialaccount/socialapp/add/>) and enter the following details:

```
provider: "github",
name: "github",
client_id: "<client id from github app>",
secret: "<secret key from the github app>",
sites: "<choose the site from the list, usually example.com>",
```

Once saved, the other users should be able to login using GitHub account. To use it as another use, try a session on browser, or logout from the admin panel.

#### IEEE Xplore Search

Robin allows importing publications using a search query in the IEEE Xplore database.

The IEEE Xplore database is accessed through API. To get an API access please check <https://developer.ieee.org/>. It might take over a week to activate the `key`. Once the `key` is active, the following information must be added by the admin using this link: <http://127.0.0.1:8000/admin/query/queryplatform/add/>

```
key: <IEEE API KEY>,
source: IEEEXplore,
params: """
{
    "params:{
        "querytext": %query%,
        "open_access": "True",
        "format": "json",
        "apikey": %key%,
        "max_records": %max_results%
        }
}
""",
url: http://ieeexploreapi.ieee.org/api/v1/search/articles,
help_link: https://developer.ieee.org/docs/read/IEEE_Xplore_Metadata_API_Overview,
```

Please note that even with APIs activated, searching is monitored and if the API keys are abused they will be banned by the providers.

#### Scopus Search

Robin allows importing publications using a search query in the Scopus database.

The Scopus database is accessed  through API. To get an API access please check <https://dev.elsevier.com/>. The activation is immediate. Once the `key` is active, the following information must be added by the admin using this link: <http://127.0.0.1:8000/admin/query/queryplatform/add/>

```
key: <SCOPUS KEY>,
source: Scopus,
params: """
{ 
    "headers":{
        "Accept": "application/json",
        "X-ELS-APIKey": %key%
    },
    "params": {
        "start":0,
        "count":%max_results%,
        "query": %query%
    }
}""",
url: https://api.elsevier.com/content/search/scopus,
help_link: "https://dev.elsevier.com/sc_search_tips.html,
```

Please note that even with APIs activated, searching is monitored and if the API keys are abused they will be banned by the providers.
