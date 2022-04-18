import unittest

from pylims import config
from pylims.dba import DataSet
from pylims.process import Process


class ProcessTest(unittest.TestCase):

    def test_default_conf(self):
        process = Process()
        self.assertDictEqual(config.database, process.get_dataset().get_conf())

    def test_process_init(self):
        conf = config.test_database
        dataset = DataSet(conf)
        process = Process(dataset)
        self.assertDictEqual(conf, process.get_dataset().get_conf())
