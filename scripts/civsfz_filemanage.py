import os
import requests
import urllib.parse
import shutil
import json
import re
from pathlib import Path
import platform
import subprocess as sp
from collections import deque
from modules import  sd_models
from colorama import Fore, Back, Style
from scripts.civsfz_shared import cmd_opts, opts, read_timeout
from modules import shared
from modules.paths import models_path
try:
    from send2trash import send2trash
    send2trash_installed = True
except ImportError:
    print("Recycle bin cannot be used.")
    send2trash_installed = False

print_ly = lambda  x: print(Fore.LIGHTYELLOW_EX + "CivBrowser: " + x + Style.RESET_ALL )
print_lc = lambda  x: print(Fore.LIGHTCYAN_EX + "CivBrowser: " + x + Style.RESET_ALL )
print_n = lambda  x: print("CivBrowser: " + x )

isDownloading = False
ckpt_dir = shared.cmd_opts.ckpt_dir or sd_models.model_path
pre_opt_folder = None

def extensionFolder() -> Path:
    return Path(__file__).parent

def name_len(s:str):
        #return len(s.encode('utf-16'))
        return len(s.encode('utf-8'))
def cut_name(s:str):
    MAX_FILENAME_LENGTH = 246
    l = name_len(s)
    #print_lc(f'filename length:{len(s.encode("utf-8"))}-{len(s.encode("utf-16"))}')
    while l >= MAX_FILENAME_LENGTH: 
        s = s[:-1]
        l = name_len(s)
    return s


def escaped_filename(model_name):
    escapechars = str.maketrans({   " ": r"_",
                                    "(": r"",
                                    ")": r"",
                                    "|": r"",
                                    ":": r"",
                                    ",": r"_",
                                    "<": r"",
                                    ">": r"",
                                    "!": r"",
                                    "?": r"",
                                    ".": r"_",
                                    "&": r"_and_",
                                    "*": r"_",
                                    "\"": r"",
                                    "\\": r"",
                                    "\t":r"_",
                                    "/": r"/" if opts.civsfz_treat_slash_as_folder_separator else r"_"
                                })
    new_name = model_name.translate(escapechars)
    new_name = re.sub('_+', '_', new_name)
    new_name = cut_name(new_name)
    return new_name


def type_path(type: str) -> Path:
    global pre_opt_folder, ckpt_dir
    if opts.civsfz_save_type_folders != "":
        try:
            folderSetting = json.loads(opts.civsfz_save_type_folders)
        except json.JSONDecodeError as e:
            if pre_opt_folder != opts.civsfz_save_type_folders:
                print_ly(f'Check subfolder setting: {e}')
            folderSetting = {}
    else:
        folderSetting = {}       
    pre_opt_folder = opts.civsfz_save_type_folders
    base = models_path
    if type == "Checkpoint":
        default = ckpt_dir
        # folder = ckpt_dir
        folder = os.path.relpath(default, base)  # os.path.join(models_path, "Stable-diffusion")
    elif type == "Hypernetwork":
        default = cmd_opts.hypernetwork_dir
        folder = os.path.relpath(default, base)
    elif type == "TextualInversion":
        default = cmd_opts.embeddings_dir
        folder = os.path.relpath(default, base)
    elif type == "AestheticGradient":
        default = os.path.join(models_path, "../extensions/stable-diffusion-webui-aesthetic-gradients/aesthetic_embeddings")
        folder = os.path.relpath(default, base)
    elif type == "LORA":
        default = cmd_opts.lora_dir  # "models/Lora"
        folder = os.path.relpath(default, base)
    elif type == "LoCon":
        #if "lyco_dir" in cmd_opts:
        #    default = f"{cmd_opts.lyco_dir}"
        #elif "lyco_dir_backcompat" in cmd_opts:  # A1111 V1.5.1
        #    default = f"{cmd_opts.lyco_dir_backcompat}"
        #else:
        default = os.path.join(models_path, "Lora/_LyCORIS")
        folder = os.path.relpath(default, base)
    elif type == "DoRA":
        default = os.path.join(models_path, "Lora/_DoRA")  # "models/Lora/_DoRA"
        folder = os.path.relpath(default, base)
    elif type == "VAE":
        if cmd_opts.vae_dir:
            default = cmd_opts.vae_dir  # "models/VAE"
        else:
            default = os.path.join(models_path, "VAE")
        folder = os.path.relpath(default, base)
    elif type == "Controlnet":
        folder = "ControlNet"
    elif type == "Poses":
        folder = "OtherModels/Poses"
    elif type == "Upscaler":
        folder = "OtherModels/Upscaler"
    elif type == "MotionModule":
        folder = "OtherModels/MotionModule"
    elif type == "Wildcards":
        folder = "OtherModels/Wildcards"
    elif type == "Workflows":
        folder = "OtherModels/Workflows"
    elif type == "Detection":
        folder = "OtherModels/Detection"
    elif type == "Other":
        folder = "OtherModels/Other"

    optFolder = folderSetting.get(type, "")
    if optFolder == "":
        pType = Path(base) / Path(folder)
    else:
        pType = Path(base) / Path(optFolder)
    return pType

