#!/usr/bin/env python
# -*- coding: utf8 -*-
#
# author: Adrian Brzezinski, adrb (at) privcore.net
# license: https://creativecommons.org/licenses/by-nc-nd/3.0/
#

import sys, os
import argparse
import yaml
import commands
import socket
import time
import locale
import shlex, subprocess
from dialog import Dialog


ANSIBLE_ROOT = './ansible'
ANSIBLE_CONFIG = '%s/group_vars/all.yml' % ANSIBLE_ROOT
ANSIBLE_HOSTS = '%s/hosts' % ANSIBLE_ROOT
ANSIBLE_PLAYBOOK = '%s/privcore.yml' % ANSIBLE_ROOT
ANSIBLE_TAGS = [ 'ssl', 'dns', 'ldap', 'xmpp', 'owncloud', 'imap', 'smtp', 'webmail' ]
ANSIBLE_CONFIG_TEMPLATE = './scripts/all.yml.template'
ANSIBLE_HOSTS_TEMPLATE = './scripts/hosts.template'

TERM_WIDTH = 78
TERM_HEIGHT = 40

def ansible_setup():

    already_initialized = False
    ansible_config = {
        'config': {},
        'ldap_config': {},
        'owncloud_config': {},
        'roundcube_config': {},
        'ldap_tree': {}  }

    new_ldap_suffix = ''
    readonly_password = ''
    admin_user = { "uid": 'privcore',
                    "passwd_plain": '',
                    "givenname": 'privcore',
                    "sn": 'privcore' } 

    #
    # set default values
    if os.path.isfile(ANSIBLE_CONFIG):
        already_initialized = True

        with open(ANSIBLE_CONFIG, 'r') as f:
            ansible_config = yaml.load(f)

        # let's make some 'links' to objects hidden much deeper in the ldap tree
        readonly_password = ansible_config['ldap_tree']['root']['dit_branch']['users']['dit_branch']['services']['dit_branch']['readonly']['userpassword']
        admin_user = ansible_config['ldap_tree']['root']['dit_branch']['users']['dit_branch']['people']['dit_branch']['admin_user']

    if 'master_passwd' not in ansible_config['config']:
        ansible_config['config']['master_passwd'] = ''

    if 'ldap_suffix' not in ansible_config['config']:
        ansible_config['config']['ldap_suffix'] = ''

    if 'internet_domain' not in ansible_config['config']:
        ansible_config['config']['internet_domain'] = ''

    if 'organization_name' not in ansible_config['config']:
        ansible_config['config']['organization_name'] = ''

    if 'timezone' not in ansible_config['config']:
        with open('/etc/timezone') as f:
            ansible_config['config']['timezone'] = f.readline().strip()

    if 'mysql_pass' not in ansible_config['owncloud_config']:
        ansible_config['owncloud_config']['mysql_pass'] = commands.getoutput('pwgen -N 1 -s 14')

    if 'mysql_pass' not in ansible_config['roundcube_config']:
        ansible_config['roundcube_config']['mysql_pass'] = commands.getoutput('pwgen -N 1 -s 14')

