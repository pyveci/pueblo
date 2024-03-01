# ruff: noqa: T201
from sphinx.ext.intersphinx import fetch_inventory, inspect_main


class SphinxInventoryDecoder:
    """
    Decode and process intersphinx inventories created by Sphinx.

    https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html
    """

    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url

    def as_text(self):
        inspect_main([self.url])

    def as_markdown(self):
        class MockConfig:
            intersphinx_timeout: int | None = None
            tls_verify = False
            tls_cacerts: str | dict[str, str] | None = None
            user_agent: str = ""

        class MockApp:
            srcdir = ""
            config = MockConfig()

        app = MockApp()
        inv_data = fetch_inventory(app, "", self.url)
        print(f"# {self.name}")
        for key in sorted(inv_data or {}):
            print(f"## {key}")
            inv_entries = sorted(inv_data[key].items())
            print("```text")
            for entry, (_proj, _ver, url_path, display_name) in inv_entries:
                display_name = display_name * (display_name != "-")
                print(f"{entry: <40} {display_name: <40}: {url_path}")
            print("```")