def basemodel_path(baseModel: str) -> Path:
    basemodelPath = ""
    if not 'SD 1' in baseModel:
        basemodelPath = '_' + baseModel.replace(' ', '_').replace('.', '_')
    return Path(basemodelPath)

def basemodel_path_all(baseModel: str) -> Path:
    basemodelPath = baseModel.replace(' ', '_').replace('.', '_')
    return Path(basemodelPath)

def generate_model_save_path2(type, modelName: str = "", baseModel: str = "", nsfw: bool = False, userName=None, mID=None, vID=None, versionName=None) -> Path:
    # TYPE, MODELNAME, BASEMODEL, NSFW, UPNAME, MODEL_ID, VERSION_ID
    subfolders = {
        # "TYPE": type_path(type).as_posix(),
        "BASEMODELbkCmpt": basemodel_path(baseModel).as_posix(),
        "BASEMODEL": basemodel_path_all(baseModel).as_posix(),
        "NSFW": "nsfw" if nsfw else None,
        "USERNAME": escaped_filename(userName) if userName is not None else None,
        "MODELNAME": escaped_filename(modelName),
        "MODELID": str(mID) if mID is not None else None,
        "VERSIONNAME": escaped_filename(versionName),
        "VERSIONID": str(vID) if vID is not None else None,
    }
    if not str.strip(opts.civsfz_save_subfolder):
        subTree = "_{{BASEMODEL}}/.{{NSFW}}/{{MODELNAME}}"
    else:
        subTree = str.strip(opts.civsfz_save_subfolder)
    subTreeList = subTree.split("/")
    newTreeList = []
    for i, sub in enumerate(subTreeList):
        if sub:
            subKeys = re.findall("(\{\{(.+?)\}\})", sub)
            newSub = ""
            replaceSub = sub
            for subKey in subKeys:
                if subKey[1] is not None:
                    if subKey[1] in subfolders:
                        folder = subfolders[subKey[1]]
                        if folder is not None:
                            replaceSub = re.sub(
                                "\{\{" + subKey[1] + "\}\}", folder, replaceSub)
                        else:
                            replaceSub = re.sub(
                                "\{\{" + subKey[1] + "\}\}", "", replaceSub)
                    else:
                        print_ly(f'"{subKey[1]}" is not defined')
                        replaceSub = "ERROR"
            newSub += replaceSub if replaceSub is not None else ""

            if newSub != "":
                newTreeList.append(newSub)
        else:
            if i != 0:
                print_lc(f"Empty subfolder:{i}")
    modelPath = type_path(type).joinpath(
        "/".join(newTreeList))
    return modelPath

def filename_normalization(filename) -> str:
    if filename:
        filename = re.sub(r"__+", "_", filename)
    return filename

def save_text_file(folder, filename, trained_words):
    filename = filename_normalization(filename)
    makedirs(folder)
    filepath = os.path.join(folder, filename.replace(".ckpt",".txt")\
                                        .replace(".safetensors",".txt")\
                                        .replace(".pt",".txt")\
                                        .replace(".yaml",".txt")\
                                        .replace(".zip",".txt")\
                        )
    if not os.path.exists(filepath):
        with open(filepath, 'w', encoding='UTF-8') as f:
            f.write(trained_words)
    print_n('Save text.')
    return "Save text"

def makedirs(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)
        print_lc(f'Make folder: {folder}')

def isExistFile(folder, file):
    file = filename_normalization(file)
    isExist = False
    if folder != "" and folder is not None:
        path = os.path.join(folder, file)
        isExist = os.path.exists(path)
    return isExist


