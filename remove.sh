#!/bin/bash

#get script path
SCRIPT=$(readlink -f $0)
SCRIPTPATH=`dirname $SCRIPT`
cd $SCRIPTPATH


#if not root user, restart script as root
if [ "$(whoami)" != "root" ]; then
	echo "Switching to root user..."
	sudo bash $SCRIPT
	exit 1
fi

#set constants
NONE='\033[00m'
CYAN='\033[36m'
FUSCHIA='\033[35m'
UNDERLINE='\033[4m'

echo
echo "Removing Dependencies..."
echo


#remove supervisor/gunicorn-gpioneer config
sudo rm -r /etc/supervisor/conf.d/gpioneer-web.conf || true
sudo rm -r /etc/udev/rules.d/10-GPioneer.rules || true

#remove GPioneer.py from /etc/rc.local
if grep --quiet "GPioneer.py" /etc/rc.local; then
echo 'editing rc.local'
file="/etc/rc.local"
sed -ni '1h;1!H;${;g;s/GPioneer.py.*\ndisown//g;p;}' $file
fi


#remove from piplay web app if present
file="/home/pi/pimame/pimame-web-frontend/app.py"
if [ -e $file ]; then
  if grep --quiet "GPioneer" $file; then
	echo "Replacing piplay web-frontend with original"
    url="https://raw.githubusercontent.com/ssilverm/pimame-web-frontend/master/app.py"
    wget $url -O $file
	sudo supervisorctl reload
  fi
else
	sudo apt-get -y remove supervisor gunicorn
	sudo apt-get autoremove
fi


file1="/etc/rc.local"
file2="/home/pi/.profile"
if grep --quiet "retrogame" $file1 $file2; then
  echo "-----------------"
  echo "retrogame utility detected..."
  echo "Enable retrogame on startup? [y/n]"
  echo "-----------------"
  read USER_INPUT
  if [[ ! -z $(echo ${USER_INPUT} | grep -i y) ]]; then
    if grep --quiet "retrogame" $file1; then
      echo "enabling retrogame in $file1"
      sed -i "/retrogame/s/^: #//" $file1
    fi
	if grep --quiet "retrogame" $file2; then
      echo "enabling retrogame in $file2"
      sed -i "/retrogame/s/^: #//" $file2
    fi
  fi
fi

