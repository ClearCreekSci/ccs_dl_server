import xml.etree.ElementTree as et

XML_PREFIX         = '<?xml version="1.0" encoding="UTF-8"?>'
XML_VERSION        = '2'

ATTRIB_VERSION     = 'version'

TAG_BASE           = 'base'
TAG_CSV            = 'csv'
TAG_INTERNAL       = 'internal'
TAG_LOG            = 'log'
TAG_PASSWORD       = 'password'
TAG_PATHS          = 'paths'
TAG_PHASH          = 'phash'
TAG_PHOTOS         = 'photos'
TAG_ROOT           = 'ccs-config'
TAG_SECRET         = 'secret'
TAG_VERSION        = 'version'
TAG_VIDEOS         = 'videos'

DEFAULT_VERSION    = 1
DEFAULT_PASSWORD   = 'MeasureYourWorld'
DEFAULT_SECRET     = 'cafebeef'

class Settings(object):

    def __init__(self):
        self.paths = dict()
        self.version = DEFAULT_VERSION
        self.password = DEFAULT_PASSWORD
        self.secret = DEFAULT_SECRET
        self.phash = None
        self.hash_func = None

    def read(self,path):
        tree = et.parse(path)
        root = tree.getroot()
        if root.tag == TAG_ROOT:
            paths_node = root.find(TAG_PATHS)
            if None is not paths_node:
                for path_node in paths_node:
                    name = path_node.tag.strip()
                    value = path_node.text.strip()
                    self.paths[name] = value
            else:
                raise InvalidSettingsFileException('No paths element in settings file: ' + str(path))
            internal_node = root.find(TAG_INTERNAL)
            if None is not internal_node:
                 version_node = internal_node.find(TAG_VERSION)
                 if None is not version_node:
                     self.version = version_node.text.strip()
                 secret_node = internal_node.find(TAG_SECRET)
                 if None is not secret_node:
                     self.secret = secret_node.text.strip()
                 password_node = internal_node.find(TAG_SECRET)
                 if None is not password_node:
                     self.password = password_node.text.strip()
            else:
                raise InvalidSettingsFileException('No "internal" element in settings file: ' + str(path))
        else:
            raise InvalidSettingsFileException(str(path) + ' is not a valid settings file') 
        if False == (TAG_BASE in self.paths.keys()):
            raise InvalidSettingsFileException('No base path found in settings file: ' + str(path))

    def write(self,path):
        with open(path,'wt') as fd:
            fd.write(XML_PREFIX + '\n')
            fd.write('<' + TAG_ROOT + ' ' + ATTRIB_VERSION + '="' + str(XML_VERSION) + '">\n')
            fd.write('<' + TAG_PATHS + '>\n')
            fd.write('<' + TAG_BASE + '>')
            fd.write(str(self.paths[TAG_BASE]))
            fd.write('</' + TAG_BASE + '>\n')
            fd.write('<' + TAG_LOG + '>')
            fd.write(str(self.paths[TAG_LOG]))
            fd.write('</' + TAG_LOG + '>\n')
            fd.write('<' + TAG_CSV + '>')
            fd.write(str(self.paths[TAG_CSV]))
            fd.write('</' + TAG_CSV + '>\n')
            fd.write('<' + TAG_PHOTOS + '>')
            fd.write(str(self.paths[TAG_PHOTOS]))
            fd.write('</' + TAG_PHOTOS + '>\n')
            fd.write('<' + TAG_VIDEOS + '>')
            fd.write(str(self.paths[TAG_VIDEOS]))
            fd.write('</' + TAG_VIDEOS + '>\n')
            fd.write('</' + TAG_PATHS + '>\n')
            fd.write('<' + TAG_DATA_BROWSER + '>\n')
            fd.write('<' + TAG_VERSION + '>')
            fd.write(str(self.version))
            fd.write('</' + TAG_VERSION + '>\n')
            fd.write('<' + TAG_SECRET + '>')
            fd.write(str(self.secret))
            fd.write('</' + TAG_SECRET + '>\n')
            if None is self.phash:
                if None is not self.hash_func:
                    self.phash = self.hash_func(self.password)
            if None is not self.phash:
                fd.write('<' + TAG_PHASH + '>')
                fd.write(str(self.phash))
                fd.write('</' + TAG_PHASH + '>\n')
            fd.write('</' + TAG_DATA_BROWSER + '>\n')
            fd.write('</' + TAG_ROOT + '>\n')

    def set_hash_function(self,v):
        self.hash_func = v

    def __repr__(self):
        rv = ''
        rv += 'paths: ' + str(self.paths) + '\n'
        rv += 'version: ' + str(self.version) + '\n'
        rv += 'secret: ' + str(self.secret) + '\n'
        rv += 'password: ' + str(self.password) + '\n'
        rv += 'phash: ' + str(self.phash) + '\n'
        return rv

