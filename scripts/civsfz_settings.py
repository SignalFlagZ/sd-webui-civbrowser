import gradio as gr
from modules import script_callbacks, shared, ui_components
from scripts.civsfz_color import BaseModelColors, familyColor

# SD.Next can not import from civsfz_shared.py
GR_V440 = True if "4.40" in gr.__version__ else False

def on_ui_settings():
    from scripts.civsfz_shared import platform
    from scripts.civsfz_api import APIInformation

    class myOption(shared.OptionInfo):
        def __init__(self, text, **kwargs):
            super().__init__(text, **kwargs)
            self.do_not_save = True

        def js(self, label, js_func):
            self.comment_before += (
                f"[<a onclick='{js_func}(this); return false'>{label}</a>]"
            )
            return self

    Api = APIInformation()

    civsfz_section = "Civsfz_Browser", "CivBrowser"
    # OptionInfo params
    # default=None, label="", component=None, component_args=None, onchange=None, section=None, refresh=None, comment_before='', comment_after='', infotext=None, restrict_api=False, category_id=None
    # SD.Next dose not have OptionHTML
    dict_user_management = (
        {
            "civsfz_msg_user_management": shared.OptionHTML(
                "<h3>Creator management</h3>"
                "Favourite creators and banned creators are stored in text files `<em>favoriteUsers.txt</em>` and `<em>bannedUsers.txt</em>` respectively. "
                "To register the creator, go to <em>User Management</em> on the CivBrowser tab. </br>"
                "The previous registration items in here have been discontinued. "
                "Previously registered users are re-registered every time the app is started. "
                "Therefore, it is not possible to delete previously registered users. "
                "To avoid this, edit your `<em>config.json</em>` file and remove the `<em>civsfz_favorite_creators</em>` and `<em>civsfz_ban_creators</em>` lines."
            ),
        }
        if not platform == "SD.Next"
        else {}
    )

    dict_api_info = (
        {
            "civsfz_msg_html1": shared.OptionHTML(
                "<h3>API-Key</h3>"
                "The command line option `<em>--civsfz-api-key</em>` is deprecated. "
                "We felt that this was a risk because some users might not notice the API-Key being displayed on the console. "
                "The API-Key here is saved in the `<em>config.json</em>` file.</br>"
                "If you do not know this, there is a risk of your API-Key being leaked."
            ),
        }
        if not platform == "SD.Next"
        else {}
    )

    dict_options1 = {
        "civsfz_api_key": shared.OptionInfo(
            "",
            label="API-Key",
            component=gr.Textbox,
            component_args={"type": "password"},
        ).info("Note: API-Key is stored in the `config.json` file."),
        "civsfz_request_timeout": shared.OptionInfo(
            30,
            label="Request timeout(s)",
            component=gr.Slider,
            component_args={"minimum": 10, "maximum": 90, "step": 5},
        ),
        "civsfz_browsing_level": shared.OptionInfo(
            [1],
            label="Browsing level",
            component=gr.CheckboxGroup,
            component_args={
                "choices": list(Api.nsfwLevel.items()),
            },
        ),
        "civsfz_number_of_tabs": shared.OptionInfo(
            3,
            label="Number of tabs",
            component=gr.Slider,
            component_args={"minimum": 1, "maximum": 8, "step": 1},
        ).needs_reload_ui(),
        "civsfz_number_of_cards": shared.OptionInfo(
            12,
            label="Number of cards per page",
            component=gr.Slider,
            component_args={"minimum": 8, "maximum": 48, "step": 1},
        ),
        "civsfz_card_size_width": shared.OptionInfo(
            8,
            label="Card width (unit:1em)",
            component=gr.Slider,
            component_args={"minimum": 5, "maximum": 30, "step": 1},
        ),
        "civsfz_card_size_height": shared.OptionInfo(
            12,
            label="Card height (unit:1em)",
            component=gr.Slider,
            component_args={"minimum": 5, "maximum": 30, "step": 1},
        ),
        "civsfz_hover_zoom_magnification": shared.OptionInfo(
            1.5,
            label="Zoom magnification when hovering",
            component=gr.Slider,
            component_args={"minimum": 1, "maximum": 2.4, "step": 0.1},
        ),
        "civsfz_treat_x_as_nsfw": shared.OptionInfo(
            True,
            label='If the first image is of type "X", treat the model as nsfw',
            component=gr.Checkbox,
        ),
        "civsfz_treat_slash_as_folder_separator": shared.OptionInfo(
            False,
            label=r'Treat "/" as folder separator. If you change this, some models may not be able to confirm the existence of the file.',
            component=gr.Checkbox,
        ),
        "civsfz_discard_different_hash": shared.OptionInfo(
            True,
            label="Discard downloaded model file if the hash value differs",
            component=gr.Checkbox,
        ),
        "civsfz_overwrite_metadata_file": shared.OptionInfo(
            False,
            label="Allow metadata files to be overwritten. (xxx.txt/xxx.json)",
            component=gr.Checkbox,
        ),
        "civsfz_length_of_conditions_history": shared.OptionInfo(
            5,
            label="Length of conditions history",
            component=gr.Slider,
            component_args={"minimum": 5, "maximum": 10, "step": 1},
        ),
        "civsfz_length_of_search_history": shared.OptionInfo(
            5,
            label="Length of search term history",
            component=gr.Slider,
            component_args={"minimum": 5, "maximum": 30, "step": 1},
        ),
    }

    dict_background_opacity = {
        "civsfz_background_opacity": shared.OptionInfo(
            0.75,
            label="Background opacity for model name",
            component=gr.Slider,
            component_args={"minimum": 0.0, "maximum": 1.0, "step": 0.05},
        ),
    }

    dict_shadow_color = {
        "civsfz_shadow_color_default": shared.OptionInfo(
            "#798a9f",
            label="Frame color for cards",
            component=gr.ColorPicker,
        ),
        "civsfz_shadow_color_alreadyhave": shared.OptionInfo(
            "#7fffd4",
            label="Frame color for cards you already have",
            component=gr.ColorPicker,
        ),
        "civsfz_shadow_color_alreadyhad": shared.OptionInfo(
            "#caff7f",
            label="Frame color for cards with updates",
            component=gr.ColorPicker,
        ),
    }
    dict_folder_info = (
        {
            "civsfz_msg_html2": shared.OptionHTML(
                "<h3>How to set subfolders</h3>"
                "Click <a href='https://github.com/SignalFlagZ/sd-webui-civbrowser/wiki'>here(Wiki|GitHub)</a> to learn how to specify the model folder and subfolders."
            ),
        }
        if not platform == "SD.Next"
        else {}
    )

    label = 'Save folders for Types. Set JSON Key-Value pair. The folder separator is "/" not "\\". The path is relative from models folder or absolute.'
    info = 'Example for Stability Matrix: {"Checkpoint":"Stable-diffusion/sd"}'
    placefolder = '{\n\
                "Checkpoint": "MY_SUBFOLDER",\n\
                "VAE": "",\n\
                "TextualInversion": "",\n\
                "LORA": "",\n\
                "LoCon": "",\n\
                "Hypernetwork": "",\n\
                "AestheticGradient": "",\n\
                "Controlnet": "ControlNet",\n\
                "Upscaler": "OtherModels/Upscaler",\n\
                "MotionModule": "OtherModels/MotionModule",\n\
                "Poses": "OtherModels/Poses",\n\
                "Wildcards": "OtherModels/Wildcards",\n\
                "Workflows": "OtherModels/Workflows",\n\
                "Other": "OtherModels/Other"\n\
                }'

    dict_folders = {
        "civsfz_save_type_folders": (
            shared.OptionInfo(
                "",
                label=label + " " + info,
                comment_after=None,
                component=gr.Code,
                component_args=lambda: {
                    "language": "python",
                    "interactive": True,
                    "lines": 4,
                },
            )
            if GR_V440
            else shared.OptionInfo(
                "",
                label=label,
                component=gr.Textbox,
                component_args={
                    "lines": 4,
                    "info": info,
                    "placeholder": placefolder,
                },
            )
        ),
        "civsfz_save_subfolder": shared.OptionInfo(
            "",
            label='Subfolders under type folders. Model information can be referenced by the key name enclosed in double curly brachets "{{}}". Available key names are "BASEMODELbkCmpt", "BASEMODEL", "NSFW", "USERNAME", "MODELNAME", "MODELID", "VERSIONNAME" and "VERSIONID". Folder separator is "/".',
            component=gr.Textbox,
            component_args={
                "lines": 1,
                "placeholder": "_{{BASEMODEL}}/.{{NSFW}}/{{MODELNAME}}",
            },
        ),
    }
    dict_color_figcaption = {
        "civsfz_background_color_figcaption": shared.OptionInfo(
            "#414758",
            label="Background color for model name",
            component=gr.ColorPicker,
        ),
    }

    dict_color_family = (
        {
            "civsfz_msg_html3": shared.OptionHTML(
                "<h3>What is Family?</h3>"
                "Families are groups of similar base models. "
                "You can register the base model to the family. "
                "You can set the color for each color family. "
                "Colors within a family will automatically change based on the family color. "
                "The color changes gradually according to the hls color wheel."
            ),
        }
        if not platform == "SD.Next"
        else {}
    )
    for k in familyColor.keys():
        if k not in "non_family":
            dict_color_family |= {
                "civsfz_"
                + k: shared.OptionInfo(
                    familyColor[k]["value"],
                    label=k.capitalize(),
                    component=ui_components.DropdownMulti,  # Prevent multiselect error on A1111 v1.10.0
                    component_args={
                        "choices": Api.getBasemodelOptions(),
                    },
                ),
                "civsfz_color_"
                + k: shared.OptionInfo(
                    familyColor[k]["color"],
                    label=k.capitalize() + " color",
                    component=gr.ColorPicker,
                ).js("preview", "civsfz_preview_colors"),
            }
        else:
            dict_color_family |= {
                "civsfz_color_"
                + k: shared.OptionInfo(
                    familyColor[k]["color"],
                    label="Non-family color",
                    component=gr.ColorPicker,
                ),
            }

    for key, opt in {
        **dict_user_management,
        **dict_api_info,
        **dict_options1,
        **dict_background_opacity,
        **dict_color_figcaption,
        **dict_color_family,
        **dict_shadow_color,
        **dict_folder_info,
        **dict_folders,
    }.items():
        opt.section = civsfz_section
        shared.opts.add_option(key, opt)


script_callbacks.on_ui_settings(on_ui_settings)
