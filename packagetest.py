#!/usr/bin/env python2
# -*- coding: utf-8 -*- 

import os
import argparse
from icserelay import icserelay #module import

#default parameter
DF_DEVPATH = '/dev'
DF_STATUSFILE = '-status'
DF_STFPATH = os.path.dirname(os.path.abspath(icserelay.__file__))

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

#main section
icse = icserelay.ICSE(args.DEVICE, args.device_path, args.status_file, args.status_file_path, args.forcech) #CLASS set

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
		result = icse.allopen() #all channels open(relay off)
	elif args.all_close:
		result = icse.allclose() #all channels close(relay on)
	else:
		if len(args.closelist)>1 or len(args.openlist)>1:
			result = icse.changebylist(args.closelist, args.openlist, args.priority_close, args.serial_off) #channels change by list[ch,]
		elif args.closelist == [] and len(args.openlist) == 1:
			result = icse.changebych(args.openlist[0], "open", args.serial_off) #only one channel open by int(ch)
		elif args.openlist == [] and len(args.closelist) == 1:
			result = icse.changebych(args.closelist[0], "close", args.serial_off) #only one channel close by int(ch)
		else: #-o,-c,-ao,-ac are not
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
