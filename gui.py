# -*- coding: utf-8 -*-

###########################################################################
# Python code generated with wxFormBuilder (version Jun 17 2015)
# http://www.wxformbuilder.org/
##
# PLEASE DO "NOT" EDIT THIS FILE!
###########################################################################
import smtplib
import time
from datetime import datetime
import pickle
import threading
from multiprocessing.pool import Pool
from operator import itemgetter

import wx
import wx.xrc
import wx.dataview
import wx.lib.mixins.listctrl as listmix

from gui_event_dlg import AddEventDialog, EditEventDialog
from gui_settings import SettingsDialog
from scraper import check_website


def send_email(message, settings, subject="Tickets available again...", retry=0):
    server = smtplib.SMTP('smtp.gmail.com', 587)
    try:
        server.starttls()
    except Exception as e:
        if retry == 10:
            print('falied with', e)
            return
        retry += 1
        return send_email(subject, message, retry)
    server.login(settings['GmailEmail'], settings['GmailPass'])
    msg = "Subject: {}\n\n{}".format(subject, message)
    msg = msg.encode()

    print('sending to', settings['NotifyEmail'])
    try:
        server.sendmail(settings['GmailEmail'], settings['NotifyEmail'], msg)
    except UnicodeEncodeError:
        pass
    time.sleep(1)
    server.quit()


def ticket_status_check(arguments):

    key = arguments[0]
    value = arguments[1]
    settings = arguments[2]
    #text_log = arguments[3]

    url = value[4]

    print('checking tickets for', value[0])
    checker = check_website(url=url, proxies=settings['Proxy'],
                            row=value[5], log=None, headless=settings['Headless'])
    status_data = checker.check_status()

    print("------------ ticket status check ------------")
    print(status_data)

    status = '|'.join(["Row {}:{}".format(x['row'], x['status'])
                      for x in status_data])
    evt_data = (value[0], value[1], status, value[3], value[4], value[5], value[6],
                datetime.today().strftime('%Y-%m-%d %H:%M'))

    old_data = {}
    # [old_data.update({int(x.split(":")[0].replace("Row ", '')): x.split(':')[1]}) for x in value[2].split('|')]

    if value[2] != '-' or value[2].strip() != '':
        for x in value[2].split("|"):
            try:
                old_data.update(
                    {int(x.split(":")[0].replace("Row ", '')): x.split(':')[1]})
            except ValueError:
                print(value[2])
    # print("000000000000000000000-------------------000000")
    # print(status_data)

    for row in status_data:
        try:
            old_status = old_data[row['row']]
        except KeyError:
            old_status = None
        new_status = row['status']
        print("NEW STATUS:", new_status, "OLD STATUS:", old_status)

        if old_status:
            if old_status == "Sold Out" and new_status != "Sold Out":
                message = "Tickets for event {}\nTicket Type: {}(ROW: {})\nURL: {}\nStatus went from {} to {}\n".format(value[0], row['name'],
                                                                                                                        row['row'], url, old_status, new_status)
                send_email(message, settings)
        if old_status is None or old_status != 'Unavailable':
            if new_status == "Unavailable":
                message = "Tickets for event {}\nTicket Type: {}(ROW: {})\nURL: {}\ntatus went from {} to {}\n".format(value[0], row['name'],
                                                                                                                       row['row'], url, old_status, new_status)
                send_email(message, settings)

    return (key, evt_data), (url, time.time())

    self.event_data[key] = evt_data
    self.save_event_data()
    self.load_data_to_list_ctrl()
    self.event_timestamps[url] = time.time()


class TestListCtrl(wx.ListCtrl):

    # ----------------------------------------------------------------------
    def __init__(self, parent, ID=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)


###########################################################################
# Class MyFrame1
###########################################################################

