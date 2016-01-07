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
IP="$(ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1')"
NONE='\033[00m'
CYAN='\033[36m'
FUSCHIA='\033[35m'
UNDERLINE='\033[4m'

echo "Running Update..."

#install dependencies
sudo apt-get update
echo
echo "Installing Dependencies..."
echo
sudo apt-get -y install python python-dev python-requests python-pip
sudo apt-get -y install supervisor gunicorn sqlite3
sudo pip install flask pyyaml flask-sqlalchemy flask-admin evdev

#Create supervisor/gunicorn-gpioneer config
match="\[program:gpioneer-web\]"
insert="directory="$SCRIPTPATH"/web-frontend/"
file=$SCRIPTPATH"/web-frontend/gpioneer-web.conf"
sed "s|$match|$match\n$insert|" $file > /etc/supervisor/conf.d/gpioneer-web.conf

#add GPioneer.py to /etc/rc.local
if ! grep --quiet "GPioneer.py" /etc/rc.local; then
echo 'editing rc.local'
match="exit 0"
insert="python "$SCRIPTPATH"/GPioneer.py \&>/dev/null \&"
file="/etc/rc.local"
sed -i "s|^$match$|$insert\n$match|" $file
fi

#create Udev rule for SDL2 applications
UDEV='SUBSYSTEM=="input", ATTRS{name}=="GPioneer", ENV{ID_INPUT_KEYBOARD}="1"'
echo $UDEV > /etc/udev/rules.d/10-GPioneer.rules
#add uinput to modules if not already there
if ! grep --quiet "uinput" /etc/modules; then echo "uinput" >> /etc/modules; fi
#add evdev to modules if not already there
if ! grep --quiet "evdev" /etc/modules; then echo "evdev" >> /etc/modules; fi

#add to piplay web app if present
file="/home/pi/pimame/pimame-web-frontend/app.py"
if [ -e $file ]; then
if ! grep --quiet "GPioneer" $file; then
echo "Patching Piplay Web-Frontend"
match="import os"
insert="import subprocess"
file="/home/pi/pimame/pimame-web-frontend/app.py"
sed -i "s@$match@$match\n$insert@" $file
match="db.create_scoped_session()"
insert="class GPioneer(db.Model):\n\
    __tablename__ = 'gpioneer'\n\
    __bind_key__ = 'config'\n\
    id = db.Column(db.Integer, primary_key=True)\n\
    name = db.Column(db.Text)\n\
    command = db.Column(db.Text)\n\
    pins = db.Column(db.Text)\n\
\n\
    def __unicode__(self):\n\
        return self.name"
file="/home/pi/pimame/pimame-web-frontend/app.py"
sed -i "s|$match|$match\n\n\n$insert|" $file
match="admin.add_view(CustomModelView(LocalRoms, db.session))"
insert="if subprocess.check_output('/sbin/udevadm info --export-db | grep -i gpioneer; exit 0', stderr=subprocess.STDOUT, shell=True):\n\
    admin.add_view(CustomModelView(GPioneer, db.session))"
file="/home/pi/pimame/pimame-web-frontend/app.py"
sed -i "s@$match@$match\n$insert@" $file
fi
fi
sudo supervisorctl reload

file1="/etc/rc.local"
file2="/home/pi/.profile"
if grep --quiet "retrogame" $file1 $file2; then
  echo "-----------------"
  echo "retrogame utility detected..."
  echo "Disable retrogame on startup? [y/n] (this can be undone)"
  echo "-----------------"
  read USER_INPUT
  if [[ ! -z $(echo ${USER_INPUT} | grep -i y) ]]; then
    if grep --quiet "retrogame" $file1; then
      echo "disabling retrogame in $file1"
      sed -i "/retrogame/s/^#*/: #/" $file1
      #how to uncomment: sed '/retrogame/s/^#//'
    fi
	if grep --quiet "retrogame" $file2; then
      echo "disabling retrogame in $file2"
      sed -i "/retrogame/s/^#*/: #/" $file2
      #how to uncomment: sed '/retrogame/s/^#//'
    fi
  fi
fi


echo "-----------------"
echo -e "${CYAN}Would you like to run the configuration now?${NONE} [y/n]"
echo "-----------------"
read USER_INPUT

#if yes, run gpioneer config
if [[ ! -z $(echo ${USER_INPUT} | grep -i y) ]]; then
sudo python GPioneer.py -c
clear
fi
sudo python GPioneer.py &>/dev/null &


echo "-------------> Setup Complete!"
echo 
echo "Type your Pi's IP address into a web browser to customize GPioneer"
echo -e "                    ${FUSCHIA}${UNDERLINE}"$IP"${NONE}"
echo
echo
echo -e "${CYAN}${UNDERLINE}/etc/rc.local has been modified to auto run GPioneer${NONE}"
echo
echo -e "${CYAN}Configure GPioneer: sudo python GPioneer.py -c"
echo "Test GPioneer     : sudo python GPioneer.py (Ctrl+C to quit)"
echo "Run GPioneer      : sudo python GPioneer.py &"
echo
echo
echo "OPTIONAL FLAGS"
echo "--combo_time	'Time in milliseconds to wait for combo buttons'"
echo "--key_repeat	'Delay in milliseconds before key repeat'"
echo "--key_delay	'Delay in milliseconds between key presses'"
echo "--pins		'Comma delimited pin numbers to watch'"
echo "--use_bcm		'use bcm numbering instead of board pin'"
echo "--debounce	'Time in milliseconds for button debounce'"
echo "--pulldown	'Use PullDown resistors instead of PullUp'"
echo "--poll_rate	'Rate to poll pins after IRQ detect'"
echo "--------------------------------------------------------------------------------"
echo "-c				'Configure GPioneer'"
echo "--configure		'Configure GPioneer'"
echo "--button_count	'Number of player buttons to configure'"
echo
