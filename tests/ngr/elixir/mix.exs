defmodule NgrTestElixir.MixProject do
  use Mix.Project

  def project do
    [
      app: :ngr_test_elixir,
      version: "0.0.1",
      elixir: "~> 1.0",
      deps: deps(),
    ]
  end

  def application() do
    []
  end

  defp deps() do
    [
      {:certifi, "~> 2.0"},
    ]
  end

end
