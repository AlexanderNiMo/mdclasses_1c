import unittest

from .test_module import TestModuleParser
from .tests_configuration import TestConfiguration

__all__ = [
    'TestModuleParser',
    'TestConfiguration',
]

if __name__ == '__main__':
    unittest.main()
