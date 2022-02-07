#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
#  _   _       _  __ _ 
# | | | |     (_)/ _(_)
# | | | |_ __  _| |_ _ 
# | | | | '_ \| |  _| |
# | |_| | | | | | | | |
#  \___/|_| |_|_|_| |_|
#
# created: 01/2022
#
# Author: Frank Baier
# E-Mail: dev@baier-nt.de
#
from datetime import date
from datetime import datetime
from dateutil.parser import parse
from cmk.base.check_api import set_item_state, get_item_state
from .agent_based_api.v1.type_defs import HostLabelGenerator
from .agent_based_api.v1 import HostLabel
from .agent_based_api.v1 import *
from .utils import if64, interfaces
import pprint
import json

from typing import (
    Any,
    Dict,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Tuple,
)

UNIFI_DEVICE_TABLE = {
    'BZ2'       : 'UAP',
    'BZ2LR'     : 'UAP-LR',
    'U2HSR'     : 'UAP-Outdoor+',
    'U2IW'      : 'UAP-IW',
    'U2L48'     : 'UAP-AC-LR',
    'U2Lv2'     : 'UAP-AC-LR',
    'U2M'       : 'UAP-Mini',
    'U2O'       : 'UAP-Outdoor',
    'U2S48'     : 'UAP-AC',
    'U2Sv2'     : 'UAP-AC',
    'U5O'       : 'UAP-Outdoor5',
    'U7E'       : 'UAP-AC',
    'U7EDU'     : 'UAP-AC-EDU',
    'U7Ev2'     : 'UAP-AC',
    'U7HD'      : 'UAP-AC-HD',
    'U7SHD'     : 'UAP-AC-SHD',
    'U7NHD'     : 'UAP-nanoHD',
    'UFLHD'     : 'UAP-FlexHD',
    'UHDIW'     : 'UAP-IW-HD',
    'UAIW6'     : 'U6-IW',
    'UAE6'      : 'U6-Extender',
    'UAL6'      : 'U6-Lite',
    'UAM6'      : 'U6-Mesh',
    'UALR6'     : 'U6-LR-EA',
    'UAP6'      : 'U6-LR',
    'UALR6v2'   : 'U6-LR',
    'UALR6v3'   : 'U6-LR',
    'UCXG'      : 'UAP-XG',
    'UXSDM'     : 'UWB-XG',
    'UXBSDM'    : 'UWB-XG-BK',
    'UCMSH'     : 'UAP-XG-Mesh',
    'U7IW'      : 'UAP-AC-IW',
    'U7IWP'     : 'UAP-AC-IW-Pro',
    'U7MP'      : 'UAP-AC-M-Pro',
    'U7LR'      : 'UAP-AC-LR',
    'U7LT'      : 'UAP-AC-Lite',
    'U7O'       : 'UAP-AC-Outdoor',
    'U7P'       : 'UAP-Pro',
    'U7MSH'     : 'UAP-AC-M',
    'U7PG2'     : 'UAP-AC-Pro',
    'p2N'       : 'PICOM2HP',
    'UDMB'      : 'UAP-BeaconHD',
    'USF5P'     : 'USW-Flex',
    'US8'       : 'US-8',
    'US8P60'    : 'US-8-60W',
    'US8P150'   : 'US-8-150W',
    'S28150'    : 'US-8-150W',
    'USC8'      : 'US-8',
    'USC8P60'   : 'US-8-60W',
    'USC8P150'  : 'US-8-150W',
    'US16P150'  : 'US-16-150W',
    'S216150'   : 'US-16-150W',
    'US24'      : 'US-24-G1',
    'US24PRO'   : 'USW-Pro-24-PoE',
    'US24PRO2'  : 'USW-Pro-24',
    'US24P250'  : 'US-24-250W',
    'US24PL2'   : 'US-L2-24-PoE',
    'US24P500'  : 'US-24-500W',
    'S224250'   : 'US-24-250W',
    'S224500'   : 'US-24-500W',
    'US48'      : 'US-48-G1',
    'US48PRO'   : 'USW-Pro-48-PoE',
    'US48PRO2'  : 'USW-Pro-48',
    'US48P500'  : 'US-48-500W',
    'US48PL2'   : 'US-L2-48-PoE',
    'US48P750'  : 'US-48-750W',
    'S248500'   : 'US-48-500W',
    'S248750'   : 'US-48-750W',
    'US6XG150'  : 'US-XG-6PoE',
    'USMINI'    : 'USW-Flex-Mini',
    'USXG'      : 'US-16-XG',
    'USC8P450'  : 'USW-Industrial',
    'UDC48X6'   : 'USW-Leaf',
    'USL8A'     : 'UniFi Switch Aggregation',
    'USAGGPRO'  : 'UniFi Switch Aggregation Pro',
    'USL8LP'    : 'USW-Lite-8-PoE',
    'USL8MP'    : 'USW-Mission-Critical',
    'USL16P'    : 'USW-16-PoE',
    'USL16LP'   : 'USW-Lite-16-PoE',
    'USL24'     : 'USW-24-G2',
    'USL48'     : 'USW-48-G2',
    'USL24P'    : 'USW-24-PoE',
    'USL48P'    : 'USW-48-PoE',
    'UGW3'      : 'USG-3P',
    'UGW4'      : 'USG-Pro-4',
    'UGWHD4'    : 'USG',
    'UGWXG'     : 'USG-XG-8',
    'UDM'       : 'UDM',
    'UDMSE'     : 'UDM-SE',
    'UDMPRO'    : 'UDM-Pro',
    'UP4'       : 'UVP-X',
    'UP5'       : 'UVP',
    'UP5t'      : 'UVP-Pro',
    'UP7'       : 'UVP-Executive',
    'UP5c'      : 'UVP',
    'UP5tc'     : 'UVP-Pro',
    'UP7c'      : 'UVP-Executive',
    'UCK'       : 'UCK',
    'UCK-v2'    : 'UCK',
    'UCK-v3'    : 'UCK',
    'UCKG2'     : 'UCK-G2',
    'UCKP'      : 'UCK-G2-Plus',
    'UASXG'     : 'UAS-XG',
    'ULTE'      : 'U-LTE',
    'ULTEPUS'   : 'U-LTE-Pro',
    'ULTEPEU'   : 'U-LTE-Pro',
    'UP1'       : 'USP-Plug',
    'UP6'       : 'USP-Strip',
    'USPPDUP'   : 'USP - Power Distribution Unit Pro',
    'USPRPS'    : 'USP-RPS',
    'US624P'    : 'UniFi6 Switch 24',
    'UBB'       : 'UBB',
    'UXGPRO'    : 'UniFi NeXt-Gen Gateway PRO'
}

