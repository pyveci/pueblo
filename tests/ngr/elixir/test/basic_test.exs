# https://hexdocs.pm/ex_unit/ExUnit.html

defmodule AssertionTest do
  use ExUnit.Case, async: true
  test "the truth" do
    assert 42 == 42
  end
end
