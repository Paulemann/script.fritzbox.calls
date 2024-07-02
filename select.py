#!/usr/bin/python
# -*- coding: utf-8 -*-

# ToDo: Use setProperty(key, value) or setPoperites(dict) instead of setLabel2(value) --> query with getProperty(key)

import os
import sys
import locale

from datetime import datetime

import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs

import pyxbmct.addonwindow as pyxbmct

import resources.lib.fbtoolbox as fb

if sys.version_info.major < 3:
    INFO = xbmc.LOGNOTICE
    from xbmc import tranlatePath
else:
    INFO = xbmc.LOGINFO
    from xbmcvfs import translatePath
DEBUG = xbmc.LOGDEBUG

__addon__      = xbmcaddon.Addon()
__setting__    = __addon__.getSetting
__localize__   = __addon__.getLocalizedString
__addon_id__   = __addon__.getAddonInfo('id')
__addon_name__ = __addon__.getAddonInfo('name')
__addon_path__ = __addon__.getAddonInfo('path')
__profile__    = __addon__.getAddonInfo('profile')


__checked_icon__   = os.path.join(__addon_path__, 'resources', 'media', 'checked.png')
__unchecked_icon__ = os.path.join(__addon_path__, 'resources', 'media', 'unchecked.png')

__list_bg__        = os.path.join(__addon_path__, 'resources', 'media', 'background.png')
__texture_nf__     = os.path.join(__addon_path__, 'resources', 'media', 'texture-nf.png')

__icon_none__      = os.path.join(__addon_path__, 'resources', 'media', 'empty.png')
__icon_incoming__  = os.path.join(__addon_path__, 'resources', 'media', 'incoming-call.png')
__icon_missed__    = os.path.join(__addon_path__, 'resources', 'media', 'missed-call.png')
__icon_outgoing__  = os.path.join(__addon_path__, 'resources', 'media', 'outgoing-call.png')
__icon_blocked__   = os.path.join(__addon_path__, 'resources', 'media', 'blocked-call.png')
__icon_newmsg__    = os.path.join(__addon_path__, 'resources', 'media', 'new-message.png')

__icons__          = [__icon_none__, __icon_incoming__, __icon_missed__, __icon_outgoing__, __icon_blocked__, __icon_newmsg__]

str_TITLE       = __localize__(30050) # 'FRITZ!Box Anruf- und Nachrichtenliste'
str_SELECTION   = __localize__(30051) # 'Auswahl'
str_CALLS       = __localize__(30052) # 'Anrufe'
str_MESSAGES    = __localize__(30053) # 'Nachr.'
str_DATE        = __localize__(30054) # 'Datum'
str_NAME        = __localize__(30055) # 'Name/Rufnummer'
str_DURATION    = __localize__(30056) # 'Dauer'
str_PLAY        = __localize__(30057) # 'Abspielen'
str_DELETE      = __localize__(30058) # 'Löschen'
str_CLOSE       = __localize__(30059) # 'Zurück'
str_CALL        = __localize__(30060) # 'Anruf'
str_MESSAGE     = __localize__(30061) # 'Nachr.'
str_DELCALLS    = __localize__(30062) # 'Hierdurch werden alle Anrufe gelöscht. Fortfahren?'
str_DELMSG      = __localize__(30063) # 'Hierdurch wird die Nachricht gelöscht. Fortfahren?'
str_DELMSGS     = __localize__(30064) # 'Hierdurch werden alle Nachrichten gelöscht. Fortfahren?'
str_CANCEL      = __localize__(30065) # 'Abbruch'
str_OK          = __localize__(30066) # 'OK'
str_PROCEED     = __localize__(30067) # 'Weiter'
str_FILTERDLG   = __localize__(30068) # 'Eigene Rufnummer(n)'
str_ACTIVE      = __localize__(30069) # 'aktiv'
str_NOCALLS     = __localize__(30070) # 'Keine Anrufe'
str_NOMESSAGES  = __localize__(30071) # 'Keine Nachrichten'
str_NOACTIVETAM = __localize__(30072) # 'Anrufbeantworter ist nicht eingeschaltet'
str_ANONYMOUS   = __localize__(30073) # 'unbekannt'
str_HRS         = __localize__(30074) # 'Std'
str_MNS         = __localize__(30075) # 'Min'
str_NOACTIVENUM = __localize__(30076) # 'Keine Rufnummer(n) eingerichtet'