def saveImageFiles(folder, versionName, html, content_type, versionInfo):
    html = versionInfo['html0']
    makedirs(folder)
    img_urls = re.findall(r'src=[\'"]?([^\'" >]+)', html)
    basename = os.path.splitext(versionName)[0]  # remove extension
    basename = filename_normalization(basename)
    preview_url = versionInfo["modelVersions"][0]["images"][0]["url"]
    preview_url = urllib.parse.quote(preview_url,  safe=':/=')
    if 'images' in versionInfo:
        for img in versionInfo['images']:
            if img['type'] == 'image':
                preview_url = img['url']
                preview_url = urllib.parse.quote(preview_url,  safe=':/=')
                break
    with requests.Session() as session:
        HTML = html
        for i, img_url in enumerate(img_urls):
            isVideo = False
            for img in versionInfo["modelVersions"][0]["images"]:
                if img['url'] == img_url:
                    if img['type'] == 'video':
                        isVideo = True
            # print(Fore.LIGHTYELLOW_EX + f'URL: {img_url}'+ Style.RESET_ALL)
            if isVideo:
                if content_type == "TextualInversion":
                    filename = f'{basename}_{i}.preview.webm'
                    filenamethumb = f'{basename}.preview.webm'
                else:
                    filename = f'{basename}_{i}.webm'
                    filenamethumb = f'{basename}.webm'
            else:
                if content_type == "TextualInversion":
                    filename = f'{basename}_{i}.preview.png'
                    filenamethumb = f'{basename}.preview.png'
                else:
                    filename = f'{basename}_{i}.png'
                    filenamethumb = f'{basename}.png'

            HTML = HTML.replace(img_url, f'"{filename}"')
            url_parse = urllib.parse.urlparse(img_url)
            if url_parse.scheme:
                # img_url.replace("https", "http").replace("=","%3D")
                img_url = urllib.parse.quote(img_url,  safe=':/=')
                try:
                    response = session.get(img_url, timeout=read_timeout())
                    with open(os.path.join(folder, filename), 'wb') as f:
                        f.write(response.content)
                        if img_url == preview_url:
                            shutil.copy2(os.path.join(folder, filename),
                                        os.path.join(folder, filenamethumb))
                        print_n(f"Save {filename}")
                    # with urllib.request.urlretrieve(img_url, os.path.join(model_folder, filename)) as dl:
                except requests.exceptions.Timeout as e:
                    print_ly(f'Error: {e.reason}')
                    print_ly(f'URL: {img_url}')
                    # return "Err: Save infos"
                except requests.exceptions.RequestException as e:
                    print_ly(f'Error: {e.reason}')
                    print_ly(f'URL: {img_url}')
    filepath = os.path.join(folder, f'{basename}.html')
    with open(filepath, 'wb') as f:
        f.write(HTML.encode('utf8'))
        print_n(f"Save {basename}.html")
    # Save json_info
    filepath = os.path.join(folder, f'{basename}.civitai.json')
    with open(filepath, mode="w", encoding="utf-8") as f:
        json.dump(versionInfo, f, indent=2, ensure_ascii=False)
        print_n(f"Save {basename}.civitai.json")
    return "Save infos"

def removeFile(file):
    if send2trash_installed:
        try:
            send2trash(file.replace('/','\\'))
        except Exception as e:
            print_ly('Error: Fail to move file to trash')
        else:
            print_lc('Move file to trash')
    else:
        print_lc('File is not deleted. send2trash module is missing.')
    return

def open_folder(f):
    '''
    [reference](https://github.com/AUTOMATIC1111/stable-diffusion-webui/blob/5ef669de080814067961f28357256e8fe27544f4/modules/ui_common.py#L109)
    '''
    if not f:
        return
    count = 0
    while not os.path.isdir(f):
        count += 1
        print_lc(f'Not found "{f}"')
        newf = os.path.abspath(os.path.join(f, os.pardir))
        if newf == f:
            break
        if count >5:
            print_lc(f'Not found the folder')
            return
        f = newf
    path = os.path.normpath(f)
    if os.path.isdir(path):
        if platform.system() == "Windows":
            # sp.Popen(rf'explorer /select,"{path}"')
            # sp.run(["explorer", path])
            os.startfile(path, operation="explore")
        elif platform.system() == "Darwin":
            # sp.run(["open", path])
            sp.Popen(["open", path])
        elif "microsoft-standard-WSL2" in platform.uname().release:
            # sp.run(["wsl-open", path])
            sp.Popen(["explorer.exe", sp.check_output(["wslpath", "-w", path])])
        else:
            # sp.run(["xdg-open", path])
            sp.Popen(["xdg-open", path])
    else:
        print_lc(f'Not found "{path}"')

