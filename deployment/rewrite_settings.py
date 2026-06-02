
import bcrypt
import dlsettings


SETTINGS_NAME = 'settings.cfg'


def hash_value(v):
    salt = bcrypt.gensalt()
    pw = v.encode('utf-8')
    return bcrypt.hashpw(pw,salt)


if '__main__' == __name__:
    settings = dlsettings.Settings()
    settings.set_hash_function(hash_value)
    settings.read(SETTINGS_NAME)
    settings.write(SETTINGS_NAME)

