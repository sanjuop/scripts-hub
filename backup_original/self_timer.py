import pyautogui
import datetime
import random
import re
from sys import exit
resolution = pyautogui.size()

pyautogui.FAILSAFE = False
width = resolution.width
height = resolution.height

check = True
exit_time = "19:16:0"
while True:
    if check:
        x = datetime.datetime.now()
        time = x.time()
        hour = str(time.hour) 
        minutes = str(time.minute)
        seconds = str(time.second)
        str_time = "{}:{}:{}".format(hour, minutes, seconds)
        if str_time != exit_time:
            if re.search("5|0", minutes) and (seconds == "0"):
                random_width = random.randint(1,
                width)
                random_height = random.randint(1, height)
                pyautogui.moveTo(random_width, random_height)
                # pyautogui.click(random_width, random_height)
                print ("yesssssssssssssssssssssssssssssssss",hour, minutes, seconds)
        else:
            check = False
    else:
        print ("exit @", exit_time)
        exit() 


# pyautogui.moveTo(100, 100, duration=0.25)
# pyautogui.moveTo(200, 100, duration=0.25)
# pyautogui.moveTo(200, 200, duration=0.25)
# pyautogui.moveTo(100, 200, duration=0.25)