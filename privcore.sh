#!/bin/bash
#
# author: Adrian Brzezinski, adrb http://privcore.adrb.pl/
# license: https://creativecommons.org/licenses/by-nc-nd/3.0/
#

set -e

if [ "$(id -u)" -ne 0 ] ; then
  echo "You must be root to run this program!"
  exit 1
fi

#
# get Debian's codename
if ( ! dpkg -l lsb-release >/dev/null 2>&1 ) ; then
  echo "Installing lsb-release..."
  apt-get --yes install lsb-release >/dev/null
fi

CODENAME=$(lsb_release --codename --short)
if [ -z "$CODENAME" ] ; then
  echo "I can't get system codename!" >&2
  exit 1
fi

#
# check and install dependencies
if [ ! -f /etc/apt/sources.list.d/backports.list ] && ( ! grep "${CODENAME}-backports" /etc/apt/sources.list >/dev/null ) ; then
  echo "Configuring debian backports..."
  cat > /etc/apt/sources.list.d/backports.list <<EOF
deb http://httpredir.debian.org/debian ${CODENAME}-backports main contrib non-free
deb-src http://httpredir.debian.org/debian ${CODENAME}-backports main contrib non-free
EOF

  echo "Updating indexes of available packages..."
  apt-get update >/dev/null
fi

_install_pkgs=''
for pkt in ansible python python-dnspython python3-dnspython acl ; do
  if ( ! dpkg -l $pkt 2>&1 | grep ^ii >/dev/null ) ; then
    _install_pkgs="$pkt $_install_pkgs"
  fi
done
if [ -n "$_install_pkgs" ]; then
  echo "Installing: $_install_pkgs..."
  apt-get --yes install $_install_pkgs >/dev/null
fi

#
# run ansible playbooks
cd $(dirname $0)/ansible

# install ansible plugins
if [ ! -d plugins ] ; then
  echo "Installing ansible plugins..."
  mkdir plugins
  pushd plugins
  wget -q https://github.com/dw/mitogen/archive/stable.zip -O mitogen-stable.zip
  unzip -q mitogen-stable.zip
  popd
fi

export ANSIBLE_CONFIG='./ansible.cfg'
ansible-playbook privcore.yml $*

