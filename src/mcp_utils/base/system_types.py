"""Base system types: VerbosityMode."""

from enum import StrEnum


class VerbosityMode(StrEnum):
  """Verbosity levels for progress notifications.

  - COARSE: Only major stage changes
  - NORMAL: Stage + percentage updates (default)
  - FINE: Detailed metrics + messages
  - DEBUG: Everything including metadata
  """

  COARSE = "coarse"
  NORMAL = "normal"
  FINE = "fine"
  DEBUG = "debug"
