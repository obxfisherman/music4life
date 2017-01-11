#!/usr/bin/env python
import RPi.GPIO as GPIO  
import smbus
import pygame
import json
import time
import os
import logging
import logging.handlers
import argparse
import sys
import signal

### Music for Life, v1
# 12.6.16 initial
# 1.9.17 updated to read m4l.config file
# 1.10.17 added logging & gracefull killer

version='v1.3'

# Deafults
LOG_FILENAME = "/tmp/m4l.log"
LOG_LEVEL = logging.INFO  # Could be e.g. "DEBUG" or "WARNING"

# Define and parse command line arguments
parser = argparse.ArgumentParser(description="Music For Life Python service")
parser.add_argument("-l", "--log", help="file to write log to (default '" + LOG_FILENAME + "')")

# If the log file is specified on the command line then override the default
args = parser.parse_args()
if args.log:
        LOG_FILENAME = args.log

# Configure logging to log to a file, making a new file at midnight and keeping the last 3 day's data
# Give the logger a unique name (good practice)
logger = logging.getLogger(__name__)
# Set the log level to LOG_LEVEL
logger.setLevel(LOG_LEVEL)
# Make a handler that writes to a file, making a new file at midnight and keeping 3 backups
handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when="midnight", backupCount=3)
# Format each log message like this
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
# Attach the formatter to the handler
handler.setFormatter(formatter)
# Attach the handler to the logger
logger.addHandler(handler)

# Make a class we can use to capture stdout and sterr in the log
class MyLogger(object):
        def __init__(self, logger, level):
                """Needs a logger and a logger level."""
                self.logger = logger
                self.level = level

        def write(self, message):
                # Only log if there is a message (not just a new line)
                if message.rstrip() != "":
                        self.logger.log(self.level, message.rstrip())

# Replace stdout with logging to file at INFO level
sys.stdout = MyLogger(logger, logging.INFO)
# Replace stderr with logging to file at ERROR level
sys.stderr = MyLogger(logger, logging.ERROR)

class GracefulKiller():
  kill_now = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self,signum, frame):
    self.kill_now = True

#-----music 4 life starts here, crap above is for logging daemon use
get_input= raw_input

program_location='/home/pi/share/music4life'

pi=True        # set to true to actually interface with the pi

# data array, access it using m4life[row][column]  column names defined below
m4life=[[17,0b00000001,0b00000000,'wav/snd_death.wav','Death'],
    [27,0b00000001,0b00000000,'wav/snd_married_bros.wav','Married Brethern'],
    [5, 0b00001000,0b00000000,'wav/snd_married_sis.wav','Married Sisters'],
    [22,0b00000100,0b00000000,'wav/snd_widowers.wav','Widowers'],
    [6, 0b00010000,0b00000000,'wav/snd_widows.wav','Widows'],
    [13,0b00100000,0b00000000,'wav/snd_single_bros.wav','Single Brothers'],
    [19,0b01000000,0b00000000,'wav/snd_single_sis.wav','Single Sisters'],
    [26,0b10000000,0b00000000,'wav/snd_old_boys.wav','Older Boys'],
    [21,0b00000000,0b00000001,'wav/snd_old_girls.wav','Older Girls'],
    [20,0b00000000,0b00000010,'wav/snd_little_bros.wav','Little Boys'],
    [16,0b00000000,0b00000100,'wav/snd_little_sis.wav','Little Sisters']]

piGPIO=0    # 1st column in m4life
bankA=1     # 2nd column in m4life
bankB=2     # 3rd column in m4life
wavfile=3   # 4th column in m4life
label=4     # 5th column in m4life
wavsnd=5    # this gets added later

DEVICE = 0x20 # Device address (A0-A2)
IODIRA = 0x00 # Pin direction register bank A
OLATA  = 0x14 # Register for outputs bank A
IODIRB = 0x01 # Pin direction register bank B
OLATB  = 0x15 # Register for outputs bank B


