#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import hashlib
import ssl
import os
import xml.etree.cElementTree as ET
import locale

from datetime import datetime

from urllib.request import Request, urlopen, urlretrieve, build_opener, install_opener, HTTPPasswordMgrWithDefaultRealm, HTTPPasswordMgrWithPriorAuth, HTTPDigestAuthHandler, HTTPBasicAuthHandler, HTTPSHandler
from urllib.parse import urlencode
from urllib.error import URLError, HTTPError

USER_AGENT="Mozilla/5.0 (U; Windows NT 5.1; rv:5.0) Gecko/20100101 Firefox/5.0"

services = {
    'WANIPConnection': ('/upnp/control/wanipconnection1', 'urn:dslforum-org:service:WANIPConnection:1'),
    'WANCommonInterfaceConfig': ('/upnp/control/wancommonifconfig1', 'urn:dslforum-org:service:WANCommonInterfaceConfig:1'),
    'X_AVM-DE_OnTel': ('/upnp/control/x_contact', 'urn:dslforum-org:service:X_AVM-DE_OnTel:1'),
    'DeviceConfig': ('/upnp/control/deviceconfig', 'urn:dslforum-org:service:DeviceConfig:1'),
    'TAM': ('/upnp/control/x_tam', 'urn:dslforum-org:service:X_AVM-DE_TAM:1'),
    'Hosts': ('/upnp/control/hosts', 'urn:dslforum-org:service:Hosts:1'),
    'VoIP': ('/upnp/control/x_voip', 'urn:dslforum-org:service:X_VoIP:1'),
    'WLANConfiguration1': ('/upnp/control/wlanconfig1', 'urn:dslforum-org:service:WLANConfiguration:1'),
    'WLANConfiguration2': ('/upnp/control/wlanconfig2', 'urn:dslforum-org:service:WLANConfiguration:2'),
    'WLANConfiguration3': ('/upnp/control/wlanconfig3', 'urn:dslforum-org:service:WLANConfiguration:3')
}

requests = { # name: {service, action, (parm1, parm2, ...), element (to be queried), validate (optional: value of element to be validated}
    'GetExternalIPAddress': ('WANIPConnection', 'GetExternalIPAddress', (), 'ExternalIPAddress', None),
    'Connected': ('WANIPConnection', 'GetStatusInfo', (), 'ConnectionStatus', 'Connected'),
    'Uptime': ('WANIPConnection', 'GetStatusInfo', (), 'Uptime', None),
    'GetTotalPacketsSent': ('WANCommonInterfaceConfig', 'GetTotalPacketsSent', (), 'TotalPacketsSent', None),
    'GetTotalPacketsReceived': ('WANCommonInterfaceConfig', 'GetTotalPacketsReceived', (), 'TotalPacketsReceived', None),
    'GetTotalBytesSent': ('WANCommonInterfaceConfig', 'GetTotalBytesSent', (), 'TotalBytesSent', None),
    'GetTotalBytesReceived': ('WANCommonInterfaceConfig', 'GetTotalBytesReceived', (), 'TotalBytesReceived', None),
    'GetLinkStatus': ('WANCommonInterfaceConfig', 'GetCommonLinkProperties', (), 'PhysicalLinkStatus', 'Up'),
    'GetUrlSID': ('DeviceConfig', 'X_AVM-DE_CreateUrlSID', (), 'X_AVM-DE_UrlSID', None),
    'GetPhonebookIDs': ('X_AVM-DE_OnTel', 'GetPhonebookList', (), 'PhonebookList', None),
    'GetPhonebook': ('X_AVM-DE_OnTel', 'GetPhonebook', ('PhonebookID',), 'PhonebookURL', None),
    'GetCallList': ('X_AVM-DE_OnTel', 'GetCallList', (), 'CallListURL', None),
    'TAMEnabled': ('TAM', 'GetInfo', ('Index',), 'Enable', '1'),
    'GetMessageList': ('TAM', 'GetMessageList', ('Index',), 'URL', None),
    'GetTAMList': ('TAM', 'GetList', (), 'TAMList', None),
    'HostActive': ('Hosts', 'GetSpecificHostEntry', ('MACAddress',), 'Active', '1'),
    'GetNumbers': ('VoIP', 'X_AVM-DE_GetNumbers', (), 'NumberList', None),
    'WLANEnabled': ('WLANConfiguration1', 'GetInfo', (), 'Enable', '1'),
    'WLAN1Enabled': ('WLANConfiguration1', 'GetInfo', (), 'Enable', '1'),
    'WLAN2Enabled': ('WLANConfiguration2', 'GetInfo', (), 'Enable', '1'),
    'WLAN3Enabled': ('WLANConfiguration3', 'GetInfo', (), 'Enable', '1')
}

