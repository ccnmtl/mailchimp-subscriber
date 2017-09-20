import unittest
from unittest.mock import patch, MagicMock
from mailchimp_subscriber import (
    load_conf, load_users, process_users, validate_email,
    add_users
)


class TestMailchimpSubscriber(unittest.TestCase):
    def test_validate_email(self):
        self.assertEqual(validate_email('foo'), False)
        self.assertEqual(validate_email('foo@notld'), False)
        self.assertEqual(validate_email('foo@columbia.edu'), True)
        self.assertEqual(validate_email('foo@columbia,edu'), False)
        self.assertEqual(validate_email('foo+bar@columbia.edu'), True)

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
        # Note that test-user-list.txt has some dummy addresses thrown in
        loaded_users = load_users('tests/test-user-list.txt')
        print(loaded_users)
        self.assertEqual(test_users, loaded_users)

    @patch('mailchimp_subscriber.MailChimp')
    def test_process_users(self, mock_mail_chimp):
        # Set up mock
        mock_client = mock_mail_chimp()
        test_list = {'members': [{'email_address': 'test0@columbia.edu'},
                     {'email_address': 'test1@columbia.edu'},
                     {'email_address': 'test2@columbia.edu'},
                     {'email_address': 'test3@columbia.edu'},
                     {'email_address': 'test4@columbia.edu'},
                     {'email_address': 'test5@columbia.edu'},
                     {'email_address': 'test6@columbia.edu'},
                     {'email_address': 'test7@columbia.edu'},
                     {'email_address': 'test8@columbia.edu'},
                     {'email_address': 'test9@columbia.edu'}]}
        mock_client.lists.members.all = MagicMock(return_value=test_list)

        # Pass in entirely unique email addresses
        test_users = {
            'alice@columbia.edu',
            'bob@columbia.edu',
            'nick@columbia.edu',
            'joe@columbia.edu'
        }
        self.assertEqual(process_users(test_users, 'ctl', '123xyz', 'bar'),
                         test_users)

        # Pass in partially unique addresses
        test_users = {
            'alice@columbia.edu',
            'bob@columbia.edu',
            'test0@columbia.edu',
            'test1@columbia.edu'
        }
        test_return = {'alice@columbia.edu', 'bob@columbia.edu'}
        self.assertEqual(process_users(test_users, 'ctl', '123xyz', 'bar'),
                         test_return)

        # Pass in entirely non-unique email addresses
        test_users = {'test0@columbia.edu', 'test1@columbia.edu',
                      'test2@columbia.edu', 'test3@columbia.edu',
                      'test4@columbia.edu', 'test5@columbia.edu',
                      'test6@columbia.edu', 'test7@columbia.edu',
                      'test8@columbia.edu', 'test9@columbia.edu'}
        test_return = set()
        self.assertEqual(process_users(test_users, 'ctl', '123xyz', 'bar'),
                         test_return)

        # Pass in an empty set
        test_users = set()
        test_return = set()
        self.assertEqual(process_users(test_users, 'ctl', '123xyz', 'bar'),
                         test_return)

    def test_add_users(self):
        self.assertEqual(add_users('f', 'o', 'o', 'o'), True)


if __name__ == "__main__":
    unittest.main()
