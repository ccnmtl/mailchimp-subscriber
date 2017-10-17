import unittest
import requests
from hypothesis import given, strategies as st
from unittest.mock import patch, MagicMock, call, mock_open
from mailchimp_subscriber import (
    load_conf, load_users, validate_email,
    add_users_to_mailchimp, Client, set_mailchimp_status,
    write_users_to_file, EMAIL_RE
)

CLIENT_FACTORY = st.builds(
                    Client,
                    st.from_regex(EMAIL_RE),
                    st.text(min_size=1),
                    st.text(min_size=1),
                    interaction_notes=st.text(min_size=1),
                    job_role=st.text(min_size=1))


class TestMailchimpSubscriber(unittest.TestCase):
    def test_validate_email(self):
        self.assertEqual(validate_email('foo'), False)
        self.assertEqual(validate_email('foo@notld'), False)
        self.assertEqual(validate_email('foo@columbia.edu'), True)
        self.assertEqual(validate_email('foo@columbia,edu'), False)
        self.assertEqual(validate_email('foo+bar@columbia.edu'), True)

    def test_Client(self):
        self.assertRaises(ValueError, Client, 'foobar', 'John', 'Doe')
        self.assertIsInstance(Client('foo@bar.com', 'John', 'Doe'),
                              Client)

    @patch('mailchimp_subscriber.MailChimp')
    def test_set_mailchimp_status(self, mock_mail_chimp):
        # Set up mock
        mock_client = mock_mail_chimp()

        # Test pending
        ctl_client = Client('foo@bar.com', 'John', 'Doe')
        mock_client.lists.members.get = MagicMock(
            return_value={'status': 'pending'})
        set_mailchimp_status(ctl_client, mock_client, '1234')
        self.assertEqual(ctl_client.mailchimp_status, 'pending')

        # Test subscribed
        ctl_client = Client('foo@bar.com', 'John', 'Doe')
        mock_client.lists.members.get = MagicMock(
            return_value={'status': 'subscribed'})
        set_mailchimp_status(ctl_client, mock_client, '1234')
        self.assertEqual(ctl_client.mailchimp_status, 'subscribed')

        # Test unsubscribed
        ctl_client = Client('foo@bar.com', 'John', 'Doe')
        mock_client.lists.members.get = MagicMock(
            return_value={'status': 'unsubscribed'})
        set_mailchimp_status(ctl_client, mock_client, '1234')
        self.assertEqual(ctl_client.mailchimp_status, 'unsubscribed')

        # Test cleaned
        ctl_client = Client('foo@bar.com', 'John', 'Doe')
        mock_client.lists.members.get = MagicMock(
            return_value={'status': 'cleaned'})
        set_mailchimp_status(ctl_client, mock_client, '1234')
        self.assertEqual(ctl_client.mailchimp_status, 'cleaned')

        # Test not_present
        ctl_client = Client('foo@bar.com', 'John', 'Doe')
        mock_client.lists.members.get = MagicMock(
            side_effect=requests.exceptions.HTTPError)
        set_mailchimp_status(ctl_client, mock_client, '1234')
        self.assertEqual(ctl_client.mailchimp_status, 'not_present')

    def test_load_conf(self):
        config = load_conf('tests/test.conf')
        self.assertEqual(config['ListID'], '1234')
        self.assertEqual(config['User'], 'ctl')
        self.assertEqual(config['Key'], '123xyz')
        self.assertEqual(config['SendMCEmail'], False)

    def test_load_users(self):
        # load_users takes in a csv file and returns Client objects
        # Note that test-user-list.csv has some dummy addresses thrown in
        loaded_users = load_users('tests/test-user-list.csv')

        self.assertTrue(len(loaded_users) == 4)

        dummy_user_1 = loaded_users['alice@columbia.edu']
        self.assertEqual(dummy_user_1.email_address, 'alice@columbia.edu')
        self.assertEqual(dummy_user_1.first_name, 'Alice')
        self.assertEqual(dummy_user_1.last_name, 'Foo Bar')

        dummy_user_2 = loaded_users['bob@columbia.edu']
        self.assertEqual(dummy_user_2.email_address, 'bob@columbia.edu')
        self.assertEqual(dummy_user_2.first_name, 'Bob')
        self.assertEqual(dummy_user_2.last_name, 'Foobar')

        dummy_user_3 = loaded_users['nick@columbia.edu']
        self.assertEqual(dummy_user_3.email_address, 'nick@columbia.edu')
        self.assertEqual(dummy_user_3.first_name, 'Nick')
        self.assertEqual(dummy_user_3.last_name, 'Buonincontri')

        dummy_user_4 = loaded_users['joe@columbia.edu']
        self.assertEqual(dummy_user_4.email_address, 'joe@columbia.edu')
        self.assertEqual(dummy_user_4.first_name, 'Joe')
        self.assertEqual(dummy_user_4.last_name, 'Foobar')

    @patch('mailchimp_subscriber.MailChimp')
    def test_add_users(self, mock_mail_chimp):
        mock_client = mock_mail_chimp()

        client_1 = Client('foo@bar.com', 'John', 'Doe')
        client_1.mailchimp_status = 'pending'
        mock_client.lists.members.update = MagicMock(
            return_value={'status': 'pending'})
        self.assertTrue(add_users_to_mailchimp(
                        [client_1], mock_client, '1234'))

        client_2 = Client('foo@bar.com', 'John', 'Doe')
        client_2.mailchimp_status = 'not_present'
        mock_client.lists.members.update = MagicMock(
            return_value={'status': 'not_present'})
        self.assertTrue(add_users_to_mailchimp(
                        [client_2], mock_client, '1234'))

        client_3 = Client('foo@bar.com', 'John', 'Doe')
        client_3.mailchimp_status = 'subscribed'
        mock_client.lists.members.update = MagicMock(
            return_value={'status': 'subscribed'})
        self.assertFalse(add_users_to_mailchimp(
                         [client_3], mock_client, '1234'))

        client_4 = Client('foo@bar.com', 'John', 'Doe')
        client_4.mailchimp_status = 'unsubscribed'
        mock_client.lists.members.update = MagicMock(
            return_value={'status': 'unsubscribed'})
        self.assertFalse(add_users_to_mailchimp(
                         [client_4], mock_client, '1234'))

        client_5 = Client('foo@bar.com', 'John', 'Doe')
        client_5.mailchimp_status = 'cleaned'
        mock_client.lists.members.update = MagicMock(
            return_value={'status': 'cleaned'})
        self.assertFalse(add_users_to_mailchimp(
                         [client_5], mock_client, '1234'))

# This test should look at the actual file stream rather than the
# system calls because you could have commas in the input which would
# break the CSV file
    @given(st.sampled_from(['pending', 'not_present']))
    @given(st.lists(CLIENT_FACTORY))
    def test_write_users_to_file(self, status, clients):
        # The mocks need to use context managers because Hypothesis @given
        # decorator does not play well with others:
        # https://github.com/HypothesisWorks/hypothesis-python/issues/198
        with patch("mailchimp_subscriber.open", mock_open(),
                   create=True) as mock_file:
            with patch("mailchimp_subscriber.csv.DictWriter.writerow")\
                                as mock_writerow:
                # this is a dummy value, we need to use mock_file to pass flake8
                mock_file.mock_calls
                # Set the mailchimp status on each client
                for client in clients:
                    client.mailchimp_status = status
                write_users_to_file(clients)
                for client in clients:
                    # assert the mock_calls contains a call for each client
                    self.assertIn(call({'email_address': client.email_address,
                                        'first_name': client.first_name,
                                        'last_name': client.last_name,
                                        'interaction_notes':
                                            client.interaction_notes,
                                        'job_role': client.job_role}),
                                  mock_writerow.mock_calls)


if __name__ == "__main__":
    unittest.main()