class History():
    def __init__(self, path=None):
        self._path = Path.joinpath(
            extensionFolder(), Path("../history.json"))
        if path != None:
            self._path = path
        self._history: deque = self.load()
    def load(self) -> list[dict]:
        try:
            with open(self._path, 'r', encoding="utf-8") as f:
                ret = json.load(f)
        except:
            ret = []
        return deque(ret,maxlen=20)
    def save(self):
        try:
            with open(self._path, 'w', encoding="utf-8") as f:
                json.dump(list(self._history), f, indent=4, ensure_ascii=False)
        except Exception as e:
            #print_lc(e)
            pass
    def len(self) -> int:
        return len(self._history) if self._history is not None else None
    def getAsChoices(self):
        ret = [
            json.dumps(h, ensure_ascii=False) for h in self._history]
        return ret

class SearchHistory(History):
    def __init__(self):
        super().__init__(Path.joinpath(
            extensionFolder(), Path("../search_history.json")))
        self._delimiter = "_._"
    def add(self, type, word):
        if type == "No" or word == "" or word == None:
            return
        if word in FavoriteCreators.getAsList():
            return
        d = { "type" : type,
                "word": word }  
        try:                  
            self._history.remove(d)
        except:
            pass
        self._history.appendleft(d)
        while self.len() > opts.civsfz_length_of_search_history:
            self._history.pop()
        self.save()
    def getAsChoices(self):
        ret = [f'{w["word"]}{self._delimiter}{w["type"]}' for w in self._history]
        # Add favorite users
        favUsers = [
            f"{s.strip()}{self._delimiter}User name{self._delimiter}⭐️"
            for s in FavoriteCreators.getAsList()
        ]
        return ret + favUsers
    def getDelimiter(self) -> str:
        return self._delimiter

class ConditionsHistory(History):
    def __init__(self):
        super().__init__(Path.joinpath(
            extensionFolder(), Path("../conditions_history.json")))
        self._delimiter = "_._"
    def add(self, sort, period, baseModels, nsfw ):
        d = {
            "sort": sort,
            "period": period,
            "baseModels": baseModels,
            "nsfw": nsfw
        }
        try:                  
            self._history.remove(d)
        except:
            pass
        self._history.appendleft(d)
        while self.len() > opts.civsfz_length_of_conditions_history:
            self._history.pop()
        self.save()
    def getAsChoices(self):
        ret = [self._delimiter.join(
                [ str(v) if k != 'baseModels' else json.dumps(v, ensure_ascii=False) for k, v in h.items()]
                ) for h in self._history]
        return ret
    def getDelimiter(self) -> str:
        return self._delimiter
HistoryS = SearchHistory()
HistoryC = ConditionsHistory()

class UserInfo:
    def __init__(self, path=None):
        self._path = Path.joinpath(extensionFolder(), Path("../users.json"))
        if path != None:
            self._path = path
        self._users: list = self.load()

    def add(self, name: str) -> bool:
        name = name.strip()
        if name == "":
            return False
        self.remove(name)
        self._users.append(name)
        self.save()
        return True

    def remove(self, name: str) -> bool:
        name = name.strip()
        if name == "":
            return False
        self._users = [u for u in self._users if u != name]
        self.save()
        return True

    def load(self) -> list:
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                line = ", ".join(lines)
                ret = [s.strip() for s in line.split(",") if s.strip()]
        except Exception as e:
            # print_lc(f"{e}")
            ret = []
        return ret

    def save(self):
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                l = len(self._users)
                n = 3
                for i in range(0,int(l),n):
                    f.write(", ".join(self._users[i : i + n]))
                    f.write("\n")
        except Exception as e:
            # print_lc(e)
            pass
    def getAsList(self) -> list[str]:
        return self._users
    def getAsText(self) -> str:
        return ", ".join(self._users)

class FavoriteUsers(UserInfo):
    def __init__(self):
        super().__init__(
            Path.joinpath(extensionFolder(), Path("../favoriteUsers.txt"))
        )
        if hasattr(opts, "civsfz_favorite_creators"):  # for backward compatibility
            users = [s.strip() for s in opts.civsfz_favorite_creators.split(",") if s.strip()]
            for u in users:
                self.add(u)

class BanUsers(UserInfo):
    def __init__(self):
        super().__init__(
            Path.joinpath(extensionFolder(), Path("../bannedUsers.txt")))
        if hasattr(opts, "civsfz_ban_creators"):  # for backward compatibility
            users = [
                s.strip() for s in opts.civsfz_ban_creators.split(",") if s.strip()
            ]
            for u in users:
                self.add(u)
FavoriteCreators = FavoriteUsers()
BanCreators = BanUsers()