# Enable or disable Estuary-based design explicitly
pyxbmct.skin.estuary = True


def log(message,loglevel=INFO):
    xbmc.log(msg='[{}] {}'.format(__addon_id__, message), level=loglevel)


class MultiChoiceDialog(pyxbmct.AddonDialogWindow):
    # Font colors
    BLUE  = '0xFF7ACAFE'
    RED   = '0xFFFF0000'
    BLACK = '0xFF000000'
    WHITE = '0xFFFFFFFF'
    GREY  = '0xAAFFFFFF'

    # Font sizes
    SMALL_FONT   = 'font10'
    REGULAR_FONT = 'font13'
    BIG_FONT     = 'font45'
    MONO_FONT    = 'Mono26'

    def __init__(self, title='', items=None, preselect=None):
        super(MultiChoiceDialog, self).__init__(title)

        self.setGeometry(300, 220, 8, 15)

        self.selected = preselect or []

        self.set_controls()
        self.connect_controls()

        self.listing.addItems(items or [])

        for index in range(self.listing.size()):
            listitem = self.listing.getListItem(index)
            try:
                listitem.setIconImage(__checked_icon if index in self.selected else __unchecked_icon__)
            except:
                listitem.setArt({'icon': __checked_icon__ if index in self.selected else __unchecked_icon__})
            listitem.setProperty('selected', 'true' if index in self.selected else 'false')

        self.set_navigation()

    def set_controls(self):
        self.listing = pyxbmct.List(_imageWidth=15, _itemTextYOffset=-1, _alignmentY=pyxbmct.ALIGN_CENTER_Y, font=self.MONO_FONT)
        self.placeControl(self.listing, 0, 0, rowspan=6, columnspan=15)

        self.ok_button = pyxbmct.Button(str_OK)
        self.placeControl(self.ok_button, 6, 1, rowspan=2, columnspan=6)

        self.cancel_button = pyxbmct.Button(str_CANCEL)
        self.placeControl(self.cancel_button, 6, 8, rowspan=2, columnspan=6)

    def connect_controls(self):
        self.connect(self.listing, self.check_uncheck)
        self.connect(self.ok_button, self.ok)
        self.connect(self.cancel_button, self.close)
        self.connect(xbmcgui.ACTION_NAV_BACK, self.close)

    def set_navigation(self):
        self.listing.controlUp(self.ok_button)
        self.listing.controlDown(self.ok_button)
        self.ok_button.setNavigation(self.listing, self.listing, self.cancel_button, self.cancel_button)
        self.cancel_button.setNavigation(self.listing, self.listing, self.ok_button, self.ok_button)

        if self.listing.size():
            self.setFocus(self.listing)
        else:
            self.setFocus(self.cancel_button)

    def check_uncheck(self):
        listitem = self.listing.getSelectedItem()
        listitem.setProperty('selected', 'false' if listitem.getProperty('selected') == 'true' else 'true')
        try:
            listitem.setIconImage(__checked_icon__ if listitem.getProperty('selected') else __unchecked_icon__)
        except:
            listitem.setArt({'icon': __checked_icon__ if listitem.getProperty('selected') == 'true'  else __unchecked_icon__})

    def ok(self):
        self.selected = [index for index in range(self.listing.size()) if self.listing.getListItem(index).getProperty('selected') == 'true']
        super(MultiChoiceDialog, self).close()

    def close(self):
        self.selected = []
        super(MultiChoiceDialog, self).close()


