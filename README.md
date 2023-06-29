# hockey-sign-up

For the .gitignore I'm following a lot of what's in [here](https://djangowaves.com/tips-tricks/gitignore-for-a-django-project/#:~:text=If%20you%20are%20using%20Git,has%20access%20to%20your%20code).

- I used the PyCharm IDE (community edition for development). Basically followed the setup wizard, nothing notable.
- I used pgAdmin 4 for the database. I installed PostgreSQL and it automatically installed pgAdmin 4 along with it (see setup wizard) from [here](https://www.postgresql.org/download/). When downloading postgresSQL, it prompts you to create a superuser for your database. Upon opening pgAdmin 4, you will be prompted to provide a master password. Upon opening pgAdmin 4, create a new user under the Login/Group Roles section ('Can Login?', 'Create Databases?', and 'Inherit rights from the parent roles?' should be enabled) and set its password. Then, create a new database with this user as the owner. Make note of the database name, database owner, and database owner password. These values will be used in the .env file later on.

To setup on your local machine, I recommend using PyCharm and pgAdmin4 described above. I used the tutorials [here](https://docs.djangoproject.com/en/4.2/) to get my project setup.
The setup instructions are all assuming that you are on Windows.

## Setup

- Make sure Python is installed. Download [here](https://www.python.org/downloads/). I followed all defaults in the setup wizard and checked "Add Python X.Y to PATH".

- Make sure Django is installed. These [install instructions](https://docs.djangoproject.com/en/4.2/topics/install/#installing-official-release) and [how to for windows](https://docs.djangoproject.com/en/4.2/howto/windows/) are useful.
	- py -m pip install Django

- Make sure other packages are installed that are used by the project
	-  py -m pip install python-decouple (for the config .env)
	-  py -m pip install django-admin-rangefilter 
		- See [this](https://github.com/silentsokolov/django-admin-rangefilter) for more details
	-  py -m pip install psycopg2
		- as I'm writing this documentation, I found something saying that this will be deprecated at [some point](https://docs.djangoproject.com/en/4.2/releases/4.2/#django-4-2-release-notes) :(

- Set up the .env file (it is stored in the project root - along with this README). Fill out the following values:
	- SECRET_KEY=
		- Get a new secret key by executing the following in a python console:
			- from django.core.management.utils import get_random_secret_key
			- get_random_secret_key()
	- DEBUG=True
	- DB_NAME=
		- DB name from pgAdmin 4 setup
	- DB_USER=
		- DB user from pgAdmin 4 setup
	- DB_PASSWORD=
		- password for DB_USER
	- DB_HOST=127.0.0.1
		- This is just the localhost
	- TIME_ZONE=America/New_York
		- This is my timezone
	- ALLOWED_HOSTS=testserver,127.0.0.1,192.168.1.67,localhost
		- servers for doing most anyting locally
	- ORGANIZER_JSON={"Name":{"paypalClientID":"","playerFees":{"skater":"17", "goalie":"0"}}}
		- This will be used to autopopulate drop in details pulled from the chiller website
		- Fields:
			- Name = Name for drop-in session as appears in chiller
			- paypalClientID = client ID from app in paypal
			- playerFees = default player/goalie payment amounts

- Get the database populated
	- python manage.py makemigrations
	- python manage.py migrate

- Set up a superuser
	- python manage.py createsuperuser
	- Follow the prompts

- Try to get a test server running 	(NOTE: when following these installation instructions on another machine, I encountered an issue where I couldn't run the server from within the terminal provided by pyCharm. I'd get an error, "Python was not found; run without arguments to install from the Microsoft Store, or disable this shortcut from Settings". So, I had to run the server from a normal command prompt terminal)
	- In a terminal, navigate to the folder path that contains the 'manage.py' file for the project
	- run this command:
		- py manage.py runserver 0.0.0.0:8888
	- Navigate to 127.0.0.1:8888 in a browser (preferably Chrome)
	- You can login as the superuser you just created to check out anything in the site

- You should be all set up now!