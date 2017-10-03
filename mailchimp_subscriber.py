import sys
import configparser
import re
import hashlib
import requests
import csv
from mailchimp3 import MailChimp

EMAIL_RE = re.compile(r'(^[a-zA-Z0-9_+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)')
EMAIL_COL = 0
FIRST_NAME_COL = 1
LAST_NAME_COL = 2
NOTES_COL = 3


def validate_email(email_address):
    """Validate the syntax of the email address"""
    match = EMAIL_RE.match(email_address)
    return match is not None


class Client:
    """Client is a representation of a CTL client"""
    def __new__(cls, row):
        if (len(row) >= 3 and
                validate_email(row[0])):
            return super(Client, cls).__new__(cls)
        else:
            raise ValueError

    def __init__(self, row):
        self.email_address = row[EMAIL_COL].strip()
        self.first_name = row[FIRST_NAME_COL].strip()
        self.last_name = row[LAST_NAME_COL].strip()
        try:
            self.interaction_notes = row[NOTES_COL].strip()
        except IndexError:
            self.interaction_notes = None
        self.email_hash = hashlib.md5(row[0].encode('utf-8')).hexdigest()
        self.mailchimp_status = ""


def set_mailchimp_status(client, mc_client, list_id):
    """Takes in a client object and checks that persons status on Mailchimp.
    It then assigns that value back to the client object"""
    try:
        status = mc_client.lists.members.get(list_id, client.email_hash)
        client.mailchimp_status = status['status']
    except requests.exceptions.HTTPError:
        client.mailchimp_status = 'not_present'


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
    Returns a set of Client objects"""
    clients = dict()
    with open(users_file, 'r') as f:
        for row in csv.reader(f):
            # Note that this isn't testing for multiple appearances of the same
            # client. If theres more than one, it takes the last appearence.
            try:
                clients[row[0]] = Client(row)
            except ValueError:
                pass

    return clients


def process_users(users, list_id, mc_user, mc_key):
    """Takes a list of emails and returns a list of those not subscribed
    to the MailChimp list"""
    mc_client = MailChimp(mc_user, mc_key)
    for client in users.values:
        set_mailchimp_status(client, mc_client, list_id)
        add_user(client, mc_client, list_id)


def add_user(client, mc_client, list_id):
    if (client.mailchimp_status == 'pending' or
            client.mailchimp_status == 'not_present'):
        try:
            mc_client.update.list.members.update(list_id, client.email_hash,
                                                 "{'status': 'pending'}")
            return True
        except requests.exceptions.HTTPError:
            return False


if __name__ == "__main__":
    list_id, mc_user, mc_key = load_conf(sys.argv[1])
    users = load_users(sys.argv[2])
    process_users(users, list_id, mc_user, mc_key)
