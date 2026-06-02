'''
    __init__.py
    Package file for the CCS Data Server databrowser

    Copyright (C) 2025 Clear Creek Scientific

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
'''

import os

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

from ccs_dlconfig import manifest

app = Flask('DataBrowser')

configpath = os.environ['CCS_DS_CFG_PATH']
manifestpath = os.environ['CCS_DS_MAN_PATH']
defaultpassword = 'MeasureYourWorld'

from databrowser import dbconfig
cfg = dbconfig.DBSettings()
cfg.read(configpath)

try:
    mnfst = manifest.Manifest(manifestpath)
except FileNotFoundError:
    mnfst = None

# bcrypt was here
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

app.config['SECRET_KEY'] = cfg.secret

bcrypt = Bcrypt(app)

from databrowser import routes