UNIFI_DEVICE_STATES = {
    "0" : "disconnected",
    "1" : "connected",
    "2" : "pending"
}


def host_labels(section: Dict) -> HostLabelGenerator:
    devtype = section.get("type")
    devtype2 = section.get("ubnt_device_type")
    if devtype:
        yield HostLabel(u'unifi_device_type', devtype)
    elif devtype2:
        yield HostLabel(u'unifi_device_type', devtype2)


def parse_unifi(string_table):
    """
    :param info: dictionary with all data for all checks and subchecks
    :return:
    """
    if string_table:
        return json.loads(str(string_table[0][0]))
    return dict()


register.agent_section(
    name = "unifi_device_users",
    parse_function=parse_unifi,
)




def discover_unifi_controller_sites(section):
    for site in section:
        yield Service(item=site.get('desc'))
        for data in site.get('health'):
            if data.get('status')!='unknown':
                yield Service(item=f"%s_%s" % (site.get('desc'), data.get('subsystem')))


def check_unifi_controller_sites(item, section):
    for site in section:
        if item==site.get('desc'):
            yield Result(state=State.OK, summary=f"Site description: %s" % site.get('desc'))
            yield Result(state=State.OK, summary=f"Site id: %s" % site.get('name'))
            yield Result(state=State.OK, summary=f"Alarms: %s" % site.get('num_new_alarms'))

        for data in site.get('health'):
            if item==f"%s_%s" % (site.get('desc'), data.get('subsystem')):
                yield Result(state=State.OK, summary=f"Status: %s" % data.get('status'))
                yield Result(state=State.OK, summary=f"adopted Devices: %s" % data.get('num_adopted'))
                yield Result(state=State.OK, summary=f"pending Devices: %s" % data.get('num_pending'))
                yield Result(state=State.OK, summary=f"disconnected Devices: %s" % data.get('num_disconnected'))
                if data.get('num_disabled')!=None:
                    yield Result(state=State.OK, summary=f"disabled Devices: %s" % data.get('num_disabled'))
                yield Result(state=State.OK, summary=f"Users: %s" % data.get('num_user'))
                yield Result(state=State.OK, summary=f"Guests: %s" % data.get('num_guest'))


