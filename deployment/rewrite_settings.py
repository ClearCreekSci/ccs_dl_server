
from databrowser import bcrypt
import dlsettings


SETTINGS_NAME = 'settings.cfg'


def hash_value(v):
    return bcrypt.generate_password_hash(v).decode('utf-8')


if '__main__' == __name__:
    settings = dlsettings.Settings()
    settings.set_hash_function(hash_value)
    settings.read(SETTINGS_NAME)
    settings.write(SETTINGS_NAME)

