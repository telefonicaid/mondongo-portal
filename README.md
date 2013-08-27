mondongo-portal
===============

Web portal for provisioning mongo SM in Joyent infrastructure

License
=======

This code is licensed under GNU Affero General Public License v3. You can find the license text in the LICENSE file
in the repository root.

Useful things to demo
=====================

Login with the 'admin' account.

```
cat /var/svc/mdata-user-script

--------- x0 ------------------
mongo localhost:27017
use local
db.slaves.find()

--------- x1 ------------------
mongo
use local
db.sources.find()

--------- SS ------------------
mongo
use config
db.databases.find()
db.shards.find()
db.chunks.find()
```

Python package versions
=======================

* Django: 1.5.1
* Requests: 1.2.2

Installing
==========

This procedure has been done in Debian.

* Install required packages:

```
apt-get install apache2 libapache2-mod-wsgi python-pip
```

* Install Django. Note that there is python-django package available in APT, but using pip we will get the newer version:

```
pip install -r requirements.txt
```

* Deploy the proyect files in a given directory. Let assume that the directory of the application (the one that contains 
manage.py) is /opt/mondongo_app.

* Configure in /opt/mondongo_app/mondongo_server/settings.py: `TEMPLATE_DIRS = ('/opt/mondongo_app/templates',)`
 
* Configure in /opt/mondongo_app/mondongo_server/settings.py database name to `'NAME': '/opt/sqlitedbs/mondongo.db'`

* Change owner of static conent files (not sure about that, but it seems it is needed):

```
chown -R www-data:www-data /opt/mondongo_app/mondongo/static
```

* Create the database file with:

```
mkdir /opt/sqlitedbs/
touch /opt/sqlitedbs/mondongo.db
chown -R www-data:www-data /opt/sqlitedbs/ # sqlite also needs permission in the database parent directory
```
* Create database schema an superuser:

```
python manage.py syncdb
```

* Ensure that the application and Django themselves are ok, running the server in a given port, e.g:

```
python manage.py runserver 0:8080
```

* Configure /etc/apache2/mods-enabled/wsgi.conf, adding:

```
WSGIPythonPath /opt/mondongo_app
```

* Configure virtual host creating file /etc/apache2/sites-available/mondongo:

```
<VirtualHost *:80>
    WSGIScriptAlias / /opt/mondongo_app/mondongo_server/wsgi.py
    Alias /static/ /opt/mondongo_app/mondongo/static/

    <Directory /opt/mondongo_app/>
    <Files wsgi.py>
    Order deny,allow
    Allow from all
    </Files>
    </Directory>

    <Directory /opt/mondongo_app/mondongo/static>
    Order deny,allow
    Allow from all
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/error.log

    # Possible values include: debug, info, notice, warn, error, crit,
    # alert, emerg.
    LogLevel warn

    CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>
``` 

* Site enable (I think there is a cleaner procedure, based on apache commands, but the following works)

```
cd /etc/apache2/sites-enabled
rm 000-default
ln -s ../sites-available/mondongo 000-default
```

* Restart HTTP server

```
/etc/init.d/apache2 restart
```

* Go to `http://<machine>/mondongo` and login with the user you set in the previous step
