#!/bin/bash

# https://askubuntu.com/questions/252743/how-do-i-prevent-mouse-movement-from-waking-up-a-suspended-computer
# Run `cat /proc/acpi/wakeup`
#
# Device  S-state   Status   Sysfs node
# RP01      S4    *disabled
# PXSX      S4    *disabled
# RP02      S4    *disabled
# PXSX      S4    *disabled
# ...
echo XHC > /proc/acpi/wakeup
echo RP09 > /proc/acpi/wakeup
echo RP13 > /proc/acpi/wakeup
echo LID0 > /proc/acpi/wakeup

# https://unix.stackexchange.com/questions/236127/acpi-wakeup-4-letters-code-meaning
# RP0x or EXPx: PCIE slot #x (aka PCI Express Root Port #x)
#
# https://askubuntu.com/questions/509017/desktop-wakes-from-suspend-at-random-14-04
# `EHC1`, `EHC2` and `XHC `represent USB controllers. Obivously `USB1 - USB7` as well, but they are
# all disabled in my case. I can't go into specifics because I don't know much about it.
#
# I would think that `PWRB` (last line) represents the power button. It would be a good idea to
# leave it enabled, since you probably want to be able to wake your computer up by using the power
# button.
#
# By giving the command `sudo sh -c "echo EHC1 > /proc/acpi/wakeup"` you toggle the setting for
# `EHC1`. If you run the command to list the devices again you will see that the setting for `EHC1`
# has changed.
#
# I tried this with the controllers `EHC1`, `EHC2`, `XHC` since I don't know
# what controller controls what USB device.
#
# For me, leaving `EHC1` and `XHC `enabled and disabling `EHC2` gives me the
# result I wanted. Now neither the keyboard or the mouse (even if turned on) can
# cause a wake up. I have to press the physical power button on the computer
# itself.
#
# Unfortunately the setting will be reset when you reboot. To combat this, you can put the code
# below in your `/etc/rc.local`. It must be edited using elevated privilegies: `sudo gedit
# /etc/rc.local` for example.
#
#     for device in EHC2
#     do
#         if grep -q "$device.*enabled" /proc/acpi/wakeup
#         then
#             echo $device > /proc/acpi/wakeup
#         fi
#     done
#
# You can add more devices by changing the first line in the code: `for device in EHC1 EHC2 XHC
# USB1` and so on. I found the script, [written by user
# toojays](https://askubuntu.com/a/308740/474925).
#