commands = { # name: {service, action, element (to be set)}
    'Reboot': ('DeviceConfig', 'Reboot', None),
    'Reconnect': ('WANIPConnection', (), 'ForceTermination', None),
    'EnableTAM': ('TAM', 'SetEnable', (), 'Enable'), # Valid parms: (New)Enable, (New)Index
    'DeleteMessage': ('TAM', 'DeleteMessage', (), 'MessageIndex'), # Valid parms: (New)MessageIndex, (New)Index
    'MarkMessage': ('TAM', 'MarkMessage', ('MarkedAsRead=1',), 'MessageIndex'), # Valid parms: (New)MessageIndex, (New)MarkedAsRead -> optional, default:1, (New)Index
    'SetPort': ('VoIP', 'X_AVM-DE_DialSetConfig', (), 'X_AVM-DE_PhoneName'),
    'Dial': ('VoIP', 'X_AVM-DE_DialNumber', (), 'X_AVM-DE_PhoneNumber'),
    'Hangup': ('VoIP', 'X_AVM-DE_DialHangup', (), None),
    'EnableWLAN': ('WLANConfiguration1', 'SetEnable', (), 'Enable'),
    'EnableWLAN1': ('WLANConfiguration1', 'SetEnable', (), 'Enable'),
    'EnableWLAN2': ('WLANConfiguration2', 'SetEnable', (), 'Enable'),
    'EnableWLAN3': ('WLANConfiguration3', 'SetEnable', (), 'Enable')
}
# https://avm.de/service/schnittstellen/
# https://avm.de/fileadmin/user_upload/Global/Service/Schnittstellen/AVM_TR-064_first_steps.pdf
# https://avm.de/fileadmin/user_upload/Global/Service/Schnittstellen/x_tam.pdf
# https://avm.de/fileadmin/user_upload/Global/Service/Schnittstellen/x_contactSCPD.pdf
# https://avm.de/fileadmin/user_upload/Global/Service/Schnittstellen/deviceconfigSCPD.pdf
# https://avm.de/fileadmin/user_upload/Global/Service/Schnittstellen/wancommonifconfigSCPD.pdf
# https://avm.de/fileadmin/user_upload/Global/Service/Schnittstellen/wanipconnSCPD.pdf
# https://avm.de/fileadmin/user_upload/Global/Service/Schnittstellen/x_voip-avm.pdf
# https://avm.de/fileadmin/user_upload/Global/Service/Schnittstellen/hostsSCPD.pdf
# https://avm.de/fileadmin/user_upload/Global/Service/Schnittstellen/wlanconfigSCPD.pdf

# Call types::
ALL_CALLS         = 0
INCOMING          = 1
MISSED            = 2
OUTGOING          = 3
ACTIVE_INCOMING   = 9  # treat as INCOMING
REJECTED_INCOMING = 10 # BLOCKED
ACTIVE_OUTGOING   = 11 # treat as OUTGOING


