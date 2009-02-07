"""
Utilities for testing tests
"""
import difflib
from pprint import pformat

class DiffTestCaseMixin(object):

    def get_diff_msg(self, first, second,
                     fromfile='First', tofile='Second'):
        """Return a unified diff between first and second."""
        # Force inputs to iterables for diffing.
        # use pformat instead of str or repr to output dicts and such
        # in a stable order for comparison.
        if isinstance(first, (tuple, list, dict)):
            first = [pformat(d) for d in first]
        else:
            first = [pformat(first)]

        if isinstance(second, (tuple, list, dict)):
            second = [pformat(d) for d in second]
        else:
            second = [pformat(second)]

        diff = difflib.unified_diff(
            first, second, fromfile=fromfile, tofile=tofile)
        # Add line endings.
        return '\n' + ''.join([d + '\n' for d in diff])

    def failIfDiff(self, first, second, fromfile='First', tofile='Second'):
        """If not first == second, fail with a unified diff."""
        if not first == second:
            msg = self.get_diff_msg(first, second, fromfile, tofile)
            raise self.failureException, msg

    assertNoDiff = failIfDiff

