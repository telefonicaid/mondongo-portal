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

from django.db import models

class Configuration(models.Model):
    api_endpoint = models.CharField(max_length=200)
    api_user = models.CharField(max_length=20)
    authorization_token = models.CharField(max_length=100)
    version_token = models.CharField(max_length=20)
    mongo_dataset = models.CharField(max_length=200)
    mongo_package = models.CharField(max_length=200)

    def __unicode__(self):
        return self.api_endpoint
