#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import argparse
import construct
import datetime
import logging
import sys

import collector
import hexdump
import registry


# pylint: disable=logging-format-interpolation

class AppCompatCacheHeader(object):
  """Class that contains the Application Compatibility Cache header."""

  def __init__(self):
    """Initializes the header object."""
    super(AppCompatCacheHeader, self).__init__()
    self.number_of_cached_entries = 0
    self.header_size = 0


class AppCompatCacheCachedEntry(object):
  """Class that contains the Application Compatibility Cache cached entry."""

  def __init__(self):
    """Initializes the cached entry object."""
    super(AppCompatCacheCachedEntry, self).__init__()
    self.cached_entry_size = 0
    self.data = None
    self.file_size = None
    self.insertion_flags = None
    self.last_modification_time = None
    self.last_update_time = None
    self.shim_flags = None
    self.path = None


class AppCompatCacheDataParser(object):
  """Class that parses the Application Compatibility Cache data."""

  FORMAT_TYPE_2000 = 1
  FORMAT_TYPE_XP = 2
  FORMAT_TYPE_2003 = 3
  FORMAT_TYPE_VISTA = 4
  FORMAT_TYPE_7 = 5
  FORMAT_TYPE_8 = 6
  FORMAT_TYPE_10 = 7

  # AppCompatCache format signature used in Windows XP.
  _HEADER_SIGNATURE_XP = 0xdeadbeef

  # AppCompatCache format used in Windows XP.
  _HEADER_XP_32BIT_STRUCT = construct.Struct(
      u'appcompatcache_header_xp',
      construct.ULInt32(u'signature'),
      construct.ULInt32(u'number_of_cached_entries'),
      construct.ULInt32(u'number_of_lru_entries'),
      construct.ULInt32(u'unknown1'),
      construct.Array(96, construct.ULInt32("lru_entry")))

  _CACHED_ENTRY_XP_32BIT_STRUCT = construct.Struct(
      u'appcompatcache_cached_entry_xp_32bit',
      construct.Array(528, construct.Byte(u'path')),
      construct.ULInt64(u'last_modification_time'),
      construct.ULInt64(u'file_size'),
      construct.ULInt64(u'last_update_time'))

  # AppCompatCache format signature used in Windows 2003, Vista and 2008.
  _HEADER_SIGNATURE_2003 = 0xbadc0ffe

  # AppCompatCache format used in Windows 2003.
  _HEADER_2003_STRUCT = construct.Struct(
      u'appcompatcache_header_2003',
      construct.ULInt32(u'signature'),
      construct.ULInt32(u'number_of_cached_entries'))

  _CACHED_ENTRY_2003_32BIT_STRUCT = construct.Struct(
      u'appcompatcache_cached_entry_2003_32bit',
      construct.ULInt16(u'path_size'),
      construct.ULInt16(u'maximum_path_size'),
      construct.ULInt32(u'path_offset'),
      construct.ULInt64(u'last_modification_time'),
      construct.ULInt64(u'file_size'))

  _CACHED_ENTRY_2003_64BIT_STRUCT = construct.Struct(
      u'appcompatcache_cached_entry_2003_64bit',
      construct.ULInt16(u'path_size'),
      construct.ULInt16(u'maximum_path_size'),
      construct.ULInt32(u'unknown1'),
      construct.ULInt64(u'path_offset'),
      construct.ULInt64(u'last_modification_time'),
      construct.ULInt64(u'file_size'))

  # AppCompatCache format used in Windows Vista and 2008.
  _CACHED_ENTRY_VISTA_32BIT_STRUCT = construct.Struct(
      u'appcompatcache_cached_entry_vista_32bit',
      construct.ULInt16(u'path_size'),
      construct.ULInt16(u'maximum_path_size'),
      construct.ULInt32(u'path_offset'),
      construct.ULInt64(u'last_modification_time'),
      construct.ULInt32(u'insertion_flags'),
      construct.ULInt32(u'shim_flags'))

  _CACHED_ENTRY_VISTA_64BIT_STRUCT = construct.Struct(
      u'appcompatcache_cached_entry_vista_64bit',
      construct.ULInt16(u'path_size'),
      construct.ULInt16(u'maximum_path_size'),
      construct.ULInt32(u'unknown1'),
      construct.ULInt64(u'path_offset'),
      construct.ULInt64(u'last_modification_time'),
      construct.ULInt32(u'insertion_flags'),
      construct.ULInt32(u'shim_flags'))

  # AppCompatCache format signature used in Windows 7 and 2008 R2.
  _HEADER_SIGNATURE_7 = 0xbadc0fee

  # AppCompatCache format used in Windows 7 and 2008 R2.
  _HEADER_7_STRUCT = construct.Struct(
      u'appcompatcache_header_7',
      construct.ULInt32(u'signature'),
      construct.ULInt32(u'number_of_cached_entries'),
      construct.Padding(120))

  _CACHED_ENTRY_7_32BIT_STRUCT = construct.Struct(
      u'appcompatcache_cached_entry_7_32bit',
      construct.ULInt16(u'path_size'),
      construct.ULInt16(u'maximum_path_size'),
      construct.ULInt32(u'path_offset'),
      construct.ULInt64(u'last_modification_time'),
      construct.ULInt32(u'insertion_flags'),
      construct.ULInt32(u'shim_flags'),
      construct.ULInt32(u'data_size'),
      construct.ULInt32(u'data_offset'))

  _CACHED_ENTRY_7_64BIT_STRUCT = construct.Struct(
      u'appcompatcache_cached_entry_7_64bit',
      construct.ULInt16(u'path_size'),
      construct.ULInt16(u'maximum_path_size'),
      construct.ULInt32(u'unknown1'),
      construct.ULInt64(u'path_offset'),
      construct.ULInt64(u'last_modification_time'),
      construct.ULInt32(u'insertion_flags'),
      construct.ULInt32(u'shim_flags'),
      construct.ULInt64(u'data_size'),
      construct.ULInt64(u'data_offset'))

  # AppCompatCache format used in Windows 8.0 and 8.1.
  _HEADER_SIGNATURE_8 = 0x00000080

  _HEADER_8_STRUCT = construct.Struct(
      u'appcompatcache_header_8',
      construct.ULInt32(u'signature'),
      construct.ULInt32(u'unknown1'),
      construct.Padding(120))

  _CACHED_ENTRY_HEADER_8_STRUCT = construct.Struct(
      u'appcompatcache_cached_entry_header_8',
      construct.ULInt32(u'signature'),
      construct.ULInt32(u'unknown1'),
      construct.ULInt32(u'cached_entry_data_size'),
      construct.ULInt16(u'path_size'))

  # AppCompatCache format used in Windows 8.0.
  _CACHED_ENTRY_SIGNATURE_8_0 = u'00ts'

  # AppCompatCache format used in Windows 8.1.
  _CACHED_ENTRY_SIGNATURE_8_1 = u'10ts'

  # AppCompatCache format used in Windows 10
  _HEADER_SIGNATURE_10 = 0x00000030

  _HEADER_10_STRUCT = construct.Struct(
      u'appcompatcache_header_8',
      construct.ULInt32(u'signature'),
      construct.ULInt32(u'unknown1'),
      construct.Padding(28),
      construct.ULInt32(u'number_of_cached_entries'),
      construct.Padding(8))

  def __init__(self, debug=False):
    """Initializes the parser object.

    Args:
      debug: optional boolean value to indicate if debug information should
             be printed. The default is false.
    """
    super(AppCompatCacheDataParser, self).__init__()
    self._debug = debug

  def CheckSignature(self, value_data):
    """Parses the signature.

    Args:
      value_data: a binary string containing the value data.

    Returns:
      The format type if successful or None otherwise.
    """
    signature = construct.ULInt32(u'signature').parse(value_data)
    if signature == self._HEADER_SIGNATURE_XP:
      return self.FORMAT_TYPE_XP

    elif signature == self._HEADER_SIGNATURE_2003:
      # TODO: determine which format version is used (2003 or Vista).
      return self.FORMAT_TYPE_2003

    elif signature == self._HEADER_SIGNATURE_7:
      return self.FORMAT_TYPE_7

    elif signature == self._HEADER_SIGNATURE_8:
      if value_data[signature:signature + 4] in [
          self._CACHED_ENTRY_SIGNATURE_8_0, self._CACHED_ENTRY_SIGNATURE_8_1]:
        return self.FORMAT_TYPE_8

    elif signature == self._HEADER_SIGNATURE_10:
      # Windows 10 uses the same cache entry signature as Windows 8.1
      if value_data[signature:signature + 4] in [
          self._CACHED_ENTRY_SIGNATURE_8_1]:
        return self.FORMAT_TYPE_10

    return

  def ParseHeader(self, format_type, value_data):
    """Parses the header.

    Args:
      format_type: integer value that contains the format type.
      value_data: a binary string containing the value data.

    Returns:
      A header object (instance of AppCompatCacheHeader).

    Raises:
      RuntimeError: if the format type is not supported.
    """
    if format_type not in [
        self.FORMAT_TYPE_XP, self.FORMAT_TYPE_2003, self.FORMAT_TYPE_VISTA,
        self.FORMAT_TYPE_7, self.FORMAT_TYPE_8, self.FORMAT_TYPE_10]:
      raise RuntimeError(u'Unsupported format type: {0:d}'.format(format_type))

    header_object = AppCompatCacheHeader()

    if format_type == self.FORMAT_TYPE_XP:
      header_object.header_size = self._HEADER_XP_32BIT_STRUCT.sizeof()
      header_struct = self._HEADER_XP_32BIT_STRUCT.parse(value_data)

    elif format_type == self.FORMAT_TYPE_2003:
      header_object.header_size = self._HEADER_2003_STRUCT.sizeof()
      header_struct = self._HEADER_2003_STRUCT.parse(value_data)

    elif format_type == self.FORMAT_TYPE_VISTA:
      header_object.header_size = self._HEADER_VISTA_STRUCT.sizeof()
      header_struct = self._HEADER_VISTA_STRUCT.parse(value_data)

    elif format_type == self.FORMAT_TYPE_7:
      header_object.header_size = self._HEADER_7_STRUCT.sizeof()
      header_struct = self._HEADER_7_STRUCT.parse(value_data)

    elif format_type == self.FORMAT_TYPE_8:
      header_object.header_size = self._HEADER_8_STRUCT.sizeof()
      header_struct = self._HEADER_8_STRUCT.parse(value_data)

    elif format_type == self.FORMAT_TYPE_10:
      header_object.header_size = self._HEADER_10_STRUCT.sizeof()
      header_struct = self._HEADER_10_STRUCT.parse(value_data)

    if self._debug:
      print(u'Header data:')
      print(hexdump.Hexdump(value_data[0:header_object.header_size]))

    if self._debug:
      print(u'Signature\t\t\t\t\t\t\t\t: 0x{0:08x}'.format(
          header_struct.get(u'signature')))

    if format_type in [
        self.FORMAT_TYPE_XP, self.FORMAT_TYPE_2003, self.FORMAT_TYPE_VISTA,
        self.FORMAT_TYPE_7, self.FORMAT_TYPE_10]:
      header_object.number_of_cached_entries = header_struct.get(
          u'number_of_cached_entries')

      if self._debug:
        print(u'Number of cached entries\t\t\t\t\t\t: {0:d}'.format(
            header_object.number_of_cached_entries))

    if format_type == self.FORMAT_TYPE_XP:
      number_of_lru_entries = header_struct.get(u'number_of_lru_entries')
      if self._debug:
        print(u'Number of LRU entries\t\t\t\t\t\t\t: 0x{0:08x}'.format(
            number_of_lru_entries))
        print(u'Unknown1\t\t\t\t\t\t\t\t: 0x{0:08x}'.format(
            header_struct.get(u'unknown1')))

        print(u'LRU entries:')
      data_offset = 16
      if number_of_lru_entries > 0 and number_of_lru_entries <= 96:
        for lru_entry_index in range(number_of_lru_entries):
          lru_entry = construct.ULInt32(u'cache_entry_index').parse(
              value_data[data_offset:data_offset + 4])
          data_offset += 4

          if self._debug:
            print((
                u'LRU entry: {0:d}\t\t\t\t\t\t\t\t: {1:d} '
                u'(offset: 0x{2:08x})').format(
                    lru_entry_index, lru_entry, 400 + (lru_entry * 552)))

        if self._debug:
          print(u'')

      if self._debug:
        print(u'Unknown data:')
        print(hexdump.Hexdump(value_data[data_offset:400]))

    elif format_type == self.FORMAT_TYPE_8:
      if self._debug:
        print(u'Unknown1\t\t\t\t\t\t\t\t: 0x{0:08x}'.format(
            header_struct.get(u'unknown1')))

    if self._debug:
      print(u'')

    return header_object

  def DetermineCacheEntrySize(
      self, format_type, value_data, cached_entry_offset):
    """Parses a cached entry.

    Args:
      format_type: integer value that contains the format type.
      value_data: a binary string containing the value data.
      cached_entry_offset: integer value that contains the offset of
                           the first cached entry data relative to the start of
                           the value data.

    Returns:
      The cached entry size if successful or None otherwise.

    Raises:
      RuntimeError: if the format type is not supported.
    """
    if format_type not in [
        self.FORMAT_TYPE_XP, self.FORMAT_TYPE_2003, self.FORMAT_TYPE_VISTA,
        self.FORMAT_TYPE_7, self.FORMAT_TYPE_8, self.FORMAT_TYPE_10]:
      raise RuntimeError(u'Unsupported format type: {0:d}'.format(format_type))

    cached_entry_data = value_data[cached_entry_offset:]
    cached_entry_size = 0

    if format_type == self.FORMAT_TYPE_XP:
      cached_entry_size = self._CACHED_ENTRY_XP_32BIT_STRUCT.sizeof()

    elif format_type in [
        self.FORMAT_TYPE_2003, self.FORMAT_TYPE_VISTA, self.FORMAT_TYPE_7]:
      path_size = construct.ULInt16(u'path_size').parse(cached_entry_data[0:2])
      maximum_path_size = construct.ULInt16(u'maximum_path_size').parse(
          cached_entry_data[2:4])
      path_offset_32bit = construct.ULInt32(u'path_offset').parse(
          cached_entry_data[4:8])
      path_offset_64bit = construct.ULInt32(u'path_offset').parse(
          cached_entry_data[8:16])

      if maximum_path_size < path_size:
        logging.error(u'Path size value out of bounds.')
        return

      path_end_of_string_size = maximum_path_size - path_size
      if path_size == 0 or path_end_of_string_size != 2:
        logging.error(u'Unsupported path size values.')
        return

      # Assume the entry is 64-bit if the 32-bit path offset is 0 and
      # the 64-bit path offset is set.
      if path_offset_32bit == 0 and path_offset_64bit != 0:
        if format_type == self.FORMAT_TYPE_2003:
          cached_entry_size = self._CACHED_ENTRY_2003_64BIT_STRUCT.sizeof()
        elif format_type == self.FORMAT_TYPE_VISTA:
          cached_entry_size = self._CACHED_ENTRY_VISTA_64BIT_STRUCT.sizeof()
        elif format_type == self.FORMAT_TYPE_7:
          cached_entry_size = self._CACHED_ENTRY_7_64BIT_STRUCT.sizeof()

      else:
        if format_type == self.FORMAT_TYPE_2003:
          cached_entry_size = self._CACHED_ENTRY_2003_32BIT_STRUCT.sizeof()
        elif format_type == self.FORMAT_TYPE_VISTA:
          cached_entry_size = self._CACHED_ENTRY_VISTA_32BIT_STRUCT.sizeof()
        elif format_type == self.FORMAT_TYPE_7:
          cached_entry_size = self._CACHED_ENTRY_7_32BIT_STRUCT.sizeof()

    elif format_type in [self.FORMAT_TYPE_8, self.FORMAT_TYPE_10]:
      cached_entry_size = self._CACHED_ENTRY_HEADER_8_STRUCT.sizeof()

    return cached_entry_size

  def ParseCachedEntry(
      self, format_type, value_data, cached_entry_index, cached_entry_offset,
      cached_entry_size):
    """Parses a cached entry.

    Args:
      format_type: integer value that contains the format type.
      value_data: a binary string containing the value data.
      cached_entry_index: integer value that contains the cached entry index.
      cached_entry_offset: integer value that contains the offset of
                           the cached entry data relative to the start of
                           the value data.
      cached_entry_size: integer value that contains the cached entry data size.

    Returns:
      A cached entry object (instance of AppCompatCacheCachedEntry).

    Raises:
      RuntimeError: if the format type is not supported.
    """
    if format_type not in [
        self.FORMAT_TYPE_XP, self.FORMAT_TYPE_2003, self.FORMAT_TYPE_VISTA,
        self.FORMAT_TYPE_7, self.FORMAT_TYPE_8, self.FORMAT_TYPE_10]:
      raise RuntimeError(u'Unsupported format type: {0:d}'.format(format_type))

    cached_entry_data = value_data[
        cached_entry_offset:cached_entry_offset + cached_entry_size]

    if format_type in [
        self.FORMAT_TYPE_XP, self.FORMAT_TYPE_2003, self.FORMAT_TYPE_VISTA,
        self.FORMAT_TYPE_7]:
      if self._debug:
        print(u'Cached entry: {0:d} data:'.format(cached_entry_index))
        print(hexdump.Hexdump(cached_entry_data))

    elif format_type in [self.FORMAT_TYPE_8, self.FORMAT_TYPE_10]:
      if self._debug:
        print(u'Cached entry: {0:d} header data:'.format(cached_entry_index))
        print(hexdump.Hexdump(cached_entry_data[:-2]))

    cached_entry_struct = None

    if format_type == self.FORMAT_TYPE_XP:
      if cached_entry_size == self._CACHED_ENTRY_XP_32BIT_STRUCT.sizeof():
        cached_entry_struct = self._CACHED_ENTRY_XP_32BIT_STRUCT.parse(
            cached_entry_data)

    elif format_type == self.FORMAT_TYPE_2003:
      if cached_entry_size == self._CACHED_ENTRY_2003_32BIT_STRUCT.sizeof():
        cached_entry_struct = self._CACHED_ENTRY_2003_32BIT_STRUCT.parse(
            cached_entry_data)

      elif cached_entry_size == self._CACHED_ENTRY_2003_64BIT_STRUCT.sizeof():
        cached_entry_struct = self._CACHED_ENTRY_2003_64BIT_STRUCT.parse(
            cached_entry_data)

    elif format_type == self.FORMAT_TYPE_VISTA:
      if cached_entry_size == self._CACHED_ENTRY_VISTA_32BIT_STRUCT.sizeof():
        cached_entry_struct = self._CACHED_ENTRY_VISTA_32BIT_STRUCT.parse(
            cached_entry_data)

      elif cached_entry_size == self._CACHED_ENTRY_VISTA_64BIT_STRUCT.sizeof():
        cached_entry_struct = self._CACHED_ENTRY_VISTA_64BIT_STRUCT.parse(
            cached_entry_data)

    elif format_type == self.FORMAT_TYPE_7:
      if cached_entry_size == self._CACHED_ENTRY_7_32BIT_STRUCT.sizeof():
        cached_entry_struct = self._CACHED_ENTRY_7_32BIT_STRUCT.parse(
            cached_entry_data)

      elif cached_entry_size == self._CACHED_ENTRY_7_64BIT_STRUCT.sizeof():
        cached_entry_struct = self._CACHED_ENTRY_7_64BIT_STRUCT.parse(
            cached_entry_data)

    elif format_type in [self.FORMAT_TYPE_8, self.FORMAT_TYPE_10]:
      if cached_entry_data[0:4] not in [
          self._CACHED_ENTRY_SIGNATURE_8_0, self._CACHED_ENTRY_SIGNATURE_8_1]:
        raise RuntimeError(u'Unsupported cache entry signature')

      if cached_entry_size == self._CACHED_ENTRY_HEADER_8_STRUCT.sizeof():
        cached_entry_struct = self._CACHED_ENTRY_HEADER_8_STRUCT.parse(
            cached_entry_data)

        cached_entry_data_size = cached_entry_struct.get(
            u'cached_entry_data_size')
        cached_entry_size = 12 + cached_entry_data_size

        cached_entry_data = value_data[
            cached_entry_offset:cached_entry_offset + cached_entry_size]

    if not cached_entry_struct:
      raise RuntimeError(u'Unsupported cache entry size: {0:d}'.format(
          cached_entry_size))

    if format_type in [self.FORMAT_TYPE_8, self.FORMAT_TYPE_10]:
      if self._debug:
        print(u'Cached entry: {0:d} data:'.format(cached_entry_index))
        print(hexdump.Hexdump(cached_entry_data))

    cached_entry_object = AppCompatCacheCachedEntry()
    cached_entry_object.cached_entry_size = cached_entry_size

    path_offset = 0
    data_size = 0

    if format_type == self.FORMAT_TYPE_XP:
      string_size = 0
      for string_index in xrange(0, 528, 2):
        if (ord(cached_entry_data[string_index]) == 0 and
            ord(cached_entry_data[string_index + 1]) == 0):
          break
        string_size += 2

      cached_entry_object.path = cached_entry_data[0:string_size].decode(
          u'utf-16-le')

      if self._debug:
        print(u'Path\t\t\t\t\t\t\t\t\t: {0:s}'.format(cached_entry_object.path))

    elif format_type in [
        self.FORMAT_TYPE_2003, self.FORMAT_TYPE_VISTA, self.FORMAT_TYPE_7]:
      path_size = cached_entry_struct.get(u'path_size')
      maximum_path_size = cached_entry_struct.get(u'maximum_path_size')
      path_offset = cached_entry_struct.get(u'path_offset')

      if self._debug:
        print(u'Path size\t\t\t\t\t\t\t\t: {0:d}'.format(path_size))
        print(u'Maximum path size\t\t\t\t\t\t\t: {0:d}'.format(
            maximum_path_size))
        print(u'Path offset\t\t\t\t\t\t\t\t: 0x{0:08x}'.format(path_offset))

    elif format_type in [self.FORMAT_TYPE_8, self.FORMAT_TYPE_10]:
      path_size = cached_entry_struct.get(u'path_size')

      if self._debug:
        print(u'Signature\t\t\t\t\t\t\t\t: {0:s}'.format(
            cached_entry_data[0:4]))
        print(u'Unknown1\t\t\t\t\t\t\t\t: 0x{0:08x}'.format(
            cached_entry_struct.get(u'unknown1')))
        print(u'Cached entry data size\t\t\t\t\t\t\t: {0:d}'.format(
            cached_entry_data_size))
        print(u'Path size\t\t\t\t\t\t\t\t: {0:d}'.format(path_size))

      cached_entry_data_offset = 14 + path_size
      cached_entry_object.path = cached_entry_data[
          14:cached_entry_data_offset].decode(u'utf-16-le')

      if self._debug:
        print(u'Path\t\t\t\t\t\t\t\t\t: {0:s}'.format(cached_entry_object.path))

      if format_type == self.FORMAT_TYPE_8:
        remaining_data = cached_entry_data[cached_entry_data_offset:]

        cached_entry_object.insertion_flags = construct.ULInt32(
            u'insertion_flags').parse(remaining_data[0:4])
        cached_entry_object.shim_flags = construct.ULInt32(
            u'shim_flags').parse(remaining_data[4:8])

        if self._debug:
          print(u'Insertion flags\t\t\t\t\t\t\t\t: 0x{0:08x}'.format(
              cached_entry_object.insertion_flags))
          print(u'Shim flags\t\t\t\t\t\t\t\t: 0x{0:08x}'.format(
              cached_entry_object.shim_flags))

        if cached_entry_data[0:4] == self._CACHED_ENTRY_SIGNATURE_8_0:
          cached_entry_data_offset += 8

        elif cached_entry_data[0:4] == self._CACHED_ENTRY_SIGNATURE_8_1:
          if self._debug:
            print(u'Unknown1\t\t\t\t\t\t\t\t: 0x{0:04x}'.format(
                construct.ULInt16(u'unknown1').parse(remaining_data[8:10])))

          cached_entry_data_offset += 10

      remaining_data = cached_entry_data[cached_entry_data_offset:]

    if format_type in [
        self.FORMAT_TYPE_XP, self.FORMAT_TYPE_2003, self.FORMAT_TYPE_VISTA,
        self.FORMAT_TYPE_7]:
      cached_entry_object.last_modification_time = cached_entry_struct.get(
          u'last_modification_time')

    elif format_type in [self.FORMAT_TYPE_8, self.FORMAT_TYPE_10]:
      cached_entry_object.last_modification_time = construct.ULInt64(
          u'last_modification_time').parse(remaining_data[0:8])

    if not cached_entry_object.last_modification_time:
      if self._debug:
        print(u'Last modification time\t\t\t\t\t\t\t: 0x{0:08x}'.format(
            cached_entry_object.last_modification_time))

    else:
      timestamp = cached_entry_object.last_modification_time // 10
      date_string = (datetime.datetime(1601, 1, 1) +
                     datetime.timedelta(microseconds=timestamp))

      if self._debug:
        print(u'Last modification time\t\t\t\t\t\t\t: {0!s} (0x{1:08x})'.format(
            date_string, cached_entry_object.last_modification_time))

    if format_type in [self.FORMAT_TYPE_XP, self.FORMAT_TYPE_2003]:
      cached_entry_object.file_size = cached_entry_struct.get(u'file_size')

      if self._debug:
        print(u'File size\t\t\t\t\t\t\t\t: {0:d}'.format(
            cached_entry_object.file_size))

    elif format_type in [self.FORMAT_TYPE_VISTA, self.FORMAT_TYPE_7]:
      cached_entry_object.insertion_flags = cached_entry_struct.get(
          u'insertion_flags')
      cached_entry_object.shim_flags = cached_entry_struct.get(u'shim_flags')

      if self._debug:
        print(u'Insertion flags\t\t\t\t\t\t\t\t: 0x{0:08x}'.format(
            cached_entry_object.insertion_flags))
        print(u'Shim flags\t\t\t\t\t\t\t\t: 0x{0:08x}'.format(
            cached_entry_object.shim_flags))

    if format_type == self.FORMAT_TYPE_XP:
      cached_entry_object.last_update_time = cached_entry_struct.get(
          u'last_update_time')

      if not cached_entry_object.last_update_time:
        if self._debug:
          print(u'Last update time\t\t\t\t\t\t\t: 0x{0:08x}'.format(
              cached_entry_object.last_update_time))

      else:
        timestamp = cached_entry_object.last_update_time // 10
        date_string = (datetime.datetime(1601, 1, 1) +
                       datetime.timedelta(microseconds=timestamp))

        if self._debug:
          print(u'Last update time\t\t\t\t\t\t\t: {0!s} (0x{1:08x})'.format(
              date_string, cached_entry_object.last_update_time))

    if format_type == self.FORMAT_TYPE_7:
      data_offset = cached_entry_struct.get(u'data_offset')
      data_size = cached_entry_struct.get(u'data_size')

      if self._debug:
        print(u'Data offset\t\t\t\t\t\t\t\t: 0x{0:08x}'.format(data_offset))
        print(u'Data size\t\t\t\t\t\t\t\t: {0:d}'.format(data_size))

    elif format_type in [self.FORMAT_TYPE_8, self.FORMAT_TYPE_10]:
      data_offset = cached_entry_offset + cached_entry_data_offset + 12
      data_size = construct.ULInt32(u'data_size').parse(remaining_data[8:12])

      if self._debug:
        print(u'Data size\t\t\t\t\t\t\t\t: {0:d}'.format(data_size))

    if self._debug:
      print(u'')

    if path_offset > 0 and path_size > 0:
      path_size += path_offset
      maximum_path_size += path_offset

      if self._debug:
        print(u'Path data:')
        print(hexdump.Hexdump(value_data[path_offset:maximum_path_size]))

      cached_entry_object.path = value_data[path_offset:path_size].decode(
          u'utf-16-le')

      if self._debug:
        print(u'Path\t\t\t\t\t\t\t\t\t: {0:s}'.format(cached_entry_object.path))
        print(u'')

    if data_size > 0:
      data_size += data_offset

      cached_entry_object.data = value_data[data_offset:data_size]

      if self._debug:
        print(u'Data:')
        print(hexdump.Hexdump(cached_entry_object.data))

    return cached_entry_object


