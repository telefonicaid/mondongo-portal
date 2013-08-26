# -*- coding: latin-1 -*-
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

# FIXME: this module is somehow abandon, as I was not able to make the thing work using
# the svcadm command at http://wiki.joyent.com/display/jpc2/Replica+Sets+through+Service+Management+Facility

_script_common = """
#!/bin/sh -x

function debug {
    if [ $DEBUG -eq 1 ]; then
        echo "DEBUG: $1"
    fi
}

DEBUG=1
MONGO_CONF_FILE=/mongodb/mongodb.conf
MONGO_DATA_DIR=/data/db

debug "Starting customization script"

# We don't want to completely remove some parameters, but commented them as they
# make autoconfiguration complicated

# Forge mongo configuration file
debug "Forge $MONGO_CONF_FILE"
echo "dbpath = /data/db" > $MONGO_CONF_FILE
echo "#bind_ip = 127.0.0.1" >> $MONGO_CONF_FILE
echo "port = 27017" >> $MONGO_CONF_FILE
echo "pidfilepath = /data/db/mongodb.pid" >> $MONGO_CONF_FILE
echo "logpath = /var/log/mongodb/mongodb.log" >> $MONGO_CONF_FILE
echo "logappend = true" >> $MONGO_CONF_FILE
echo "journal = true" >> $MONGO_CONF_FILE
echo "nohttpinterface = true" >> $MONGO_CONF_FILE
echo "directoryperdb = true" >> $MONGO_CONF_FILE
echo "auth = true" >> $MONGO_CONF_FILE

# Ensure that db is empty (otherwise we can get "ERROR - couldn't initiate : member x.x.x.x has data already,
# cannot initiate set"
debug "Delete $MONGO_DATA_DIR"
rm -rf $MONGO_DATA_DIR/*

# See http://wiki.joyent.com/display/jpc2/Replica+Sets+through+Service+Management+Facility
# Note we have to wait until 'svcadm enable ipfilter' finish (which is captured in $IPFILTER_STATUS)
# because otherwise we get an "ERROR - To use replication ipfilter must be enabled."
debug "Enable ipfilter"
svcadm enable ipfilter
IPFILTER_RESULT=$(svcs ipfilter | tail -n 1 | awk '{print $1}')
until [ "$IPFILTER_RESULT" == "online" ]; do
    debug "Waiting (1s) for ipfilter..."
    sleep 1s
    IPFILTER_RESULT=$(svcs ipfilter | tail -n 1 | awk '{print $1}')
done

debug "Configuring common repl set properties"
svccfg -s network/mongodb setprop replication/name = mondongo
svccfg -s network/mongodb setprop replication/key = mondongokey
"""


def script_initiator(ips):

    s = _script_common + """
SELF_IP=$(ifconfig net0 | grep inet | awk '{print $2}')
debug "Configuring members"
"""

    ips_string = ''
    for ip in ips:
        ips_string += ip + ':27017,'

    s += "svccfg -s network/mongodb setprop replication/members = " + ips_string + "$SELF_IP:27017"

    s += """
debug "Refreshing mongodb service"
svcadm refresh mongodb
debug "Restarting mongodb service"
svcadm restart mongodb

debug "Init replica set"
repl-init -i

debug "Ending customization script"
"""

    return s


def script_noinitiator():

    s = _script_common + """
debug "Refreshing mongodb service"
svcadm refresh mongodb
debug "Restarting mongodb service"
svcadm restart mongodb

debug "Ending customization script"
"""

    return s
