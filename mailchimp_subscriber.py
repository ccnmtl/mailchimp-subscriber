import sys
import configparser
import re
from mailchimp3 import MailChimp

EMAIL_RE = re.compile(r'(^[a-zA-Z0-9_+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)')


def validate_email(email_address):
    """Validate the syntax of the email address"""
    match = EMAIL_RE.match(email_address)
    if match:
        return True
    else:
        return False


def load_conf(conf_file):
    """Load the configuration file. Returns a tuple
    containing the MC List Id, MC User, and MC API key"""
    config = configparser.ConfigParser()
    config.read(conf_file)
    return (config['DEFAULT']['MailchimpListID'],
            config['DEFAULT']['MailchimpUser'],
            config['DEFAULT']['MailchimpKey'])


def load_users(users_file):
    """Read the email addresses from disk.
    Returns a set of email addresses"""
    with open(users_file, 'r') as f:
        return {l.rstrip() for l in f.readlines() if validate_email(l)}


def process_users(users, list_id, mc_user, mc_key):
    """Takes a list of emails and returns a list of those not subscribed
    to the MailChimp list"""
    client = MailChimp(mc_user, mc_key)
    contacts = client.lists.members.all(list_id, get_all=True,
                                        status='subscribed',
                                        fields="members.email_address")
    email_addresses = {contact['email_address']
                       for contact in contacts['members']}
    return users.difference(email_addresses)


def add_users(users, list_id, mc_user, mc_key):
    return False


if __name__ == "__main__":
    list_id, mc_user, mc_key = load_conf(sys.argv[1])
    users = load_users(sys.argv[2])
    process_users(users, list_id, mc_user, mc_key)