register.agent_section(
    name = "unifi_controller_sites",
    parse_function=parse_unifi,
    #host_label_function=host_labels,
)

register.check_plugin(
    name = "unifi_controller_sites",
    sections=["unifi_controller_sites"],
    service_name="Site %s",
    discovery_function=discover_unifi_controller_sites,
    check_function=check_unifi_controller_sites,
)




def discover_unifi_controller(section):
    '''
    pprint.pprint(section)
    devtype = section.get("type")
    devtype2 = section.get("ubnt_device_type")

    if devtype:
        yield Service()
    elif devtype2:
        yield Service()
    '''
    yield Service()


def check_unifi_controller(section):
    yield Result(state=State.OK, summary=f"Name: %s" % section.get('name'))
    yield Result(state=State.OK, summary=f"Type: %s" % section.get('ubnt_device_type'))
    yield Result(state=State.OK, summary=f"Build: %s" % section.get('build'))

    if section.get('unsupported_device_count')==0:
        yield Result(state=State.OK, summary=f"Unsupported devices: %s" % section.get('unsupported_device_count'))
    else:
        yield Result(state=State.WARN, summary=f"Unsupported devices: %s" % section.get('unsupported_device_count'))
        #yield Result(state=State.WARN, notice=f"Unsupported devices:  %s" % section.get('unsupported_device_list'))


register.agent_section(
    name = "unifi_controller",
    parse_function=parse_unifi,
    host_label_function=host_labels,
)

register.check_plugin(
    name = "unifi_controller",
    sections=["unifi_controller"],
    service_name="Unifi Controller",
    discovery_function=discover_unifi_controller,
    check_function=check_unifi_controller,
)






def discover_unifi_device(section):
    devtype = section.get("type")
    name = section.get("name")

    if devtype:
        yield Service()


def check_unifi_device(section):
    
    #yield Result(state=State.OK, notice=f"Type: %s" % section.get('type'))
    yield Result(state=State.OK, summary=f"Name: %s" % section.get('name'))
    yield Result(state=State.OK, summary=f"%s" % section.get('ip'))

    if section.get('state')==1:
        yield Result(state=State.OK, summary=f"State: %s" % section.get('state'))
    else:
        yield Result(state=State.CRIT, summary=f"State: %s" % section.get('state'))

    if section.get('adopted'):
        yield Result(state=State.OK, summary=f"Adopted")
    else:
        yield Result(state=State.WARN, summary=f"waiting for adoption")

    yield Result(state=State.OK, summary=f"Type: %s" % section.get('type'))
    yield Result(state=State.OK, summary=f"Model: %s" % section.get('model'))
    yield Result(state=State.OK, summary=f"Serial: %s" % section.get('serial'))


