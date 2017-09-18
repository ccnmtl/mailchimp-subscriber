import sys
import configparser
from mailchimp3 import MailChimp


def load_conf(conf_file):
    config = configparser.ConfigParser()
    config.read(conf_file)
    return (config['DEFAULT']['MailchimpListID'],
            config['DEFAULT']['MailchimpUser'],
            config['DEFAULT']['MailchimpKey'])


def load_users(users_file):
    with open(users_file, 'r') as f:
        return {l.rstrip() for l in f.readlines()}


def process_users(users, list_id, mc_user, mc_key):
    client = MailChimp(mc_user, mc_key)
    print(client.lists.members.all(list_id, get_all=True))
    return False


if __name__ == "__main__":
    list_id, mc_user, mc_key = load_conf(sys.argv[1])
    users = load_users(sys.argv[2])
    process_users(users, list_id, mc_user, mc_key)
