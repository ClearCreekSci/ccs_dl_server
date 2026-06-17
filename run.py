'''
    run.py
    Starts the CCS Data Server (Flask application) 

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

from databrowser import app
from databrowser import bcrypt
from databrowser import cfg
from databrowser import defaultpassword
from databrowser import configpath 
from databrowser.logging import initlog 
from databrowser.logging import logmsg 

if '__main__' == __name__:
    initlog(cfg)
    if len(cfg.passwd) == 0:
        logmsg(cfg,__name__,'Writing default password')
        cfg.passwd = bcrypt.generate_password_hash(defaultpassword).decode('utf-8')
        cfg.write(configpath)
    logmsg(cfg,__name__,'Starting app')
    app.run(debug=False,host='0.0.0.0',port=5000)


