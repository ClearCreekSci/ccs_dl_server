"""
    dbconfig.py
    data browser specific settings

    Copyright (C) 2026 Clear Creek Scientific

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
from ccs_dlconfig import config
import xml.etree.ElementTree as et

TAG_INTERNAL = 'internal'
TAG_PHASH = 'phash'
TAG_SECRET = 'secret'
TAG_USE_METRIC = 'metric'

DEFAULT_USE_METRIC = True
DEFAULT_SECRET = 'deadbeef'
DEFAULT_PASSWORD = ''


class DBSettings(config.Settings):

    def __init__(self):
        super().__init__()
        self.use_metric = DEFAULT_USE_METRIC
        self.secret = DEFAULT_SECRET
        #self.passwd = DEFAULT_PASSWORD
        self.passwd = ''

    def set_use_metric(self,v):
        self.use_metric = v

    def set_secret(self,v):
        self.secret = v

    def set_password(self,v):
        self.passwd = v

    def read(self,path):
        try:
            super().read(path)
            for node in self.root.findall(TAG_INTERNAL):
                secret = node.find(TAG_SECRET)
                if None is not secret:
                    self.secret = secret.text.strip()
                password = node.find(TAG_PHASH)
                if None is not password:
                    if None is password.text:
                        self.passwd = ''
                    else:
                        self.passwd = password.text.strip()
        except FileNotFoundError as ex:
            self.write(path)
            self.read(path)

    def write(self,path):
        with open(path,'wt') as fd:
            self.write_prefix(fd)
            fd.write('<' + TAG_INTERNAL + '>\n')
            fd.write('<' + TAG_SECRET + '>' + str(self.secret) + '</' + TAG_SECRET + '>\n')
            fd.write('<' + TAG_PHASH + '>' + str(self.passwd) + '</' + TAG_PHASH + '>\n')
            fd.write('</' + TAG_INTERNAL + '>\n')
            self.write_suffix(fd)

