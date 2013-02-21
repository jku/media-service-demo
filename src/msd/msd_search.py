# media-service-demo
#
# Copyright (C) 2012 Intel Corporation. All rights reserved.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU Lesser General Public License,
# version 2.1, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St - Fifth Floor, Boston, MA 02110-1301 USA.
#
# Mark Ryan <mark.d.ryan@intel.com>
#

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import cStringIO
import dateutil.parser
import datetime

from msd_sort_order import *
from msd_upnp import *

class SearchModel(gtk.ListStore):
    filter = ["Artist", "DisplayName", "URLs", "Date", "Path", "Type"]

    buffer_size = 50

    @staticmethod
    def __create_query_string(query, images, videos, music):
        search_string = None

        if images or videos or music:
            q_buffer = cStringIO.StringIO()
            try:
                if query != "":
                    q_buffer.write('(Artist contains "{0}"\
 or DisplayName contains "{0}")'.format(query))
                    q_buffer.write(' and ')
                q_buffer.write(' ( ')
                if images:
                    q_buffer.write('Type derivedfrom "image" ')
                if videos:
                    if images:
                        q_buffer.write(' or ')
                    q_buffer.write('Type derivedfrom "video" ')
                if music:
                    if images or videos:
                        q_buffer.write(' or ')
                    q_buffer.write('Type derivedfrom "audio" ')
                q_buffer.write(' ) and ( RefPath exists false )')

                search_string = q_buffer.getvalue()
            finally:
                q_buffer.close()

        return search_string

    def __on_search_reply(self, items, max_items):
        max_items = max(max_items, len(items))

        if max_items != self.__max_items:
            self.__max_items = max_items
        for item in items:
            try:
                date = dateutil.parser.parse(item['Date'].strftime("%x"))
            except:
                date = ''
            self.append([item.get('DisplayName', ''),
                         item.get('Artist', ''),
                         date,
                         item.get('Type').capitalize().split('.', 1)[0],
                         item.get('Path', ''),
                         item.get('URLs', [''])[0]])

    def __on_search_error(self, error):
        print "Search failed: %s" % error

    def __get_search_items(self, start, count):
        sort_descriptor = self.__sort_order.get_upnp_sort_order()
        self.__root.search(self.__search_string,
                           start, count,
                           SearchModel.filter,
                           sort_descriptor,
                           self.__on_search_reply,
                           self.__on_search_error)

    def flush(self):
        self.clear()
        self.__max_items = 0
        self.__get_search_items(0, SearchModel.buffer_size)

    def __init__(self, root, query, images, videos, music, sort_order):
        gtk.ListStore.__init__(self,
                               gobject.TYPE_STRING, # DisplayName
                               gobject.TYPE_STRING, # Artist
                               gobject.TYPE_STRING, # Date
                               gobject.TYPE_STRING, # Type
                               gobject.TYPE_STRING, # Path
                               gobject.TYPE_STRING) # URLs[0]
        self.__max_items = 0
        self.__sort_order = sort_order
        self.__root = root
        self.__search_string = SearchModel.__create_query_string(query, images,
                                                                 videos, music)
        self.flush()
