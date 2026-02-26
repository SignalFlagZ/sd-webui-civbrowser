import gradio as gr
import itertools
import json
import math
import os
import re
from html.parser import HTMLParser
from datetime import datetime, timedelta, timezone
from modules import script_callbacks, ui_components
from colorama import Fore, Back, Style
from scripts.civsfz_shared import VERSION, GR_V440, cmd_opts, opts, read_timeout, HTML2txt
from scripts.civsfz_api import CivitaiModels
from scripts.civsfz_filemanage import (
    open_folder,
    HistoryS,
    HistoryC,
    HistoryKwd,
    FavoriteCreators,
    BanCreators,
    filename_normalization,
)
from scripts.civsfz_downloader import Downloader
from scripts.civsfz_color import dictBasemodelColors


print_ly = lambda  x: print(Fore.LIGHTYELLOW_EX + "CivBrowser: " + x + Style.RESET_ALL )
print_lc = lambda  x: print(Fore.LIGHTCYAN_EX + "CivBrowser: " + x + Style.RESET_ALL )
print_n = lambda  x: print("CivBrowser: " + x )

class Components():
    newid = itertools.count()
    downloader = None
    def __init__(self, downloader:Downloader, tab=None):
        '''id: Event ID for javascrypt'''
        from scripts.civsfz_filemanage import generate_model_save_path2, existence_check, \
            save_text_file, saveImageFiles
        Components.downloader = downloader
        self.gr_version = gr.__version__
        # print_ly(f"{self.gr_version}")
        self.tab = tab
        # Set the URL for the API endpoint
        self.Civitai = CivitaiModels()
        self.id = next(Components.newid)
        self.searchtype:list[str] = ["No"] # Remember previous search type
        contentTypes = self.Civitai.getTypeOptions()
        self.APIKey = ""
        if opts.civsfz_api_key:
            self.APIKey = opts.civsfz_api_key[0:32]
        def defaultContentType():
            value = contentTypes[self.id % len(contentTypes)]
            return value
        def defaultPeriod():
            return "Month"

        with gr.Column() as self.components:
            with gr.Row():
                with gr.Column(scale=1):
                    grChkbxGrpContentType = gr.CheckboxGroup(
                        label='Types:', choices=contentTypes, value=defaultContentType)
                with gr.Column(scale=1):
                    with gr.Row():
                        grDrpdwnSortType = gr.Dropdown(
                            label='Sort List by:', choices=self.Civitai.getSortOptions(), value="Newest", type="value")
                        with gr.Accordion(label="Sensitive", open=False):
                            grChkboxShowNsfw = gr.Checkbox(
                                label="nsfw", info="WARNING", value=False)
                    with gr.Row():
                        grDrpdwnPeriod = gr.Dropdown(label='Period', choices=self.Civitai.getPeriodOptions(
                        ), value=defaultPeriod, type="value")
                        grDrpdwnBasemodels = gr.Dropdown(label="Base Models", choices=self.Civitai.getBasemodelOptions(
                        ), value=None, type="value", multiselect=True)
                    with gr.Row():
                        grDrpdwnCHistory = gr.Dropdown(
                            elem_id=f"civsfz_conditions_history{self.id}",
                            label="Conditions History",
                            choices=HistoryC.getAsChoices(),
                            type="value",
                            tooltip="You can choose search conditions from your history",
                        )

            # with gr.Row():  # deprecated
            #    grRadioSearchType = gr.Radio(scale=2, label="Search", choices=self.Civitai.getSearchTypes(),value="No")
            #    grDropdownSearchTerm = gr.Dropdown(
            #        scale=1,
            #        label="Search Term",
            #        elem_id=f"civsfz_search_term{self.id}",
            #        choices=HistoryS.getAsChoices(),
            #        type="value",
            #        interactive=True,
            #        allow_custom_value=True,
            #        tooltip="Enter your search term or choose from your history and favorites",
            #    )
            with gr.Row():
                grChkbxgrpSearch = gr.CheckboxGroup(
                    scale=3,
                    label="Search",
                    choices=self.Civitai.getSearchTypes(),
                    value=self.searchtype,
                    interactive=True,
                    elem_id=f"civsfz_search_type{self.id}",
                    tooltip="Keyword, username and tag can be searched simultaneously",
                )
                grchkbxfav = gr.Checkbox(
                    scale=1,
                    label="Liked on Civitai",
                    value=False,
                    elem_id=f"civsfz_search_liked{self.id}",
                    tooltip="Search for models liked on civitai",
                )
            with gr.Row():
                grDrpdwnKeyword = gr.Dropdown(
                    scale=0,
                    label="Keyword",
                    choices=HistoryKwd.getAsChoices("Keyword"),
                    type="value",
                    visible=False,
                    allow_custom_value=True,
                    elem_id=f"civsfz_search_keyword{self.id}",
                    tooltip="Enter a search term or choose from your history",
                )
                grDrpdwnUserName = gr.Dropdown(
                    scale=0,
                    label="User Name",
                    choices=HistoryKwd.getAsChoices("User name"),
                    type="value",
                    visible=False,
                    allow_custom_value=True,
                    elem_id=f"civsfz_search_user{self.id}",
                    tooltip="Enter a user name or choose from your history and favorites",
                )
                grDrpdwnTag = gr.Dropdown(
                    scale=0,
                    label="Tag",
                    choices=HistoryKwd.getAsChoices("Tag"),
                    type="value",
                    visible=False,
                    allow_custom_value=True,
                    elem_id=f"civsfz_search_tag{self.id}",
                    tooltip="Enter a tag or choose from your history",
                )
                grDrpdwnID = gr.Dropdown(
                    scale=0,
                    label="ID/Hash",
                    choices=HistoryKwd.getAsChoices("ID"),
                    type="value",
                    visible=False,
                    allow_custom_value=True,
                    elem_id=f"civsfz_search_id{self.id}",
                    tooltip="Enter the number or choose from your history",
                )

            with gr.Column(elem_id=f"civsfz_model-navigation{self.id}"):
                with gr.Row(elem_id=f"civsfz_apicontrol{self.id}", elem_classes="civsfz-navigation-buttons civsfz-sticky-element"):
                    with gr.Column(scale=3):
                        grBtnGetListAPI = gr.Button(
                            value="GET cards",
                            elem_id=f"civsfz_get_cards{self.id}",
                            tooltip="Get model list and display as model cards",
                        )
                    with gr.Column(scale=2,min_width=80):
                        grBtnPrevPage = gr.Button(
                            value="PREV",
                            elem_id=f"civsfz_previous_page{self.id}",
                            tooltip="Previous page",
                            interactive=False,
                        )
                    with gr.Column(scale=2,min_width=80):
                        grBtnNextPage = gr.Button(
                            value="NEXT",
                            elem_id=f"civsfz_next_page{self.id}",
                            tooltip="Next page",
                            interactive=False,
                        )
                    with gr.Column(scale=1,min_width=80):
                        grTxtPages = gr.Textbox(label='Pages',show_label=False)
                with gr.Row():
                    grHtmlCards = gr.HTML()
                    grTxtProperties = gr.Textbox(elem_id="civsfz_css-properties", label="CSS Properties", value="", visible=False, interactive=False, lines=1)
                with gr.Row(elem_classes="civsfz-jump-page-control civsfz-sticky-element"):
                    with gr.Column(scale=3):
                        grSldrPage = gr.Slider(label="Page", minimum=1, maximum=10,value = 1, step=1, interactive=False, scale=3)
                    with gr.Column(scale=1,min_width=80):
                        grBtnGoPage = gr.Button(
                            value="JUMP",
                            elem_id=f"civsfz_jump_page{self.id}",
                            interactive=False,
                            scale=1,
                            tooltip="Jump to the specified page. Can also be used to reload.",
                        )
                    with gr.Accordion(label="Browsing Level", open=False):
                        with gr.Column(min_width=80):
                            grChkbxgrpLevel = gr.CheckboxGroup(label='Browsing Level', choices=list(self.Civitai.nsfwLevel.items()) ,value=opts.civsfz_browsing_level, interactive=True, show_label=False)

            with gr.Column(elem_id=f"civsfz_model-data{self.id}"):
                grHtmlBackToTop = gr.HTML(
                    elem_classes="civsfz-back-to-top",
                    value=f"<div onclick='civsfz_scroll_to(\"#civsfz_model-navigation{self.id}\");'><span style='font-size:200%;color:transparent;text-shadow:0 0 0 orange;cursor: pointer;pointer-events: auto;'>&#x1F51D;</span></div>",
                )  # 🔝
                with gr.Row():
                    grHtmlModelName = gr.HTML(elem_id=f"civsfz_modellist{self.id}", value=None, visible=True)
                with gr.Row(elem_classes="civsfz-save-buttons civsfz-sticky-element"):
                    with gr.Column(scale=2):
                        with gr.Row():
                            # grBtnSaveText = gr.Button(value="Save trained tags",interactive=False, min_width=80)
                            grBtnSaveImages = gr.Button(
                                value="Save model infos",
                                elem_id=f"civsfz_save_images{self.id}",
                                tooltip="Save model information. Model file is not saved.",
                                interactive=False,
                                min_width=80,
                            )
                            grBtnDownloadModel = gr.Button(
                                value="Download model",
                                elem_id=f"civsfz_downloadbutton{self.id}",
                                tooltip="Save model file",
                                interactive=False,
                                min_width=80,
                            )
                    with gr.Column(scale=1):
                        with gr.Row():
                            grTextProgress = gr.Textbox(
                                label="Download status", show_label=False
                            )
                            # deprecated grBtnCancel = gr.Button(value="Cancel",interactive=False, variant='stop', min_width=80)
                with gr.Row():
                    with gr.Accordion(
                        label="User Management",
                        open=False,
                    ):
                        with gr.Row():
                            grTxtCreator = gr.Textbox(
                                label="Creator name",
                                value="",
                                visible=True,
                            )
                            grBtnAddFavorite = ui_components.ToolButton(
                                "⭐️",
                                elem_id=f"civsfz_user_manager_favorite{self.id}",
                                interactive=False,
                                tooltip="Add creator to favorites",
                            )
                            grBtnAddBan = ui_components.ToolButton(
                                "🚷",
                                elem_id=f"civsfz_user_manager_ban{self.id}",
                                interactive=False,
                                tooltip="Add creator to ban",
                            )
                            grBtnClearUser = ui_components.ToolButton(
                                "↻",
                                elem_id=f"civsfz_user_manager_clear{self.id}",
                                interactive=False,
                                tooltip="Remove creator status",
                            )
                    grTxtJsEvent = gr.Textbox(
                        label="Event text",
                        value=None,
                        elem_id=f"civsfz_eventtext{self.id}",
                        visible=False,
                        interactive=True,
                        lines=1,
                    )
                    # txt_list = ""
                    # grTxtTrainedWords = gr.Textbox(
                    #    label="Trained Tags (if any)",
                    #    value=f"{txt_list}",
                    #    interactive=False,
                    #    lines=1,
                    #    visible=False,
                    # )
                with gr.Row():
                    grRadioVersions = gr.Radio(
                        label="Version",
                        choices=[],
                        interactive=True,
                        elem_id=f"civsfz_versionlist{self.id}",
                        value=None,
                    )
                with gr.Accordion(label="Download Settings"):
                    with gr.Row():
                        grTxtBaseModel = gr.Textbox(scale=1, label='Base Model', value='', interactive=True, lines=1, visible=False)
                        grDrpdwnSelectFile = gr.Dropdown(scale=3, label="File select", choices=[], interactive=True, value=None)
                    with gr.Row(equal_height=False):
                        # grBtnFolder = gr.Button(value="\N{Open file folder}", interactive=True, elem_classes="civsfz-small-buttons")  # 📂
                        grBtnFolder = ui_components.ToolButton(value="\N{Open file folder}",elem_id=f"civsfz_open_save_folder{self.id}", tooltip="Open save folder")  # 📂
                        grTxtSaveFolder = gr.Textbox(
                            label="Save folder",
                            elem_id=f"civsfz_save_folder{self.id}",
                            tooltip="Folder path to save the model. Editable.",
                            interactive=True,
                            value="",
                            lines=1,
                        )
                        grMrkdwnFileMessage = gr.HTML(value="<span style='color:Aquamarine;'>You have</span>", elem_classes ="civsfz-msg", visible=False)
                        grTxtSaveFilename = gr.Textbox(
                            label="Save file name",
                            elem_id=f"civsfz_save_file_name{self.id}",
                            tooltip="File name of model file to save. Editable.",
                            interactive=True,
                            value=None,
                        )
                    with gr.Row():
                        grTxtDlUrl = gr.Textbox(label="Download Url", interactive=False, value=None)
                        grTxtEarlyAccess = gr.Textbox(label='Early Access', interactive=False, value=None, visible=False)
                        grTxtHash = gr.Textbox(label="File hash", interactive=False, value="", visible=False)
                        grTxtApiKey = gr.Textbox(
                            label="API Key",
                            elem_id=f"civsfz_api_key{self.id}",
                            tooltip="Enter API key obtained from CivitAI. You can also enter it in Settings.",
                            value=lambda: self.APIKey,
                            type="password",
                            lines=1,
                        )
                    with gr.Row():
                        # grBtnCopyWords = gr.Button(value="📋", interactive=True, elem_classes="civsfz-small-buttons", visible=False)
                        grBtnCopyWords = ui_components.ToolButton(
                            value="📋",
                            interactive=True,
                            visible=False,
                            elem_id=f"civsfz_copy_triggerwords{self.id}",
                            tooltip="Copy trigger words",
                            )
                        # grBtnSendWords = gr.Button(value="📝", interactive=True, elem_classes="civsfz-small-buttons", visible=False)
                        grBtnSendWords = ui_components.ToolButton(
                            value="📝",
                            interactive=True,
                            visible=False,
                            elem_id=f"civsfz_send_triggerwords{self.id}",
                            tooltip="Send trigger words to txt2img",
                            )
                        grTxtLoraPrompt = gr.Textbox(
                            label="Prompt to activate the model",
                            elem_id=f"civsfz_lora_prompt{self.id}",
                            tooltip="A prompt to call a model configured from Trained Tags",
                            interactive=True,
                            value=None,
                            visible=False,
                        )
                with gr.Row():
                    grTxtVersionInfo = gr.Textbox(label="Version base model",value="",visible=False)
                    grHtmlModelInfo = gr.HTML(elem_id=f"civsfz_model-info{self.id}")

            # def renameTab(type):
            #    return gr.TabItem.update(label=f'{self.id}:{type}')
            # grRadioContentType.change(
            #    fn = renameTab,
            #    inputs=[
            #        grRadioContentType
            #       ],
            #    outputs=[
            #            self.tab
            #        ]
            #    )
            # def check_key_length(key):
            #    return key[0:32]
            # grTxtApiKey.change(
            #    fn=check_key_length,
            #    inputs=[grTxtApiKey],
            #    outputs=[grTxtApiKey],
            #    )

            def updateLoraPrompt(grTxtSaveFilename):
                if self.Civitai.modelIndex is None:
                    return (gr.Textbox.update(value="", visible=False),gr.Button.update(visible=False), gr.Button.update(visible=False))
                modelType = self.Civitai.getSelectedModelType()
                filename = filename_normalization(grTxtSaveFilename)
                vInfo = self.Civitai.getModelVersionInfo()
                triggerWords = vInfo.get('trainedWords')
                wildcard = ""
                if triggerWords:
                    triggerWords = vInfo['trainedWords'][0]
                    if len(vInfo['trainedWords']) > 1:
                        wildcard = f", {{ {' | '.join(vInfo['trainedWords'][1:])}}}"
                else:
                    triggerWords = ""
                triggerWords = re.sub(r"<.+?>", "", triggerWords)  # delete "<lora:xxx>"
                wildcard = re.sub(r"<.+?>", "", wildcard)
                prompt = ""
                visible = True
                if modelType in ["LORA", "LoCon", "DoRA"]:
                    prompt = f"<lora:{os.path.splitext(filename)[0]}:{opts.extra_networks_default_multiplier}> {triggerWords} {wildcard}"
                elif modelType == "TextualInversion":
                    prompt = f"{triggerWords}"
                else:
                    visible = False
                return (gr.Textbox.update(value=prompt, visible=visible),
                        gr.Button.update(visible=visible),
                        gr.Button.update(visible=visible)
                        )

            grTxtSaveFilename.change(
                fn=updateLoraPrompt,
                inputs=[grTxtSaveFilename],
                outputs=[grTxtLoraPrompt, grBtnSendWords, grBtnCopyWords],
            )

            grBtnSendWords.click(
                fn = None,
                _js=f'(x) => {{civsfz_send2txt2img(x);}}',
                inputs=[grTxtLoraPrompt],
                outputs=[],
            )
            grBtnCopyWords.click(
                fn = None,
                _js=f'(x) => {{civsfz_send2txt2img(x, send=false);}}',
                inputs=[grTxtLoraPrompt],
                outputs=[],
            )

            def updateUserManageButton(grTxtCreator):
                if grTxtCreator == "":
                    blFav = False
                    blBan = False
                    blClr = False
                else:
                    _blFav = not grTxtCreator in FavoriteCreators.getAsList()
                    _blBan = not grTxtCreator in BanCreators.getAsList() 
                    blFav = _blFav and _blBan
                    blBan = _blFav and _blBan
                    blClr = not (blFav and blBan)
                return (
                    gr.Button.update(interactive=blFav),
                    gr.Button.update(interactive=blBan),
                    gr.Button.update(interactive=blClr),
                )
            grTxtCreator.change(
                fn=updateUserManageButton,
                inputs=[grTxtCreator],
                outputs=[grBtnAddFavorite, grBtnAddBan, grBtnClearUser],
            )

            def addFavorite(grTxtCreator):
                if FavoriteCreators.add(grTxtCreator):
                    gr.Info(f"Add {grTxtCreator} to favorite")
                BanCreators.remove(grTxtCreator)
                return updateUserManageButton(grTxtCreator)

            def addBan(grTxtCreator):
                if BanCreators.add(grTxtCreator):
                    gr.Info(f"Ban {grTxtCreator}")
                FavoriteCreators.remove(grTxtCreator)
                return updateUserManageButton(grTxtCreator)
            def clearUser(grTxtCreator):
                if FavoriteCreators.remove(grTxtCreator):
                    gr.Info(f"Reset {grTxtCreator}")
                BanCreators.remove(grTxtCreator)
                return updateUserManageButton(grTxtCreator)
            def updateSearchTermChoices():
                return gr.Dropdown.update(choices=HistoryKwd.getAsChoices("User name"))

            grBtnAddFavorite.click(
                fn=addFavorite,
                inputs=[grTxtCreator],
                outputs=[grBtnAddFavorite, grBtnAddBan, grBtnClearUser],
            ).then(
                fn=updateSearchTermChoices, inputs=[], outputs=[grDrpdwnUserName]
            )
            grBtnAddBan.click(
                fn=addBan,
                inputs=[grTxtCreator],
                outputs=[grBtnAddFavorite, grBtnAddBan, grBtnClearUser],
            )
            grBtnClearUser.click(
                fn=clearUser,
                inputs=[grTxtCreator],
                outputs=[grBtnAddFavorite, grBtnAddBan, grBtnClearUser],
            ).then(fn=updateSearchTermChoices, inputs=[], outputs=[grDrpdwnUserName])

            def save_image_files(grTxtSaveFolder, grTxtSaveFilename, grTxtLoraPrompt, grHtmlModelInfo):
                modelInfo = self.Civitai.getModelVersionInfo()
                html = modelInfo["description"]
                description = ""
                parser = HTML2txt()
                parser.addText(f'Base Model:"{modelInfo["baseModel"]}"  ')
                parser.addText(f'Creator:"{modelInfo.get("creator").get("username")}"  ')
                parser.addText(f'Model ID:"{modelInfo["id"]}"  ')
                parser.addText(f'Version ID:"{modelInfo["versionId"]}"\n')
                parser.addText(f'Tags:"{ ", ".join(modelInfo["tags"])}"\n')
                parser.feed("<hr/>")
                if html is not None:
                    parser.feed(html)
                    parser.close()
                    description = parser.text
                    parser.reset()
                html = modelInfo["versionDescription"]
                if html is not None:
                    parser.addText("\nVersion description\n")
                    parser.feed(html)
                    parser.close()
                    description = parser.text
                    parser.reset()
                # description = re.sub(r"<p>", "\n", description)
                # description = re.sub(r"<.+?>", "", description)
                res1 = save_text_file(
                    grTxtSaveFolder,
                    grTxtSaveFilename,
                    grTxtLoraPrompt,
                    description,
                )
                res2 = saveImageFiles(
                    grTxtSaveFolder,
                    grTxtSaveFilename,
                    grHtmlModelInfo,
                    self.Civitai.getSelectedModelType(),
                    modelInfo,
                )
                return res1 + " / " + res2

            grBtnSaveImages.click(
                fn=save_image_files,
                inputs=[
                    grTxtSaveFolder,
                    grTxtSaveFilename,
                    grTxtLoraPrompt, # grTxtTrainedWords,
                    grHtmlModelInfo,
                ],
                outputs=[grTextProgress],
            )
            grBtnDownloadModel.click(
                fn=Components.downloader.add,
                inputs=[
                    grTxtSaveFolder,
                    grTxtSaveFilename,
                    grTxtDlUrl,
                    grTxtHash,
                    grTxtApiKey,
                    grTxtEarlyAccess
                    ],
                outputs=[grTextProgress]
                )

            # def selectSHistory(grDropdownSearchTerm):
            #    if grDropdownSearchTerm == None:
            #        return (gr.Dropdown.update(),
            #                gr.Radio.update())
            #    """
            #    m = re.match(rf'(.+){HistoryS.getDelimiter()}(.+)$', grDropdownSearchTerm)
            #    if m is None:
            #        return (gr.Dropdown.update(),
            #                gr.Radio.update())
            #    if len(m.groups()) < 2:
            #        return ( gr.Dropdown.update(),
            #            gr.Radio.update())
            #    return (gr.Dropdown.update(value=m.group(1)),
            #            gr.Radio.update(value=m.group(2)))
            #    """
            #    term = grDropdownSearchTerm.split(HistoryS.getDelimiter())
            #    if term[0] == "":
            #        return (gr.Dropdown.update(), gr.Radio.update())
            #    return (
            #        gr.Dropdown.update(value=term[0]),
            #        gr.Radio.update(value=term[1]),
            #    )
            # grDropdownSearchTerm.select(
            #    fn=selectSHistory,
            #    inputs=[grDropdownSearchTerm],
            #    outputs=[grDropdownSearchTerm,
            #            grRadioSearchType]
            # )

            def selectUserHistory(grDrpdwnUserName):
                term = grDrpdwnUserName.removeprefix('⭐️')
                return gr.CheckboxGroup.update(value=term)

            grDrpdwnUserName.select(
                fn=selectUserHistory,
                inputs=[grDrpdwnUserName],
                outputs=[grDrpdwnUserName],
            )

            def selectCHistory(grDrpdwnHistory):
                if grDrpdwnHistory:
                    conditions = grDrpdwnHistory.split(HistoryC.getDelimiter())
                    return (gr.Dropdown.update(value=conditions[0]),
                            gr.Dropdown.update(value=conditions[1]),
                            gr.Dropdown.update(value=json.loads(conditions[2])),
                            gr.Checkbox.update(value=conditions[3].lower() in 'true')
                            )
                else:
                    return (#gr.CheckboxGroup.update(),
                            gr.Dropdown.update(),
                            gr.Dropdown.update(),
                            gr.Dropdown.update(),
                            gr.Checkbox.update()
                            )
            grDrpdwnCHistory.select(fn=selectCHistory,
                                   inputs=[grDrpdwnCHistory],
                                   outputs=[#grChkbxGrpContentType,
                                            grDrpdwnSortType,
                                            grDrpdwnPeriod,
                                            grDrpdwnBasemodels,
                                            grChkboxShowNsfw]
                                   )
            def CHistoryUpdate():
                return gr.Dropdown.update(choices=HistoryC.getAsChoices())
            self.tab.select(fn=CHistoryUpdate,
                                inputs=[],
                                outputs=[grDrpdwnCHistory]
                            )
            def updatePropertiesText():
                basemodelColor = dictBasemodelColors(
                    self.Civitai.getBasemodelOptions()
                )
                escapeColor = {
                    k.replace(".", "_").replace(" ", "_"): v
                    for k, v in basemodelColor.items()
                }
                opacity = f"{int(opts.civsfz_background_opacity*255):02x}"
                propertiesText = ";".join(
                    [
                        str(opts.civsfz_background_color_figcaption) + opacity,
                        str(opts.civsfz_shadow_color_default),
                        str(opts.civsfz_shadow_color_alreadyhave),
                        str(opts.civsfz_shadow_color_alreadyhad),
                        str(opts.civsfz_hover_zoom_magnification),
                        str(opts.civsfz_card_size_width),
                        str(opts.civsfz_card_size_height),
                        json.dumps(escapeColor),
                    ]
                )
                return gr.Textbox.update(value=propertiesText)

            # https://github.com/SignalFlagZ/sd-webui-civbrowser/issues/59
            # grHtmlCards.change(
            #    fn=updatePropertiesText,
            #    inputs=[],
            #    outputs=[grTxtProperties]
            #    ).then(
            #    _js='(x) => civsfz_overwriteProperties(x)',
            #    fn = None,
            #    inputs=[grTxtProperties],
            #    outputs=[]
            #    )

            def newSearchTypeChose(grChkbxgrpSearch):
                addChoice=list((set(self.searchtype)^set(grChkbxgrpSearch))-set(self.searchtype) )
                delChoice=list((set(self.searchtype)^set(grChkbxgrpSearch))-set(grChkbxgrpSearch) )
                # print_lc(f"{addChoice=} / {delChoice=}")
                if len(addChoice) + len(delChoice) == 0:
                    return (
                        gr.CheckboxGroup.update(),
                        gr.Textbox.update(),
                        gr.Textbox.update(),
                        gr.Textbox.update(),
                        gr.Textbox.update(),
                    )
                if "No" in addChoice or len(grChkbxgrpSearch) == 0:
                    self.searchtype = ["No"]
                elif "Keyword" in addChoice:
                    self.searchtype = list(set(grChkbxgrpSearch)-set(["No", "Model ID", "Version ID", "Hash"]))
                elif "User name" in addChoice:
                    self.searchtype = list(set(grChkbxgrpSearch) - set(["No", "Model ID", "Version ID", "Hash"]))
                elif "Tag" in addChoice:
                    self.searchtype = list(set(grChkbxgrpSearch) - set(["No", "Model ID", "Version ID", "Hash"]))
                elif len(addChoice) > 0:
                    self.searchtype = addChoice
                else:
                    self.searchtype = grChkbxgrpSearch
                return (
                    gr.CheckboxGroup.update(value=self.searchtype),
                    gr.Textbox.update(visible="Keyword" in self.searchtype),
                    gr.Textbox.update(visible="User name" in self.searchtype),
                    gr.Textbox.update(visible="Tag" in self.searchtype),
                    gr.Textbox.update(
                        visible=len(
                            set(self.searchtype)
                            & set(["Model ID", "Version ID", "Hash"])
                        )
                        > 0
                    ),
                )

            grChkbxgrpSearch.input(
                fn=newSearchTypeChose,
                inputs=[grChkbxgrpSearch],
                outputs=[
                    grChkbxgrpSearch,
                    grDrpdwnKeyword,
                    grDrpdwnUserName,
                    grDrpdwnTag,
                    grDrpdwnID,
                ],
            )

            def update_model_list(
                grChkbxGrpContentType,
                grDrpdwnSortType,
                grChkbxgrpSearch,
                # grDropdownSearchTerm,
                grChkboxShowNsfw,
                grDrpdwnPeriod,
                grDrpdwnBasemodels,
                grChkbxgrpLevel: list,
                grDrpdwnKeyword,
                grDrpdwnUserName,
                grDrpdwnTag,
                grDrpdwnID,
                grchkbxfav,
            ):
                if grDrpdwnID is not None: grDrpdwnID = str.strip(grDrpdwnID) # Remove spaces
                response = None
                self.Civitai.clearRequestError()
                query = self.Civitai.makeRequestQuery(
                    grChkbxGrpContentType,
                    grDrpdwnSortType,
                    grDrpdwnPeriod,
                    grChkbxgrpSearch,
                    # grDropdownSearchTerm,
                    grDrpdwnBasemodels,
                    grChkboxShowNsfw,
                    grDrpdwnKeyword,
                    grDrpdwnUserName,
                    grDrpdwnTag,
                    grDrpdwnID,
                    grchkbxfav,
                )
                # print_lc(f"{query=}")
                if query == "":
                    gr.Warning(f'Enter a number')
                vIdAsmId = False # 
                if "Version ID" in grChkbxgrpSearch:
                    if query != "":
                        url = self.Civitai.getVersionsApiUrl(query)
                        response = self.Civitai.requestApi(url=url, timeout=read_timeout())
                        if self.Civitai.getRequestError() is None:
                            # Some key is not included in the response
                            vIdAsmId = True
                            query = str(response["modelId"])
                if "Hash" in grChkbxgrpSearch:
                    if query != "":
                        url = self.Civitai.getVersionsByHashUrl(query)
                        response = self.Civitai.requestApi(url=url, timeout=read_timeout())
                        if self.Civitai.getRequestError() is None:
                            # Some key is not included in the response
                            vIdAsmId = True
                            query = str(response["modelId"])
                if "Model ID" in grChkbxgrpSearch or vIdAsmId:
                    if query != "":
                        url = self.Civitai.getModelsApiUrl(query)
                        response = self.Civitai.requestApi(url=url, timeout=read_timeout())
                        response = {
                            'requestUrl': response['requestUrl'],
                            "items":[response],
                            'metadata': {
                                'currentPage': "1",
                                'pageSize': "1",
                                }
                            } if self.Civitai.getRequestError() is None else None
                else:
                    response = self.Civitai.requestApi(query=query, timeout=read_timeout())
                err = self.Civitai.getRequestError()
                if err is not None:
                    gr.Warning(str(err))
                if response is None:
                    return (
                        gr.HTML.update(value=None),
                        gr.Radio.update(choices=[], value=None),
                        gr.HTML.update(value=None),
                        gr.Button.update(interactive=False),
                        gr.Button.update(interactive=False),
                        gr.Button.update(interactive=False),
                        gr.Slider.update(interactive=False),
                        gr.Textbox.update(value=None),
                        gr.Dropdown.update(),
                        gr.Textbox.update(),
                        gr.Dropdown.update(),
                        gr.Dropdown.update(),
                        gr.Dropdown.update(),
                        gr.Dropdown.update(),
                    )  # HistoryS.add(grRadioSearchType, grDropdownSearchTerm)
                if "Keyword" in grChkbxgrpSearch:
                    HistoryKwd.add("Keyword", grDrpdwnKeyword)
                if "User name" in grChkbxgrpSearch:
                    HistoryKwd.add("User name", grDrpdwnUserName)
                if "Tag" in grChkbxgrpSearch:
                    HistoryKwd.add("Tag", grDrpdwnTag)
                if "Model ID" in grChkbxgrpSearch:
                    HistoryKwd.add("ID", grDrpdwnID)
                if "Version ID" in grChkbxgrpSearch:
                    HistoryKwd.add("ID", grDrpdwnID)
                if "Hash" in grChkbxgrpSearch:
                    HistoryKwd.add("ID", grDrpdwnID)

                HistoryC.add(
                    grDrpdwnSortType,
                    grDrpdwnPeriod,
                    grDrpdwnBasemodels,
                    grChkboxShowNsfw,
                )
                self.Civitai.updateJsonData(response) #, grRadioContentType)
                if err is None:
                    self.Civitai.addFirstPage(response, grChkbxGrpContentType, grDrpdwnSortType, grChkbxgrpSearch,
                                              "search", grChkboxShowNsfw, grDrpdwnPeriod, grDrpdwnBasemodels)
                self.Civitai.setShowNsfw(grChkboxShowNsfw)
                grTxtPages = self.Civitai.getPages()
                hasPrev = not self.Civitai.prevPage() is None
                hasNext = not self.Civitai.nextPage() is None
                enableJump = hasPrev or hasNext
                # model_names = self.Civitai.getModelNames() if (grChkboxShowNsfw) else self.Civitai.getModelNamesSfw()
                # HTML = self.Civitai.modelCardsHtml(model_names, self.id)
                models = self.Civitai.getModels(grChkboxShowNsfw)
                HTML = self.Civitai.modelCardsHtml(models, jsID=self.id, nsfwLevel=sum(grChkbxgrpLevel))
                return (
                    gr.HTML.update(value=""),
                    gr.Radio.update(choices=[], value=None),
                    gr.HTML.update(value=HTML),
                    gr.Button.update(interactive=hasPrev),
                    gr.Button.update(interactive=hasNext),
                    gr.Button.update(interactive=enableJump),
                    gr.Slider.update(
                        interactive=enableJump,
                        value=int(self.Civitai.getCurrentPage()),
                        maximum=int(self.Civitai.getTotalPages()),
                    ),
                    gr.Textbox.update(value=grTxtPages),
                    gr.Dropdown.update(
                        choices=HistoryC.getAsChoices(),
                        value=HistoryC.getAsChoices()[0],
                    ),
                    gr.Textbox.update(value=""),
                    gr.Dropdown.update(choices=HistoryKwd.getAsChoices("Keyword")),
                    gr.Dropdown.update(choices=HistoryKwd.getAsChoices("User name")),
                    gr.Dropdown.update(choices=HistoryKwd.getAsChoices("Tag")),
                    gr.Dropdown.update(choices=HistoryKwd.getAsChoices("ID")),
                )

            def preload_nextpage():
                import threading
                hasNext = not self.Civitai.nextPage() is None
                if hasNext:
                    url = self.Civitai.nextPage()
                    thread = threading.Thread(target=self.Civitai.requestApi, args=(url,), kwargs= {"timeout": read_timeout()}) 
                    thread.start()

            grBtnGetListAPI.click(
                fn=update_model_list,
                inputs=[
                    grChkbxGrpContentType,
                    grDrpdwnSortType,
                    grChkbxgrpSearch,
                    # grDropdownSearchTerm,
                    grChkboxShowNsfw,
                    grDrpdwnPeriod,
                    grDrpdwnBasemodels,
                    grChkbxgrpLevel,
                    grDrpdwnKeyword,
                    grDrpdwnUserName,
                    grDrpdwnTag,
                    grDrpdwnID,
                    grchkbxfav,
                ],
                outputs=[
                    grHtmlModelName,
                    grRadioVersions,
                    grHtmlCards,
                    grBtnPrevPage,
                    grBtnNextPage,
                    grBtnGoPage,
                    grSldrPage,
                    grTxtPages,
                    # grDropdownSearchTerm,
                    grDrpdwnCHistory,
                    grTxtCreator,
                    grDrpdwnKeyword,
                    grDrpdwnUserName,
                    grDrpdwnTag,
                    grDrpdwnID,
                ],
            ).then(  # for custum settings
                fn=updatePropertiesText, inputs=[], outputs=[grTxtProperties]
            ).then(
                fn=preload_nextpage,
                inputs=[],
                outputs=[],
            ).then(
                _js=f'() => {{civsfz_scroll_to("#civsfz_model-navigation{self.id}");}}',
                fn=None,
                inputs=[],
                outputs=[],
            )

            # for custum settings
            grTxtProperties.change(
                _js='(x) => civsfz_overwriteProperties(x)',
                fn = None,
                inputs=[grTxtProperties],
                outputs=[]
            )

            def  update_model_info(model_version=None, grChkbxgrpLevel=[0]):
                if model_version is not None and self.Civitai.selectVersionByIndex(model_version) is not None:
                    path = generate_model_save_path2(self.Civitai.getSelectedModelType(),
                                                self.Civitai.getSelectedModelName(),
                                                self.Civitai.getSelectedVersionBaseModel(),
                                                self.Civitai.treatAsNsfw(), #isNsfwModel()
                                                self.Civitai.getUserName(),
                                                self.Civitai.getModelID(),
                                                self.Civitai.getVersionID(),
                                                self.Civitai.getSelectedVersionName()
                                            )
                    modelInfo = self.Civitai.makeModelInfo2(nsfwLevel=sum(grChkbxgrpLevel))
                    txtEarlyAccess = self.Civitai.getSelectedVersionEarlyAccessDeadline()
                    if modelInfo["modelVersions"][0]["files"] == []:
                        drpdwn =  gr.Dropdown.update(choices=[], value="")
                        grTxtSaveFilename = gr.Textbox.update(value="")
                        grHtmlModelName = gr.HTML.update(value="")
                    else:
                        filename = modelInfo["modelVersions"][0]["files"][0]["name"]
                        for f in modelInfo["modelVersions"][0]["files"]:
                            if 'primary' in f:
                                if f['primary']:
                                    filename = f["name"]
                                    break
                        drpdwn = gr.Dropdown.update(
                            choices=[
                                f["name"]
                                for f in modelInfo["modelVersions"][0]["files"]
                            ],
                            value=filename,
                        )
                        grTxtSaveFilename = gr.Textbox.update(value=filename)
                        grHtmlModelName = gr.HTML.update(
                            value=self.Civitai.modelNameTitleHtml(
                                self.Civitai.getSelectedModelName(),
                                self.Civitai.getSelectedVersionName(),
                                self.Civitai.getSelectedVersionBaseModel(),
                                self.Civitai.getUserName(),
                                txtEarlyAccess,
                            ),
                        )

                    return (
                        gr.HTML.update(value=modelInfo["html"]),
                        #gr.Textbox.update(value=", ".join(modelInfo["trainedWords"])),
                        drpdwn,
                        gr.Textbox.update(value=modelInfo["baseModel"]),
                        gr.Textbox.update(value=str(path)),
                        gr.Textbox.update(value=txtEarlyAccess),
                        grTxtSaveFilename,
                        grHtmlModelName,
                        gr.Textbox.update(value=self.Civitai.getUserName()),
                    )
                else:
                    return (
                        gr.HTML.update(value=None),
                        #gr.Textbox.update(value=None),
                        gr.Dropdown.update(choices=[], value=None),
                        gr.Textbox.update(value=None),
                        gr.Textbox.update(value=None),
                        gr.Textbox.update(value=None),
                        gr.Textbox.update(value=None),
                        gr.HTML.update(value=None),
                        gr.Textbox.update(value=None),
                    )
            grRadioVersions.change(
                fn=update_model_info,
                inputs=[grRadioVersions, grChkbxgrpLevel],
                outputs=[
                    grHtmlModelInfo,
                    #grTxtTrainedWords,
                    grDrpdwnSelectFile,
                    grTxtBaseModel,
                    grTxtSaveFolder,
                    grTxtEarlyAccess,
                    grTxtSaveFilename,
                    grHtmlModelName,
                ],
            )

            def save_folder_changed(folder, filename):
                self.Civitai.setSaveFolder(folder)
                isExist = None
                if filename is not None:
                    isExist = file_exist_check(folder, filename)
                return gr.HTML.update(visible = True if isExist else False)
            grTxtSaveFolder.blur(
                fn=save_folder_changed,
                inputs={grTxtSaveFolder,grDrpdwnSelectFile},
                outputs=[grMrkdwnFileMessage])

            grTxtSaveFolder.change(
                fn=self.Civitai.setSaveFolder,
                inputs={grTxtSaveFolder},
                outputs=[])

            def updateDlUrl(grDrpdwnSelectFile):
                return (
                    gr.Textbox.update(
                        value=self.Civitai.getUrlByName(grDrpdwnSelectFile)
                    ),
                    gr.Textbox.update(
                        value=self.Civitai.getHashByName(grDrpdwnSelectFile)
                    ),
                    gr.Button.update(interactive=True if grDrpdwnSelectFile else False),
                    gr.Button.update(interactive=True if grDrpdwnSelectFile else False),
                    gr.Textbox.update(value=""),
                    gr.Textbox.update(value=grDrpdwnSelectFile),
                )

            def checkEarlyAccess(grTxtEarlyAccess):
                return gr.Textbox.update(value="" if grTxtEarlyAccess == "" else "Early Access")
                msg = ""
                if grTxtEarlyAccess != "":
                    dtPub = self.Civitai.getPublishedDatetime()
                    dtNow = datetime.now(timezone.utc)
                    # dtEndat = dtPub + timedelta(days=int(grTxtEarlyAccess))
                    dtEndat = self.Civitai.getEarlyAccessDeadlineDatetime()
                    tdDiff = dtNow - dtEndat
                    # print_lc(f'{tdDiff=}')
                    if tdDiff / timedelta(days=1) >= 0:
                        msg = f"Early Access: expired" # {dtDiff.days}/{grTxtEarlyAccess}
                    elif tdDiff / timedelta(hours=1) >= -1:
                        msg = f"Early Access: {math.ceil(abs(tdDiff / timedelta(minutes=1)))} minutes left"
                    elif tdDiff / timedelta(hours=1) >= -24:
                        msg = f"Early Access: {math.ceil(abs(tdDiff / timedelta(hours=1)))} hours left"
                    else:
                        msg = f"Early Access: {math.ceil(abs(tdDiff / timedelta(days=1)))} days left"
                return gr.Textbox.update(value="" if grTxtEarlyAccess == "" else f"{msg} ")

            grDrpdwnSelectFile.change(
                fn=updateDlUrl,
                inputs=[grDrpdwnSelectFile],
                outputs=[
                    grTxtDlUrl,
                    grTxtHash,
                    # grBtnSaveText,
                    grBtnSaveImages,
                    grBtnDownloadModel,
                    grTextProgress,
                    grTxtSaveFilename,
                ],
            ).then(
                fn=checkEarlyAccess, inputs=[grTxtEarlyAccess], outputs=[grTextProgress]
            )

            def file_exist_check(grTxtSaveFolder, grDrpdwnSelectFile):
                isExist = existence_check(grTxtSaveFolder, grDrpdwnSelectFile)            
                return gr.HTML.update(visible = True if isExist else False)
            grTxtDlUrl.change(
                fn=file_exist_check,
                inputs=[grTxtSaveFolder,
                        grDrpdwnSelectFile
                        ],
                outputs=[
                        grMrkdwnFileMessage
                        ]
                )

            def update_next_page(grChkboxShowNsfw, grChkbxgrpLevel, isNext=True):
                url = self.Civitai.nextPage() if isNext else self.Civitai.prevPage()
                response = self.Civitai.requestApi(url, timeout=read_timeout())
                err = self.Civitai.getRequestError()
                if err is not None:
                    gr.Warning(str(err))
                if response is None:
                    return None, None,  gr.HTML.update(),None,None,gr.Slider.update(),gr.Textbox.update()
                self.Civitai.updateJsonData(response)
                if err is None:
                    self.Civitai.addNextPage(
                        response) if isNext else self.Civitai.backPage(response)
                self.Civitai.setShowNsfw(grChkboxShowNsfw)
                grTxtPages = self.Civitai.getPages()
                hasPrev = not self.Civitai.prevPage() is None
                hasNext = not self.Civitai.nextPage() is None
                # model_names = self.Civitai.getModelNames() if (grChkboxShowNsfw) else self.Civitai.getModelNamesSfw()
                # HTML = self.Civitai.modelCardsHtml(model_names, self.id)
                models = self.Civitai.getModels(grChkboxShowNsfw)
                HTML = self.Civitai.modelCardsHtml(models, self.id, nsfwLevel=sum(grChkbxgrpLevel))
                return  gr.HTML.update(value=None),\
                        gr.Radio.update(choices=[], value=None),\
                        gr.HTML.update(value=HTML),\
                        gr.Button.update(interactive=hasPrev),\
                        gr.Button.update(interactive=hasNext),\
                        gr.Slider.update(value=self.Civitai.getCurrentPage(), maximum=self.Civitai.getTotalPages()),\
                        gr.Textbox.update(value=grTxtPages),\
                        gr.Textbox.update(value="")

            grBtnNextPage.click(
                fn=update_next_page,
                inputs=[grChkboxShowNsfw, grChkbxgrpLevel],
                outputs=[
                    grHtmlModelName,
                    grRadioVersions,
                    grHtmlCards,
                    grBtnPrevPage,
                    grBtnNextPage,
                    grSldrPage,
                    grTxtPages,
                    grTxtCreator,
                    # grTxtSaveFolder
                ],
            ).then(
                fn=preload_nextpage,
                inputs=[],
                outputs=[],
            )
            def update_prev_page(grChkboxShowNsfw, grChkbxgrpLevel):
                return update_next_page(grChkboxShowNsfw, grChkbxgrpLevel, isNext=False)
            grBtnPrevPage.click(
                fn=update_prev_page,
                inputs=[grChkboxShowNsfw, grChkbxgrpLevel],
                outputs=[
                    grHtmlModelName,
                    grRadioVersions,
                    grHtmlCards,
                    grBtnPrevPage,
                    grBtnNextPage,
                    grSldrPage,
                    grTxtPages,
                    grTxtCreator,
                    # grTxtSaveFolder
                ],
            )

            def jump_to_page(grChkboxShowNsfw, grSldrPage, grChkbxgrpLevel):
                # url = self.Civitai.nextPage()
                # if url is None:
                #    url = self.Civitai.prevPage()
                # addQuery =  {'page': grSldrPage }
                # newURL = self.Civitai.updateQuery(url, addQuery)
                newURL = self.Civitai.getJumpUrl(grSldrPage)
                if newURL is None:
                    return None, None,  gr.HTML.update(), None, None, gr.Slider.update(), gr.Textbox.update()
                # print(f'{newURL}')
                response = self.Civitai.requestApi(newURL, timeout=read_timeout())
                err = self.Civitai.getRequestError()
                if err is not None:
                    gr.Warning(str(err))
                if response is None:
                    return None, None,  gr.HTML.update(),None,None,gr.Slider.update(),gr.Textbox.update()
                self.Civitai.updateJsonData(response)
                if err is None:
                    self.Civitai.pageJump(response,grSldrPage)
                self.Civitai.setShowNsfw(grChkboxShowNsfw)
                grTxtPages = self.Civitai.getPages()
                hasPrev = not self.Civitai.prevPage() is None
                hasNext = not self.Civitai.nextPage() is None
                # model_names = self.Civitai.getModelNames() if (grChkboxShowNsfw) else self.Civitai.getModelNamesSfw()
                # HTML = self.Civitai.modelCardsHtml(model_names, self.id)
                models = self.Civitai.getModels(grChkboxShowNsfw)
                HTML = self.Civitai.modelCardsHtml(models, jsID=self.id, nsfwLevel=sum(grChkbxgrpLevel))
                return (
                    gr.HTML.update(value=None),
                    gr.Radio.update(choices=[], value=None),
                    gr.HTML.update(value=HTML),
                    gr.Button.update(interactive=hasPrev),
                    gr.Button.update(interactive=hasNext),
                    gr.Slider.update(value=self.Civitai.getCurrentPage()),
                    gr.Textbox.update(value=grTxtPages),
                    gr.Textbox.update(value=""),
                )
            grBtnGoPage.click(
                fn=jump_to_page,
                inputs=[grChkboxShowNsfw, grSldrPage, grChkbxgrpLevel],
                outputs=[
                    grHtmlModelName,
                    grRadioVersions,
                    grHtmlCards,
                    grBtnPrevPage,
                    grBtnNextPage,
                    grSldrPage,
                    grTxtPages,
                    grTxtCreator,
                ],
            )

            def updateVersionsByModelID(model_ID=None):
                if model_ID is not None:
                    self.Civitai.selectModelByID(model_ID)
                    if self.Civitai.getSelectedModelIndex() is not None:
                        list = self.Civitai.getModelVersionsList()
                        self.Civitai.selectVersionByIndex(0)
                        # print(Fore.LIGHTYELLOW_EX + f'{dict=}' + Style.RESET_ALL)
                    # return gr.Dropdown.update(choices=[k for k, v in dict.items()], value=f'{next(iter(dict.keys()), None)}')
                    return gr.Radio.update(choices=list, value=0)
                else:
                    return gr.Radio.update(choices=[],value = None)
            def eventTextUpdated(grTxtJsEvent, grChkbxgrpLevel):
                if grTxtJsEvent is not None:
                    grTxtJsEvent = grTxtJsEvent.split(':')
                    # print(Fore.LIGHTYELLOW_EX + f'{grTxtJsEvent=}' + Style.RESET_ALL)
                    if grTxtJsEvent[0].startswith('Index'):
                        index = int(grTxtJsEvent[1]) # str: 'Index:{index}:{id}'
                        self.Civitai.selectModelByIndex(index)
                        grRadioVersions = updateVersionsByModelID(self.Civitai.getSelectedModelID())
                        (
                            grHtmlModelInfo,
                            #grTxtTrainedWords,
                            grDrpdwnSelectFile,
                            grTxtBaseModel,
                            grTxtSaveFolder,
                            grTxtEarlyAccess,
                            grTxtSaveFilename,
                            grHtmlModelName,
                            grTxtCreator,
                        ) = update_model_info(grRadioVersions["value"], grChkbxgrpLevel)
                        # grTxtDlUrl = gr.Textbox.update(value=self.Civitai.getUrlByName(grDrpdwnSelectFile['value']))
                        grTxtHash = gr.Textbox.update(value=self.Civitai.getHashByName(grDrpdwnSelectFile['value']))
                        grTxtVersionInfo = gr.Textbox.update(
                            value=json.dumps(self.Civitai.modelVersionsInfo())
                        )
                        return (
                            grHtmlModelName,
                            grRadioVersions,
                            grHtmlModelInfo,
                            grTxtEarlyAccess,
                            grTxtHash,
                            #grTxtTrainedWords,
                            grDrpdwnSelectFile,
                            grTxtBaseModel,
                            grTxtSaveFolder,
                            grTxtSaveFilename,
                            grTxtCreator,
                            grTxtVersionInfo,
                        )
                    else:
                        return (
                            gr.HTML.update(value=None),
                            gr.Radio.update(value=None),
                            gr.HTML.update(value=None),
                            gr.Textbox.update(value=None),
                            gr.Textbox.update(value=""),
                            #gr.Textbox.update(value=None),
                            gr.Dropdown.update(value=None),
                            gr.Textbox.update(value=None),
                            gr.Textbox.update(value=None),
                            gr.Textbox.update(value=None),
                            gr.Textbox.update(value=None),
                            gr.Textbox.update(value=None),
                        )
                else:
                    return (
                        gr.HTML.update(value=None),
                        gr.Radio.update(value=None),
                        gr.HTML.update(value=None),
                        gr.Textbox.update(value=None),
                        gr.Textbox.update(value=""),
                        #gr.Textbox.update(value=None),
                        gr.Dropdown.update(value=None),
                        gr.Textbox.update(value=None),
                        gr.Textbox.update(value=None),
                        gr.Textbox.update(value=None),
                        gr.Textbox.update(value=None),
                        gr.Textbox.update(value=None),
                    )

            grTxtJsEvent.change(
                fn=eventTextUpdated,
                inputs=[grTxtJsEvent, grChkbxgrpLevel],
                outputs=[
                    grHtmlModelName,
                    grRadioVersions,
                    grHtmlModelInfo,
                    grTxtEarlyAccess,
                    grTxtHash,
                    #grTxtTrainedWords,
                    grDrpdwnSelectFile,
                    grTxtBaseModel,
                    grTxtSaveFolder,
                    grTxtSaveFilename,
                    grTxtCreator,
                    grTxtVersionInfo,
                ],
            ).then(
                _js=f'(x) => {{civsfz_scroll_and_color("#civsfz_model-data{self.id}", "#civsfz_versionlist{self.id}", x);}}',
                fn=None,
                inputs=[grTxtVersionInfo],
                outputs=[],
            )

            grBtnFolder.click(fn=open_folder, inputs=[grTxtSaveFolder], outputs=[])

    def getComponents(self):
        return self.components