def xmlCalls2dict(xmldata):
    #url = box.SOAPget('GetCallList')
    #xmldata = box.SOAPgetURL(url)
    if not xmldata:
        return

    calls = []

    try:
        tree = ET.fromstring(xmldata)
        for c in tree.iter('Call'):
            call = {}
            call['id']       = int(c.find('Id').text)
            call['type']     = int(c.find('Type').text)
            call['caller']   = c.find('Caller').text or ''
            call['called']   = c.find('Called').text or ''
            call['callerID'] = call['caller'] if (call['type'] % 8) != OUTGOING else (c.find('CallerNumber').text or '')
            call['calledID'] = call['called'] if (call['type'] % 8) == OUTGOING else (c.find('CalledNumber').text or '')
            call['name']     = c.find('Name').text or ''
            call['numtype']  = c.find('Numbertype').text
            call['device']   = c.find('Device').text
            call['port']     = int(c.find('Port').text)
            call['date']     = datetime.strptime(c.find('Date').text, '%d.%m.%y %H:%M')
            call['duration'] = c.find('Duration').text
            call['count']    = int(c.find('Count').text or -1)
            call['path']     = c.find('Path').text or ''
            calls.append(call)
    except:
        raise

    return calls

def xmlMessages2dict(xmldata):
    #url = box.SOAPget('GetMessageList', Index=index)
    #xmldata = box.SOAPgetURL(url)

    if not xmldata:
        return

    messages = []

    try:
        tree = ET.fromstring(xmldata)
        for m in tree.iter('Message'):
            message = {}
            message['index']    = int(m.find('Index').text)
            message['tamID']    = int(m.find('Tam').text)
            message['calledID'] = m.find('Called').text or ''
            message['date']     = datetime.strptime(m.find('Date').text, '%d.%m.%y %H:%M')
            message['duration'] = m.find('Duration').text
            message['name']     = m.find('Name').text or ''
            message['inbook']   = (m.find('Inbook').text == '1')
            message['new']      = (m.find('New').text == '1')
            message['callerID'] = m.find('Number').text or ''
            message['path']     = m.find('Path').text or ''
            messages.append(message)
    except:
        raise

    return messages

def xmlContacts2dict(xmldata):
    #url = box.SOAPget('GetPhonebook', PhonebookID=index)
    #xmldata = box.SOAPgetURL(url)

    if not xmldata:
        return

    contacts = []

    try:
        tree = ET.fromstring(xmldata)
        phonebook = tree[0]

        #id = int(phonebook.get('owner'))
        #name = phonebook.get('name')

        for contact in phonebook.iter('contact'):
            entry = {}
            for element in contact:
                if element.tag == 'person':
                    name = element.find('realName').text.strip()
                    name = ' '.join(name.split())
                    entry['name'] = name
                if element.tag == 'uniqueid':
                    entry['uid'] = int(element.text)
                if element.tag == 'telephony':
                    entries = len([num for num in element.iter('number') if num.text])
                    for num in element.iter('number'):
                        if 'type' in num.attrib and num.text:
                            type = num.attrib['type']
                            index = 1
                            while type in entry.keys():
                                index += 1
                                type = num.attrib['type'] + str(index)
                            entry[type] = num.text
                        elif num.text:
                            entry['number'] = num.text
                    if 'name' in entry.keys() and len(entry.keys()) > 1:
                        contacts.append(entry)
    except:
        raise

    return contacts

def xmlTAMList2dict(xmldata):
    #xmldata = self.box.SOAPget('GetTAMList')

    if not xmldata:
        return

    tams = []

    try:
        tree = ET.fromstring(xmldata)

        for item in tree.iter('Item'):
            tam = {}
            tam['index']   = int(item.find('Index').text)
            tam['display'] = (item.find('Display').text == '1')
            tam['enabled'] = (item.find('Enable').text == '1')
            tam['name']    = item.find('Name').text or ''
            tams.append(tam)
    except:
        raise

    return tams

def xmlNumberList2dict(xmldata):
    #xmldata = self.boxSOAPget('GetNumbers')

    if not xmldata:
        return

    numbers = []
    types = {}

    try:
        tree = ET.fromstring(xmldata)

        tree = ET.fromstring(xmldata)
        for item in tree.iter('Item'):
            number = {}
            number['index']   = int(item.find('Index').text)
            number['type']    = item.find('Type').text
            number['number']  = item.find('Number').text
            if number['type'] not in types.keys():
                types[number['type']] = [number['number']]
            else:
                types[number['type']].append(number['number'])
            number['name']    = item.find('Name').text or '{}#{}'.format(number['type'][1:], len(types[number['type']]))
            numbers.append(number)
    except:
        raise

    return numbers

