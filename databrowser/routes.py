'''
    routes.py
    Web routes for the CCS Data Server

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
import pathlib
import zipfile

from io import BytesIO

from datetime import datetime

from flask import render_template
from flask import flash
from flask import redirect
from flask import url_for
from flask import request
from flask import send_file
from flask_login import login_user
from flask_login import logout_user
from flask_login import current_user
from flask_login import login_required


from databrowser import app
from databrowser import cfg
from databrowser import mnfst
 
from databrowser import fbcrypt
from databrowser.models import Admin
from databrowser.logging import logmsg

from databrowser import ccs_base

from databrowser import forms

DOWNLOAD_SUFFIX                      = '_ccs_logger.zip'

def get_timestamp_from_path(path):
    parts = path.split('_')
    return ''.join(parts[0:2])

def get_event_from_path(path):
    parts = path.split('_')
    return '_'.join(parts[2:4])

def get_event_path_from_list(evnt,lst):
    rv = None
    for v in lst:
        if evnt in v:
            rv = v
            break
    return rv

def get_csv_events_from_filenames(path):
    rv = list()
    files = os.listdir(path)
    for f in files:
        event = get_event_from_path(f)
        if False == (event in rv):
            rv.append(event)
    return rv

def get_most_recent_file_paths(events):
    rv = list()
    most_recent = 0
    files = os.listdir(events)
    for f in files:
        full_path = os.path.join(events,f)
        parts = f.split('_')
        event = get_event_from_path(f)
        new_ts = get_timestamp_from_path(f)
        most_recent_path = get_event_path_from_list(event,rv)

        if None is most_recent_path:
            rv.append(full_path)
        else:
            most_recent_ts = get_timestamp_from_path(most_recent_path)
            if new_ts > most_recent_ts:
                try:
                    idx = rv.index(most_recent_path)
                    rv[idx] = full_path
                except ValueError:
                    pass
    return rv

def parse_most_recent():
    rv = list()
    events = get_csv_events_from_filenames(cfg.csv_dir)
    print('[parse_most_recent] events: ' + str(events))
    datafiles = get_most_recent_file_paths(cfg.csv_dir)
    print('[parse_most_recent] datafiles: ' + str(datafiles))
    for file in datafiles:
        header = None
        data = None
        if None is not file:
            with open(file,'r') as fd:
                for line in fd:
                    if None is header:
                        header = line
                    data = line
            if None is not header and None is not data:
                header_parts = header.split(',')
                data_parts = data.split(',')
                if len(header_parts) == len(data_parts):
                    idx = 0
                    for hp in header_parts:
                        hp = hp.strip()
                        label = ccs_base.getName(hp)
                        value = ccs_base.getValue(hp,data_parts[idx],cfg.use_metric)
                        value += ' ' + ccs_base.getUnits(hp,cfg.use_metric)
                        rv.append((label,value))
                        idx += 1
    return rv

# Returns a list of files
# Each file contains a list of tuples
#    The first tuple contains the header information
#        The header information is a list of UUIDs
#    The rest of the tuples contain data information
#        The data information is a list of data points
def parse_data():
    rv = list()
    data = None
    files = os.listdir(cfg.csv_dir)
    files.sort()

    for f in files:
        file_list = list()
        header = None
        datafile = os.path.join(cfg.csv_dir,f)
        with open(datafile,'r') as fd:
            for line in fd:
                if None is header:
                    header = list()
                    cooked_header = list()
                    parts = line.split(',')
                    for part in parts:
                        part = part.strip()
                        header.append(part)
                        name = ccs_base.getName(part)
                        if ccs_base.UNKNOWN == name:
                            cooked_header.append(part)
                        else:
                            s = name + ' ' + ccs_base.getUnits(part,cfg.use_metric)
                            cooked_header.append(s)
                    file_list.append(cooked_header)
                else:
                    parts = line.split(',')
                    data = list()
                    didx = 0
                    for part in parts:
                        part = part.strip()
                        name = ccs_base.getName(header[didx])
                        if name == ccs_base.UNKNOWN: 
                            data.append(part)
                        else:
                            v = ccs_base.getValue(header[didx],part,cfg.use_metric)
                            data.append(str(v))
                        didx += 1
                    file_list.append(data)
        rv.append(file_list)
    return rv

def download_csv_files(entries):
    global cfg

    if 0 == len(entries):
        return render_template('csv.html',title='Download CSV Files',files=os.listdir(cfg.csv_dir))
    ts = datetime.now()
    dst = ts.strftime('%Y%m%d%H%M%S') + DOWNLOAD_SUFFIX
    with zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED) as zippy: 
        for entry in entries:
            path = os.path.join(cfg.csv_dir,entry)
            with open(path,'rt') as fd:
                data = ''
                header = list()
                for line in fd:
                    parts = line.split(',')
                    if len(data) == 0:
                        idx = 0
                        for part in parts:
                            part = part.strip()
                            s = ''
                            header.append(part)   
                            name = ccs_base.getName(part)
                            if ccs_base.UNKNOWN == name:
                                if 0 == idx:
                                    s = part
                                else:
                                    s = ',' + part
                            else:
                                units = ccs_base.getUnits(part,cfg.use_metric)
                                if 0 == idx:
                                    s = name + ' ' + units
                                else:
                                    s = ',' + name + ' ' + units
                            data += s
                            idx += 1
                        data += '\n'
                    else:
                        idx = 0
                        for part in parts:
                            s = ''
                            part = part.strip()
                            name = ccs_base.getName(header[idx])
                            if 0 == idx:
                                if ccs_base.UNKNOWN == name:
                                    s = part
                                else:
                                    s = ccs_base.getValue(header[idx],part,cfg.use_metric)
                            else:
                                if ccs_base.UNKNOWN == name:
                                    s = ',' + part
                                else:
                                    s = ',' +  ccs_base.getValue(header[idx],part,cfg.use_metric)
                            data += s
                            idx += 1
                        data += '\n'
            if None is not data:
                zippy.writestr(os.path.basename(path),data,compress_type=zipfile.ZIP_DEFLATED)
    return send_file(dst,mimetype='zip',download_name=dst,as_attachment=True) 

def delete_csv_files(entries):
    for entry in entries:
        path = os.path.join(cfg.csv_dir,entry)
        if os.path.exists(path):
            pathlib.Path.unlink(path)

def remove_leftovers():
    # When we create the zip files for downloads, they are created in the home 
    # directory and never cleaned up. Look for them here and try to delete 
    # them...
    files = os.listdir('.')
    for file in files:
        if file.endswith('.zip'):
            pathlib.Path.unlink(file)

# We have moved configuration of frequency and package rate to the data logger
# We no longer use two "package" functions here, but may want to move them to 
# the data logger configuration application when it is written...
def calculate_package_rate(index,frequency):
    rv = 0
    if forms.PKG_15_MIN == index:
        rv = int(15/frequency)
    elif forms.PKG_30_MIN == index:
        rv = int(30/frequency)
    elif forms.PKG_HOURLY == index:
        rv = int(60/frequency)
    elif forms.PKG_DAILY == index:
        rv = int(1440/frequency)
    elif forms.PKG_WEEKLY == index:
        rv = int(10080/frequency)
    else:
        print('[calculate_package_rate] Unrecognized index: ' + str(index))
    return rv

def calculate_package_index(package_rate,frequency):
    rv = 0
    x = frequency * package_rate

    if x <= 15:
        rv = forms.PKG_15_MIN
    elif x <= 30:
        rv = forms.PKG_30_MIN 
    elif x <= 60:
        rv = forms.PKG_HOURLY 
    elif x <= 1440:
        rv = forms.PKG_DAILY 
    else:
        rv = forms.PKG_WEEKLY 
    return rv

@app.route('/')
@app.route('/home')
def home():
    d = parse_most_recent()
    if len(d) > 0:
        return render_template('home.html',title='Home',data=d)
    else:
        return render_template('home.html',title='Home',data=None)

@app.route('/history')
def history():
    d = parse_data()
    if len(d) > 0:
        return render_template('history.html',title='History',data=d)
    else:
        return render_template('home.html',title='Home',data=None)

def get_photos():
    global cfg
    rv = list()
    # FIXME:
    files = os.listdir(cfg.photos_dir)
    for f in files:
       target = os.path.join(cfg.photos_dir,f)
       cwd = os.getcwd()
       link = os.path.join(cwd,'static/photos')
       link = os.path.join(link,f)
       if False == os.path.exists(link) or False == os.path.islink(link):
           os.symlink(target,link)
       rv.append((f,'photos/' + f,target))
    return rv

def download_photos(entries):
    global cfg

    if 0 == len(entries):
        return render_template('photos.html',title='Photos',data=get_photos())
    ts = datetime.now()
    dst = ts.strftime('%Y%m%d%H%M%S') + DOWNLOAD_SUFFIX
    with zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED) as zippy: 
        for entry in entries:
            data = None
            path = os.path.join(cfg.photos_dir,entry)
            with open(path,'rb') as fd:
                data = fd.read()
            if None is not data:
                zippy.writestr(os.path.basename(path),data,compress_type=zipfile.ZIP_DEFLATED)
    return send_file(dst,mimetype='zip',download_name=dst,as_attachment=True) 

@app.route('/photos',methods=['GET','POST'])
@login_required
def photos():
    if 'POST' == request.method:
        entries = request.form.getlist('entry') 
        file_entries = list()
        for entry in entries:
            file_entries.append(os.path.basename(entry))
        if 'download' == request.form['action']:
            return download_photos(file_entries)
        elif 'delete' == request.form['action']:
            delete_photos(file_entries)
    v = get_photos()
    return render_template('photos.html',title='Photos',data=v)

def delete_photos(entries):
    for entry in entries:
        # Delete the link to the photo file
        cwd = os.getcwd()
        link = os.path.join(cwd,'static/photos')
        link = os.path.join(link,entry)
        print('to delete: ' + link)
        if os.path.exists(link):
            print('deleting: ' + link)
            pathlib.Path.unlink(link)
        # Delete the photo file
        path = os.path.join(cfg.photos_dir,entry)
        print('to delete: ' + path)
        if os.path.exists(path):
            print('deleting: ' + path)
            pathlib.Path.unlink(path)


@app.route('/graphs')
def graphs():
    return render_template('graphs.html',title='Graphs')

@app.route('/csv',methods=['GET','POST'])
@login_required
def csv():
    remove_leftovers()
    if 'POST' == request.method:
        entries = request.form.getlist('entry')
        if 'download' == request.form['action']:
            return download_csv_files(entries)
        elif 'delete' == request.form['action']:
            delete_csv_files(entries)
    return render_template('csv.html',title='Download',files=os.listdir(cfg.csv_dir))

@app.route('/settings',methods=['GET','POST'])
@login_required
def settings():
    #global cfg
    form = forms.SettingsForm()
    #form.errors = list()
    if form.validate_on_submit():
        if form.units.data == forms.METRIC_VALUE:
            cfg.use_metric = True
        else:
            cfg.use_metric = False
        if len(form.password.data) > 0:
            cfg.passwd = fbcrypt.generate_password_hash(form.password.data).decode('utf-8')
            logout_user()
        cfg.write()
        return redirect(url_for('home'))
    else:
        if cfg.use_metric:
            form.units.default = forms.METRIC_VALUE
        else:
            form.units.default = forms.IMPERIAL_VALUE
        form.process()
    return render_template('settings.html',title='Settings',form=form)

@app.route('/about')
def about():
    if None == mnfst:
        return render_template('about.html',version='unknown',commit='unknown',title='About')
    else:
        return render_template('about.html',version=mnfst.version,commit=mnfst.commit,title='About')

#FIXME: error checking needs to be done...
@app.route('/downloadcsv/<name>')
@login_required
def downloadcsv(name):
    data = None
    path = os.path.join(cfg.csv_dir,name)
    with open(path,'rb') as fd:
        data = fd.read()
    return send_file(BytesIO(data),download_name=name,as_attachment=True) 


@app.route('/login',methods=['GET','POST'])
def login():
    #global cfg
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = forms.LoginForm()
    if form.validate_on_submit():
        password = form.password.data
        user = Admin()
        if fbcrypt.check_password_hash(cfg.passwd,password):
            login_user(user,True)
            next_page = request.args.get('next')
            if None is not next_page:
                return redirect(next_page)
            else:
                return redirect(url_for('home'))
    return render_template('login.html',title='Login',form=form)