class WindowsAppCompatCacheCollector(collector.WindowsVolumeCollector):
  """Class that defines a Windows Application Compatibility Cache collector.

  Attributes:
    found_app_compat_cache_key: boolean value to indicate the Windows
                                Application Compatibility Cache Registry
                                key was found.
  """

  def __init__(self, debug=False):
    """Initializes the Windows known folders collector object.

    Args:
      debug: optional boolean value to indicate if debug information should
             be printed. The default is false.
    """
    super(WindowsAppCompatCacheCollector, self).__init__()
    self._debug = debug
    registry_file_reader = collector.CollectorRegistryFileReader(self)
    self._registry = registry.WinRegistry(registry_file_reader)

    self.found_app_compat_cache_key = False

  def _CollectAppCompatCacheFromKey(self, output_writer, key_path):
    """Collects Application Compatibility Cache from a Windows Registry key.

    Args:
      output_writer: the output writer object.
      key_path: the path of the Application Compatibility Cache key.
    """
    app_compat_cache_key = self._registry.GetKeyByPath(key_path)
    if not app_compat_cache_key:
      return

    self.found_app_compat_cache_key = True
    value = app_compat_cache_key.get_value_by_name(u'AppCompatCache')
    if not value:
      logging.warning(u'Missing AppCompatCache value in key: {0:s}'.format(
          key_path))
      return

    value_data = value.data
    value_data_size = len(value.data)

    # TODO: add non debug output
    # parser = AppCompatCacheDataParser(debug=self._debug)
    parser = AppCompatCacheDataParser(debug=True)

    if self._debug:
      # TODO: replace WriteText by more output specific method e.g.
      # WriteValueData.
      output_writer.WriteText(u'Value data:')
      output_writer.WriteText(hexdump.Hexdump(value_data))

    format_type = parser.CheckSignature(value_data)
    if not format_type:
      logging.warning(u'Unsupported signature.')
      return

    header_object = parser.ParseHeader(format_type, value_data)

    # On Windows Vista and 2008 when the cache is empty it will
    # only consist of the header.
    if value_data_size <= header_object.header_size:
      return

    cached_entry_offset = header_object.header_size
    cached_entry_size = parser.DetermineCacheEntrySize(
        format_type, value_data, cached_entry_offset)

    if not cached_entry_size:
      logging.warning(u'Unsupported cached entry size.')
      return

    cached_entry_index = 0
    while cached_entry_offset < value_data_size:
      cached_entry_object = parser.ParseCachedEntry(
          format_type, value_data, cached_entry_index, cached_entry_offset,
          cached_entry_size)
      cached_entry_offset += cached_entry_object.cached_entry_size
      cached_entry_index += 1

      if (header_object.number_of_cached_entries != 0 and
          cached_entry_index >= header_object.number_of_cached_entries):
        break

  def Collect(self, output_writer):
    """Collects the Application Compatibility Cache.

    Args:
      output_writer: the output writer object.
    """
    self.found_app_compat_cache_key = False

    # Windows XP
    key_path = (
        u'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Control\\Session Manager\\'
        u'AppCompatibility')
    self._CollectAppCompatCacheFromKey(output_writer, key_path)

    # Windows 2003 and later
    key_path = (
        u'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Control\\Session Manager\\'
        u'AppCompatCache')
    self._CollectAppCompatCacheFromKey(output_writer, key_path)

    # TODO: handle multiple control sets.


