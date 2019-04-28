# icserelay
ICStation usb-relay controller by Python2.7

__Usage__  
Please read helper:  
    'icserelay/icserelay.py --help' or 'packagetest.py --help'  

As an example:  
(Start up ttyUSB0)  
./icserelay.py ttyUSB0 -stu  
(close channel 0 and 2)  
./icserelay.py ttyUSB0 -c 0,2  
(close channel 1, open channel 0)  
./icserelay.py ttyUSB0 -o 0 -c 1  
(close all channels)  
./icserelay.py ttyUSB0 -ao  
(open all channels)  
./icserealy.py ttyUSB0 -ac

I test this only in ICSE014A.  
I am not confident of operation at 012A and 013A.
  

In making, I referred to https://github.com/xypron/icsectl.  
I thank for Heinrich Schuchardt.
