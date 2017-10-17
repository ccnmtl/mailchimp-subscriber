import sys
import configparser
import re
import hashlib
import requests
import csv
import time
import json
from mailchimp3 import MailChimp

# Configuration Global
CONFIG = ''
SEND_MC_EMAIL = False

EMAIL_RE = re.compile(r'(^[a-zA-Z0-9_+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)')
EMAIL_COL = 0
FIRST_NAME_COL = 1
LAST_NAME_COL = 2
INTERACTION_NOTES_COL = 3
JOB_ROLE_COL = 4
COLUMNS = ['email_address', 'first_name', 'last_name', 'interaction_notes',
           'job_role']


def validate_email(email_address):
    """Validate the syntax of the email address"""
    match = EMAIL_RE.match(email_address)
    return match is not None


class Client:
    """Client is a representation of a CTL client"""
    def __new__(cls, email, first_name, last_name, **kwargs):
        if (validate_email(email) and len(first_name) > 0 and
                len(last_name) > 0):
            return super(Client, cls).__new__(cls)
        else:
            raise ValueError

    def __init__(self, email, first_name, last_name, **kwargs):
        self.email_address = email.strip()
        self.first_name = first_name.strip().replace(",", "")
        self.last_name = last_name.strip().replace(",", "")
        self.interaction_notes = ''
        self.job_role = ''
        for key, value in kwargs.items():
            if (key == 'interaction_notes'):
                self.interaction_notes = kwargs['interaction_notes']\
                                               .strip().replace(",", "")

            if (key == 'job_role'):
                self.job_role = kwargs['job_role'].strip().replace(",", "")

        self.email_hash = hashlib.md5(self.email_address.encode('utf-8'))\
            .hexdigest()
        self.mailchimp_status = ""

    def __repr__(self):
        return '<Client: email_mail: {} first_name: {} last_name: {} >'\
                .format(self.email_address, self.first_name, self.last_name)

    def get_all_fields(self):
        return {'email_address': self.email_address,
                'first_name': self.first_name,
                'last_name': self.last_name,
                'interaction_notes': self.interaction_notes,
                'job_role': self.job_role}

    def get_mc_fields_json(self):
        """ returns a JSON string to be used as the data payload
        for the Mailchimp API."""
        values = {'FNAME': self.first_name,
                  'LNAME': self.last_name}
        return json.dumps(values)


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

    return ({'ListID': config['DEFAULT']['MailchimpListID'],
             'User': config['DEFAULT']['MailchimpUser'],
             'Key': config['DEFAULT']['MailchimpKey'],
             'SendMCEmail': send_mc_email})


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
                    client = Client(row[EMAIL_COL], row[FIRST_NAME_COL],
                                    row[LAST_NAME_COL])
                    clients[client.email_address] = client
            except ValueError:
                pass

    return clients


def process_users(users, list_id, mc_user, mc_key):
    """Takes a list of emails and returns a list of those not subscribed
    to the MailChimp list"""
    mc_client = MailChimp(mc_user, mc_key)
    for client in users.values():
        set_mailchimp_status(client, mc_client, list_id)

    if (SEND_MC_EMAIL):
        add_users_to_mailchimp(users.values(), mc_client, list_id)
    else:
        write_users_to_file(users.values())


def add_users_to_mailchimp(clients, mc_client, list_id):
    for client in clients:
        if (client.mailchimp_status == 'pending'):
            try:
                mc_client.update.list.members\
                                        .update(list_id,
                                                client.email_hash,
                                                client.get_mc_fields_json())
                return True
            except requests.exceptions.HTTPError:
                return False

        if (client.mailchimp_status == 'not_present'):
            try:
                mc_client.update.list.members\
                                        .create(list_id,
                                                client.get_mc_fields_json())
                return True
            except requests.exceptions.HTTPError:
                return False


def write_users_to_file(clients):
    """ Takes in a dictionary of client objects, and writes them out a
    csv file."""
    filename = 'Non-subscribed Clients ' + time.asctime() + '.csv'
    with open(filename, 'w') as f:
        writer = csv.DictWriter(f, COLUMNS)
        writer.writeheader()
        for client in clients:
            if (client.mailchimp_status == 'pending' or
                    client.mailchimp_status == 'not_present'):
                writer.writerow(client.get_all_fields())

if __name__ == "__main__":
    CONFIG = load_conf(sys.argv[1])
    users = load_users(sys.argv[2])
    process_users(users, CONFIG['ListID'], CONFIG['User'], CONFIG['Key'])
