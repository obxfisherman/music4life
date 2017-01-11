import RPi.GPIO as GPIO  
import smbus
import pygame
from time import sleep
from timeit import default_timer as timer
import json

get_input = raw_input

# all the valid R pi button inputs
btns=[26,19,13,6,5,22,21,20,16,12,7,8]

#all the valid LED register combos
leds=[[128,0],
    [64,0],
    [32,0],
    [16,0],
    [8,0],
    [4,0],
    [0,1],
    [0,2],
    [0,4],
    [0,8],
    [0,16],
    [0,32]]

# data array, access it using m4life[row][column]  column names defined below
m4life=[[26,0,0,'wav/snd_death.wav','Death'],
    [19,0,0,'wav/snd_married_bros.wav','Married Brethern'],
    [13,0,0,'wav/snd_married_sis.wav','Married Sisters'],
    [6,0,0,'wav/snd_widowers.wav','Widowers'],
    [5,0,0,'wav/snd_widows.wav','Widows'],
    [22,0,0,'wav/snd_single_bros.wav','Single Brothers'],
    [21,0,0,'wav/snd_single_sis.wav','Single Sisters'],
    [20,0,0,'wav/snd_old_boys.wav','Older Boys'],
    [16,0,0,'wav/snd_old_girls.wav','Older Girls'],
    [12,0,0,'wav/snd_little_bros.wav','Little Boys'],
    [7,0,0,'wav/snd_little_sis.wav','Little Sisters']]

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
def get_key_input(msg='? ', default=''):
    try:
        cmd = get_input(msg.format(default))
    except:
        cmd = default
    if cmd=='':
        return default
    else:
        return cmd

# --------------------------------------------------------------------------
def poll_buttons(timeout=4):
    timeexpires=timer()+timeout
    while timer()<timeexpires:
        for btn in btns:
            if GPIO.input(btn):
                #print 'Button press {}'.format(btn)
                return btn
    return False

# --------------------------------------------------------------------------
def button_identify():
    print 'Identify GPIO button, timeout in 10s'
    b=poll_buttons(10)
    print 'GPIO button {} pressed'.format(b)

# --------------------------------------------------------------------------
def display_data():
    print     'Button          GPIO ledA ledB'
    for line in m4life:
        print '{:16.12} {:3} {:3} {:3}'.format(line[label], line[piGPIO], line[bankA], line[bankB])

# --------------------------------------------------------------------------
def assign_buttons():
    print 'This will assign buttons to the displayed sound.\nYou have 10s to press the corresponding button'
    for line in m4life:
        print '\nPress {}'.format(line[label])
        b=poll_buttons(10)
        if b:
            line[piGPIO]=b
            print 'GPIO {} assigned to {}'.format(b, line[label])
            sleep(3)
        else:
            print 'failed to press button {}'.format(line[label])
            break

# --------------------------------------------------------------------------
def assign_led():
    print 'When a button illuminates, press it.'
    for led in leds:
        print '\nPress the illuminated button'
        bus.write_byte_data(DEVICE,OLATA,led[0])
        bus.write_byte_data(DEVICE,OLATB,led[1])
        b=poll_buttons(10)
        if b:
            for line in m4life:
                if line[piGPIO]==b:
                    line[bankA]=led[0]
                    line[bankB]=led[1]
                    print 'LED ({},{}) assigned to {}, {}'.format(line[bankA], line[bankB], line[piGPIO], line[label])
                    sleep(3)
        else:
            print 'failed to press button'
            break

# --------------------------------------------------------------------------
def test_all():
    print '\nPress any button to test. LED should illuminate, label should display'
    running=True
    while running:
        for line in m4life:
            if GPIO.input(line[piGPIO]):
                print '{}'.format(line[label])
                bus.write_byte_data(DEVICE,OLATA,line[bankA])
                bus.write_byte_data(DEVICE,OLATB,line[bankB])                
                running=False
    sleep(2)
    bus.write_byte_data(DEVICE,OLATA,0b00000000)
    bus.write_byte_data(DEVICE,OLATB,0b00000000) 


# --------------------------------------------------------------------------
if __name__ == "__main__":
    print '\nMusic for Life Configurator v1\nAssign buttons first then assign LEDs'
    print 'ab=assign buttons, al=assign LEDs, q=quit program, load=load config'
    print 'save=save config, bt=identify single button'
    GPIO.setmode(GPIO.BCM)      # set up BCM GPIO numbering 
    bus = smbus.SMBus(1)        # Rev 2 Pi uses 1
    for btn in btns:
        GPIO.setup(btn, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    # Set all GPA pins as outputs by setting
    # all bits of IODIRA register to 0
    bus.write_byte_data(DEVICE,IODIRA,0x00)
    bus.write_byte_data(DEVICE,IODIRB,0x00)
    bus.write_byte_data(DEVICE,OLATA,0b00000000)
    bus.write_byte_data(DEVICE,OLATB,0b00000000) 

    while True:
        cmd=get_key_input()
        cmd=cmd.lower()

        if cmd=='q':        # quit
            print 'quit'
            break

        if cmd=='bt':       # button test
            button_identify()

        if cmd=='data':     # list data
            display_data()

        if cmd=='load':
            print 'loading config'
            f=open('m4l.config','r')
            m4life=json.load(f)
            f.close
            display_data()

        if cmd=='save':
            print 'saving config'
            f=open('m4l.config','w')
            json.dump(m4life, f)
            f.close

        if cmd=='ab':
            assign_buttons()

        if cmd=='al':
            assign_led()

        if cmd=='test':
            test_all()

    GPIO.cleanup()
    bus.write_byte_data(DEVICE,OLATA,0b00000000)
    bus.write_byte_data(DEVICE,OLATB,0b00000000)
    pygame.quit()