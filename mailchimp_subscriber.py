import sys
import configparser
import re
import hashlib
import requests
import csv
import time
from mailchimp3 import MailChimp

# Configuration Global
SEND_MC_EMAIL = False

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
    def __new__(cls, email, first_name, last_name):
        if (validate_email(email) and len(first_name) > 0 and
                len(last_name) > 0):
            return super(Client, cls).__new__(cls)
        else:
            raise ValueError

    def __init__(self, email, first_name, last_name):
        self.email_address = email.strip()
        self.first_name = first_name.strip()
        self.last_name = last_name.strip()
        self.email_hash = hashlib.md5(self.email_address.encode('utf-8'))\
            .hexdigest()
        self.mailchimp_status = ""

    def __repr__(self):
        return '<Client: email_mail: {} first_name: {} last_name: {} >'\
                .format(self.email_address, self.first_name, self.last_name)


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
    send_mc_email = False
    try:
        if (config['DEFAULT'].getboolean('SendMCEmail',
                                         fallback=False)):
            send_mc_email = True
    except ValueError:
        pass

    return (config['DEFAULT']['MailchimpListID'],
            config['DEFAULT']['MailchimpUser'],
            config['DEFAULT']['MailchimpKey'],
            send_mc_email)


def load_users(users_file):
    """Read the email addresses from disk.
    Returns a set of Client objects"""
    clients = dict()
    with open(users_file, 'r') as f:
        for row in csv.reader(f):
            # Note that this isn't testing for multiple appearances of the same
            # client. If theres more than one, it takes the last appearence.
            try:
                if (len(row) >= 3):
                    clients[row[EMAIL_COL]] = Client(row[EMAIL_COL],
                                                     row[FIRST_NAME_COL],
                                                     row[LAST_NAME_COL])
            except ValueError:
                pass

    return clients


def process_users(users, list_id, mc_user, mc_key):
    """Takes a list of emails and returns a list of those not subscribed
    to the MailChimp list"""
    mc_client = MailChimp(mc_user, mc_key)
    for client in users.values:
        set_mailchimp_status(client, mc_client, list_id)

    if (SEND_MC_EMAIL):
        add_users_to_mailchimp(users.values, mc_client, list_id)
    else:
        write_users_to_file(users.values)


def add_users_to_mailchimp(clients, mc_client, list_id):
    for client in clients:
        if (client.mailchimp_status == 'pending' or
                client.mailchimp_status == 'not_present'):
            try:
                mc_client.update.list.members.update(list_id,
                                                     client.email_hash,
                                                     "{'status': 'pending'}")
                return True
            except requests.exceptions.HTTPError:
                return False


def write_users_to_file(clients):
    """ Takes in a dictionary of client objects, and writes them out a
    csv file."""
    filename = 'Non-subscribed Clients ' + time.asctime()
    with open(filename, 'w') as f:
        for client in clients:
            if (client.mailchimp_status == 'pending' or
                    client.mailchimp_status == 'not_present'):
                f.write(client.email_address + ', ')
                f.write(client.first_name + ', ')
                f.write(client.last_name + ', ')
                f.write('\n')


if __name__ == "__main__":
    list_id, mc_user, mc_key, SEND_MC_EMAIL = load_conf(sys.argv[1])
    users = load_users(sys.argv[2])
    process_users(users, list_id, mc_user, mc_key)
