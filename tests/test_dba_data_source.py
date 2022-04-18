import inspect
import unittest

from pylims.dba import DataSource


class DataSourceTest(unittest.TestCase):

    def test_abstract(self):
        ds = DataSource()
        names = [x for x in dir(ds) if not x.startswith('__')]
        for name in names:
            method = getattr(ds, name)
            sig = inspect.signature(method)
            nargs = len(sig.parameters)
            args = tuple() + (None,) * nargs
            # Test that methods raise NotImplementedError
            # to enforce implementation in subclasses.
            with self.assertRaises(NotImplementedError):
                method(*args)
