#!/usr/bin/env python2
# -*- coding: utf-8 -*- 

import os
import sys
import serial
import pickle
import argparse

#default parameter
DF_DEVPATH = '/dev'
DF_STATUSFILE = '-status'
DF_STFPATH = os.path.dirname(os.path.abspath(__file__))
ICSE012A = 171 #0xAB 4chrelay
ICSE013A = 173 #0xAD 2chrelay
ICSE014A = 172 #0xAC 8chrelay

#direct run argument section
if __name__ == '__main__':
	tplist = lambda x:list(map(int, x.split(',')))

	parser = argparse.ArgumentParser(description='ICStation(PL2303) MicroUSB Relay module ICSE012A(4ch 0-3),ICSE013A(2ch 0,1),ICSE014A(8ch 0-7)\n' \
												 'CAUTION:Startup option is required at the time of the first start.\n' \
												 '         (If not startup, ICSE does not operate relay even if it receive bits.)\n' \
												 '        While power is on, please use only one time of startup option.\n' \
												 '         (When it recieved startup command after second,ICSE performs unanticipated relay operation.)\n'\
												 '        You should not use this with \'icseudev&99-icsectl.rules\'.\n' \
												 '        Because ICSE gives back ID number only once unless power reset.\n' \
												 '        Option\'s priority is \'-cl > -ao > -ac > -o > -c\'.', formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('DEVICE',help='tty device name{e.g. \'ttyUSB1\'}')
	parser.add_argument('-stu', '--startup', action='store_true', help='start up ICStation.\n(If status&type files are alived, send command \'0x51\'.\nElse, make files by command \'0x50&0x51\'.)')
	parser.add_argument('-o', '--openlist', type=tplist, default=[], help='circuit open(relay off) channle[LIST \',\']')
	parser.add_argument('-c', '--closelist', type=tplist, default=[], help='circuit close(relay on) channel[LIST \',\']')
	parser.add_argument('-ao', '--all_open', action='store_true', help='circuit all open(relay off)')
	parser.add_argument('-ac', '--all_close', action='store_true', help='circuit all close(relay on)')
	parser.add_argument('-dp', '--device_path', default=DF_DEVPATH, help='set device path default=%s' %DF_DEVPATH)
	parser.add_argument('-sf', '--status_file', default=DF_STATUSFILE, help='status file=\'DEVICE+status_file\'[e.g. \'ttyUSB1-status\']\ndefault=%s' %DF_STATUSFILE)
	parser.add_argument('-sp', '--status_file_path', default=DF_STFPATH, help='set status file path default=%s' %DF_STFPATH)
	parser.add_argument('-so', '--serial_off', action='store_true', help='only write status file, serial comuunication is off')
	parser.add_argument('-np', '--no_print', action='store_true', help='not print result')
	parser.add_argument('-pc', '--priority_close', action='store_true', help='In the case conflict lists,give a priority to close')
	parser.add_argument('-ch', '--forcech', type=int, help='set force channels\n(You should use this,only in case channels is mismatch or use unknown device')
	parser.add_argument('-cl', '--clear', action='store_true', help='delete status,type file & channels all open(switch off)')
	args = parser.parse_args()


#class define
class ICSE:
	def __init__(self, device, devpath=DF_DEVPATH, statusfile=DF_STATUSFILE, stfpath=DF_STFPATH, force_ch=0):
		self.ttydevice = devpath + "/" + device #device name(full path)
		self.statusfile = stfpath + "/" + device + statusfile #status file name(full path)
		self.typefile = stfpath + "/" + device + "-type" #type file name(full path)
		self.force_ch = force_ch
		self.channels = 0
		self.bitslist =[]
		self.basebits = 0
		self.bits = 0
		
		try:
			file = open(self.typefile, 'r')
#		except FileNotFoundError as err:
		except IOError as err:
			self.devicetype = "not identified"
		else:
			self.devicetype = file.read()
			file.close()
	
	def startup(self):
		#startup relay operation
		result = []
		if os.path.exists(self.statusfile):
			self.send_only_0x51()
			result.append('Find status file.')
			result.append('Start up relay operation.')
		else:
			result.append('Status file is not exists.')
			result.append(self.get_devicetype())
			if self.force_ch > 0:
				self.channels = self.force_ch
				result.append('Channels(={0}) set from force channels'.format(self.channels))
			self.bitslist = []
			if self.channels > 0:
				n = 0
				while n < self.channels:
					self.bitslist.append(1)
					n += 1
			else:
				result.append('Caution! Channels=0, please use force channels next time.') 
			file = open(self.typefile, 'w')
			file.write(self.devicetype)
			file.close
			self.write_status()
			result.append('Created type&status files.')
		return result
	
	def get_devicetype(self):
		#send command 0x50(get ID number),0x51(device startup)
		ser = serial.Serial(
			port = self.ttydevice, \
			baudrate =  9600, \
			stopbits = serial.STOPBITS_ONE, \
			bytesize = serial.EIGHTBITS, \
			timeout = .1)
		c = ser.read(1)
		ser.write(b'P') #send bytearray([0x50])=bytearray([0b1010000])=b'P'
		c = ser.read(1)
		if len(c) > 0:
			a = ord(c)
			if a == ICSE012A:
				channels = 4
				self.devicetype = "ICSE012A"
			elif a == ICSE013A:
				channels = 2
				self.devicetype = "ICSE013A"
			elif a == ICSE014A:
				channels = 8
				self.devicetype = "ICSE014A"
			else:
				channels = 0
				self.devicetype = "maybe other PL2303 device"
			result = 'Receive IDnum={0}, send startup(0x51).'.format(a)
			ser.write(b'Q') #send bytearray([0x51])=bytearray([0b1010001])=b'Q'
		else:
			try:
				file = open(self.typefile, 'r')
#			except FileNotFoundError as err:
			except IOError as err:
				self.devicetype = "unknown device"
			else:
				self.devicetype = file.read()
				file.close()
			channels = 0
			result = 'Can\'t receive IDnum, don\'t send startup(0x51).'
		ser.close() # Close serial connection
		self.channels = channels
		return result
	
	def send_only_0x51(self):
		#send command 0x51(device startup)
		ser = serial.Serial(
			port = self.ttydevice, \
			baudrate =  9600, \
			stopbits = serial.STOPBITS_ONE, \
			bytesize = serial.EIGHTBITS, \
			timeout = .1)
		ser.write(b'Q') #send bytearray([0x51])=bytearray([0b1010001])=b'Q'
		ser.close() # Close serial connection
	
	def read_status(self):
		try:
			file = open(self.statusfile, 'rb')
#		except FileNotFoundError as err:
		except IOError as err:
			if self.force_ch > 0:
				self.channels = self.force_ch
				self.bitslist = []
				n = 0
				while n < self.channels:
					self.bitslist.append(1)
					n += 1
				self.basebits = pow(2, self.channels) - 1
			return False
		self.bitslist = pickle.load(file)
		file.close()
		if self.force_ch > 0:
			back_bitslist = self.bitslist
			self.channels = self.force_ch
			self.bitslist = []
			n = 0
			while n < self.channels:
				if n < len(back_bitslist):
					self.bitslist.append(back_bitslist[n])
				else:
					self.bitslist.append(1)
				n += 1
		else:
			self.channels = len(self.bitslist)
		self.basebits = pow(2, self.channels) - 1
		return True
	
	def write_status(self):
		with open(self.statusfile, 'wb') as file:
			pickle.dump(self.bitslist, file)
	
	def set_openlist(self, openlist=[]):
		for ch in openlist:
			if ch < self.channels:
				self.bitslist[ch] = 1
	
	def set_closelist(self, closelist=[]):
		for ch in closelist:
			if ch < self.channels:
				self.bitslist[ch] = 0
	
	def make_bits(self):
		n=0
		self.bits=0
		while n<self.channels:
			if self.bitslist[n] == 0:
				self.bits += pow(2,n)
			n += 1
		self.bits = self.basebits - self.bits
	
	def send_serial(self):
		ser = serial.Serial(
			port = self.ttydevice, \
			baudrate =  9600, \
			stopbits = serial.STOPBITS_ONE, \
			bytesize = serial.EIGHTBITS, \
			timeout = .1)
		ser.write(bytearray([self.bits]))
		ser.close()
	
	def changebylist(self, closelist=[], openlist=[], priority_close=False, serial_off=False):
		result = []
		if not self.read_status():
			if self.channels > 0:
				result.append('Status file is not exists, use and create status file by force channels.')
			else:
				result.append('Status file is not exists, please use force channels next time.')
		else:
			result.append('Find status file.')
		if self.channels > 0:
			if priority_close:
				self.set_openlist(openlist)
				self.set_closelist(closelist)
			else:
				self.set_closelist(closelist)
				self.set_openlist(openlist)
			self.write_status()
			self.make_bits()
			if serial_off == False:
				self.send_serial()
		return result
	
	def changebych(self,ch, flag="open", serial_off=False):
		result = []
		if not self.read_status():
			if self.channels > 0:
				result.append('Status file is not exists, use and create status file by force channels.')
			else:
				result.append('Status file is not exists, please use force channels next time.')
		else:
			result.append('Find status file.')
		if self.channels > 0:
			if ch < self.channels:
				if flag == "open":
					self.bitslist[ch] = 1
				elif flag == "close":
					self.bitslist[ch] = 0
				self.write_status()
			self.make_bits()
			if serial_off == False:
				self.send_serial()
		return result
	
	def allclose(self, serial_off=False):
		result = []
		if not self.read_status():
			if self.channels > 0:
				result.append('Status file is not exists, use and create status file by force channels.')
			else:
				result.append('Status file is not exists, please use force channels next time.')
		else:
			result.append('Find status file.')
		if self.channels > 0:
			n=0
			while n < self.channels:
				self.bitslist[n] = 0
				n += 1
			self.write_status()
			self.make_bits()
			if serial_off == False:
				self.send_serial()
		return result
	
	def allopen(self, serial_off=False):
		result = []
		if not self.read_status():
			if self.channels > 0:
				result.append('Status file is not exists, use and create status file by force channels.')
			else:
				result.append('Status file is not exists, please use force channels next time.')
		else:
			result.append('Find status file.')
		if self.channels > 0:
			n=0
			while n < self.channels:
				self.bitslist[n] = 1
				n += 1
			self.write_status()
			self.make_bits()
			if serial_off == False:
				self.send_serial()
		return result
	
	def files_clear(self, serial_off=False):
		result = []
		serial = serial_off
		self.read_status()
		if self.channels > 0:
			if serial:
				result.append('Don\'t change channels,reason[serial off]')
			else:
				self.allopen()
				result.append('Channels were all opened.')
		else:
			result.append('Can\'t change channels,reason[channels=0]')
		if os.path.exists(self.statusfile):
			os.remove(self.statusfile)
			result.append("Statusfile was deleted.")
		else:
			result.append("Statusfile does not exist anymore.")
		if os.path.exists(self.typefile):
			os.remove(self.typefile)
			result.append("Typefile was deleted.")
		else:
			result.append("Typefile does not exist anymore.")
		return result


#direct use main section
if __name__ == '__main__':
	icse = ICSE(args.DEVICE, args.device_path, args.status_file, args.status_file_path, args.forcech) #CLASS set
	
	if args.startup:
		result = icse.startup() #first time startup ICstation
		if args.no_print == False:
			for n in result:
				print(n)
	
	if args.clear:
		result = icse.files_clear(args.serial_off) #delete status file & try all open
		if args.no_print == False:
			print('DeviceName = {0}, ch={1}'.format(icse.devicetype,icse.channels))
			print('Device = {0}'.format(icse.ttydevice))
			print('Status File = {0}'.format(icse.statusfile))
			print('type File = {0}'.format(icse.typefile))
			for n in result:
				print(n)
	else:
		if args.all_open:
			result = icse.allopen(args.serial_off) #all channels open(switch off)
		elif args.all_close:
			result = icse.allclose(args.serial_off) #all channels close(switch on)
		else:
			if len(args.closelist)>1 or len(args.openlist)>1:
				result = icse.changebylist(args.closelist, args.openlist, args.priority_close, args.serial_off) #channels change from lists
			elif args.closelist == [] and len(args.openlist) == 1:
				result = icse.changebych(args.openlist[0], "open", args.serial_off) #only one channel open
			elif args.openlist == [] and len(args.closelist) == 1:
				result = icse.changebych(args.closelist[0], "close", args.serial_off) #only one channel close
			else: #-o,-c,-ao,-ac was not
				if args.no_print == False:
					result = ['No change.']

		if args.no_print == False:
			print('DeviceName = {0}, ch={1}'.format(icse.devicetype,icse.channels))
			print('Device = {0}'.format(icse.ttydevice))
			print('Status File = {0}'.format(icse.statusfile))
			print('type File = {0}'.format(icse.typefile))
			print('Close List = {0}'.format(args.closelist))
			print('Open List = {0}'.format(args.openlist))
			print('Bits list = {0}'.format(icse.bitslist))
			print('Sending Bits = {0}[INT]'.format(icse.bits))
			print('             = {0}[BIN]'.format(bin(icse.bits)))
			print('             = {0}[HEX]'.format(hex(icse.bits)))
			for n in result:
				print(n)
	del icse #CLASS delete
