"""Tests for base system types."""

from mcp_utils.base.system_types import VerbosityMode


class TestVerbosityMode:
  def test_members(self):
    assert set(VerbosityMode) == {
      VerbosityMode.COARSE,
      VerbosityMode.NORMAL,
      VerbosityMode.FINE,
      VerbosityMode.DEBUG,
    }

  def test_string_values(self):
    assert VerbosityMode.COARSE == "coarse"
    assert VerbosityMode.NORMAL == "normal"
    assert VerbosityMode.FINE == "fine"
    assert VerbosityMode.DEBUG == "debug"

  def test_str_enum(self):
    assert isinstance(VerbosityMode.COARSE, str)