#    if ansible_config['owncloud_config'] is None:
#        ansible_config['owncloud_config'] = { 'mysql_pass': commands.getoutput('pwgen -N 1 -s 14') }
#
#    if ansible_config['roundcube_config'] is None:
#        ansible_config['roundcube_config'] = { 'mysql_pass': commands.getoutput('pwgen -N 1 -s 14') }

    if readonly_password == '':
        readonly_password = commands.getoutput('pwgen -N 1 -s 14')

    hostname = socket.getfqdn()

    #
    # set mandatory variables
    while not already_initialized:
        code, ansible_config['config']['master_passwd'] = d.passwordbox(
            "Please enter master password. It' used as administrator password "
            "for various services. It should be the same as root password for your machines.\n\n"
            "Note, that we don't support further changing that password. "
            "Probably easiest way to do that, is by purging all packages and "
            "initializing setup again. In that case, you are going to lose all your data\n ",
            insecure=True)

        if code != d.OK: return 0

        if len(ansible_config['config']['master_passwd']) < 4:
            d.msgbox("Password too short. We need at least 4 characters.")
            continue

        code, _master_passwd = d.passwordbox("Type password again:",insecure=True)
        if code != d.OK: return 0

        if ansible_config['config']['master_passwd'] == _master_passwd:
            break
        else:
            d.msgbox("Password missmatch!")

    while True:
        code, ansible_config['config']['internet_domain'] = d.inputbox("The domain under which your machine can be accessed from the Internet network.\n\n" \
            "If you don't have any, it may be also IP address, but it's more like workaround and isn't recommended.",
            init=ansible_config['config']['internet_domain'])

        if code != d.OK: return 0

        if len(ansible_config['config']['internet_domain']) > 2:
            for dc in ansible_config['config']['internet_domain'].split('.'):
                new_ldap_suffix += ",dc=%s" % dc
            new_ldap_suffix = new_ldap_suffix[1:]

            break

    while True:
        code, new_ldap_suffix = d.inputbox("Please enter the name of root object for you LDAP tree.\n\n" \
            "Generally it should be similar as domain name, but split up with 'dc=' instead of dots.\n ",
            init=new_ldap_suffix)

        if code != d.OK: return 0

        if "dc=" in new_ldap_suffix:
            break

    # If LDAP tree was initialized and ldap_suffix is not going to change,
    # then we can't overwrite values for which we ask below that point.
    # Therefore it's no point in asking about them
    ldap_fresh_tree = True
    if already_initialized and new_ldap_suffix == ansible_config['config']['ldap_suffix']:
        ldap_fresh_tree = False
    else:
        ansible_config['config']['ldap_suffix'] = new_ldap_suffix

    while ldap_fresh_tree:
        code, ansible_config['config']['organization_name'] = d.inputbox("Please enter the name of your organization, for eg: Home or Company Name\n ",
            init=ansible_config['config']['organization_name'])

        if code != d.OK: return 0

        if len(ansible_config['config']['organization_name']) > 1:
            break

    while ldap_fresh_tree:
        code, ansible_config['config']['timezone'] = d.inputbox("Please enter your time zone.\n \n",
            init=ansible_config['config']['timezone'])

        if code != d.OK: return 0

        if len(ansible_config['config']['timezone']) > 3:
            break

    while ldap_fresh_tree:
        code, form = d.form("Please provide data for the first user.\n\n" \
            "It will also have the power to administer all services and sites.\n ",
            elements=[("Firstname :", 1, 1, admin_user["givenname"], 1, 15, 30, 100),
                ("Lastname :", 3, 1, admin_user["sn"], 3, 15, 30, 100)])

        if code != d.OK: return 0

        if len(form[0]) > 0 and len(form[1]) > 0:
            admin_user["givenname"] = form[0]
            admin_user["sn"] = form[1]
            admin_user["uid"] = "%s.%s" % ( form[0].lower(), form[1].lower() )
            break

    while ldap_fresh_tree:
        code, uid = d.inputbox("Please enter login name for '%s %s'.\n\n" \
            "That name you need to type in into login forms\n " % (admin_user["givenname"], admin_user["sn"]),
            init=admin_user["uid"])

        if code != d.OK: return 0

        if len(uid) > 1:
            admin_user["uid"] = uid
            break

    while ldap_fresh_tree:
        code, admin_passwd = d.passwordbox(
            "Please enter password for '%s'.\n\n" \
            "Note, that this is administrative user.\n " % admin_user["uid"],
            insecure=True)
        if code != d.OK: return 0

        if len(admin_passwd) < 4:
            d.msgbox("Password too short. We need at least 4 characters.")
            continue

        code, _admin_passwd = d.passwordbox("Type password again:",insecure=True)
        if code != d.OK: return 0

        if admin_passwd == _admin_passwd:
            admin_user["userpassword"] = admin_passwd
            break

        else:
            d.msgbox("Password missmatch!")

    # Ok, it's time to generate config files
    replace_dict = {
        "%master_passwd%": ansible_config['config']['master_passwd'],
        "%ldap_suffix%": ansible_config['config']['ldap_suffix'],
        "%internet_domain%": ansible_config['config']['internet_domain'],
        "%organization_name%": ansible_config['config']['organization_name'],
        "%timezone%": ansible_config['config']['timezone'],
        "%hostname%": hostname,
        "%readonly_password%": readonly_password,
        "%admin_user_uid%": admin_user["uid"],
        "%admin_user_givenname%": admin_user["givenname"],
        "%admin_user_sn%": admin_user["sn"],
        "%admin_user_password%": admin_user["userpassword"],
        "%owncloud_mysql_pass%": ansible_config['owncloud_config']['mysql_pass'],
        "%roundcube_mysql_pass%": ansible_config['roundcube_config']['mysql_pass'],
    }
    template_file(ANSIBLE_CONFIG_TEMPLATE, ANSIBLE_CONFIG, replace_dict)

    replace_dict = { "%hostname%": hostname, }
    template_file(ANSIBLE_HOSTS_TEMPLATE, ANSIBLE_HOSTS, replace_dict)

    ansible_play(ANSIBLE_TAGS)

    return 0