register.agent_section(
    name = "unifi_device",
    parse_function=parse_unifi,
    host_label_function=host_labels,
)

register.check_plugin(
    name = "unifi_device",
    sections=["unifi_device"],
    service_name="Unifi Device",
    discovery_function=discover_unifi_device,
    check_function=check_unifi_device,
)




def parse_unifi_device_if(string_table: type_defs.StringTable) -> interfaces.Section:
    port_table = parse_unifi(string_table)

    #new_info=[]

    #for line in port_table:
    return [
        interfaces.Interface(
            #index=str(line.get('port_idx')),
            index=str(line.get('port_idx')) if str(line.get('port_idx')).isdecimal() else str(idx),
            descr=line.get('name'),
            alias=line.get('name'),
            type='6',  # Ethernet
            #speed=if64.fix_if_64_highspeed(line.get('speed')),
            speed=line.get('speed', 0)*1000000,
            oper_status='1' if line.get('up') else '2',
            in_octets=line.get('rx_bytes', 0),
            in_ucast=line.get('rx_bytes', 0),
            in_mcast=line.get('rx_multicast', 0),
            in_bcast=line.get('rx_broadcast', 0),
            in_discards=line.get('rx_dropped', 0),
            in_errors=line.get('rx_errors', 0),
            out_octets=line.get('tx_bytes', 0),
            out_ucast=line.get('tx_bytes', 0),
            out_mcast=line.get('tx_multicast', 0),
            out_bcast=line.get('tx_broadcast', 0),
            out_discards=line.get('tx_dropped', 0),
            out_errors=line.get('tx_errors', 0),
        )
        for idx, line in enumerate(port_table)
    ]


register.agent_section(
    name = "unifi_device_if",
    parse_function=parse_unifi_device_if,
)


register.check_plugin(
    name="unifi_device_if",
    sections=["unifi_device_if"],
    service_name="Interface %s",
    discovery_ruleset_name="inventory_if_rules",
    discovery_ruleset_type=register.RuleSetType.ALL,
    discovery_default_parameters=dict(interfaces.DISCOVERY_DEFAULT_PARAMETERS),
    discovery_function=interfaces.discover_interfaces,
    check_ruleset_name="if",
    check_default_parameters=interfaces.CHECK_DEFAULT_PARAMETERS,
    check_function=if64.generic_check_if64,
    cluster_check_function=interfaces.cluster_check,
)




'''
'poe_caps': 7,
'poe_class': 'Class 4',
'poe_current': '151.12', mA
'poe_enable': True,
'poe_good': True,
'poe_mode': 'auto',
'poe_power': '8.02', W
'poe_voltage': '53.08', V

Class1: 12,95W/15,4W
Class2: 12,95W/15,4W
Class3: 12,95W/15,4W
Class4: 25,50W/30,0W
Class5: 40,00W/45,0W
Class6: 51,00W/60,0W
Class7: 62,00W/75,0W
Class8: 71,00W/90,0W
'''
def discovery_unifi_poe(section_unifi_device, section_unifi_device_users):
    poe_port_data = section_unifi_device.get('port_table')
    for port in poe_port_data:
        if port.get('port_poe', False):
            yield Service(item=str(port.get('port_idx')).zfill(2))


def check_unifi_poe(item, section_unifi_device, section_unifi_device_users):
    poe_port_data = section_unifi_device.get('port_table')
    for port in poe_port_data:
        if port.get('port_poe', False):
            if item==str(port.get('port_idx')).zfill(2):
                yield Result(state=State.OK, summary=f"POE: %s" % port.get('poe_enable'))
                yield Result(state=State.OK, summary=f"good: %s" % port.get('poe_good'))
                yield Result(state=State.OK, summary=f"mode: %s" % port.get('poe_mode'))
                if float(port.get('poe_power', 0))>0:
                    yield Result(state=State.OK, summary=f"class: %s" % port.get('poe_class'))
                    if 50 < float(port.get('poe_voltage', 0)) < 57:
                        yield Result(state=State.OK, summary=f"voltage: %sV" % port.get('poe_voltage', 0))
                    else:
                        yield Result(state=State.CRIT, summary=f"voltage: %sV" % port.get('poe_voltage', 0))
                    yield Result(state=State.OK, summary=f"current: %smA" % port.get('poe_current', 0))
                    yield Result(state=State.OK, summary=f"power: %sW" % port.get('poe_power', 0))


