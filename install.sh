#!/bin/bash

#get script path
SCRIPT=$(readlink -f $0)
SCRIPTPATH=`dirname $SCRIPT`
cd $SCRIPTPATH

if [ "$(whoami)" != "root" ]; then
	echo "Switching to root user..."
	sudo bash $SCRIPT
	exit 1
fi

echo "Installing Dependencies..."

#install dependencies
sudo apt-get update
sudo apt-get -y install python python-dev python-requests python-pip
sudo apt-get -y install supervisor gunicorn sqlite3
sudo pip install flask pyyaml flask-sqlalchemy flask-admin evdev

#Create supervisor/gunicorn config
match="\[program:gunicorn\]"
insert="directory="$SCRIPTPATH"/web-frontend/"
file="web-frontend/gunicorn-gpioneer.conf"
sed "s|$match|$match\n$insert|" $file > /etc/supervisor/conf.d/gunicorn-gpioneer.conf
sudo supervisorctl reload

#add GPioneer.py to /etc/rc.local
if ! grep --quiet "GPioneer.py" /etc/rc.local
then
match="exit 0"
insert="python "$SCRIPTPATH"/GPioneer.py"
file="/etc/rc.local"
sed -i "s|$match|$insert\n$match|" $file
fi

#create Udev rule for SDL2 applications
UDEV='SUBSYSTEM=="input", ATTRS{name}=="GPioneer", ENV{ID_INPUT_KEYBOARD}="1"'
echo $UDEV > /etc/udev/rules.d/10-GPioneer.rules
#add uinput to modules if not already there
if ! grep --quiet "uinput" /etc/modules; then 'uinput' >> /etc/modules; fi

echo "-----------------"
echo "${CYAN}Would you like to run the configuration now?${NONE} [y/n]"
echo "-----------------"
read USER_INPUT

if [[ ! -z $(echo ${USER_INPUT} | grep -i y) ]]; then
sudo python GPioneer.py -c
fi

IP="$(ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1')"
NONE='\033[00m'
CYAN='\033[36m'
FUSCHIA='\033[35m'
UNDERLINE='\033[4m'

clear
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
