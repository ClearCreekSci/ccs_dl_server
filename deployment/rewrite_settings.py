
import bcrypt
import dlsettings


SETTINGS_NAME = 'settings.cfg'



if '__main__' == '__file__':
    settings = dlsettings.Settings()
    settings.read(SETTINGS_NAME)
    settings.write(SETTINGS_NAME)