class CheckerApp(wx.Frame, listmix.ColumnSorterMixin):

    def __init__(self, parent):
        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title=wx.EmptyString, pos=wx.DefaultPosition,
                          size=wx.Size(1000, 1000), style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL)

        # Main variables
        self.event_data = {}
        self.event_timestamps = {}
        with open('settings.pickle', 'rb') as f:
            self.settings = pickle.load(f)

        self.SetSizeHintsSz(wx.DefaultSize, wx.DefaultSize)
        self.SetTitle('X-checker')

        bSizer1 = wx.BoxSizer(wx.VERTICAL)

        bSizer2 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_button_start = wx.Button(
            self, wx.ID_ANY, u"Start", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_button_start.Bind(wx.EVT_BUTTON, self.start_checking)
        bSizer2.Add(self.m_button_start, 0, wx.ALL, 5)

        self.m_gauge1 = wx.Gauge(
            self, wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL)
        self.m_gauge1.SetValue(0)
        bSizer2.Add(self.m_gauge1, 0, wx.ALL, 5)

        m_comboBox1Choices = [u'Date', u'Added on', u'Last Check']
        self.m_comboBox1 = wx.ComboBox(self, wx.ID_ANY, u"Select...", wx.DefaultPosition, wx.DefaultSize,
                                       m_comboBox1Choices, 0)
        bSizer2.Add(self.m_comboBox1, 0, wx.ALL, 5)

        self.m_button_up = wx.Button(
            self, wx.ID_ANY, u"↑", wx.DefaultPosition, wx.Size(25, 25), 0)
        self.m_button_up.Bind(wx.EVT_BUTTON, self.sort_up)
        bSizer2.Add(self.m_button_up, 0, wx.ALL, 5)

        self.m_button_down = wx.Button(
            self, wx.ID_ANY, u"↓", wx.DefaultPosition, wx.Size(25, 25), 0)
        self.m_button_down.Bind(wx.EVT_BUTTON, self.sort_down)
        bSizer2.Add(self.m_button_down, 0, wx.ALL, 5)

        self.m_text_log = wx.TextCtrl(
            self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(300, -1), 0)
        bSizer2.Add(self.m_text_log, 0, wx.ALL | wx.EXPAND, 5)

        bSizer1.Add(bSizer2, 0, wx.ALL, 5)

        bSizer3 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_button_add = wx.Button(
            self, wx.ID_ANY, u"Add Event", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_button_add.Bind(wx.EVT_BUTTON, self.add_event)
        bSizer3.Add(self.m_button_add, 0, wx.ALL, 5)

        self.m_button_edit = wx.Button(
            self, wx.ID_ANY, u"Edit Event", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_button_edit.Bind(wx.EVT_BUTTON, self.edit_event)
        bSizer3.Add(self.m_button_edit, 0, wx.ALL, 5)

        self.m_button_remove = wx.Button(
            self, wx.ID_ANY, u"Remove Event", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_button_remove.Bind(wx.EVT_BUTTON, self.remove_event)
        bSizer3.Add(self.m_button_remove, 0, wx.ALL, 5)

        self.m_button_settings = wx.Button(
            self, wx.ID_ANY, u"Settings", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_button_settings.Bind(wx.EVT_BUTTON, self.edit_settings)
        bSizer3.Add(self.m_button_settings, 0, wx.ALL, 5)

        bSizer1.Add(bSizer3, 0, wx.ALL, 5)

        self.list_ctrl = TestListCtrl(self, size=(-1, 1500),
                                      style=wx.LC_REPORT
                                      | wx.BORDER_SUNKEN
                                      | wx.LC_SORT_ASCENDING
                                      | wx.LC_REPORT
                                      )
        self.list_ctrl.InsertColumn(0, "Event Name")
        self.list_ctrl.InsertColumn(1, "Date", wx.LIST_FORMAT_RIGHT)
        self.list_ctrl.InsertColumn(2, "Status")
        self.list_ctrl.InsertColumn(3, "Interval")
        self.list_ctrl.InsertColumn(4, 'URL')
        self.list_ctrl.InsertColumn(6, 'Rows')
        self.list_ctrl.InsertColumn(7, 'Added on')
        self.list_ctrl.InsertColumn(8, 'Last Check')
        bSizer1.Add(self.list_ctrl, 0, wx.ALL | wx.EXPAND, 5)

        self.SetSizer(bSizer1)
        self.Layout()

        self.Centre(wx.BOTH)
        self.load_data_to_list_ctrl()

    # BUTTONS
    def sort_up(self, event):
        self.sort_by_date(True)

    def sort_down(self, event):
        self.sort_by_date(False)

    def sort_by_date(self, ascending):
        if self.m_comboBox1.GetValue() == 'Sort Column...':
            return
        column_indexes = {
            'Date': 1,
            'Added on': 7,
            'Last Check': 8
        }
        column_idx = column_indexes[self.m_comboBox1.GetValue()]

        print("Sorting by column:", self.m_comboBox1.GetValue())
        data_lst = []
        for key, data in self.event_data.items():
            if data[column_idx] == '-':
                dat = list(data)
                dat[column_idx] = '1900-01-01'
                if column_idx == 8:
                    dat[column_idx] += ' 00:00'
                data = tuple(dat)
            data_lst.append(data)

        data_lst.sort(key=itemgetter(1), reverse=True)

        date_format = "%Y-%m-%d"
        if column_idx == 8:
            date_format += ' %H:%M'
        data_lst.sort(key=lambda L: datetime.strptime(
            L[column_idx], date_format))

        data_lst2 = []
        for d in data_lst:
            if '1900-01-01' in d[column_idx]:
                dat = list(d)
                dat[column_idx] = '-'
                d = tuple(dat)
            data_lst2.append(d)

        if not ascending:
            data_lst2.reverse()

        self.event_data = {}
        for i, data in enumerate(data_lst2, 1):
            self.event_data[i] = data

        self.save_event_data()
        self.load_data_to_list_ctrl()

    def edit_event(self, event):
        selected = self.list_ctrl.GetFirstSelected()
        if selected >= 0:
            url = self.list_ctrl.GetItemText(selected, 4)
            data_key = None
            for key, value in self.event_data.items():
                if value[4] == url:
                    print(key)
                    data_key = key
                    break

            dlg = EditEventDialog(self, value)
            if dlg.ShowModal() == wx.ID_OK:
                data = dlg.add_event()
                url = data['url']
                date = data['date']
                name = data['name']
                interval = data['interval']
                ticket_row = data['row']

                evt_data = (
                    name, date, value[2], interval, url, ticket_row, value[6], value[7])
                self.event_data[key] = evt_data
                self.save_event_data()
                self.load_data_to_list_ctrl()

    def fix_ids(self):
        events = {}
        i = 1
        for key, value in self.event_data.items():
            events[i] = value
            i += 1
        return events

    def remove_event(self, event):
        selected = self.list_ctrl.GetFirstSelected()
        if selected >= 0:
            url = self.list_ctrl.GetItemText(selected, 4)
            data_key = None
            for key, value in self.event_data.items():
                if value[4] == url:
                    data_key = key
                    break
            self.event_data.pop(data_key)
            self.event_data = self.fix_ids()
            self.save_event_data()
            self.load_data_to_list_ctrl()
            # self.mas.remove_event(value)

    def edit_settings(self, event):
        dlg = SettingsDialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            self.settings = dlg.get_data()
            with open('settings.pickle', 'wb+') as f:
                pickle.dump(self.settings, f)

    def add_event(self, event):
        dlg = AddEventDialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.add_event()
            url = data['url']
            date = data['date']
            name = data['name']
            interval = data['interval']
            ticket_row = data['row']
            date_created = datetime.today().strftime('%Y-%m-%d')
            # print(self.event_data)
            evt_dat = (name, date, '-', interval, url,
                       ticket_row, date_created, "-")
            self.event_data[len(self.event_data.keys())+1] = evt_dat
            self.save_event_data()
            self.load_data_to_list_ctrl()
        dlg.Destroy()

    def start_checking(self, event):
        if self.m_button_start.LabelText == "Start":
            self.m_gauge1.Pulse()
            self.m_button_start.SetLabel("Stop")
            self.th = threading.Thread(target=self.update_gui)
            self.th.start()
        elif self.m_button_start.LabelText == "Stop":
            self.m_gauge1.SetValue(0)
            self.m_button_start.SetLabel("Start")

    def update_gui(self):
        self.shutdown_event = threading.Event()

        while True:
            if self.m_button_start.LabelText == "Start":
                self.shutdown_event.set()
                break

            # Here go events from event_data that are due to be checked (timestamp)
            events_to_check = {}
            for key, value in self.event_data.items():
                url = value[4]
                if url in self.event_timestamps.keys():
                    interval = int(value[3]) * 60
                    current_time = time.time()
                    last_time_check = self.event_timestamps[url]
                    if current_time - last_time_check > interval:
                        events_to_check[key] = value
                else:
                    events_to_check[key] = value

            event_lst = [(x[0], x[1], self.settings)
                         for x in events_to_check.items()]

            def chunks(l, n):
                """Yield successive n-sized chunks from l."""
                for i in range(0, len(l), n):
                    yield l[i:i + n]

            number_of_threads = 4  # TODO Add threads to settings
            for lst in chunks(event_lst, number_of_threads):
                # with Pool(number_of_threads) as p:
                #     r = p.map(ticket_status_check, lst)

                r = []
                for l in lst:
                    r.append(ticket_status_check(l))

                data_lst = [x[0] for x in r if x]
                timestamp_lst = [x[1] for x in r if x]
                for key, evt_data in data_lst:
                    self.event_data[key] = evt_data
                for url, ts in timestamp_lst:
                    self.event_timestamps[url] = ts

                self.save_event_data()
                self.load_data_to_list_ctrl()

            # ########################################################
            #
            # for key, value in self.event_data.items():
            #     url = value[4]
            #     if url in self.event_timestamps.keys():
            #         interval = int(value[3])*60
            #         current_time = time.time()
            #         last_time_check = self.event_timestamps[url]
            #         if current_time - last_time_check <= interval:
            #             continue
            #
            #     if self.m_button_start.LabelText == "Start":
            #         self.shutdown_event.set()
            #         break
            #     print('checking tickets for', value[0])
            #     checker = check_website(url=url, proxies=self.settings['Proxy'],
            #                             row=value[5], log=self.m_text_log)
            #     status_data = checker.check_status()
            #
            #
            #
            #     status = '|'.join(["Row {}:{}".format(x['row'], x['status']) for x in status_data])
            #     evt_data = (value[0], value[1], status, value[3], value[4], value[5], value[6],
            #                             datetime.today().strftime('%Y-%m-%d %H:%M'))
            #
            #     old_data = {}
            #     #[old_data.update({int(x.split(":")[0].replace("Row ", '')): x.split(':')[1]}) for x in value[2].split('|')]
            #
            #     if value[2] != '-':
            #         for x in value[2].split("|"):
            #             old_data.update({int(x.split(":")[0].replace("Row ", '')): x.split(':')[1]})
            #
            #
            #     for row in status_data:
            #         try:
            #             old_status = old_data[row['row']]
            #         except KeyError:
            #             old_status = None
            #         new_status = row['status']
            #         print("NEW STATUS:", new_status, "OLD STATUS:", old_status)
            #         if old_status:
            #             if old_status == "Sold Out" and new_status != "Sold Out":
            #                 message = "Tickets for event {}\nTicket Type: {}(ROW: {})\nURL: {}".format(value[0], row['name'], row['row'], url)
            #                 self.send_email(message)
            #
            #
            #     self.event_data[key] = evt_data
            #     self.save_event_data()
            #     self.load_data_to_list_ctrl()
            #     self.event_timestamps[url] = time.time()

    # Other

    def send_email(self, message, subject="Tickets available again...", retry=0):
        server = smtplib.SMTP('smtp.gmail.com', 587)
        try:
            server.starttls()
        except Exception as e:
            if retry == 10:
                print('falied with', e)
                return
            retry += 1
            return self.send_email(subject, message, retry)
        server.login(self.settings['GmailEmail'], self.settings['GmailPass'])
        msg = "Subject: {}\n\n{}".format(subject, message)
        msg = msg.encode()

        print('sending to', self.settings['NotifyEmail'])
        try:
            server.sendmail(
                self.settings['GmailEmail'], self.settings['NotifyEmail'], msg)
        except UnicodeEncodeError:
            pass
        time.sleep(1)
        server.quit()

    def load_event_data(self):
        with open('data.pickle', 'rb') as f:
            self.event_data = pickle.load(f)

    def save_event_data(self):
        with open('data.pickle', 'wb') as f:
            pickle.dump(self.event_data, f)

    def load_data_to_list_ctrl(self):
        self.list_ctrl.DeleteAllItems()
        self.load_event_data()

        for x in list(self.event_data.keys()):
            self.list_ctrl.InsertItem(10000, '')

        for key, data in self.event_data.items():
            index = key - 1
            self.list_ctrl.SetItem(index, 0, data[0])
            self.list_ctrl.SetItem(index, 1, data[1])
            self.list_ctrl.SetItem(index, 2, data[2])
            self.list_ctrl.SetItem(index, 3, data[3])
            self.list_ctrl.SetItem(index, 4, data[4])
            self.list_ctrl.SetItem(index, 5, data[5])
            self.list_ctrl.SetItem(index, 6, data[6])
            self.list_ctrl.SetItem(index, 7, data[7])
            #self.list_ctrl.SetItem(index, 8, data[8])
            self.list_ctrl.SetItemData(index, key)

        self.itemDataMap = self.event_data
        listmix.ColumnSorterMixin.__init__(self, 5)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick, self.list_ctrl)

    def GetListCtrl(self):
        return self.list_ctrl

    def OnColClick(self, event):
        event.Skip()

    # Threading
    def startThread(self, event):
        th = threading.Thread(target=self.start, args=(event,))
        th.start()

    def stopThread(self, event):
        self.shutdown_event.set()


if __name__ == "__main__":
    app = wx.App(False)
    frame = CheckerApp(None)
    frame.Show(True)
    # start the applications
    app.MainLoop()