class FritzBox():
    _body = """
<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    <u:{0} xmlns:u="{1}">{2}</u:{0}>
  </s:Body>
</s:Envelope>"""

    def __init__(self, username, password, host='fritz.box', timeout=5):
        self._fritzbox = host
        self._username = username
        self._password = password
        self._timeout = int(timeout)

        self._sid = self._get_sid()

    def _get_sid(self):
        url = 'http://{}/login_sid.lua'.format(self._fritzbox)

        headers = {'User-Agent': USER_AGENT}

        req = Request(url, headers=headers)

        try:
            with urlopen(req, timeout=self._timeout) as content:
                tree = ET.fromstring(content.read())
                challenge = tree.find('.//Challenge').text

            response = hashlib.md5("{}-{}".format(challenge, self._password).encode('utf-16le')).hexdigest()
            response = '{}-{}'.format(challenge, response)

            data = urlencode({'username': self._username, 'response': response}).encode()

            with urlopen(req, data=data, timeout=self._timeout) as content:
                tree = ET.fromstring(content.read())
                sid = tree.find('.//SID').text
                if sid != '0000000000000000':
                    return sid

        except (HTTPError, URLError) as e:
            #print(e)
            raise

        return None

    def deleteCallList(self):
        try:
            self.get('/data.lua', clear='', oldpage='/fon_num/foncalls_list.lua')
        except Exception as e:
            #print(e)
            raise

    def get(self, selector, **parms):
        url = 'http://{}/{}'.format(self._fritzbox, selector[1:] if selector[0] == '/' else selector)

        headers = {'User-Agent': USER_AGENT}

        if not parms or not isinstance(parms, dict):
            parms = {}
        fields = {'sid': self._sid, **parms}
        data = urlencode(fields).encode()

        req = Request(url, data=data, headers=headers)

        try:
            with urlopen(req, timeout=self._timeout) as content:
                if content.status != 200:
                    return

                return content.read() #.decode()

        except (HTTPError, URLError) as e:
            #print(e)
            raise

        return

    def saveRecording(self, path, dest='message.wav'):
        if '/' not in path:
            path = '/data/tam/rec/' + path

        try:
            data = self.get('/cgi-bin/luacgi_notimeout', script='/lua/photo.lua', myabfile=path)
        except Exception as e:
            #print(e)
            raise

        if not data:
            return

        if os.path.sep in dest:
            outdir, outname = dest.rsplit(os.path.sep, 1)
        else:
            outdir = '.' + os.path.sep
            outname = dest

        if not outname:
            outname = 'message.wav'

        if '.' in outname:
            name, ext = outname.rsplit('.', 1)
            ext = '.' + ext
        else:
            name = outname
            ext = ''

        index = 1
        while os.path.isfile(os.path.join(outdir, outname)):
            index += 1
            outname = '{}({}){}'.format(name, index, ext)

        outpath = os.path.join(outdir, outname)

        try:
            if not os.path.isdir(outdir):
                os.makedirs(outdir) #, exist_ok=True)

            with open(outpath, "wb") as f:
                f.write(data)

        except Exception as e:
            #print(e)
            raise

        return outpath

    def SOAPgetURL(self, url, **parms):
        if url[0] == '/':
            url = 'https://{}:49443{}'.format(self._fritzbox, url)
        if parms is not None and isinstance(parms, dict):
            url = '{}{}{}'.format(url, '&' if '?' in url else '?', urlencode(parms))
        if 'sid=' not in url:
            url = '{}{}sid={}'.format(url, '&' if '?' in url else '?', self._sid)

        headers = {
            'User-Agent':   USER_AGENT,
            'Content-Type': 'text/xml; charset="utf-8"'
        }

        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        auth_handler = HTTPDigestAuthHandler(HTTPPasswordMgrWithDefaultRealm())
        auth_handler.add_password (None, url, self._username, self._password)
        ssl_handler = HTTPSHandler(context=context) #,debuglevel=1)

        opener = build_opener(ssl_handler, auth_handler)
        install_opener(opener)

        req = Request(url, headers=headers)

        try:
            with urlopen(req, timeout=self._timeout) as content:
                if content.status != 200:
                    # #if connection fails retry with new SID from result of self.SOAPget('GetUrlSID') -> sid=...
                    # result = self.SOAPget('GetUrlSID')
                    # if len(result) == 20:
                    #     sid = url.split('sid=', 1)[1][:16]
                    #     url.replace('sid={}'.format(sid), result)
                    #     return self.SOAPgetURL(url)
                    return

                return content.read() #.decode()

        except (HTTPError, URLError) as e:
            #print(e)
            raise

        return

    def SOAPget(self, request, **parms):
        if request in requests.keys():
            service, action, plist, element, validate = requests[request]
            url, service = services[service]
        else:
            return

        url = 'https://{}:49443{}'.format(self._fritzbox, url)

        headers = {
            'User-Agent':   USER_AGENT,
            'Content-Type': 'text/xml; charset="utf-8"',
            'SOAPAction':   '{}#{}'.format(service, action)
        }

        value = ''
        if parms is not None and isinstance(parms, dict):
            for p, v in parms.items():
                if isinstance(plist, tuple) and p not in plist:
                    print("Parameter '{}' is invalid. Only '{}' allowed.".format(p, ', '.join(plist)))
                    return
                value += '<New{0}>{1}</New{0}>'.format(p, v)

        body = self._body.format(action, service, value)

        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        auth_handler = HTTPDigestAuthHandler(HTTPPasswordMgrWithDefaultRealm())
        auth_handler.add_password (None, url, self._username, self._password)
        ssl_handler = HTTPSHandler(context=context) #,debuglevel=1)

        opener = build_opener(ssl_handler, auth_handler)
        install_opener(opener)

        req = Request(url, data=body.encode(), headers=headers, method='POST')

        try:
            with urlopen(req, timeout=self._timeout) as content:
                if content.status != 200:
                    return

                if element is None:
                    return

                tree = ET.fromstring(content.read())
                element = tree.find('.//New{}'.format(element))

                if validate is None:
                    try:
                        return int(element.text)
                    except:
                        return element.text
                else:
                    return element.text == validate

        except (HTTPError, URLError) as e:
            #print(e)
            raise

        return

    def SOAPset(self, command, Value='', Index=None):
        if command in commands.keys():
            service, action, plist, element = commands[command]
            url, service = services[service]
        else:
            return 'Command not found'

        url = 'https://{}:49443{}'.format(self._fritzbox, url)

        headers = {
            'User-Agent':   USER_AGENT,
            'Content-Type': 'text/xml; charset="utf-8"',
            'SOAPAction':   '{}#{}'.format(service, action)
        }

        if element:
            value = '<New{0}>{1}</New{0}>'.format(element, Value)
            if isinstance(plist, tuple):
                for p in plist:
                    try:
                        k, v = p.split('=', 1)
                        value += '<New{0}>{1}</New{0}>'.format(k, v)
                    except Exception as e:
                        continue

        if Index is not None:
            value = '<{0}>{1}</{0}>{2}'.format('NewIndex', Index, value)  # für tam notwendig

        body = self._body.format(action, service, value)

        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        auth_handler = HTTPDigestAuthHandler(HTTPPasswordMgrWithDefaultRealm())
        auth_handler.add_password (None, url, self._username, self._password)
        ssl_handler = HTTPSHandler(context=context) #,debuglevel=1)

        opener = build_opener(ssl_handler, auth_handler)
        install_opener(opener)

        req = Request(url, data=body.encode(), headers=headers, method='POST')

        try:
            content = urlopen(req, timeout=self._timeout)
        except (HTTPError, URLError) as e:
            #print(e)
            raise

        return 'status={}'.format(content.status)

