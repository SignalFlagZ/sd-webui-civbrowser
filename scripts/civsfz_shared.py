VERSION = "v2.6.8"

platform = "A1111"
forge_version = None

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
