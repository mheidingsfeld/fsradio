#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'fsradio'))

from fsradio import FsRadio, FsRadioModes

fsr = FsRadio("192.168.1.5")

#%%
fsr.power_on()

#%%
fsr.set_mode(FsRadioModes.INTERNET_RADIO)

#%%
fsr.increase_volume()

#%%
fsr_power_off()