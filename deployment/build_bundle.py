# build_bundle.py output the full path of the install file created.
# If it fails to do so, the caller will assume an error

import argparse
import dlsettings
import os
import requests
import subprocess
import stat
import sys
import zipfile

import datetime as dt
import xml.etree.ElementTree as et

from glob import glob

DEFAULT_VERSION         = '1'
DEFAULT_PREFIX          = 'ccs_data_server'

MANIFEST_NAME           = 'manifest.xml'
ZIP_SUFFIX              = '.zip'
SCRIPT_SUFFIX           = '.sh'

SCRIPT_LEN_REPLACE_STR  = '<***>'

TAG_BASE                = 'base'
TAG_INTERNAL            = 'internal'
TAG_LOG                 = 'log'
TAG_NAME                = 'name'
TAG_PASSWORD            = 'pword'
TAG_PATHS               = 'paths'
TAG_ROOT                = 'ccs-config'
TAG_SECRET              = 'sec'
TAG_VERSION             = 'version'

TOPLEVEL_DST            = '/opt/ccs'
SITE_DIR                = 'site-packages'
DATASERVER_DST          = TOPLEVEL_DST + '/DataServer'
SYSTEMD_SERVICE_DST     = '/etc/systemd/system'
UNZIP_DST               = './unzip'
SETTINGS_FILE_NAME      = 'settings.cfg'
SERVICE_FILE_NAME       = './system/ccsdataserver.service'
VENV_NAME               = 'venv'

class InvalidSettingsFileException(Exception):
    pass

def get_settings(path):
    rv = None
    if os.path.exists(path):
        try:
            rv = dlsettings.Settings()
            rv.read(path)
        except Exception as ex:
            rv = None
            sys.stderr.write('Exception reading settings file: ' + str(ex) + '\n')
    else:
        sys.stderr.write("Couldn't find settings file: " + str(path) + '\n')
    return rv

def add_glob_to_zip(zf,src,dst,glob_str):
    files = glob(os.path.join(src,glob_str))
    for f in files:
        basename = os.path.basename(f)
        dst_path = os.path.join(dst,basename)
        zf.write(f,dst_path)

