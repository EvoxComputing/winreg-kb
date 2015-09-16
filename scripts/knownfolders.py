#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import argparse
import sys

import collector
import registry


class KnownFolder(object):
  """Class that defines a known folder."""

  def __init__(self, guid, name, localized_name):
    """Initializes the known folder object.

    Args:
      guid: the identifier.
      name: the name.
      localized_name: the localized name.
    """
    super(KnownFolder, self).__init__()
    self.guid = guid
    self.localized_name = localized_name
    self.name = name


class WindowsKnownFoldersCollector(collector.WindowsVolumeCollector):
  """Class that defines a Windows known folders collector.

  Attributes:
    found_folder_descriptions_key: boolean value to indicate a Known Folder
                                   descriptions Registry key was found.
  """

  DEFAULT_VALUE_NAME = u''

  _FOLDER_DESCRIPTIONS_KEY_PATH = (
      u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\'
      u'Explorer\\FolderDescriptions')

  def __init__(self):
    """Initializes the Windows known folders collector object."""
    super(WindowsKnownFoldersCollector, self).__init__()
    registry_file_reader = collector.CollectorRegistryFileReader(self)
    self._registry = registry.WinRegistry(registry_file_reader)

    self.found_folder_descriptions_key = False

  def _GetValueAsStringFromKey(self, key, value_name, default_value=u''):
    """Retrieves a value as a string from the key.

    Args:
      key: the key object (instance of pyregf.key).
      value_name: string containing the name of the value.
      default_value: optional default value. The default is an empty string.

    Returns:
      The value as a string or the default value if not available.
    """
    if not key:
      return default_value

    value = key.get_value_by_name(value_name)
    if not value:
      return default_value

    return value.get_data_as_string()

  def Collect(self, output_writer):
    """Collects the known folders.

    Args:
      output_writer: the output writer object.
    """
    self.found_folder_descriptions_key = False

    folder_descriptions_key = self._registry.GetKeyByPath(
        self._FOLDER_DESCRIPTIONS_KEY_PATH)
    if not folder_descriptions_key:
      return

    self.found_folder_descriptions_key = True

    for sub_key in folder_descriptions_key.sub_keys:
      guid = sub_key.name.lower()
      name = self._GetValueAsStringFromKey(sub_key, u'Name')
      localized_name = self._GetValueAsStringFromKey(
          sub_key, u'LocalizedName')

      known_folder = KnownFolder(guid, name, localized_name)
      output_writer.WriteKnownFolder(known_folder)


class StdoutWriter(object):
  """Class that defines a stdout output writer."""

  def Close(self):
    """Closes the output writer object."""
    return

  def Open(self):
    """Opens the output writer object.

    Returns:
      A boolean containing True if successful or False if not.
    """
    return True

  def WriteKnownFolder(self, known_folder):
    """Writes a known folder to the output.

    Args:
      known_folder: a known folder (instance KnownFolder).
    """
    print(u'{0:s}\t{1:s}\t{2:s}'.format(
        known_folder.guid, known_folder.name, known_folder.localized_name))


def Main():
  """The main program function.

  Returns:
    A boolean containing True if successful or False if not.
  """
  argument_parser = argparse.ArgumentParser(description=(
      u'Extract the known folders from a SOFTWARE Registry File (REGF).'))

  argument_parser.add_argument(
      u'source', nargs=u'?', action=u'store', metavar=u'PATH', default=None,
      help=(
          u'path of the volume containing C:\\Windows, the filename of '
          u'a storage media image containing the C:\\Windows directory,'
          u'or the path of a SOFTWARE Registry file.'))

  options = argument_parser.parse_args()

  if not options.source:
    print(u'Source value is missing.')
    print(u'')
    argument_parser.print_help()
    print(u'')
    return False

  output_writer = StdoutWriter()

  if not output_writer.Open():
    print(u'Unable to open output writer.')
    print(u'')
    return False

  collector_object = WindowsKnownFoldersCollector()

  if not collector_object.GetWindowsVolumePathSpec(options.source):
    print((
        u'Unable to retrieve the volume with the Windows directory from: '
        u'{0:s}.').format(options.source))
    print(u'')
    return False

  collector_object.Collect(output_writer)
  output_writer.Close()

  if not collector_object.found_folder_descriptions_key:
    print(u'No folder descriptions key found.')

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