class StdoutWriter(object):
  """Class that defines a stdout output writer."""

  def Open(self):
    """Opens the output writer object.

    Returns:
      A boolean containing True if successful or False if not.
    """
    return True

  def Close(self):
    """Closes the output writer object."""
    pass

  def WriteText(self, text):
    """Writes text to stdout.

    Args:
      text: the text to write.
    """
    print(text)


def Main():
  """The main program function.

  Returns:
    A boolean containing True if successful or False if not.
  """
  argument_parser = argparse.ArgumentParser(description=(
      u'Extract the Application Compatibility Cache information from a SYSTEM '
      u'Registry File (REGF).'))

  argument_parser.add_argument(
      u'-d', u'--debug', dest=u'debug', action=u'store_true', default=False,
      help=u'enable debug output.')

  argument_parser.add_argument(
      u'source', nargs=u'?', action=u'store', metavar=u'PATH', default=None,
      help=(
          u'path of the volume containing C:\\Windows, the filename of '
          u'a storage media image containing the C:\\Windows directory,'
          u'or the path of a SYSTEM Registry file.'))

  options = argument_parser.parse_args()

  if not options.source:
    print(u'Source value is missing.')
    print(u'')
    argument_parser.print_help()
    print(u'')
    return False

  logging.basicConfig(
      level=logging.INFO, format=u'[%(levelname)s] %(message)s')

  output_writer = StdoutWriter()

  if not output_writer.Open():
    print(u'Unable to open output writer.')
    print(u'')
    return False

  collector_object = WindowsAppCompatCacheCollector(debug=options.debug)

  if not collector_object.GetWindowsVolumePathSpec(options.source):
    print((
        u'Unable to retrieve the volume with the Windows directory from: '
        u'{0:s}.').format(options.source))
    print(u'')
    return False

  collector_object.Collect(output_writer)
  output_writer.Close()

  if not collector_object.found_app_compat_cache_key:
    print(u'No Application Compatibility Cache key found.')

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
