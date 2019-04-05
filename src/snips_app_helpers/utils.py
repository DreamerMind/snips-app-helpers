

class BaseObj(object):
    def __repr__(self):
        return self.__str__()

    def __unicode__(self):
        return self.__str__()
