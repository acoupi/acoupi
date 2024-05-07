"""Message formatter for acoupi.

The MessageFormatter is reponsible to format messages that are sent by the Messengs."""

from acoupi import data
from acoupi.components import types

__all__ = []


class EachDetectionFormatter(types.MessageFormatter):
  """ A Message Formatter that formats each positive detection."""

  def format_message(data.Message) -> data.Response:
    return


class DailyDetectionFormatter(types.MessageFormatter):
  """A MessageFormater that builds daily detections summary.

  This detection formatter builds a message from the detections store in the SQLite DB. 
  The created message contain summary of detections and includes the following information:

  - name of detected species
  - number of detection for each species
  - mean probability, with min and maximum band. """

    def format_message(data.Message) -> data.Response:
      return
