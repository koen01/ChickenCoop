#!/usr/bin/env python
# coding: latin-1
 
# Import library functions we need
import PicoBorgRev
import thread
import time
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
import httplib, urllib
import base64
import urllib2

# Settings for the domoticz server
domoticzserver="xxxx:8080"
domoticzusername = "xxxx"
domoticzpassword = "xxxx"
base64string = base64.encodestring('%s:%s' % (domoticzusername, domoticzpassword)).replace('\n', '')
switchid = '111'

#Function for pushovermessages
def send_message(message):
	conn = httplib.HTTPSConnection("api.pushover.net:443")
	conn.request("POST", "/1/messages.json",
	  urllib.urlencode({
	    "token": "xxxx",
	    "user": "xxxx",
	    "title" : "Kippenhok",
	    "message": message,
	  }), { "Content-type": "application/x-www-form-urlencoded" })
	conn.getresponse()
	return
# Domotics login
def domoticzrequest (url):
  request = urllib2.Request(url)
  request.add_header("Authorization", "Basic %s" % base64string)
  response = urllib2.urlopen(request)
  return response.read()

 
# Name the global variables
global PBR
PBR = PicoBorgRev.PicoBorgRev()
contact1 = 23
contact2 = 24
TimeStart = time.time()
runtime = 0
MaxRunTime = int(300)


#Pin Setup 
GPIO.setup(contact1, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # activate input with PullUp
GPIO.setup(contact2, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # activate input with PullUp

sensor1 = GPIO.input(23)
sensor2 = GPIO.input(24)

# Setup the PicoBorg Reverse
PBR = PicoBorgRev.PicoBorgRev()
#PBR.i2cAddress = 0x44                   # Uncomment and change the value if you have changed the board address
PBR.Init()
if not PBR.foundChip:
    boards = PicoBorgRev.ScanForPicoBorgReverse()
    if len(boards) == 0:
        print 'No PicoBorg Reverse found, check you are attached :)'
    else:
        print 'No PicoBorg Reverse at address %02X, but we did find boards:' % (PBR.i2cAddress)
        for board in boards:
            print '    %02X (%d)' % (board, board)
        print 'If you need to change the I²C address change the setup line so it is correct, e.g.'
        print 'PBR.i2cAddress = 0x%02X' % (boards[0])
    sys.exit()
#PBR.SetEpoIgnore(True)                 # Uncomment to disable EPO latch, needed if you do not have a switch / jumper
PBR.ResetEpo()

def get_door_status():
	    if GPIO.input(23) == True and GPIO.input(24) == False: door_status = 'Open'
	    elif GPIO.input(23) == False and GPIO.input(24) == True: door_status = 'Closed'
	    elif GPIO.input(23) == True and GPIO.input(24) == True: door_status = 'Moving'
 	    else: door_status = 'Unknown'
	    return door_status

while True:
	door = get_door_status()
	if runtime <=  MaxRunTime and door == 'Closed' or runtime <=  MaxRunTime and door =='Moving':
		PBR.SetMotor1(1)
		print 'Opening door!' + '    ' 'Status:' + ' ' + str(door)
		runtime = int(runtime + (time.time() - TimeStart))
		print runtime
		time.sleep(1)
	elif door == 'Open':
		print 'Stop motor'
		PBR.MotorsOff()
		GPIO.cleanup()
		domoticzrequest("http://" + domoticzserver + "/json.htm?type=command&param=switchlight&idx=" + switchid + "&switchcmd=On&level=0")
		runtime = float(time.time() - TimeStart)
		text = 'Door status:' + door + '  ' +'Runtime:' + str(runtime)
		send_message(text)			
		break
	else:
                print 'MaxRunTime exceeded!'
                PBR.MotorsOff()
                GPIO.cleanup()
                runtime = float(time.time() - TimeStart)
                text = 'MaxRunTime exceeded!' + '   ' + 'Door status:' + door + '  ' +'Runtime:' + str(runtime)
                send_message(text)
                break
