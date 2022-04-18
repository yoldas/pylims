import inspect
import unittest

from pylims.process import Methods


class MethodsTest(unittest.TestCase):

    def test_abstract(self):
        instance = Methods()
        names = [x for x in dir(instance) if not x.startswith('__')]
        for name in names:
            method = getattr(instance, name)
            sig = inspect.signature(method)
            nargs = len(sig.parameters)
            args = tuple() + (None,) * nargs
            # Methods must raise NotImplementedError to enforce
            # implementation in subclasses, for example Process.
            with self.assertRaises(NotImplementedError):
                method(*args)