# FIXME: WHAT ABOUT UNINSTALL?
def create_base_script(zip_size,settings):
    rv = ''
    # Create the base script
    rv = '#!/usr/bin/bash\n'
    rv += 'TOPLEVEL_DST="' + settings.paths[TAG_BASE] + '"\n'
    rv += 'VENV_DST="${TOPLEVEL_DST}/' + VENV_NAME + '"\n'
    rv += 'VENV_LIB_DIR="${VENV_DST}/lib"\n'

    rv += 'if [ ! $EUID -eq 0 ]; then\n'
    rv += '    echo "Please run this install script as root"\n'
    rv += '    exit\n'
    rv += 'fi\n'
    rv += '# Make sure we can connect to the internets\n'
    rv += 'ping -c 1 google.com > /dev/null 2>&1\n'
    rv += 'if [ $? -ne 0 ]; then\n'
    rv += '    echo "Unable to connect to internet to download required Python files. Installation failed."\n'
    rv += '    exit\n'
    rv += 'fi\n'
    rv += 'echo "Extracting files..."\n'
    rv += 'rm -rf ' + UNZIP_DST + '\n'
    rv += 'mkdir ' + UNZIP_DST + '\n'
    rv += 'ME=$(basename "$0")\n'
        # Extract the zip file from the install script
    rv += 'dd bs=1 if="$ME" of=script.zip skip=' + SCRIPT_LEN_REPLACE_STR + ' count=' + str(zip_size) + '\n'

    rv += 'unzip -q -d ' + UNZIP_DST + ' script.zip\n'

    rv += '# Setup up the data server files...\n'
    for key in settings.paths.keys():
        rv += 'mkdir -p ' + settings.paths[key] + '\n'

    rv += '# Setup up the python virtual environment...\n'
    rv += 'echo "Creating Python virtual environment at ${VENV_DST}. This may take some time..."\n'
    rv += 'python -m venv "${VENV_DST}"\n'
    rv += 'echo "Installing required Python packages..."\n'
    rv += 'source "${VENV_DST}/bin/activate"\n'
    rv += 'pip install pip --upgrade\n'
    rv += 'pip install pip setuptools wheel\n'
    rv += 'UN=`uname -a`\n'
    rv += 'if [[ $UN == *"armv6l"* ]]; then\n'
    rv += '    pip install "' + UNZIP_DST + '/system/bcrypt-5.0.0-cp313-cp313-linux_armv6l.whl"\n'
    rv += 'fi\n'

    rv += 'if [[ $UN == *"armv7l"* ]]; then\n'
    rv += '    cp "' + UNZIP_DST + '/system/bcrypt-5.0.0-cp313-cp313-linux_arm6l.whl" "' + UNZIP_DST + '/system/bcrypt-5.0.0-cp313-cp313-linux_arm7l.whl"\n'
    rv += '    pip install "' + UNZIP_DST + '/system/bcrypt-5.0.0-cp313-cp313-linux_armv7l.whl"\n'
    rv += 'fi\n'

    rv += 'pip install -r ' + UNZIP_DST + '/requirements.txt\n'

    # FIXME: DO WE NEED THIS?
    #rv += 'for entry in "${VENV_LIB_DIR}"/*\n'
    #rv += 'do\n'
    #rv += '    PYTHON_VER=`basename "${entry}"`\n'
    #rv += 'done\n'

    rv += 'pushd ' + UNZIP_DST + '\n'
    rv += 'python rewrite_settings.py\n'
    rv += 'popd\n'

    # We can deactive the virtual environment, once we have run rewrite_settings.py 
    rv += 'deactivate\n'

    rv += '# Setup up the DataServer files...\n'
    rv += 'echo "Copying Weather Data Server files..."\n'
    rv += 'cp ' + UNZIP_DST + '/run.py ' + DATASERVER_DST + '\n'
    rv += 'cp -r  ' + UNZIP_DST + '/manifest.xml ' + DATASERVER_DST + '\n'
    rv += 'cp -r  ' + UNZIP_DST + '/settings.cfg ' + DATASERVER_DST + '\n'
    rv += 'cp -r  ' + UNZIP_DST + '/ccs_dlconfig ' + DATASERVER_DST + '\n'
    rv += 'cp -r  ' + UNZIP_DST + '/databrowser ' + DATASERVER_DST + '\n'
    rv += 'cp -r  ' + UNZIP_DST + '/static ' + DATASERVER_DST + '\n'
    rv += 'cp -r  ' + UNZIP_DST + '/templates ' + DATASERVER_DST + '\n'
    rv += 'cp ' + UNZIP_DST + '/system/ccsdataserver.service ' + SYSTEMD_SERVICE_DST + '\n'

    rv += 'echo "Creating ccsdataserver systemd service..."\n'
    rv += 'systemctl daemon-reload\n'
    rv += 'systemctl enable ccsdataserver.service\n'
    rv += 'systemctl start ccsdataserver.service\n'

    #rv += 'rm -rf ' + UNZIP_DST + '\n'
    #rv += 'rm -rf script.zip\n'
    rv += 'echo "Installation completed succesfully."\n'
    rv += 'exit\n'
    return rv