def on_ui_tabs():
    ver = VERSION
    tabNames = []
    downloader = Downloader()
    for i in range(1, opts.civsfz_number_of_tabs + 1):
        tabNames.append(f'Browser{i}')
    with gr.Blocks() as civitai_interface:
        with gr.Accordion(label="Update information", open=False):
            gr.HTML(
                value=(
                    "<h3>Changes " + "in v2.10" + "</h3>"
                    "<ul>"
                    "<li>Move the download status to an independent tab.</li>"
                    "</ul>"
                    "<div>For more information, please click <a href='https://github.com/SignalFlagZ/sd-webui-civbrowser'>here(CivBrowser|GitHub)]'</a></div>"
                )
            )
        with gr.Tabs(elem_id='civsfz_tab-element', elem_classes="civsfz-custom-property"):
            for i,name in enumerate(tabNames):
                with gr.Tab(label=name, id=f"tab{i}", elem_id=f"civsfz_tab{i}") as tab:
                    Components(downloader, tab)  # (tab)
            with gr.Tab(
                label="Download Status",
                id=f"Download Status",
                elem_id=f"Download Status",
            ):
                gr.HTML(value=f'<h2>Download queue</h2>')
                if GR_V440:
                    grHtmlDlQueue = downloader.uiDlList(gr)
                    # Use the Timer component because there are problems with `every` on HTML component.
                    grTimer = gr.Timer(value=1.5)
                    grTimer.tick(
                        fn=lambda: gr.HTML.update(value=downloader.dlHtml()),
                        inputs=[],
                        outputs=[grHtmlDlQueue],
                    )
                else:
                    grHtmlDlQueue = downloader.uiDlList(gr, every=1.0)
        with gr.Row():
            gr.HTML(value=f'<div style="text-align:center;">CivBrowser {ver}</div>')
            downloader.uiJsEvent(gr)
    return [(civitai_interface, "CivBrowser", "civsfz_interface")]

script_callbacks.on_ui_tabs(on_ui_tabs)
