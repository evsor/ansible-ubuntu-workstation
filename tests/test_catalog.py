"""Unit tests for the `managed` filter. No privileges needed:

    python3 -m unittest discover tests
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'filter_plugins'))

from ansible.errors import AnsibleFilterError  # noqa: E402
from catalog import managed  # noqa: E402


def ws(profile='personal', state='present', remove_user_data=False):
    return {'profile': profile, 'profiles': ['personal', 'work'],
            'state': state, 'remove_user_data': remove_user_data}


def states(catalog, workstation, only=None):
    return {e['name']: e['state'] for e in managed(catalog, workstation, only)}


CATALOG = [
    {'name': 'everywhere'},
    {'name': 'work-only', 'profiles': {'personal': 'absent'}},
    {'name': 'work-only-untouched', 'profiles': {'personal': 'ignore'}},
    {'name': 'removed-everywhere', 'profiles': {'personal': 'absent', 'work': 'absent'}},
    {'name': 'userdata', 'user_data': True},
]


class Converge(unittest.TestCase):
    def test_personal(self):
        self.assertEqual(states(CATALOG, ws('personal')), {
            'everywhere': 'present',
            'work-only': 'absent',
            'removed-everywhere': 'absent',
            'userdata': 'present',
        })

    def test_work(self):
        self.assertEqual(states(CATALOG, ws('work')), {
            'everywhere': 'present',
            'work-only': 'present',
            'work-only-untouched': 'present',
            'removed-everywhere': 'absent',
            'userdata': 'present',
        })

    def test_only_filters_by_state(self):
        self.assertEqual(set(states(CATALOG, ws('personal'), 'absent')),
                         {'work-only', 'removed-everywhere'})

    def test_entries_are_copies(self):
        catalog = [{'name': 'x'}]
        managed(catalog, ws())
        self.assertNotIn('state', catalog[0])


class Teardown(unittest.TestCase):
    def test_everything_absent_except_ignored_and_user_data(self):
        self.assertEqual(states(CATALOG, ws('personal', 'absent')), {
            'everywhere': 'absent',
            'work-only': 'absent',
            'removed-everywhere': 'absent',
        })

    def test_user_data_removed_only_when_asked(self):
        got = states(CATALOG, ws('personal', 'absent', remove_user_data=True))
        self.assertEqual(got['userdata'], 'absent')

    def test_user_data_flag_accepts_strings(self):
        # -e remove_user_data=false arrives as a string
        got = states(CATALOG, ws('personal', 'absent', remove_user_data='false'))
        self.assertNotIn('userdata', got)


class Protection(unittest.TestCase):
    def test_user_data_kept_when_profile_says_absent(self):
        catalog = [{'name': 'cache', 'user_data': True, 'profiles': {'personal': 'absent'}}]
        self.assertEqual(states(catalog, ws('personal')), {})
        self.assertEqual(states(catalog, ws('personal', remove_user_data=True)), {'cache': 'absent'})


class Validation(unittest.TestCase):
    def assertRejects(self, catalog, message):
        with self.assertRaisesRegex(AnsibleFilterError, message):
            managed(catalog, ws())

    def test_old_list_format(self):
        self.assertRejects([{'name': 'x', 'profiles': ['personal', 'work']}], 'must be a mapping')

    def test_unknown_profile(self):
        self.assertRejects([{'name': 'x', 'profiles': {'persnal': 'absent'}}], 'unknown profile')

    def test_bad_state(self):
        self.assertRejects([{'name': 'x', 'profiles': {'personal': 'removed'}}], 'must be one of')

    def test_state_key_reserved(self):
        self.assertRejects([{'name': 'x', 'state': 'absent'}], "must not set 'state'")

    def test_bad_only(self):
        with self.assertRaisesRegex(AnsibleFilterError, "'only'"):
            managed([], ws(), 'ignore')


if __name__ == '__main__':
    unittest.main()
