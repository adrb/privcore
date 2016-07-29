#!/bin/bash
#
# author: Adrian Brzezinski, adrb (at) privcore.net
# license: https://creativecommons.org/licenses/by-nc-nd/3.0/
#

if [ "$(id -u)" -ne 0 ] ; then
  echo "You must be root to run this program!"
  exit 1
fi

#
# check and install dependencies
if [ ! -f /etc/apt/sources.list.d/backports.list ] && ( ! grep "jessie-backports" /etc/apt/sources.list >/dev/null ) ; then
  echo "Configuring debian backports..."
  cat > /etc/apt/sources.list.d/backports.list <<EOF
deb http://ftp.pl.debian.org/debian/ jessie-backports main contrib non-free
deb-src http://ftp.pl.debian.org/debian/ jessie-backports main contrib non-free
EOF

  echo "Updating the package index files..."
  apt-get update >/dev/null || exit 1
fi

if ( ! dpkg -l ansible >/dev/null 2>&1 ) ; then
  echo "Installing ansible from jessie-backports..."
  apt-get --yes -t jessie-backports install ansible >/dev/null || exit 1
fi

for pkt in python python-dialog python-yaml pwgen sshpass ; do
  if ( ! dpkg -l $pkt 2>&1 | grep ^ii >/dev/null ) ; then
    echo "Installing $pkt..."
    apt-get --yes install $pkt >/dev/null || exit 1
  fi
done

#
# Reset some env vars
export TERM=xterm-color
export ANSIBLE_CONFIG='./ansible/ansible.cfg'

#
# Clear log file
rm -f /tmp/privcore*.log

#
# run setup
cd $(dirname $0)
./scripts/privcore_setup.py $*

