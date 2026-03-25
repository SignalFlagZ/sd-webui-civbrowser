VERSION = "v2.12.4"

platform = "A1111"
forge_version = None
card_no_preview = "./file=html/card-no-preview.png"  # Neo uses jpg

from html.parser import HTMLParser

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
