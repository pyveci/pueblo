import unittest


class ExampleTest(unittest.TestCase):
    """
    Verify `ngr test` invokes `python -m unittest` when instructed to.
    """

    def test_foobar(self):
        assert 42 == 42
