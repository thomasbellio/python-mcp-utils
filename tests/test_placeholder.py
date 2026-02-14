"""Basic test to ensure package imports correctly."""

from mcp_utils import __version__


def test_version() -> None:
  """Test that version is defined."""
  assert __version__ is not None
  assert isinstance(__version__, str)


def test_package_import() -> None:
  """Test that package can be imported."""
  import mcp_utils

  assert mcp_utils is not None