class FritzBoxDialog(pyxbmct.AddonDialogWindow):
    # Font colors
    BLUE  = '0xFF7ACAFE'
    RED   = '0xFFFF0000'
    BLACK = '0xFF000000'
    WHITE = '0xFFFFFFFF'
    GREY  = '0xAAFFFFFF'

    # Font sizes
    SMALL_FONT   = 'font10'
    REGULAR_FONT = 'font13'
    BIG_FONT     = 'font45'
    MONO_FONT    = 'Mono26'

    MAXTAMS = 5

    def __init__(self, box, title="", numbers=()):
        super(FritzBoxDialog, self).__init__(title)

        # tmpdir must end with slash/backslash!
        self.tmpdir = os.path.join(__profile__, 'tmp' + os.path.sep)

        self.box = box

        self.sort_by = 'date'
        self.sort_reverse = True

        self.items = None
        self.selected_item = -1

        try:
            xmldata = self.box.SOAPget('GetTAMList')
            tamlist = fb.xmlTAMList2dict(xmldata)
        except Exception as e:
            log(e)
            raise

        if tamlist:
            self.tamIDs = tuple(t['index'] for t in tamlist if t['enabled'])
            self.tamID  = self.tamIDs[0]
        else:
            self.tamIDs = ()
            self.tamID = -1

        self.tam_select_button = [None] * self.MAXTAMS

        try:
            xmldata = self.box.SOAPget('GetNumbers')
            self.numlist = fb.xmlNumberList2dict(xmldata)
        except Exception as e:
            log(e)
            raise

        self.numfilter = tuple(element['number'] for element in self.numlist if element['number'] in numbers)
        if len(self.numfilter) == len(self.numlist):
            self.numfilter = ()

        self.num_select_button = [None] * len(self.numlist)

        self._monitor = xbmc.Monitor()
        self._player  = xbmc.Player()

        self.setGeometry(880, 600, 25, 20)

        self.set_controls()
        self.place_controls()
        self.connect_controls()

        self.set_navigation()

        self.show_calls_button.setSelected(True)
        self.show_messages_button.setEnabled(len(self.tamIDs) > 0)

        self.update_list(True)
        self.setFocus(self.list)

    def set_controls(self):
        self.select_label = pyxbmct.Label(str_SELECTION + ':', textColor=self.BLUE, alignment=pyxbmct.ALIGN_CENTER_Y)
        self.show_calls_button = pyxbmct.RadioButton(str_CALLS, _alignment=pyxbmct.ALIGN_CENTER_Y, noFocusTexture=__texture_nf__)
        self.show_messages_button = pyxbmct.RadioButton(str_MESSAGES, _alignment=pyxbmct.ALIGN_CENTER_Y, noFocusTexture=__texture_nf__)

        for i in range(self.MAXTAMS):
            self.tam_select_button[i] = pyxbmct.Button(str(i + 1), alignment=pyxbmct.ALIGN_CENTER_X|pyxbmct.ALIGN_CENTER_Y)

        self.numitems_label = pyxbmct.Label('', textColor=self.BLUE, alignment=pyxbmct.ALIGN_CENTER_Y|pyxbmct.ALIGN_RIGHT)
        self.sort_date_button = pyxbmct.Button(str_DATE, alignment=pyxbmct.ALIGN_CENTER_X|pyxbmct.ALIGN_CENTER_Y, font=self.MONO_FONT)
        self.sort_name_button = pyxbmct.Button(str_NAME, alignment=pyxbmct.ALIGN_CENTER_X|pyxbmct.ALIGN_CENTER_Y, font=self.MONO_FONT)
        self.sort_duration_button = pyxbmct.Button(str_DURATION, alignment=pyxbmct.ALIGN_CENTER_X|pyxbmct.ALIGN_CENTER_Y, font=self.MONO_FONT)
        self.list_bg = pyxbmct.Image(__list_bg__)
        self.list = pyxbmct.List(_imageWidth=18, _itemTextYOffset=-1, _alignmentY=pyxbmct.ALIGN_CENTER_Y, font=self.MONO_FONT, _space=0, buttonTexture=__texture_nf__)
        self.delete_button = pyxbmct.Button(str_DELETE)
        self.play_button = pyxbmct.Button(str_PLAY)
        self.close_button = pyxbmct.Button(str_CLOSE)

    def place_controls(self):
        self.placeControl(self.select_label, 1, 1, rowspan=2, columnspan=3)
        self.placeControl(self.show_calls_button, 1, 4, rowspan=2, columnspan=3)
        self.placeControl(self.show_messages_button, 1, 7, rowspan=2, columnspan=3)

        for i in range(5):
            self.placeControl(self.tam_select_button[i], 1, 10 + i, rowspan=2)

        self.placeControl(self.numitems_label, 1, 15, rowspan=2, columnspan=4)
        self.placeControl(self.sort_date_button, 4, 2, rowspan=2, columnspan=4)
        self.placeControl(self.sort_name_button, 4, 6, rowspan=2, columnspan=9)
        self.placeControl(self.sort_duration_button, 4, 15, rowspan=2, columnspan=4)
        self.placeControl(self.list_bg, 6, 1, rowspan=16, columnspan=18)
        self.placeControl(self.list, 6, 1, rowspan=18, columnspan=18)
        self.placeControl(self.delete_button, 23, 1, rowspan=2, columnspan=4)
        self.placeControl(self.play_button, 23, 5, rowspan=2, columnspan=4)
        self.placeControl(self.close_button, 23, 15, rowspan=2, columnspan=4)

    def connect_controls(self):
        self.connect(self.show_calls_button, self.show_calls)
        self.connect(self.show_messages_button, self.show_messages)

        for i in range(self.MAXTAMS):
            self.connect(self.tam_select_button[i], self.set_tam(i))

        self.connect(self.sort_date_button, self.sort_by_date)
        self.connect(self.sort_name_button, self.sort_by_name)
        self.connect(self.sort_duration_button, self.sort_by_duration)
        self.connect(self.list, self.select)
        self.connect(self.delete_button, self.delete)
        self.connect(self.play_button, self.play_message)
        self.connect(self.close_button, self.close)
        self.connect(xbmcgui.ACTION_NAV_BACK, self.close)
        self.connect(xbmcgui.ACTION_PLAYER_PLAY, self.play_selected)

    def set_navigation(self):
        self.show_calls_button.controlRight(self.show_messages_button)
        self.show_calls_button.controlDown(self.sort_date_button)

        self.show_messages_button.controlLeft(self.show_calls_button)
        self.show_messages_button.controlDown(self.sort_date_button)
        self.show_messages_button.controlRight(self.tam_select_button[0])

        for i in range(self.MAXTAMS - 1):
            self.tam_select_button[i].controlRight(self.tam_select_button[i + 1])
            self.tam_select_button[i + 1].controlLeft(self.tam_select_button[i])
            self.tam_select_button[i + 1].controlDown(self.list)
        self.tam_select_button[0].controlLeft(self.show_messages_button)
        self.tam_select_button[0].controlDown(self.list)

        self.sort_date_button.controlUp(self.show_calls_button)
        self.sort_date_button.controlRight(self.sort_name_button)
        self.sort_date_button.controlDown(self.list)

        self.sort_name_button.controlUp(self.show_messages_button)
        self.sort_name_button.controlLeft(self.sort_date_button)
        self.sort_name_button.controlRight(self.sort_duration_button)
        self.sort_name_button.controlDown(self.list)

        self.sort_duration_button.controlUp(self.show_messages_button)
        self.sort_duration_button.controlLeft(self.sort_name_button)
        self.sort_duration_button.controlDown(self.list)

        self.list.controlUp(self.sort_date_button)
        self.list.controlLeft(self.sort_date_button)
        self.list.controlRight(self.delete_button)
        self.list.controlDown(self.close_button)

        self.close_button.controlUp(self.list)
        self.close_button.controlLeft(self.play_button)

        self.play_button.controlUp(self.list)
        self.play_button.controlRight(self.close_button)
        self.play_button.controlLeft(self.delete_button)

        self.delete_button.controlUp(self.list)
        self.delete_button.controlRight(self.play_button)

    def set_tam(self, index):
        def update_tam():
            if self.tamID == self.tamIDs[index]:
                return

            self.tamID = self.tamIDs[index]

            self.update_list(True)

        return update_tam

    def play_message(self):
        if self.show_calls_button.isSelected() or self.selected_item == -1:
           return

        listitem = self.list.getListItem(self.list.getSelectedPosition())
        try:
            message_path = self.items[int(listitem.getProperty('index'))]['path'].split('=')[1]
            #message_path = listitem.getProperty('path')
            message_id   = self.items[int(listitem.getProperty('index'))]['id'] 
            #message_id = int(listitem.getProperty('id'))

            if not xbmcvfs.exists(self.tmpdir):
                xbmcvfs.mkdirs(self.tmpdir)

            tmpfile = self.box.saveRecording(message_path, dest=translatePath(self.tmpdir))

        except Exception as e:
            log(e)
            return

        # Use Builtin PlayMedia to play tmpfile asynchronously (code execution will continue immmediately):
        #xbmc.executebuiltin('PlayMedia({})'.format(tmpfile))
        #xbmc.sleep(500) # wait until playing has started

        # Alternative call of xbmc.Player().play() with full control, wait until tmpfile has stopped playing:
        self._player.play(tmpfile)            # self._player = xbmc.Player() set in __init__
        xbmc.sleep(500)                       # wait until playing has started

        while self._player.isPlaying():
            if self._monitor.waitForAbort(1): # self._monitor = xbmc.Monitor() set in __init__
                log('Abort requested.')
                raise SystemExit

        result = self.box.SOAPset('MarkMessage', Value=message_id, Index=0)

        # Change icon for selected message: new (5) -> none (0)
        self.items[int(listitem.getProperty('index'))]['type'] = 0
        try:
            listitem.setIconImage(__icons__[0])
        except:
            listitem.setArt({'icon': __icons__[0]})

        # Maybe too early here since PlayMedia might still be accessing the file -> Cleanup in self.close()
        xbmcvfs.delete(tmpfile)

        return

    def delete(self):
        if self.show_calls_button.isSelected():
            if not xbmcgui.Dialog().yesno(__addon_name__, str_DELCALLS, str_CANCEL, str_PROCEED):
                return

            self.box.deleteCallList()

        elif self.show_messages_button.isSelected():
            if self.selected_item == -1:
                if not xbmcgui.Dialog().yesno(__addon_name__, str_DELMSGS, str_CANCEL, str_PROCEED):
                    return

                try:
                    for item in self.items:
                        message_id = item['id']
                        self.box.SOAPset('DeleteMessage', Value=message_id, Index=0)

                except Exception as e:
                    log(e)
                    #return
            else:

                if not xbmcgui.Dialog().yesno(__addon_name__, str_DELMSG, str_CANCEL, str_PROCEED):
                    return

                listitem = self.list.getListItem(self.list.getSelectedPosition())
                try:
                    message_id = self.items[int(listitem.getProperty('index'))]['id'] # = listitem.getProperty('id')
                    result = self.box.SOAPset('DeleteMessage', Value=message_id, Index=0)

                except Exception as e:
                    log(e)
                    return

        self.update_list(True)
        self.setFocus(self.list)

        return

    def play_selected(self):
        self.select(play=True)

    def select(self, play=False):
        if self.show_calls_button.isSelected():
            items = ['{} ({})'.format(n['number'], n['name']) for n in self.numlist]
            preselect = [i for i in range(len(self.numlist)) if (self.numlist[i]['number'] in self.numfilter or len(self.numfilter)==0)]

            dialog = MultiChoiceDialog(str_FILTERDLG, items, preselect=preselect)
            dialog.doModal()
            selected = dialog.selected
            del dialog
            #selected = xbmcgui.Dialog().multiselect(str_FILTERDLG, items, preselect=preselect)

            if selected:
                filter = tuple(self.numlist[i]['number'] for i in range(len(self.numlist)) if i in selected)
                if len(filter) == len(self.numlist):
                    filter = ()
                if filter == self.numfilter:
                    return
                self.numfilter = filter
                self.update_list(True)
            return

        #listitem = self.list.getListItem(self.list.getSelectedPosition())
        listitem = self.list.getSelectedItem()

        if self.selected_item != -1:
            lastitem = self.list.getListItem(self.selected_item)
            lastitem.setLabel('{}'.format(lastitem.getLabel()[1:]))

        if self.selected_item != self.list.getSelectedPosition():
            listitem.setLabel('{}{}'.format('>', listitem.getLabel()))
            self.selected_item = self.list.getSelectedPosition()
            self.play_button.setVisible(True)
            if play:
                self.play_message()
        else:
            self.selected_item = -1
            self.play_button.setVisible(False)

    def sort_by_date(self):
        if self.sort_by == 'date':
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_by = 'date'
            self.sort_reverse = True
        self.update_list()

    def sort_by_name(self):
        if self.sort_by == 'name':
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_by = 'name'
            self.sort_reverse = False
        self.update_list()

    def sort_by_duration(self):
        if self.sort_by == 'duration':
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_by = 'duration'
            self.sort_reverse = False
        self.update_list()

    def show_calls(self):
        update = self.show_messages_button.isSelected()
        self.show_calls_button.setSelected(True)
        self.show_messages_button.setSelected(False)
        if update:
            self.sort_by = 'date'
            self.sort_reverse = True
            self.update_list(True)

    def show_messages(self):
        update = self.show_calls_button.isSelected()
        self.show_calls_button.setSelected(False)
        self.show_messages_button.setSelected(True)
        if update:
            self.sort_by = 'date'
            self.sort_reverse = True
            self.update_list(True)

    def update_list(self, new=False):
        self.list.reset()

        if self.show_calls_button.isSelected():
            if new or not self.items:
                self.items = self.list_calls()

            for i in range(self.MAXTAMS):
                self.tam_select_button[i].setVisible(False)

        elif self.show_messages_button.isSelected(): # 'else:' should bes sufficient
            if new or not self.items:
                self.items = self.list_messages()

            for i in range(self.MAXTAMS):
                self.tam_select_button[i].setVisible((i in self.tamIDs) and (len(self.tamIDs) > 1))

        # disable 'play' button until message is selected
        self.play_button.setVisible(False)

        if self.sort_by == 'name':
            self.items.sort(key=lambda x: locale.strxfrm(x[self.sort_by]), reverse=self.sort_reverse)
        else:
            self.items.sort(key=lambda x: x[self.sort_by], reverse=self.sort_reverse)

        self.list.addItems([item['text'] for item in self.items])

        for index in range(self.list.size()):
            if self.items[index]['type'] < len(__icons__):
                try:
                    self.list.getListItem(index).setIconImage(__icons__[self.items[index]['type']])
                except:
                    self.list.getListItem(index).setArt({'icon': __icons__[self.items[index]['type']]})
            else:
                try:
                    self.list.getListItem(index).setIconImage(__icons__[0])
                except:
                    self.list.getListItem(index).setArt({'icon': __icons__[0]})
            self.list.getListItem(index).setProperty('index', str(index))
            #self.list.getListItem(index).setProperties({'index': str(index), \
            #     'type': str(self.items[index]['type']), \
            #     'id': str(self.items[index]['type']), \
            #     'path': self.items[index]['path'].split('=')[1]})

        if new:
            if self.list.size() == 1 and ((str_NOCALLS in self.list.getListItem(0).getLabel()) or (str_NOMESSAGES in self.list.getListItem(0).getLabel())):
                self.numitems_label.setLabel('0 {}'.format(str_CALLS if self.show_calls_button.isSelected() else str_MESSAGES))
                self.delete_button.setEnabled(False)
            else:
                if self.list.size() == 1:
                    self.numitems_label.setLabel('{} {}'.format(self.list.size(), str_CALL if self.show_calls_button.isSelected() else str_MESSAGE))
                else:
                    self.numitems_label.setLabel('{} {}'.format(self.list.size(), str_CALLS if self.show_calls_button.isSelected() else str_MESSAGES))
                self.delete_button.setEnabled(True)

        self.selected_item = -1

        return

    def close(self):
        # Cleanup
        if xbmcvfs.exists(self.tmpdir):
            xbmcvfs.rmdir(self.tmpdir, force=True)

        super(FritzBoxDialog, self).close()

    def list_messages(self, showall=True):
        noitem = {
            'id': 0,
            'type': 0,
            'path': '',
            'date': datetime.now(),
            'name': '',
            'duration': '0:00',
            'text': str_NOMESSAGES
            }

        if len(self.tamIDs) == 0:
            return [noitem]

        messages = []
        try:
            url = self.box.SOAPget('GetMessageList', Index=self.tamID)
            xmldata = self.box.SOAPgetURL(url)
            messages = fb.xmlMessages2dict(xmldata)
        except Exception as e:
            log(e)
            raise

        if not showall:
            messages = [m for m in messages if m['new']]

        if len(messages) == 0:
            return [noitem]

        items = []

        for message in messages:
            item = {}
            item['id']   = message['index']
            item['type'] = 5 if message['new'] else 0 # NEW --> type=5
            item['path'] = message['path']

            date = datetime.strftime(message['date'], '%d.%m.%y %H:%M')
            name = message['name'] or (message['callerID'] or str_ANONYMOUS)
            duration = (message['duration'].split(':')[0] + ' ' + str_HRS + ' ' \
                if message['duration'].split(':')[0] != '0' else \
                ('< ' if message['duration'] == '0:01' else '')) \
                + str(int(message['duration'].split(':')[1])) + ' ' + str_MNS
            item['text'] = '{:<16s}{:<35s}{:>12s}'.format(date, name[:34], duration)

            item['name'] = name
            item['date'] = message['date']
            item['duration'] = message['duration']

            items.append(item)

        return items

    def list_calls(self, type=0, days=0):
        noitem = {
            'id': 0,
            'type': 0,
            'path': '',
            'date': datetime.now(),
            'name': '',
            'duration': '0:00',
            'text': str_NOCALLS
            }

        if len(self.numlist) == 0:
           noitem['text'] = str_NOACTIVENUM
           return [noitem]

        url = self.box.SOAPget('GetCallList')
        if days > 0:
            xmldata = self.box.SOAPgetURL(url, days=days)
        else:
            xmldata = self.box.SOAPgetURL(url)

        calls = []
        try:
            calls = fb.xmlCalls2dict(xmldata)
        except Exception as e:
            log(e)

        # Call types:
        # -----------
        # ALL_CALLS = 0
        # INCOMING  = 1
        # MISSED    = 2
        # OUTGOING  = 3
        # ACTIVE_INCOMING = 9 (treat as INCOMING)
        # REJECTED_INCOMING  = 10 (BLOCKED)
        # ACTIVE_OUTGOING = 11 (treat as OUTGOING)

        if type > 0:
            calls = [c for c in calls if c['type'] == type]

        if len(self.numfilter) > 0:
            calls = [c for c in calls if (c['callerID'] in self.numfilter or c['calledID'] in self.numfilter)]

        if len(calls) == 0:
            return [noitem]

        items = []

        for call in calls:
            item = {}
            item['id'] = call['id']
            item['type'] = call['type'] % 8 # type modulo 8: 9 -- 1, 10 --> 2, 11 --> 3
            if call['type'] == fb.REJECTED_INCOMING: # BLOCKED: 10 --> 4
                item['type'] = 4
            item['path'] = call['path']

            name = call['name'] or (call['calledID'] if (call['type'] % 8) == fb.OUTGOING else (call['callerID'] or str_ANONYMOUS))
            date = datetime.strftime(call['date'], '%d.%m.%y %H:%M')
            if call['type'] in (fb.ACTIVE_INCOMING, fb.ACTIVE_OUTGOING):
                duration = str_ACTIVE
            else:
                duration = (call['duration'].split(':')[0] + ' ' + str_HRS + ' ' \
                    if call['duration'].split(':')[0] != '0' else \
                    ('< ' if call['duration'] == '0:01' else '')) \
                    + str(int(call['duration'].split(':')[1])) + ' ' + str_MNS
            item['text'] = '{:<16s}{:<35s}{:>12s}'.format(date, name[:34], duration)

            item['name'] = name
            item['date'] = call['date']
            item['duration'] = call['duration']

            items.append(item)

        return items


if __name__ == '__main__':
    #
    # Set locale; will affect sorting of strings with special characters (e.g. German umlauts)
    # => might require installation of languae pack, e.g.: sudo apt install language-pack-de
    #
    locale.setlocale(locale.LC_COLLATE, 'de_DE.UTF-8')

    try:
        username = __setting__('username')
        password = __setting__('password')
        hostname = __setting__('hostname')

        numbers  = tuple(number.strip() for number in __setting__('numbers').split(','))

        box = fb.FritzBox(username, password, host=hostname)

        dialog = FritzBoxDialog(box, str_TITLE, numbers=numbers)
    except Exception as e:
        log(e)
        sys.exit(1)

    dialog.doModal()

    del dialog
