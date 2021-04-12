#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import logging
from enum import IntEnum, Enum
from bs4 import BeautifulSoup

class FsApiGetResponse:
    def __init__(self, text):
        self.ok = False
        self.status = None
        self.value = None

def parse_fsapi_get_response(text):
    response = FsApiGetResponse
    soup = BeautifulSoup(text, 'xml')
    response.status = soup.status.text  
    if "FS_OK" == soup.status.text:
        response.ok = True  
        if soup.value.find_all("u8"):
            response.value = int(soup.value.u8.text)
        if soup.value.find_all("u32"):
            response.value = int(soup.value.u32.text)
        if soup.value.find_all("c8_array"):
            response.value = soup.value.c8_array.text
    return response
            

def parse_fsapi_get_multiple_response(text):
    responses = [] 
    soup = BeautifulSoup(text, 'xml')
    for t in soup.find_all("fsapiMultipleGetResponse"):
        response = parse_fsapi_get_response(t.text)
        responses.append(response)    
    return responses


class FsApiNodes(str, Enum):
    SYS_POWER                = "netRemote.sys.power"
    SYS_MODE                 = "netRemote.sys.mode"
    SYS_AUDIO_VOLUME         = "netRemote.sys.audio.volume"
    SYS_AUDIO_MUTE           = "netRemote.sys.audio.volume"
    NAV_STATE                = "netRemote.nav.state"
    NAV_ACTION_SELECT_PRESET = "netRemote.nav.action.selectPreset"
    PLAY_INFO_TEXT           = "netRemote.play.info.text"
    PLAY_INFO_NAME           = "netRemote.play.info.name"    

class FsApi:
    FSAPI_URL_GET = "http://{0}:{1}/fsapi/GET/{3}?pin={2}"
    FSAPI_URL_SET = "http://{0}:{1}/fsapi/SET/{3}?pin={2}&value={4}"
    FSAPI_URL_GET_MULTIPLE = "http://{0}:{1}/fsapi/GET_MULTIPLE?pin={2}{3}"
    FSAPI_URL_SET_MULTIPLE = "http://{0}:{1}/fsapi/SET_MULTIPLE?pin={2}{3}"
    
    def __init__(self, host, port = "80", pin = "1234"):
        self.host = host
        self.port = port
        self.pin = pin
        
    def get(self, node):
        if not isinstance(node, FsApiNodes):
            logging.warning("GET unknown node: " + node)
            return None
            
        url = self.FSAPI_URL_GET.format(self.host, self.port, self.pin, node)
        logging.debug("GET request: " + url)
        response = requests.get(url, headers={"Connection":"close"})
        if response.ok:
            return parse_fsapi_get_response(response.content)
        else:
            logging.warning("GET request failed: " + response.status_code)
            return None
        
    def set(self, node, value):
        if not isinstance(node, FsApiNodes):
            logging.warning("GET unknown node: " + node)
            return None
        
        url = self.FSAPI_URL_SET.format(self.host, self.port, self.pin, node, value)
        logging.debug("SET request: " + url)
        response = requests.get(url, headers={"Connection":"close"})
        if response.ok:
            return response.content
        else:
            logging.warning("SET request failed: " + response.status_code)
            return None
    
    def get_multiple(self, nodes):
        if not all(isinstance(n, FsApiNodes) for n in nodes):
            logging.warning("GET unknown node: " + nodes)
            return None        
        
        nodes_url = ""
        for n in nodes:
            nodes_url = nodes_url + "&node=" + n
        url = self.FSAPI_URL_GET_MULTIPLE.format(self.host, self.port, self.pin, nodes_url)
        logging.debug("GET_MULTIPLE request: " + url)
        response = requests.get(url, headers={"Connection":"close"})
        if response.ok:
            return parse_fsapi_get_multiple_response(response.content)
        else:
            logging.warning("GET_MULTIPLE request failed: " + response.status_code)
            return None
    
    def set_multiple(self, nodes_values):
        # TODO
        pass
        
    
class FsRadioModes(IntEnum):
    """FsRadio operating modes"""

    INTERNET_RADIO = 0
    SPOTIFY        = 1
    PLAYER         = 2
    USB            = 3
    DAB_RADIO      = 4
    FM_RADIO       = 5
    BLUETOOTH      = 6
    AUX_IN         = 7
    

class FsRadio:
    MAX_VOLUME = 32
    
    def __init__(self, host, port = '80', pin = '1234'):
        self.fsapi = FsApi(host, port, pin)
    
    def set_power(self, value):
        self.fsapi.set(FsApiNodes.SYS_POWER, int(value))
        
    def power_on(self):
        self.set_power(1)
        
    def power_off(self):
        self.set_power(0)
        
    def get_mute(self):
        return self.fsapi.get(FsApiNodes.SYS_AUDIO_MUTE).value

    def set_mute(self, value):     
        self.fsapi.set(FsApiNodes.SYS_AUDIO_MUTE, int(value))
        
    def toggle_mute(self):
        self.set_mute(not self.get_mute())
        
    def get_volume_absolute(self):
        """ Read the radios volume """
        return self.fsapi.get(FsApiNodes.SYS_AUDIO_VOLUME).value
        
    def set_volume_absolute(self, value):
        """ Set the radios volume """
        if value >= 0 and value <= self.MAX_VOLUME:
            self.fsapi.set(FsApiNodes.SYS_AUDIO_MUTE, value)
        else:
            logging.warning("Invalid volume requested.")
            
    def get_volume_percent(self):
        return self.get_volume_absolute() / self.MAX_VOLUME
        
    def set_volume_percent(self, value):
        if value >= 0.0 and value <= 1.0:
            self.set_volume_absolute(round(value * self.MAX_VOLUME))
        else:
            logging.warning("Invalid volume requested.")
            
    def increase_volume(self):
        volume = self.get_volume_absolute()
        if volume < self.MAX_VOLUME:
            self.set_volume_absolute(volume + 1)
        else:
            logging.warning("Maximum volume reached")
            
    def decrease_volume(self):
        volume = self.get_volume_absolute()
        if volume > 0:
            self.set_volume_absolute(volume - 1)
        else:
            logging.warning("Minimum volume reached")                          
        
    def get_mode(self):
        """ Read the radios operating mode """
        return self.fsapi.get(FsApiNodes.SYS_MODE).value    

    def set_mode(self, mode):
        """ Set the radios operating mode """
        if isinstance(mode, FsRadioModes):
            self.fsapi.set(FsApiNodes.SYS_MODE, int(mode))
        else:
            logging.warning("Invalid mode requested.")
            
    def get_play_info_name(self):
        return self.fsapi.get(FsApiNodes.PLAY_INFO_NAME).value       
                
    def get_play_info_text(self):
        return self.fsapi.get(FsApiNodes.PLAY_INFO_TEXT).value     