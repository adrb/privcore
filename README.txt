
PrivCore 12.0 (bookworm)
Author: Adrian Brzezinski

-------------------------------------------------------------------------------

Self-hosted solution for your files, email, mobile contacts, calendar and more.
Perfect not only for small and medium size companies, but virtually for
anyone who want to keep data on own servers without giving up new Cloud
based capabilities. Among others it includes:

- Nextcloud (sharing files, contacts and calendars)
- LibreOffice Online (online editing of a range of document types)
- Video Conferencing
- Mail server (including greylist and server side Sieve filters)
- Centralized user management

For detailed information, please visit http://privcore.adrb.pl

-------------------------------------------------------------------------------

Quick install:

- Install a fresh copy of the Debian 12 system on all machines, where you plan
to install PrivCore

- Clone PrivCore git repository

- Edit "ansible/hosts" and "ansible/group_vars/all.yml" files

- Copy your ssh public key to "/root/.ssh/authorized_keys" for all machines, where
PrivCore is to be installed.

- Run "./privcore.sh" script from current directory

-------------------------------------------------------------------------------

This software is distributed under CreativeCommons BY-SA 4.0 license.
Full license text you can read on :

 - https://creativecommons.org/licenses/by-sa/4.0/legalcode

-------------------------------------------------------------------------------

