VERSION = "v2.8.2"

platform = "A1111"
forge_version = None

from html.parser import HTMLParser

import gradio as gr
# GRADIO_VERSION = gr.__version__
GR_V440 = True if "4.40" in gr.__version__ else False

try:
    from modules_forge import forge_version
except ImportError:
    from modules.cmd_args import parser
    if parser.description:
        platform = "SD.Next"
    pass
else:
    platform = "Forge"
    forge_version = forge_version
# print(f'Working on {platform}')


from modules.shared import opts as opts
try:
    # SD web UI >= v1.6.0-RC
    # Forge
    from modules.shared_cmd_options import cmd_opts as cmd_opts
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
    def __init__(self, start_text:str=""):
        super().__init__()
        self.text = start_text
        self.prevEndTag=""
    def handle_starttag(self, tag, attrs):
        if tag in ["li"]:
            self.text += "  "  # indent
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
            "hr",
            "caption",
            "thread",
            "tr",
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
    def setInnerText(self, text:str=""):
        # for reset
        self.text = text
