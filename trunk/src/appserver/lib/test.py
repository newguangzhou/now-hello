#!/usr/bin/python
import sys
sys.path.append("../")
from lib.config import *
from lib import utils
from lib import pet_mongo_dao
from lib.pet_dao import PetDAO
from tornado import ioloop, gen
from configs.mongo_config import MongoConfig2

@gen.coroutine
def testfun(uid):
        conf = loadJsonConfig("../configs/config.json")
        mongo_conf = MongoConfig2(conf["mongodb"])
        pet_dao=PetDAO.new(mongo_meta=mongo_conf.pet_mongo_meta)
        count = yield pet_dao.get_pet_count(uid)
        print "count:",count

if __name__ == '__main__':
    print "main", sys.argv[1]
    try:
        ioloop.IOLoop.instance().run_sync(lambda: testfun(int(sys.argv[1])))
    except Exception,e :
        print e
