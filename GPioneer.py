#!/usr/bin/env python

import argparse
import os
import select
import sys
import time
import sqlite3
import signal
import subprocess
from evdev import UInput, ecodes as e

try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("This script must be run as sudo!")


#------------------------------- ARGUMENTS -------------------------------------
#-------------------------------------------------------------------------------
parser = argparse.ArgumentParser(description='PiScraper')
parser.add_argument('--combo_time', 
								metavar = '50', default = 50.0, type = float,
								help='Time in milliseconds to wait for combo buttons')
								
parser.add_argument('--key_repeat', 
								metavar = '350', default = 350.0, type = float,
								help='Delay in milliseconds before key repeat')
								
parser.add_argument('--key_delay', 
								metavar = '10', default = 10.0, type = float,
								help='Delay in milliseconds between key presses')
								
parser.add_argument('--pins', 
								metavar = '3,5,7,11', default = '', type = str,
								help='Comma delimited pin numbers to watch')
								
parser.add_argument('--button_count', 
								metavar='6', default = 6, type = int,
								help='Number of player buttons to configure')

parser.add_argument('--debounce', 
								metavar='20', default = 20, type = int,
								help = 'Time in milliseconds for button debounce')

parser.add_argument('--pulldown', 
								dest='pulldown', default = False, action='store_true',
								help = 'Use PullDown resistors instead of PullUp')
								
parser.add_argument('--poll_rate', 
								metavar='20', default = 20.0, type = float,
								help = 'Rate to poll pins after IRQ detect')
								
parser.add_argument('--configure', 
								dest='configure', default = False, action='store_true',
								help='Configure GPioneer')
								
parser.add_argument('-c', 
								dest='configure', default = False, action='store_true',
								help='Configure GPioneer')
								
parser.add_argument('--use_bcm', 
								dest='bcm', default = False, action='store_true',
								help='use bcm numbering')
								
parser.add_argument('--dev', 
								dest='dev', default = False, action='store_true',
								help='Show Warnings')
								
parser.add_argument('--init',  
								dest='init', default = False, action='store_true',
								help='Initialize udev.rule/uinput module')
								
args = parser.parse_args()

if args.bcm and not args.pins:
    parser.error('--use_bcm can only be set in conjunction with --pins')


def pcolor(color, string):
	ENDC = '\033[0m'
	colors = {'red': '\033[31m',
	'green': '\033[32m',
	'yellow': '\033[33m',
	'blue': '\033[34m',
	'fuschia': '\033[35m',
	'cyan': '\033[36m'}
	
	return colors[color.lower()] + string + ENDC
	
#--------------------------- BUTTON OBJECT -------------------------------------
#-------------------------------------------------------------------------------
class button(object):
	def __init__(self, name, pin, commands):
		self.name = name
		self.pin = eval(pin + ',')
		self.is_combo = True if len(self.pin) > 1 else False
		self.time_stamp = 0
		self.pressed = 0
		self.key = []
		self.command = []
		for entry in commands.split('|'):
			if 'KEY' in entry[:3]:
				self.key.append('e.' + entry.upper())
			else:
				self.command.append(entry)

		self.mask = 0L
		try:
			for p in self.pin:
				self.mask |= (1L << int(p))
		except ValueError:
			print self.name, 'non-integer in pin configuration list'
	
	
	def append(self, command):
		if 'KEY' in command[:3]:
			self.key.append('e.' + command.upper())
		else:
			self.command.append(command)
		