def ansible_play(playtags=[]):

    #
    # read config file
    if os.path.isfile(ANSIBLE_CONFIG):
        with open(ANSIBLE_CONFIG, 'r') as f:
            ansible_config = yaml.load(f)
    else:
        d.msgbox("Run setup first!")
        return 0

    if 'master_passwd' not in ansible_config['config']:
        ansible_config['config']['master_passwd'] = ''

    while ansible_config['config']['master_passwd'] == '':
        code, ansible_config['config']['master_passwd'] = d.passwordbox("Type master password:", insecure=True)
        if code != d.OK: return 0

    #
    # select which tasks you want to play
    if not playtags:
        code, playtags = d.checklist('Please slect tags/jobs you want to play:',
            choices=[('ssl', 'Generate certificates for machines and its services',True),
                ('dns', 'Configure bind as local DNS server',True),
                ('ldap', 'Prepare openldap tree',True),
                ('xmpp', 'Prosody XMPP/Jabber server',True),
                ('owncloud', 'Sharing server (file, contacts, calendar)',True),
                ('imap', 'Dovecot IMAP server',True),
                ('smtp', 'Exim SMTP server',True),
                ('webmail', 'Roundcube e-mail and Jabber webclient',True),
            ])
        if code != d.OK: return 0

    # PrivCore role should always be performed at the end
    playtags.append('privcore')

    # execute ansible playbooks
    for tag_name in playtags:

        ansible_log_file = "/tmp/privcore.log"

        ansible_cmd = shlex.split('sshpass -p "%s" ansible-playbook %s -i %s -t %s -c local --ask-pass -v' %
            (ansible_config['config']['master_passwd'], ANSIBLE_PLAYBOOK, ANSIBLE_HOSTS, tag_name))
        ansible_proc = subprocess.Popen(ansible_cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)

        d.progressbox(fd=ansible_proc.stdout.fileno(),
                text="Executing playbook: %s (%i/%i)\n" % (tag_name, playtags.index(tag_name)+1, len(playtags)),
                height=TERM_HEIGHT, width=TERM_WIDTH)

        ansible_proc.wait()
        if ansible_proc.returncode != 0:
            d.msgbox("Oops, something went terribly wrong. Please check your log file for error messages" \
                    " and then try to replay playbooks:\n\n%s" % ansible_log_file )
            return 1

    d.msgbox("We are done. Please try your services at\n\n   https://%s/" % ansible_config['config']['internet_domain'] )

    return 0

def ansible_uninstall():

    d.msgbox("Uninstall currently not supported.", height=TERM_HEIGHT, width=TERM_WIDTH)

    return 0

def template_file(src, dest, replace_dict):
    with open(src, "rt") as fsrc:
        with open(dest, "wt") as fdest:
            for line in fsrc:
                for key, value in replace_dict.items():
                    line = line.replace(str(key), str(value))

                fdest.write(line)

if __name__ == '__main__':
    locale.setlocale(locale.LC_ALL, '')

    TERM_HEIGHT, TERM_WIDTH = commands.getoutput('stty size').split()
    TERM_HEIGHT = int(TERM_HEIGHT)-10
    TERM_WIDTH = int(TERM_WIDTH)-15

    d = Dialog(dialog="dialog", autowidgetsize=True)
    d.set_background_title("PrivCore Setup (http://privcore.net)")

    while True:
        # check whatewer something was actually configured
        if os.path.isfile(ANSIBLE_CONFIG):
            menu_desc = "It's seems that you already configured PrivCore.\n\n" \
                "Note, that if you choose to edit your configuration, then you will be not allowed to change master password!\n "
            code, tag = d.menu(menu_desc,
                choices=[("setup", "Edit current configuration"),
                    ("replay", "Replay configuration scripts (your manuall changes may be overwritten)"),
                    ("uninstall", "Uninstall selected services"),
                    ("exit","Quit setup program")])
        else:
            menu_desc = "Welcome to PrivCore simple setup wizzard.\n\nCurrently we support only all-in-one setup type. " \
                "It means, that all services will be installed on single machine. Other installation methods require manual " \
                "editing of PrivCore configuration files, with means that they are reserved for advanced users.\n "
            code, tag = d.menu(menu_desc,
                choices=[("setup", "Initialize configuration"),
                    ("exit","Quit setup program")])

        if code != d.OK:
            sys.exit(0)

        menu = {
            "setup": ansible_setup,
            "replay": ansible_play,
            "uninstall": ansible_uninstall,
        }
        menu.get(tag, sys.exit)()

