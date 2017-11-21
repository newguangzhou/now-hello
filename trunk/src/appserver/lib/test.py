#!/usr/bin/python
import sys
sys.path.append("../")
#from lib import sys
from lib import config
from lib import utils
from lib import pet_mongo_dao

def testfun():
        conf = loadJsonConfig("../config/config.json")
        mongo_conf = MongoConfig2(conf["mongodb"])
        pet_dao=PetDAO.new(mongo_meta=mongo_conf.pet_mongo_meta)
        tornado.ioloop.IOLoop.instance().start()
        count = yield pet_dao.get_pet_count()
        return count
if __name__ == '__main__':
    print "main"
    try:
        print "fun return:",testfun()
    except Exception,e :
        print e