#------------------------------ GPIONEER ---------------------------------------
#-------------------------------------------------------------------------------
class Gpioneer (object):
	ui = UInput(name="GPioneer")
	#Pi 1 (A/B)
	REV1_PIN_LIST = [3,5,7,11,13,15,19,21,23,
								8,10,12,16,18,22,24,26] 
	#Pi 1 (A+/B+), Pi 2
	REV2_PIN_LIST = [3,5,7,11,13,15,19,21,23,29,31,33,35,37,
								8,10,12,16,18,22,24,26,32,36,38,40] 
	
	
	def signal_handler(self, signal, frame):
		pins = [pin['#'] for pin in self.PIN_LIST]
		GPIO.cleanup(pins)
		print
		print 'Kaaaaahhhnn!'
		sys.exit(0)
		

	def set_args(self, args):
		#Use P1 Header pin numbering
		GPIO.setmode(GPIO.BOARD)
		#if BCM, require
		if args.bcm and args.pins:
			#Use SoC CHANNEL REVISION NUMBERS 
			GPIO.setmode(GPIO.BCM)
		
		GPIO.setwarnings(args.dev)
			
		self.debounce = args.debounce
		self.RESISTOR_PULL = (GPIO.PUD_UP 
											if not args.pulldown 
											else GPIO.PUD_DOWN)
		self.I2C_RESISTOR_PULL = GPIO.PUD_UP
		self.POLL_RATE = args.poll_rate / 1000
		self.BUTTON_COUNT = args.button_count #6 by default
		
		#if pin argument passed, use those
		if args.pins:
			try:
				self.PIN_LIST = [int(x) 
										for x in args.pins.split(',') 
										if int(x) in self.REV2_PIN_LIST]
			except ValueError:
				print 'Pin list had errors, using defaults'
				self.PIN_LIST = (self.REV2_PIN_LIST 
										if GPIO.RPI_INFO['P1_REVISION'] >= 3 
										else self.REV1_PIN_LIST)
		
		#if configure 
		#and not arg.pins,
		#then set all pins
		elif args.configure:
			self.PIN_LIST = (self.REV2_PIN_LIST 
									if GPIO.RPI_INFO['P1_REVISION'] >= 3 
									else self.REV1_PIN_LIST)
		#set only configured 
		#pins for main method
		else:
			query = 'SELECT pins FROM gpioneer'
			self.PIN_LIST = sorted(set([pins 
										for combo 
										in self.CC.execute(query).fetchall()
										for pins in eval(combo[0] + ',')]))
		
		#supposedly not necessary
		#but some pins didn't register correctly
		#without this first cleanup
		GPIO.cleanup(self.PIN_LIST)
		self.COMBO_TIME = max(args.combo_time / 1000, 0.0)
		self.KEY_REPEAT = args.key_repeat / 1000
		self.KEY_DELAY = args.key_delay / 1000
		
		if args.configure:
			self.debounce = max(self.debounce, 250)
			self.COMBO_TIME = max(self.COMBO_TIME, 0.1)
		
		
	def __init__(self, args):
		
		#set signal handlers
		signal.signal(signal.SIGINT, self.signal_handler)
		signal.signal(signal.SIGTERM, self.signal_handler)

		#Connect to database
		path = '/home/pi/pimame/pimame-menu/database/'
		self.DATABASE_PATH = os.path.realpath(path)
		
		#use current folder if piplay not installed
		if not os.path.isdir(self.DATABASE_PATH):
			self.DATABASE_PATH = os.path.join(os.path.realpath(sys.argv[0]),'web-frontend/')
			
		self.CONFIG = sqlite3.connect(os.path.join(self.DATABASE_PATH, 'config.db'), 
																check_same_thread=False)
		self.CC = self.CONFIG.cursor()
		
		#Create database table
		query = ' '.join(['CREATE TABLE IF NOT EXISTS gpioneer', 
						'(id INTEGER PRIMARY KEY AUTOINCREMENT',
						'UNIQUE, name TEXT UNIQUE, command TEXT, pins TEXT)'])
		self.CC.execute(query)
		self.CONFIG.commit()
		
		#set config flags
		self.set_args(args)
		
		#i2c resistor check
		self.RC = {3: GPIO.PUD_UP,
						5: GPIO.PUD_UP}
		
		#setup pins
		self.PIN_LIST = [{'#': pin, 
								#set pulldown/pullup (21,22)
								'pull': self.RESISTOR_PULL if pin not in [3,5] 
								else self.I2C_RESISTOR_PULL,
								#set rising/falling (31,32)
								'event': self.RESISTOR_PULL + 10 if pin not in [3,5] 
								else self.I2C_RESISTOR_PULL + 10}
								for pin in self.PIN_LIST]
		
		#set pins
		for pin in self.PIN_LIST:
			GPIO.setup(pin['#'], GPIO.IN, pull_up_down=pin['pull'])

		self.running = True
		if args.configure: 
			self.configure()
		else:
			self.main()

			
	def prompt(self, text, timeout=5.0, choices = None, default = False):
		answer = ''
		if not choices:
			choices = {'yes': True, 'no': False}
		sys.stdout.flush()
		while not answer and timeout >= 0:
			sys.stdout.write('\r[%ds] %s ' % (timeout, text)),
			sys.stdout.flush()
			rlist, _, _ = select.select([sys.stdin], [], [], 1)
			if rlist:
				answer = sys.stdin.readline().replace('\n','').lower()
			timeout -= 1
		sys.stdout.flush()
		print '\r' + ('  ' * 30) + '\r',
		if answer:
			for key, value in choices.iteritems():
				if answer in key:
					return value
		return default
	
	#-------------------------- MAIN FUNCTIONS ---------------------------------
	#---------------------------------------------------------------------------
	def button_pressed(self, channel, wait = 0.02):
		time.sleep(wait)
		#22 = pressed
		#LOW->0 + PULLUP->22 = 22
		#HIGH->1 + PULLDOWN->21 = 22
		return GPIO.input(channel) + self.RC.get(channel, self.RESISTOR_PULL) == 22
	
	
	def set_bitmask(self, channel):
		bit = (1L << channel)
		if self.button_pressed(channel, self.POLL_RATE):
			self.bitMask |= bit #add channel
		else:
			self.bitMask &= ~(bit) #remove channel
			self.update = True
		
		
	def emit_key(self, keys, value):
		for key in keys:
			self.ui.write(e.EV_KEY, eval(key), value)
			time.sleep(self.KEY_DELAY)
	
	def exec_command(self, commands):
		for command in commands:
			subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
			
			
			
	def compare_bitmask(self):
		currentMask = 0L
		current_time = time.time()
		for b in self.button_map:
			if (self.bitMask & b.mask) == b.mask:
				if not b.time_stamp: b.time_stamp = current_time
				if not (currentMask & b.mask) == b.mask:
					currentMask |= b.mask
					if b.key: 
						if current_time - b.time_stamp > self.KEY_REPEAT:
							b.pressed = 2
						elif not b.pressed:
							b.pressed = 1
						self.emit_key(b.key, b.pressed)
					if b.command: self.exec_command(b.command)
			else:
				if b.time_stamp and b.pressed:
					b.pressed = 0
					b.time_stamp = 0
					if b.key: self.emit_key(b.key, b.pressed)
		self.ui.syn()
		self.bitMask = 0L
		for pin in self.PIN_LIST:
			if self.button_pressed(pin['#'], wait = 0.0):
				self.bitMask |= (1L << pin['#'])

			
	def main(self):
		self.bitMask = 0L
		self.update = False
		query = 'SELECT name, pins, command FROM gpioneer'
		temp = self.CC.execute(query).fetchall()
		self.button_map = {}
		
		#Create list of commands for each button
		#if same button assigned to multiple commands
		#we will iterate over each command/key
		if not temp:
			print 'No pins set! Please run configuration! sudo python Gpioneer -c'
			sys.exit()
		for entry in temp:
			temp_button = button(entry[0], entry[1], entry[2])
			if temp_button.mask in self.button_map:
				self.button_map[temp_button.mask].append(entry[2])
			else:
				self.button_map[temp_button.mask] = temp_button
		#sort button_map, combos first
		self.button_map = sorted([value 
								for key, value in self.button_map.iteritems()], 
								key = lambda x: x.is_combo, reverse = True)
		
		#add event listener for each pin
		for pin in self.PIN_LIST:
			GPIO.add_event_detect(pin['#'], GPIO.BOTH, 
												callback=self.set_bitmask, 
												bouncetime = self.debounce)
		try:
			while self.running:
				time.sleep(self.COMBO_TIME)
				if self.bitMask or self.update:
					self.update = False
					self.compare_bitmask()
		except KeyboardInterrupt:
			GPIO.cleanup(self.PIN_LIST)       # clean up GPIO on CTRL+C exit
		GPIO.cleanup(self.PIN_LIST)           # clean up GPIO on normal exit

		
	#------------------------ CONFIG FUNCTIONS ---------------------------------
	#---------------------------------------------------------------------------
	def get_control_name(self):
		if self.controls[self.index][0] == '*':
			control_name = self.current_control[1:]
		else:
			prefix = 'P' + str(self.current_player + 1) + '_'
			control_name = prefix + self.current_control
		
		return control_name
		
		
	def add_channel(self, channel):
		if not channel in self.current_channel_list:
			self.current_channel_list.append(channel)
	
	
	def configure_channel(self, channel_list):
		print 'Pin(s)', pcolor('cyan', str(channel_list)), 'activated'
		if self.current_control:
			self.current_channel = channel_list
			if self.current_channel == self.previous_channel:
				
				#get key name, ex. KEY_A
				if self.current_control in self.keys: 
					key = self.keys[self.current_control][self.current_player]
				else:
					key = self.keys['BUTTONS'][self.current_button_key]
					self.current_button_key = min(self.current_button_key + 1, 
												len(self.keys['BUTTONS']) - 1)
				
				#set arbitrary control name (for id in database)
				control_name = self.get_control_name()

				#add info to button mapping
				if self.current_channel != self.skipKey:
					channels = str(self.current_channel).strip('[]')
					self.current_player_mapping.append([control_name, key, channels])

					print 'mapped to %s' % pcolor('cyan', key)
					print '----------------'
				else:
					print 'Skipping current control'
					print '----------------'
				
				if control_name == "P1_UP": 
					self.skipKey = self.current_channel
					print pcolor('fuschia', 'Press P1_UP (x2) to bypass any config')
					print '---------------'
				
				#proceed to next button
				#else: prompt to configure another player
				#write everything to database if user is done
				self.previous_channel = None
				if self.index < len(self.controls) - 1:
					self.index += 1
				else:
					answer = self.prompt("Would you like to configure another player? (y/n)", 10.0)
					if answer == True and self.current_player < 4:
						self.current_player += 1
						self.index = 0
					elif answer == False or self.current_player == 4:
						os.system('clear')
						if self.current_player == 4: print 'Cannot configure any more players'
						print 'Saving configuration...', 
						self.CC.execute('DELETE FROM gpioneer')
						query = 'INSERT INTO gpioneer (name, command, pins) VALUES (?,?,?)'
						self.CC.executemany(query, self.current_player_mapping)
						self.CONFIG.commit()
						print 'Finished'
						self.running = False
			else:
				self.previous_channel = self.current_channel


	def configure(self):
		os.system('clear')
		self.current_control = None
		self.current_channel = None
		self.previous_channel = None
		self.skipKey = None
		self.current_player_mapping = []
		self.index = 0
		self.current_channel_list = []
		self.current_player = 0
		self.current_button_key = 0
		self.keys = {'UP': ['KEY_UP', 'KEY_W', 'KEY_KP8', 'KEY_I'],
						'DOWN': ['KEY_DOWN', 'KEY_S', 'KEY_KP2', 'KEY_K'],
						'LEFT': ['KEY_LEFT', 'KEY_A', 'KEY_KP4', 'KEY_J'],
						'RIGHT': ['KEY_RIGHT', 'KEY_D', 'KEY_KP6', 'KEY_L'],
						'START': ['KEY_Z', 'KEY_X', 'KEY_C', 'KEY_V'],
						'SELECT': ['KEY_B', 'KEY_N', 'KEY_M', 'KEY_COMMA'],
						'COIN': ['KEY_KP1', 'KEY_KP3', 'KEY_7', 'KEY_9'],
						'*EXIT': ['KEY_ESC'],
						'BUTTONS': ['KEY_ENTER', 'KEY_Q', 'KEY_E', 
										'KEY_R', 'KEY_T', 'KEY_Y', 'KEY_U', 
										'KEY_O', 'KEY_P', 'KEY_F', 'KEY_G', 
										'KEY_H', 'KEY_LEFTBRACE', 
										'KEY_RIGHTBRACE', 'KEY_SEMICOLON',
										'KEY_APOSTROPHE', 'KEY_DOT', 
										'KEY_SLASH', 'KEY_BACKSLASH', 
										'KEY_LEFTCTRL', 'KEY_RIGHTCTRL',
										'KEY_LEFTALT', 'KEY_RIGHTALT', 
										'KEY_MINUS', 'KEY_EQUAL',
										'KEY_LEFTSHIFT', 'KEY_RIGHTSHIFT', 
										'KEY_KPMINUS', 'KEY_KPPLUS', 
										'KEY_KPASTERISK']}
		
		#add event listener for each pin
		for pin in self.PIN_LIST:
			GPIO.add_event_detect(pin['#'], pin['event'], 
									callback=self.add_channel,
									bouncetime = self.debounce)
		
		self.controls = (['UP', 'DOWN', 'LEFT', 'RIGHT'] + 
							['*EXIT', 'START', 'SELECT', 'COIN'] +
							['BUTTON ' + str(x) 
							for x in range(1, self.BUTTON_COUNT + 1)])
		
		print 'Press Ctrl + C to quit'
		print
		while self.running:
			time.sleep(self.COMBO_TIME)
			if self.current_control != self.controls[self.index]:
				self.current_control = self.controls[self.index]
				while '*' in self.controls[self.index] and self.current_player:
					if self.index < len(self.controls) - 1:
						self.index += 1
						self.current_control = self.controls[self.index]
				print 'Press %s twice' % pcolor('fuschia', self.current_control)
				time.sleep(.1)
			if self.current_channel_list:
				self.configure_channel(sorted(set((self.current_channel_list))))
				self.current_channel_list = []



a = Gpioneer(args)
