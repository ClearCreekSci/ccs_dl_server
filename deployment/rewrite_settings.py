
import bcrypt
import dlsettings


SETTINGS_NAME = 'settings.cfg'


def hash_value(v):
    # Match default flask_bcrypt values
    rounds = 12
    prefix = '2b'.encode('utf-8')
    salt = bcrypt.gensalt(rounds,prefix)
    pw = v.encode('utf-8')
    return bcrypt.hashpw(pw,salt)


if '__main__' == __name__:
    settings = dlsettings.Settings()
    settings.set_hash_function(hash_value)
    settings.read(SETTINGS_NAME)
    settings.write(SETTINGS_NAME)