# --------------------------------------------------------------------------
def gpio_setup():
    print 'configuring Pi GPIO input ports: ',
    for line in m4life:
        if pi: GPIO.setup(line[piGPIO], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)    # set as input (button)
        print line[piGPIO],
    print '\nconfiguring MCP23017 expander chip ',

    if pi:
        # Set all GPA pins as outputs by setting
        # all bits of IODIRA register to 0
        bus.write_byte_data(DEVICE,IODIRA,0x00)
        bus.write_byte_data(DEVICE,IODIRB,0x00)
         
        # Set output all 7 output bits for each bank to 0
        bus.write_byte_data(DEVICE,OLATA,0) 
        bus.write_byte_data(DEVICE,OLATB,0) 
        print 'ok'
        log_msg('gpio setup')
    else:
        print 'skipped'


# --------------------------------------------------------------------------
def load_wav():
    print 'loading wav files: ',
    for line in m4life:
        print line[wavfile],
        snd=pygame.mixer.Sound(os.path.join(program_location, line[wavfile]))
        line.append(snd)
    print '\nfinished loading wav'
    log_msg('wav files loaded')

# --------------------------------------------------------------------------
def led_test(delay=0.1):
    print "LED test"
    if pi:
        for line in m4life:
            bus.write_byte_data(DEVICE,OLATA,line[bankA])
            bus.write_byte_data(DEVICE,OLATB,line[bankB])
            sleep(delay)
        bus.write_byte_data(DEVICE,OLATA,0) #turn off all button led
        bus.write_byte_data(DEVICE,OLATB,0) #turn off all button led
    log_msg('led test')

# --------------------------------------------------------------------------
def led_off():
    bus.write_byte_data(DEVICE,OLATA,0) #turn off all button led
    bus.write_byte_data(DEVICE,OLATB,0) #turn off all button led

# --------------------------------------------------------------------------
def log_msg(msg='na'):
    fn = os.path.join(program_location, 'logs', time.strftime('%Y-%m-%d') + '.log')
    tm= time.strftime('%H:%M:%S')
    f=open(fn, 'a')
    f.write('{} {}\n'.format(tm, msg))
    f.close

# --------------------------------------------------------------------------
if __name__ == "__main__":
    print '\nMusic for Life {}'.format(version)
    print 'pygame init'
    log_msg('program start {}'.format(version))
    pygame.mixer.pre_init(44100, -16, 2, 2048) # setup mixer to avoid sound lag
    pygame.init()  

    # this incorporates the MCP23017 expander chip to control the LED
    if pi: GPIO.setmode(GPIO.BCM)     # set up BCM GPIO numbering 
    if pi: bus = smbus.SMBus(1) # Rev 2 Pi uses 1

    print 'loading config'
    f=open(os.path.join(program_location, 'm4l.config'),'r')
    m4life=json.load(f)
    f.close
    log_msg('config loaded')

    gpio_setup()
    load_wav()
    #led_test()

    killer = GracefulKiller()
    playing=False
    try:
        print 'ready for button presses!'
        log_msg('ready')
        while True:
            for line in m4life:
                if GPIO.input(line[piGPIO]) and playing==False:
                    bus.write_byte_data(DEVICE,OLATA,line[bankA])
                    bus.write_byte_data(DEVICE,OLATB,line[bankB])
                    line[wavsnd].play()
                    print line[label]
                    log_msg(line[label])
                    playing=True
            if playing:
                if pygame.mixer.get_busy()==False:
                    if pi: bus.write_byte_data(DEVICE,OLATA,0) #turn off all button led
                    if pi: bus.write_byte_data(DEVICE,OLATB,0) #turn off all button led
                    playing=False
            if killer.kill_now:
                log_msg('terminate signal received')
                print 'terminate signal received'
                break

    finally:
        GPIO.cleanup()
        led_off()
        print 'done'
        log_msg('program end')