def run(args):
    global DATASERVER_DST
    commit = ''
    prefix = DEFAULT_PREFIX
    version = DEFAULT_VERSION
    if None is not args.prefix:
        prefix = args.prefix
    if None is not args.commit:
        commit = args.commit
    else:
        # Popen call example...
        # Source - https://stackoverflow.com/a/92395
        # Posted by Eli Courtwright, modified by community. See post 'Timeline' for change history
        # Retrieved 2026-05-22, License - CC BY-SA 4.0
        commit = subprocess.Popen('git rev-parse HEAD', shell=True, stdout=subprocess.PIPE).stdout.read()
        commit = str(commit).strip()

    settings = get_settings(SETTINGS_FILE_NAME)
    if None is settings:
        sys.stderr.write('[!] settings is NULL\n')
        return

    if TAG_BASE in settings.paths.keys():
        DATASERVER_DST = settings.paths[TAG_BASE]
    else:
        sys.stderr.write('[!] Base path not found\n')
        return

    if settings.version is not None:
        version = settings.version

    # Create the manifest
    with open(MANIFEST_NAME,'wt') as fd:
        fd.write('<manifest>\n')
        current_time = dt.datetime.now(dt.timezone.utc).isoformat(timespec='minutes')
        fd.write('<time>' + current_time + '</time>\n')
        fd.write('<commit>' + commit + '</commit>\n')
        fd.write('<version>' + str(version) + '</version>\n')
        fd.write('</manifest>\n')

    # Create the systemd service file
    with open(SERVICE_FILE_NAME,'wt') as fd:
        fd.write('[Unit]\n')
        fd.write('Description=Clear Creek Scientific Data Server\n')
        fd.write('StartLimitIntervalSec=300\n')
        fd.write('#StartLimitBurst=5\n')
        fd.write('[Service]\n')
        fd.write('WorkingDirectory=' + settings.paths[TAG_BASE] + '\n')
        s = 'Environment="CCS_DS_MAN_PATH=' + settings.paths[TAG_BASE] + '/' + MANIFEST_NAME + '"\n'
        fd.write(s)
        s = 'Environment="CCS_DS_CFG_PATH=' + settings.paths[TAG_BASE] + '/' + SETTINGS_FILE_NAME + '"\n'
        fd.write(s)
        s = 'ExecStart='
        venv_dir = settings.paths[TAG_BASE] + '/' + VENV_NAME
        s += venv_dir + '/bin/python3'
        s += ' ' + settings.paths[TAG_BASE] + '/run.py\n'
        fd.write(s)
        fd.write('Restart=on-failure\n')
        fd.write('RestartSec=10s\n')
        fd.write('[Install]\n')
        fd.write('WantedBy=default.target\n')

    # Create the zip file
    zip_name = str(prefix) + '_v' + str(version) + ZIP_SUFFIX
    with zipfile.ZipFile(zip_name,mode='w') as zf:
        zf.write('settings.cfg','settings.cfg')
        zf.write('dlsettings.py','dlsettings.py')
        zf.write('rewrite_settings.py','rewrite_settings.py')
        zf.write('manifest.xml','manifest.xml')
        zf.write('../run.py','./run.py')
        zf.write('../requirements.txt','./requirements.txt')
        zf.mkdir('databrowser')
        add_glob_to_zip(zf,'../databrowser','./databrowser','*')
        add_glob_to_zip(zf,'../databrowser/ccs_base','./databrowser/ccs_base','*')
        zf.mkdir('ccs_dlconfig')
        add_glob_to_zip(zf,'../ccs_dlconfig','./ccs_dlconfig','*.py')
        zf.mkdir('static')
        add_glob_to_zip(zf,'../static','./static','*')
        zf.mkdir('templates')
        add_glob_to_zip(zf,'../templates','./templates','*')
        zf.mkdir('system')
        add_glob_to_zip(zf,'./system','./system','*')

    zip_size = os.path.getsize(zip_name)

    script = create_base_script(zip_size,settings)

    base_len = len(script)
    idx = script.find(SCRIPT_LEN_REPLACE_STR)
    if idx > 0:
        x = f'{base_len:05d}'
        parts = script.split(SCRIPT_LEN_REPLACE_STR)
        if 2 == len(parts):
            script = parts[0] + x + parts[1]

    # Concatenate the base script and the zip file
    read_buf = ''
    install_script_name = str(prefix) + '_install_v' + str(version) + SCRIPT_SUFFIX
    with open(install_script_name,'wb') as fd:
        script = script.encode('utf-8')
        fd.write(script)
        with open(zip_name,'rb') as zfd:
            zip_buf = zfd.read()
        fd.write(zip_buf)
    os.chmod(install_script_name,stat.S_IRWXU|stat.S_IRGRP|stat.S_IRGRP|stat.S_IROTH)

    cwd = os.getcwd()
    script_path = os.path.join(cwd,install_script_name)
    sys.stdout.write(script_path)
    

if '__main__' == __name__:
    parser = argparse.ArgumentParser()
    # We ignore the version that is passed in
    parser.add_argument('-v','--version',help='version string')
    parser.add_argument('-c','--commit',help='commit string')
    parser.add_argument('-p','--prefix',help='prefix string')
    args = parser.parse_args()
    run(args)



