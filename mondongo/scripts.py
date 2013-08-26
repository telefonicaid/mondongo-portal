# Copyright 2013 Telefonica Investigación y Desarrollo, S.A.U
#
# This file is part of Mondongo Portal
#
# Mondongo Portal is free software: you can redistribute it and/or modify it under the terms
# of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Mondongo Portal is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License
# for more details.
#
# You should have received a copy of the GNU Affero General Public License along with Mondongo Portal. If not,
# see http://www.gnu.org/licenses/.
#
# For those usages not covered by the GNU Affero General Public License please contact with fermin at tid dot es

__author__ = 'fermin'

# These scripts are adapted to work with mongo dataset version: sdc:sdc:mongodb:1.4.5

_script_common = """#!/bin/sh -x

function debug {
    if [ $DEBUG -eq 1 ]; then
        echo "DEBUG: $1"
    fi
}

DEBUG=1
MONGO_CONF_FILE=/opt/local/etc/mongodb.conf
MONGO_DATA_DIR=/var/mongodb
MONGO_PID_FILE=/var/mongodb/mongodb.pid
MONGO_USER=mongodb

debug "Starting customization script"

# We disable the mongo Solaris service, as we prefer to start mongod directly to avoid interference. We have tested
# to use the procedure at http://wiki.joyent.com/display/jpc2/Replica+Sets+through+Service+Management+Facilitybut
# there are problems (the smartdc-mdata:execute work fails by timeout when # trying to 'svcadm enable ipfilter' and
# get it online).
debug "Disable mongodb"
# Not use "-" this time... some PATH magic does that using the "-" login variant, the svcadm command is not
# found for admin user
su admin -c "svcadm disable mongodb"
# Sleep some time to let svc framework to shutdown mongodb
sleep 10s

# We don't want to completely remove some parameters, but commented them as they
# make autoconfiguration complicated
# Forge mongo configuration file
debug "Forge $MONGO_CONF_FILE"
cp $MONGO_CONF_FILE $MONGO_CONF_FILE.old
echo "dbpath = $MONGO_DATA_DIR" > $MONGO_CONF_FILE
echo "#bind_ip = 127.0.0.1" >> $MONGO_CONF_FILE
echo "#port = 27017" >> $MONGO_CONF_FILE
echo "pidfilepath = $MONGO_PID_FILE" >> $MONGO_CONF_FILE
echo "logpath = /var/log/mongodb/mongodb.log" >> $MONGO_CONF_FILE
echo "logappend = true" >> $MONGO_CONF_FILE
echo "journal = true" >> $MONGO_CONF_FILE
echo "nohttpinterface = true" >> $MONGO_CONF_FILE
echo "directoryperdb = true" >> $MONGO_CONF_FILE
echo "#auth = true" >> $MONGO_CONF_FILE

# Extra security measure
if [ -s $MONGO_PID_FILE ]; then
    PID=`cat $MONGO_PID_FILE`
    debug "Killing mongodb process: $PID"
    kill $PID
fi

# Ensure that db is empty
debug "Delete $MONGO_DATA_DIR"
rm -rf $MONGO_DATA_DIR/*

"""


def script_master():

    s = _script_common + """debug "Launch mongo as master"
#See https://groups.google.com/forum/?fromgroups#!topic/mongodb-user/vJpJNzCareY to know about
#the export in the next line
export LC_ALL=C
su - $MONGO_USER -c "/opt/local/bin/mongod --fork -f $MONGO_CONF_FILE --master"
"""

    return s


def script_slave(ip_master):

    s = _script_common + "debug \"Launch mongo as slave with master " + ip_master + "\"\n"
    s += """#See https://groups.google.com/forum/?fromgroups#!topic/mongodb-user/vJpJNzCareY to know about
#the export in the next line
export LC_ALL=C
"""
    s += "su - $MONGO_USER -c \"/opt/local/bin/mongod --fork -f $MONGO_CONF_FILE --slave --source " + ip_master + "\"\n"

    return s


def script_mongos(ip_shards, ip_config_server, db, col, key):

    s = _script_common + """debug "Wait until config db is up and running"
RESULT=1
until [ $RESULT -eq 0 ]; do
    debug "...1 second"
    sleep 1s
"""
    s += "    nc -z " + ip_config_server + " 27019\n"

    s += """    RESULT=$?
done
"""

    for ip in ip_shards:
        s += "debug \"Wait until shard " + ip + " is up and running\"\n"
        s += """RESULT=1
until [ $RESULT -eq 0 ]; do
    debug "... 1 second"
    sleep 1s
"""
        s += "    nc -z " + ip + " 27017\n"

        s += """    RESULT=$?
done
"""

    s += """debug "Launch mongos"
#See https://groups.google.com/forum/?fromgroups#!topic/mongodb-user/vJpJNzCareY to know about
#the export in the next line
export LC_ALL=C
"""
    s += "su - $MONGO_USER -c \"/opt/local/bin/mongos --fork --configdb " + ip_config_server + " --logpath=/var/log/mongodb/mongos.log --logappend\"\n"
    s +="""sleep 5s

debug "Set sharding"
su - $MONGO_USER -c '/opt/local/bin/mongo admin <<EOF
"""
    for ip in ip_shards:
        s += "db.runCommand({addshard : \"" + ip + ":27017\"})\n"

    s += "db.runCommand({\"enablesharding\" : \"" + db + "\"})\n"

    s += "db.runCommand({\"shardcollection\" : \"" + db + "." + col + "\", \"key\" : {\"" + key + "\" : 1}})\n"

    s += """quit()
EOF
'
"""

    return s


def script_config_server():

    s = _script_common + """debug "Launch mongo config server"
#See https://groups.google.com/forum/?fromgroups#!topic/mongodb-user/vJpJNzCareY to know about
#the export in the next line
export LC_ALL=C
su - $MONGO_USER -c "/opt/local/bin/mongod --fork -f $MONGO_CONF_FILE --configsvr"
"""

    return s