register.check_plugin(
    name="unifi_device_if_poe",
    sections=["unifi_device", "unifi_device_users"],
    service_name="POE %s",
    discovery_function=discovery_unifi_poe,
    check_function=check_unifi_poe,
)



def wifi_type(ssid):
    if ssid.get('channel') < 15:
        return "2.4G"
    else:
        return "5G"


def discovery_unifi_wifi(section):
    wifi_ssid_data = section.get('vap_table')
    if wifi_ssid_data:
        for ssid in wifi_ssid_data:
            yield Service(item=f"%s_%s" % (ssid.get('radio_name'), ssid.get('essid')))


def check_unifi_wifi(item, section):
    wifi_ssid_data = section.get('vap_table')
    for ssid in wifi_ssid_data:
        if item==f"%s_%s" %(ssid.get('radio_name'), ssid.get('essid')):
            yield Result(state=State.OK, summary=f"SSID: %s" % ssid.get('essid'))
            yield Result(state=State.OK, summary=f"State/Up: %s/%s" % (ssid.get('state'), ssid.get('up')))
            yield Result(state=State.OK, summary=f"Usage: %s" % ssid.get('usage'))
            yield Result(state=State.OK, summary=f"Interface: %s" % ssid.get('name'))
            if int(ssid.get('avg_client_signal'))<0:
                yield Result(state=State.OK, summary=f"avgClientSig: %sdBm" % ssid.get('avg_client_signal'))


register.check_plugin(
    name="unifi_device_if_wifi",
    sections=["unifi_device"],
    service_name="SSID %s",
    discovery_function=discovery_unifi_wifi,
    check_function=check_unifi_wifi,
)




def discovery_unifi_radio(section_unifi_device, section_unifi_device_users):
    radio_data = section_unifi_device.get('radio_table')
    if radio_data:
        for radio in radio_data:
            yield Service(item=f"%s" % radio.get('name'))


def check_unifi_radio(item, section_unifi_device, section_unifi_device_users):
    radio_data = section_unifi_device.get('radio_table')
    for idx, radio in enumerate(radio_data):
        if item==f"%s" % radio.get('name'):
            radio_stats = section_unifi_device.get('radio_table_stats')[idx]
            yield Result(state=State.OK, summary=f"State: %s" % radio_stats.get('state'))
            yield Result(state=State.OK, summary=f"Type: %s/%s" % (wifi_type(radio), radio.get('radio')))
            yield Result(state=State.OK, summary=f"Channel: %s" % radio.get('channel'))
            yield Result(state=State.OK, summary=f"Width: %sMHz" % radio.get('ht'))
            if radio.get('antenna_gain'):
                yield Result(state=State.OK, summary=f"Ant.Gain: %sdBm" % radio.get('antenna_gain'))
            yield Result(state=State.OK, summary=f"curr.AntGain: %sdBm" % radio.get('current_antenna_gain'))
            yield Result(state=State.OK, summary=f"Users/Guests: %s/%s" % (radio_stats.get('user-num_sta'), radio_stats.get('guest-num_sta')))


register.check_plugin(
    name="unifi_device_radio",
    sections=["unifi_device", "unifi_device_users"],
    service_name="Radio %s",
    discovery_function=discovery_unifi_radio,
    check_function=check_unifi_radio,
)

