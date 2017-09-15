import unittest
from mailchimp_subscriber import (
    load_conf, load_users  # , process_users
)


class TestMailchimpSubscriber(unittest.TestCase):

    def test_load_conf(self):
        list_id, mc_user, mc_key = load_conf('tests/test.conf')
        self.assertEqual(list_id, '1234')
        self.assertEqual(mc_user, 'ctl')
        self.assertEqual(mc_key, '123xyz')

    def test_load_users(self):
        test_users = {
            'alice@columbia.edu',
            'bob@columbia.edu',
            'nick@columbia.edu',
            'joe@columbia.edu'
        }
        loaded_users = load_users('tests/test-user-list.txt')
        self.assertEqual(test_users, loaded_users)

    def test_process_users(self):
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
