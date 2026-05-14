VERSION = "v2.15.3"

platform = "A1111"
forge_version = None
card_no_preview = "./file=html/card-no-preview.png"  # Neo uses jpg

from html.parser import HTMLParser
from urllib.parse import urlparse, urlunparse
from requests.auth import HTTPProxyAuth
import gradio as gr
# GRADIO_VERSION = gr.__version__
# Forge Neo uses 4.39.0
GR_V440 = True if gr.__version__.startswith(("4.40", "4.39")) else False

try:
    from modules_forge.forge_version import version as forge_version
except ImportError:
    from modules.cmd_args import parser
    if parser.description:
        platform = "SD.Next"
    pass
else:
    if forge_version in ["classic", "neo"]:
        platform = "Forge Classic"
        card_no_preview = "./file=html/card-no-preview.jpg"
    else:
        platform = "Forge"
# print(f"Working on {platform=} {forge_version=}")

from modules.shared import opts as opts
try:
    # SD web UI >= v1.6.0-RC
    # Forge
    # Forge Classic/neo
    from modules.shared_cmd_options import cmd_opts as cmd_opts
    if forge_version in ["classic", "neo"]:
        from modules.sd_models import model_path
        if getattr(cmd_opts, "ckpt_dir", None) is None:
            setattr(cmd_opts, "ckpt_dir", model_path)
        import os
        from modules import paths
        if getattr(cmd_opts, "hypernetwork_dir", None) is None:
            setattr(
                cmd_opts,
                "hypernetwork_dir",
                os.path.abspath(os.path.join(paths.models_path, "hypernetworks")),
            )
        if getattr(cmd_opts, "vae_dir", None) is None:
            setattr(
                cmd_opts,
                "vae_dir",
                os.path.abspath(os.path.join(paths.models_path, "VAE")),
            )
        #print(f"{cmd_opts=}")
except ImportError:
    # SD web UI < v1.6.0-RC
    # SD.Next
    from modules.shared import cmd_opts as cmd_opts

try:
    from modules.hashes import calculate_sha256_real as calculate_sha256
except ImportError:
    from modules.hashes import calculate_sha256 as calculate_sha256

# Proxy
def get_proxies() -> tuple[dict, HTTPProxyAuth]:
    proxies = None
    proxy_auth = None
    uname = None
    upassword = None
    if getattr(opts, "civsfz_proxy", None) is not None:
        if opts.civsfz_proxy:
            try:
                parsed = urlparse(opts.civsfz_proxy)
            except ValueError:
                # Invalid URL
                # print(f"CivBrowser: Proxy URL is invalid. '{opts.civsfz_proxy}'")
                print(f"CivBrowser: Proxy URL is invalid.")
            else:
                netloc = parsed.netloc
                new_netloc = netloc
                if '@' in netloc:
                    # Get user_name and password
                    auth, host = netloc.split('@', 1)
                    new_netloc = f"{host}"
                    if ':' in auth:
                        uname, upassword = auth.split(':', 1)
                    else:
                        uname = auth
                # remove auth
                parsed_list = [
                    parsed.scheme,
                    new_netloc,
                    parsed.path,
                    parsed.params,
                    parsed.query,
                    parsed.fragment
                ]
                url = urlunparse(parsed_list)
                # print(f"Proxy {url=}")
                proxies = {
                    "http": url,
                    "https": url,
                }
                proxy_auth = HTTPProxyAuth(uname, upassword)
    # print(f"CivBrowser: The proxy URL is '{opts.civsfz_proxy}'")
    return proxies, proxy_auth

def read_timeout():
    return 15, getattr(opts, "civsfz_request_timeout", 30)

class HTML2txt(HTMLParser):
    text = ""
    prevEndTag = ""

    def __init__(self, start_text: str = ""):
        super().__init__()
        self.text = start_text
        self.prevEndTag = ""

    def handle_starttag(self, tag, attrs):
        if tag in ["li"]:
            self.text += "  - "  # indent
        elif tag in ["hr"]:
            self.text += "----------\n"
        self.prevEndTag = ""

    def handle_endtag(self, tag):
        if tag in [
            "p",
            "br",
            "title",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "ul",
            "ol",
            "dl",
            "dir",
            "menu",
            "table",
            "li",
            "caption",
            "thread",
            "tr",
            "pre",
        ]:
            if self.prevEndTag in ["p"] and tag in ["li"]:
                pass
            else:
                self.text += "\n"
        else:
            self.text += " "
        self.prevEndTag = tag

    def handle_data(self, data):
        self.text += data

    def addText(self, addedText=""):
        self.text += addedText

    def setInnerText(self, text: str = ""):
        # for reset
        self.text = text
