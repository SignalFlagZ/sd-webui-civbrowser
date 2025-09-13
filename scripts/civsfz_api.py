import re
import datetime
from dateutil import tz
import json
import urllib.parse
from pathlib import Path
import requests
# from requests_cache import CachedSession
from colorama import Fore, Back, Style
from scripts.civsfz_filemanage import (
    generate_model_save_path2,
    extensionFolder,
    FavoriteCreators,
    BanCreators,
    isExistFile,
)
from scripts.civsfz_color import dictBasemodelColors
from scripts.civsfz_shared import opts, read_timeout
from jinja2 import Environment, FileSystemLoader

print_ly = lambda  x: print(Fore.LIGHTYELLOW_EX + "CivBrowser: " + x + Style.RESET_ALL )
print_lc = lambda  x: print(Fore.LIGHTCYAN_EX + "CivBrowser: " + x + Style.RESET_ALL )
print_n = lambda  x: print("CivBrowser: " + x )

templatesPath = Path.joinpath(
    extensionFolder(), Path("../templates"))
environment = Environment(
    loader=FileSystemLoader(templatesPath.resolve()),
    extensions=["jinja2.ext.loopcontrols"],
)

class Browser:
    session = None
    
    def __init__(self):
        if Browser.session is None:
            Browser.session = requests.Session()
        Browser.session.headers.update(
            {'User-Agent': r'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0'})
        #self.setAPIKey("")
    def __enter__(self):
        return Browser.session
    def __exit__(self):
        Browser.session.close()
    def newSession(self):
        Browser.session = requests.Session()
    def reConnect(self):
        Browser.session.close()
        self.newSession()
    def setAPIKey(self, api_key):
        if len(api_key) == 32:
            Browser.session.headers.update(
                {"Authorization": f"Bearer {api_key}"})
            print_lc("Apply API key")


class ModelCardsPagination:
    def __init__(self, response:dict, types:list=None, sort:str=None, searchType:str=None, searchTerm:str=None, nsfw:bool=None, period:str=None, basemodels:list=None) -> None:
        self.types  = types
        self.sort = sort
        self.searchType = searchType
        self.searchTerm = searchTerm
        self.nsfw = nsfw
        self.period = period
        self.baseModels = basemodels
        self.pages=[]
        self.pageSize = 1 #response['metadata']['pageSize'] if 'pageSize' in response['metadata'] else None
        self.currentPage = 1
        page = { 'url': response['requestUrl'],
                 'nextUrl': response['metadata']['nextPage'] if 'nextPage' in response['metadata'] else None,
                 'prevUrl': None
                }
        self.pages.append(page)
    
    def getNextUrl(self) -> str:
        return self.pages[self.currentPage-1]['nextUrl']
    def getPrevUrl(self) -> str:
        return self.pages[self.currentPage-1]['prevUrl']
    def getJumpUrl(self, page) -> str:
        if page <= len(self.pages):
            return self.pages[page-1]['url']
        else:
            return None
    def getPagination(self):
        ret = { "types": self.types,
                "sort": self.sort,
                "searchType": self.searchType,
                "searchTerm": self.searchTerm,
                "nsfw": self.nsfw,
                "period": self.period,
                "basemodels": self.baseModels,
                "pageSize": len(self.pages),
                "currentPage": self.currentPage,
                "pages": self.pages
               }
        return ret
    def setPagination(self, pagination:dict):
        self.pages = pagination['pages']
        self.currentPage = pagination['currentPage']
        self.pageSize = pagination['pageSize']
    
    def nextPage(self, response:dict) -> None:
        prevUrl = self.pages[self.currentPage-1]['url']
        page = { 'url': response['requestUrl'],
                 'nextUrl': response['metadata']['nextPage'] if 'nextPage' in response['metadata'] else None,
                 'prevUrl': prevUrl
                }
        #if self.currentPage + 1 == self.pageSize:
        #    page['nextUrl'] = None
        if self.currentPage < len(self.pages):
            self.pages[self.currentPage] = page
        else:
            self.pages.append(page)
            if len(self.pages) > self.pageSize:
                self.pageSize = len(self.pages)
        self.currentPage += 1
        return

    def prevPage(self, response: dict) -> None:
        page = {'url': response['requestUrl'],
                'nextUrl': response['metadata']['nextPage'] if 'nextPage' in response['metadata'] else None,
                'prevUrl': None
                }
        if self.currentPage  > 1:
            page['prevUrl'] = self.pages[self.currentPage-2]['url']
        self.pages[self.currentPage-1] = page
        self.currentPage -= 1
        return
    def pageJump(self, response, pageNum):
        page = {'url': response['requestUrl'],
                'nextUrl': response['metadata']['nextPage'] if 'nextPage' in response['metadata'] else None,
                'prevUrl': None
                }
        if pageNum > 1:
            page['prevUrl'] = self.pages[pageNum-1]['prevUrl']
        self.pages[pageNum-1] = page
        self.currentPage = pageNum
        return

class APIInformation():
    baseUrl = "https://civitai.com"
    modelsApi = f"{baseUrl}/api/v1/models"
    imagesApi = f"{baseUrl}/api/v1/images"
    versionsAPI = f"{baseUrl}/api/v1/model-versions"
    byHashAPI = f"{baseUrl}/api/v1/model-versions/by-hash"
    typeOptions:list = None
    sortOptions:list = None
    basemodelOptions:list = None
    periodOptions:list = None
    searchTypes = [
        "No",
        "Keyword",
        "User name",
        "Tag",
        "Model ID",
        "Version ID",
        "Hash",
    ]
    nsfwLevel = {"PG": 1,
                 "PG-13": 2,
                 "R": 4,
                 "X": 8,
                 "XXX": 16,
                 #"Blocked":  32,
                 "Banned":  256,
                 } 
    def __init__(self) -> None:
        if APIInformation.typeOptions is None:
            self.getOptions()
    def setBaseUrl(self,url:str):
        APIInformation.baseUrl = url
    def getBaseUrl(self) -> str:
        return APIInformation.baseUrl
    def getModelsApiUrl(self, id=None):
        url = APIInformation.modelsApi
        url += f'/{id}' if id is not None else ""
        return url
    def getImagesApiUrl(self):
        return APIInformation.imagesApi
    def getVersionsApiUrl(self, id=None):
        url = APIInformation.versionsAPI
        url += f'/{id}' if id is not None else ""
        return url
    def getVersionsByHashUrl(self, hash=None):
        url = APIInformation.byHashAPI
        url += f'/{hash}' if id is not None else ""
        return url
    def getTypeOptions(self) -> list:
        # global typeOptions, sortOptions, basemodelOptions
        return APIInformation.typeOptions
    def getSortOptions(self) -> list:
        # global typeOptions, sortOptions, basemodelOptions
        return APIInformation.sortOptions
    def getBasemodelOptions(self) -> list:
        # global typeOptions, sortOptions, basemodelOptions
        return APIInformation.basemodelOptions
    def getPeriodOptions(self) -> list:
        return APIInformation.periodOptions
    def getSearchTypes(self) -> list:
        return APIInformation.searchTypes
    def strNsfwLevel(self, nsfwLevel:int) -> str:
        keys = []
        for k, v in APIInformation.nsfwLevel.items():
            if nsfwLevel & v > 0:
                keys.append(k)
        return ", ".join(keys)

    def requestApiOptions(self, url=None, query=None):
        if url is None:
            url = self.getModelsApiUrl()
        if query is not None:
            query = urllib.parse.urlencode(
                query, doseq=True, quote_via=urllib.parse.quote)
        # print_lc(f'{query=}')

        # Make a GET request to the API
        try:
            # with requests.Session() as request:
            browser = Browser()
            response = browser.session.get(
                url, params=query, timeout=read_timeout()
            )
            # print_lc(f'Page cache: {response.headers["CF-Cache-Status"]}')
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            # print(f"{(response.status_code)=}")
            if response.status_code == 400: # Bad Request
                # expected under normal conditions
                response.encoding = "utf-8"
                data = (
                json.loads(response.text)
            )
            else:
                data = ""
                print_ly("Civitai server may be down or under maintenance.")
        else:
            data = ""
        # Check the status code of the response
        # if response.status_code != 200:
        #  print("Request failed with status code: {}".format(response.status_code))
        #  exit()
        return data

    def getOptions(self):
        '''Get choices from Civitai'''
        url = self.getModelsApiUrl()
        query = { 'types': ""}
        data = self.requestApiOptions(url, query)
        types = [
                  "Checkpoint",
                  "TextualInversion",
                  "Hypernetwork",
                  "AestheticGradient",
                  "LORA",
                  "LoCon",
                  "DoRA",
                  "Controlnet",
                  "Upscaler",
                  "MotionModule",
                  "VAE",
                  "Poses",
                  "Wildcards",
                  "Workflows",
                  "Detection",
                  "Other"
                ]
        try:
            # types = data['error']['issues'][0]['unionErrors'][0]['issues'][0]['options']
            res = json.loads(data['error']['message'])
            newList = res[0]["errors"][0][0]["values"]
            # print_lc(f"{res[0]['errors'][0][0]['values']=}")
            diff = set(types) ^ set(newList)
            if len(diff) != 0:
                print_lc(f"Type options have been updated.\n{diff=}")
            types = newList
        except:
            print_ly(f'ERROR: Get types')
        else:
            # print_lc(f'Set types')
            pass
        priorityTypes = [
            "Checkpoint",
            "TextualInversion",
            "LORA",
            "LoCon",
            "DoRA"
        ]
        dictPriority = {
            priorityTypes[i]: priorityTypes[i] for i in range(0, len(priorityTypes))}
        dict_types = dictPriority | {types[i]: types[i]
                                        for i in range(0, len(types))}
        APIInformation.typeOptions = [dictPriority.get(
            key, key) for key, value in dict_types.items()]

        query = {'baseModels': ""}
        data = self.requestApiOptions(url, query)
        APIInformation.basemodelOptions = [
            "AuraFlow",
            "Chroma",
            "CogVideoX",
            "Flux.1 S",
            "Flux.1 D",
            "Flux.1 Krea",
            "Flux.1 Kontext",
            "HiDream",
            "Hunyuan 1",
            "Hunyuan Video",
            "Illustrious",
            "Imagen4",
            "Kolors",
            "LTXV",
            "Lumina",
            "Mochi",
            "Nano Banana",
            "NoobAI",
            "ODOR",
            "OpenAI",
            "Other",
            "PixArt a",
            "PixArt E",
            "Playground v2",
            "Pony",
            "Qwen",
            "Stable Cascade",
            "SD 1.4",
            "SD 1.5",
            "SD 1.5 LCM",
            "SD 1.5 Hyper",
            "SD 2.0",
            "SD 2.0 768",
            "SD 2.1",
            "SD 2.1 768",
            "SD 2.1 Unclip",
            "SD 3",
            "SD 3.5",
            "SD 3.5 Large",
            "SD 3.5 Large Turbo",
            "SD 3.5 Medium",
            "SDXL 0.9",
            "SDXL 1.0",
            "SDXL 1.0 LCM",
            "SDXL Lightning",
            "SDXL Hyper",
            "SDXL Turbo",
            "SDXL Distilled",
            "Seedream",
            "SVD",
            "SVD XT",
            "Veo 3",
            "Wan Video",
            "Wan Video 1.3B t2v",
            "Wan Video 14B t2v",
            "Wan Video 14B i2v 480p",
            "Wan Video 14B i2v 720p",
            "Wan Video 2.2 TI2V-5B",
            "Wan Video 2.2 I2V-A14B",
            "Wan Video 2.2 T2V-A14B",
        ]
        try:
            # APIInformation.basemodelOptions = data['error']['issues'][0]['unionErrors'][0]['issues'][0]['options']
            res = json.loads(data['error']['message'])
            # print_lc(f"{res[0]['errors'][0][0]['values']=}")
            newList = res[0]["errors"][0][0]["values"]
            diff = set(APIInformation.basemodelOptions) ^ set(newList)
            if len(diff) != 0:
                print_lc(f"Base model options have been updated.\n{diff=}")
            APIInformation.basemodelOptions = newList
        except:
            print_ly(f'ERROR: Get base models')
        else:
            # print_lc(f'Set base models')
            pass

        query = {'sort': ""}
        data = self.requestApiOptions(url, query)
        APIInformation.sortOptions = [
            "Highest Rated",
            "Most Downloaded",
            "Most Liked",
            "Most Discussed",
            "Most Collected",
            "Most Images",
            "Newest",
            "Oldest",
        ]
        try:
            # APIInformation.sortOptions = data['error']['issues'][0]['options']
            res = json.loads(data['error']['message'])
            # print_lc(f"{res[0]['values']=}")
            newList = res[0]["values"]
            diff = set(APIInformation.sortOptions) ^ set(newList)
            if len(diff) != 0:
                print_lc(f"Sort options have been updated.\n{diff=}")
            APIInformation.sortOptions = newList
        except:
            print_ly(f'ERROR: Get sorts')
        else:
            # print_lc(f'Set sorts')
            pass

        query = {'period': ""}
        data = self.requestApiOptions(url, query)
        APIInformation.periodOptions = [
                "Day",
                "Week",
                "Month",
                "Year",
                "AllTime"
            ]
        try:
            # APIInformation.periodOptions = data['error']['issues'][0]['options']
            res = json.loads(data['error']['message'])
            # print_lc(f"{res[0]['values']=}")
            newList = res[0]["values"]
            diff = set(APIInformation.periodOptions) ^ set(newList)
            if len(diff) != 0:
                print_lc(f"Period options have been updated.\n{diff=}")
            APIInformation.periodOptions = newList
        except:
            print_ly(f'ERROR: Get periods')
        else:
            # print_lc(f'Set periods')
            pass

class CivitaiModels(APIInformation):
    '''CivitaiModels: Handle the response of civitai models api v1.'''
    def __init__(self, url:str=None, json_data:dict=None, content_type:str=None):
        super().__init__()
        self.jsonData = json_data
        # self.contentType = content_type
        self.showNsfw = False
        self.baseUrl = APIInformation.baseUrl if url is None else url
        self.modelIndex = None
        self.versionsInfo = None    # for radio button and file exist check
        self.versionIndex = None
        self.modelVersionInfo = None
        self.requestError = None
        self.saveFolder = None
        self.cardPagination = None
    def updateJsonData(self, json_data:dict=None, content_type:str=None):
        '''Update json data.'''
        self.jsonData = json_data
        # self.contentType = self.contentType if content_type is None else content_type
        self.showNsfw = False
        self.modelIndex = None
        self.versionIndex = None
        self.modelVersionInfo = None
        self.requestError = None
        self.saveFolder = None
    def getJsonData(self) -> dict:
        return self.jsonData

    def setShowNsfw(self, showNsfw:bool):
        self.showNsfw = showNsfw
    def isShowNsfw(self) -> bool:
        return self.showNsfw
    # def setContentType(self, content_type:str):
    #    self.contentType = content_type
    # def getContentType(self) -> str:
    #    return self.contentType
    def getRequestError(self) -> requests.exceptions.RequestException:
        return self.requestError
    def clearRequestError(self):
        self.requestError = None
    def setSaveFolder(self, path):
        self.saveFolder = path
    def getSaveFolder(self):
        return self.saveFolder
    def matchLevel(self, modelLevel:int, browsingLevel:int) -> bool:
        if bool(browsingLevel & self.nsfwLevel["Banned"]) :
            # Show banned users
            if browsingLevel == self.nsfwLevel["Banned"]:
                # Show all if Browsing Level is unchecked
                return True
            return modelLevel & browsingLevel > 0
        else:
            if browsingLevel == 0: # Show all if Browsing Level is unchecked
                return not bool(modelLevel & self.nsfwLevel["Banned"])
        return bool(modelLevel & browsingLevel) and not bool(
            modelLevel & self.nsfwLevel["Banned"]
        )

    # Models
    def getModels(self, showNsfw = False) -> list:
        '''Return: [(str: Model name, str: index)]'''
        model_list = [] 
        for index, item in enumerate(self.jsonData['items']):
            # print_lc(
            #    f"{item['nsfwLevel']}-{item['nsfwLevel'] & sum(opts.civsfz_browsing_level)}-{opts.civsfz_browsing_level}")
            # if (item['nsfwLevel'] & 2*sum(opts.civsfz_browsing_level)-1) > 0:
            if showNsfw:
                model_list.append((item['name'], index))
            elif not self.treatAsNsfw(modelIndex=index):  #item['nsfw']:
                model_list.append((item['name'], index))
        return model_list

    # def getModelNames(self) -> dict: #include nsfw models
    #    model_dict = {}
    #    for item in self.jsonData['items']:
    #        model_dict[item['name']] = item['name']
    #    return model_dict
    # def getModelNamesSfw(self) -> dict: #sfw models
    #    '''Return SFW items names.'''
    #    model_dict = {}
    #    for item in self.jsonData['items']:
    #        if not item['nsfw']:
    #            model_dict[item['name']] = item['name']
    #    return model_dict

    # Model
    def getModelNameByID(self, id:int) -> str:
        name = None
        for item in self.jsonData['items']:
            if int(item['id']) == int(id):
                name = item['name']
        return name
    def getIDByModelName(self, name:str) -> str:
        id = None
        for item in self.jsonData['items']:
            if item['name'] == name:
                id = int(item['id'])
        return id
    def getModelNameByIndex(self, index:int) -> str:
        return self.jsonData['items'][index]['name']
    def isNsfwModelByID(self, id:int) -> bool:
        nsfw = None
        for item in self.jsonData['items']:
            if int(item['id']) == int(id):
                nsfw = item['nsfw']
        return nsfw
    def selectModelByIndex(self, index:int):
        if index >= 0 and index < len(self.jsonData['items']):
            self.modelIndex = index
        return self.modelIndex
    def selectModelByID(self, id:int):
        for index, item in enumerate(self.jsonData['items']):
            if int(item['id']) == int(id):
                self.modelIndex = index
        return self.modelIndex
    def selectModelByName(self, name:str) -> int:
        if name is not None:
            for index, item in enumerate(self.jsonData['items']):
                if item['name'] == name:
                    self.modelIndex = index
            # print(f'{name} - {self.modelIndex}')
        return self.modelIndex
    def isNsfwModel(self) -> bool:
        return self.jsonData['items'][self.modelIndex]['nsfw']
    def treatAsNsfw(self, modelIndex=None, versionIndex=None):
        modelIndex = self.modelIndex if modelIndex is None else modelIndex
        modelIndex = 0 if modelIndex is None else modelIndex
        versionIndex = self.versionIndex if versionIndex is None else versionIndex
        versionIndex = 0 if versionIndex is None else versionIndex
        ret = self.jsonData['items'][modelIndex]['nsfw']
        if opts.civsfz_treat_x_as_nsfw:
            try:
                picNsfw = self.jsonData['items'][modelIndex]['modelVersions'][versionIndex]['images'][0]['nsfwLevel']
            except Exception as e:
                # print_ly(f'{e}')
                pass
            else:
                # print_lc(f'{picNsfw}')
                if picNsfw > 1:
                    ret = True
        return ret
    def getIndexByModelName(self, name:str) -> int:
        retIndex = None
        if name is not None:
            for index, item in enumerate(self.jsonData['items']):
                if item['name'] == name:
                    retIndex = index
        return retIndex
    def getSelectedModelIndex(self) -> int:
        return self.modelIndex
    def getSelectedModelName(self) -> str:
        item = self.jsonData['items'][self.modelIndex]
        return item['name']
    def getSelectedModelID(self) -> str:
        item = self.jsonData['items'][self.modelIndex]
        return int(item['id'])
    def getSelectedModelType(self) -> str:
        item = self.jsonData['items'][self.modelIndex]
        return item['type']
    def getModelTypeByIndex(self, index:int) -> str:
        item = self.jsonData['items'][index]
        return item['type'] 
    def getUserName(self):
        item = self.jsonData['items'][self.modelIndex]
        return item['creator']['username'] if 'creator' in item else ""
    def getModelID(self):
        item = self.jsonData['items'][self.modelIndex]
        return item['id']

    def allows2permissions(self) -> dict:
        '''Convert allows to permissions. Select model first.
            [->Reference](https://github.com/civitai/civitai/blob/main/src/components/PermissionIndicator/PermissionIndicator.tsx#L15)'''
        permissions = {}
        if self.modelIndex is None:
            print_ly('Select item first.')
        else:
            if self.modelIndex is not None:
                canSellImagesPermissions = {
                    'Image'}
                canRentCivitPermissions = {'RentCivit'}
                canRentPermissions = {'Rent'}
                canSellPermissions = {'Sell'}

                item = self.jsonData['items'][self.modelIndex]
                allowCommercialUse = set(item['allowCommercialUse'])
                allowNoCredit = item['allowNoCredit']
                allowDerivatives = item['allowDerivatives']
                allowDifferentLicense = item['allowDifferentLicense']

                canSellImages = len(allowCommercialUse & canSellImagesPermissions) > 0 
                canRentCivit = len(allowCommercialUse & canRentCivitPermissions) > 0
                canRent = len(allowCommercialUse & canRentPermissions) > 0
                canSell = len(allowCommercialUse & canSellPermissions) > 0

                permissions['allowNoCredit'] = allowNoCredit
                permissions['canSellImages'] = canSellImages
                permissions['canRentCivit'] = canRentCivit
                permissions['canRent'] = canRent
                permissions['canSell'] = canSell
                permissions['allowDerivatives'] = allowDerivatives
                permissions['allowDifferentLicense'] = allowDifferentLicense
        return permissions
    def getModelVersionsList(self) -> list:
        '''Return modelVersions list. Select item before.'''
        self.getModelVersionsInfo()
        return [(item["name"], i) for i, item in enumerate(self.versionsInfo)]
        # versionNames = []
        # if self.modelIndex is None:
        #     print_ly('Select item first.')
        # else:
        #     item = self.jsonData['items'][self.modelIndex]
        #     versionNames = [ (version['name'],i) for i,version in enumerate(item['modelVersions'])]
        #     # versionNames[version['name']] = version["name"]
        # return versionNames

    def modelVersionsInfo(self) -> list:
        return self.versionsInfo

    def getModelVersionsInfo(self) -> list:
        info = []
        if self.modelIndex is None:
            pass
            # print_ly("Select item first.")
        else:
            hasVersions = self.checkAlreadyHave()
            # print_lc(f"{hasVersions=}")
            item = self.jsonData["items"][self.modelIndex]
            info = [
                {
                    "name": l1["name"],
                    "base_model": l1["baseModel"],
                    "have": l2,
                }
                for l1,l2 in zip(item["modelVersions"], hasVersions)
            ]
        self.versionsInfo = info
        return info

    def checkAlreadyHave(self, index:int=None) -> list[bool]:
        if index == None:
            index = self.modelIndex
        item = self.jsonData["items"][index]
        hasVersions = []
        for i,ver in enumerate(item['modelVersions']):
            have = False
            for file in ver['files']:
                folder = generate_model_save_path2(
                    item["type"],
                    item["name"],
                    ver["baseModel"],
                    self.treatAsNsfw(modelIndex=index, versionIndex=i),
                    item["creator"]["username"] if "creator" in item else "",
                    item["id"],
                    ver["id"],
                    ver["name"],
                )
                # print(f"{folder}")
                file_name = file['name']
                path_file = folder / Path(file_name)
                # print(f"{path_file}")
                if isExistFile(folder, file_name):
                    have = True
                    break
            hasVersions.append(have)
        return hasVersions

    # Version
    def selectVersionByIndex(self, index:int) -> int:
        numVersions = len(self.jsonData['items'][self.modelIndex]['modelVersions'])
        index = 0 if index < 0 else index
        index = numVersions -1 if index > numVersions-1 else index
        self.versionIndex = index
        return self.versionIndex
    def selectVersionByID(self, ID:int) -> int:
        item = self.jsonData['items'][self.modelIndex]
        for index, model in enumerate(item['modelVersions']):
            if int(model['id']) == int(ID):
                self.versionIndex = index
        return self.versionIndex
    def selectVersionByName(self, name:str) -> int:
        '''Select model version by name. Select model first.
        
        Args:
            ID (int): version ID
        Returns:
            int: index number of the version
        '''
        if name is not None:
            item = self.jsonData['items'][self.modelIndex]
            for index, model in enumerate(item['modelVersions']):
                if model['name'] == name:
                    self.versionIndex = index
        return self.versionIndex
    def getSelectedVersionName(self):
        return self.jsonData['items'][self.modelIndex]['modelVersions'][self.versionIndex]['name']
    def getSelectedVersionBaseModel(self):
        # print(f"{self.jsonData['items'][self.modelIndex]['modelVersions']}")
        return self.jsonData['items'][self.modelIndex]['modelVersions'][self.versionIndex]['baseModel']
    def getSelectedVersionEarlyAccessTimeFrame(self):
        '''
        earlyAccessTimeFrame is missing from the API response
        '''
        return self.jsonData['items'][self.modelIndex]['modelVersions'][self.versionIndex]['earlyAccessTimeFrame']
    def getSelectedVersionEarlyAccessDeadline(self):
        # if 'earlyAccessDeadline' in self.jsonData['items'][self.modelIndex]['modelVersions'][self.versionIndex]:
        #    return self.jsonData['items'][self.modelIndex]['modelVersions'][self.versionIndex]['earlyAccessDeadline']
        if self.jsonData['items'][self.modelIndex]['modelVersions'][self.versionIndex]['availability'] == "EarlyAccess":
            return "EA"
        else:
            return ""
    def setModelVersionInfo(self, modelInfo: str):
        self.modelVersionInfo = modelInfo
    def getModelVersionInfo(self) -> str:
        return self.modelVersionInfo
    def getVersionDict(self) -> dict:
        version_dict = {}
        item = self.jsonData['items'][self.modelIndex]
        version_dict = item['modelVersions'][self.versionIndex]
        return version_dict

    def getCreatedDatetime(self) -> datetime.datetime :
        item = self.jsonData['items'][self.modelIndex]
        version_dict = item['modelVersions'][self.versionIndex]
        strCreatedAt = version_dict['createdAt'].replace('Z', '+00:00') # < Python 3.11
        dtCreatedAt = datetime.datetime.fromisoformat(strCreatedAt)
        # print_lc(f'{dtCreatedAt} {dtCreatedAt.tzinfo}')
        return dtCreatedAt
    def getUpdatedDatetime(self) -> datetime.datetime:
        item = self.jsonData['items'][self.modelIndex]
        version_dict = item['modelVersions'][self.versionIndex]
        strUpdatedAt = version_dict['updatedAt'].replace(
            'Z', '+00:00')  # < Python 3.11
        dtUpdatedAt = datetime.datetime.fromisoformat(strUpdatedAt)
        # print_lc(f'{dtUpdatedAt} {dtUpdatedAt.tzinfo}')
        return dtUpdatedAt
    def getPublishedDatetime(self) -> datetime.datetime:
        item = self.jsonData['items'][self.modelIndex]
        version_dict = item['modelVersions'][self.versionIndex]
        if version_dict['publishedAt'] is None:
            return None
        if version_dict['publishedAt'][-1] == "Z":
            strPublishedAt = version_dict['publishedAt'].replace(
                'Z', '+00:00')  # < Python 3.11
        else:
            strPublishedAt = version_dict['publishedAt'][:19] + '+00:00'
        # print_lc(f'{version_dict["publishedAt"]=}  {strPublishedAt=}')
        dtPublishedAt = datetime.datetime.fromisoformat(strPublishedAt)
        # print_lc(f'{dtPublishedAt} {dtPublishedAt.tzinfo}')
        return dtPublishedAt
    def getEarlyAccessDeadlineDatetime(self) -> datetime.datetime:
        item = self.jsonData['items'][self.modelIndex]
        version_dict = item['modelVersions'][self.versionIndex]
        if 'earlyAccessDeadline' in version_dict:
            strEarlyAccessDeadline = version_dict['earlyAccessDeadline'].replace(
                'Z', '+00:00')  # < Python 3.11
            dtEarlyAccessDeadline = datetime.datetime.fromisoformat(strEarlyAccessDeadline)
        else:
            dtEarlyAccessDeadline=""
            # print_lc(f'{dtPublishedAt} {dtPublishedAt.tzinfo}')
        return dtEarlyAccessDeadline
    def getVersionID(self):
        item = self.jsonData['items'][self.modelIndex]
        version_dict = item['modelVersions'][self.versionIndex]
        return version_dict['id']

    def addMetaVID(self, vID, modelInfo: dict) -> dict:
        versionRes = self.requestVersionByVersionID(vID)
        if versionRes is not None:
            # print_lc(f'{len(modelInfo["modelVersions"][0]["images"])}-{len(versionRes["images"])}')
            for i, img in enumerate(versionRes["images"]):
                # if 'meta' not in modelInfo["modelVersions"][0]["images"][i]:
                modelInfo["modelVersions"][0]["images"][i]["meta"] = img['meta'] if 'meta' in img else {
                }
            for i, img in enumerate(modelInfo["modelVersions"][0]["images"]):
                if 'meta' not in img:
                    img["meta"] = {
                        "WARNING": "Model Version API has no information"}
        else:
            for i, img in enumerate(modelInfo["modelVersions"][0]["images"]):
                if 'meta' not in img:
                    img["meta"] = {
                        "WARNING": "Model Version API request error"}
        return modelInfo

    def addMetaIID(self, vID:dict, modelInfo:dict) -> dict:
        imagesRes = self.requestImagesByVersionId(vID)
        if self.requestError is not None:
            print_ly(f"Version ID API Request Error: Fail to get meta info.")
        if imagesRes is not None:
            IDs = {item["id"]: item["meta"] for item in imagesRes["items"] if 'meta' in item}
            for i, img in enumerate(modelInfo["modelVersions"][0]["images"]):
                if 'id' not in img:
                    # Extract image ID from url
                    id = re.findall(r'/(\d+)\.\w+$', img['url'])
                    # print_lc(f'{img["url"]}   {id=}')
                    if 'id' not in img:
                        img['id'] = int(id[0])

                if 'id' in img:
                    if img['id'] in IDs.keys():
                        img['meta']=IDs[img['id']]
                    else:
                        img['meta'] = {
                            "WARNING": "Images API has no information"}
                else:
                    img['meta'] = {
                        "WARNING": "Version ID API response does not include Image ID. Therefore the Infotext cannot be determined. Try searching by model name."}
        else:
            for i, img in enumerate(modelInfo["modelVersions"][0]["images"]):
                if 'meta' not in img:
                    img["meta"] = {"ERROR": "Images API request error"}
        return modelInfo

    def makeModelInfo2(self, modelIndex=None, versionIndex=None, nsfwLevel=0) -> dict:
        """make selected version info"""
        modelIndex = self.modelIndex if modelIndex is None else modelIndex
        versionIndex = self.versionIndex if versionIndex is None else versionIndex
        item = self.jsonData["items"][modelIndex]
        version = item["modelVersions"][versionIndex]
        modelInfo = {"infoVersion": "2.4"}
        for key, value in item.items():
            if key not in ("modelVersions"):
                modelInfo[key] = value
        modelInfo["allow"] = {}
        modelInfo["allow"]["allowNoCredit"] = item["allowNoCredit"]
        modelInfo["allow"]["allowCommercialUse"] = item["allowCommercialUse"]
        modelInfo["allow"]["allowDerivatives"] = item["allowDerivatives"]
        modelInfo["allow"]["allowDifferentLicense"] = item["allowDifferentLicense"]
        modelInfo["modelVersions"] = [version]
        modelInfo["modelVersions"][0]["files"] = version["files"]
        modelInfo["modelVersions"][0]["images"] = version["images"]
        # add version info
        modelInfo['versionId'] = version['id']
        modelInfo['versionName'] = version['name']
        # modelInfo['createdAt'] = version['createdAt']
        # modelInfo['updatedAt'] = version['updatedAt']
        modelInfo['publishedAt'] = version['publishedAt']
        modelInfo['trainedWords'] = version['trainedWords'] if 'trainedWords' in version else ""
        modelInfo['baseModel'] = version['baseModel']
        modelInfo['versionDescription'] = version['description'] if 'description' in version else None
        modelInfo["downloadUrl"] = (
            version["downloadUrl"] if "downloadUrl" in version else None
        )
        # self.addMetaVID(version["id"], modelInfo)
        self.addMetaIID(version["id"], modelInfo)
        html = self.modelInfoHtml(modelInfo, nsfwLevel)
        modelInfo["html"] = html
        modelInfo["html0"] = self.modelInfoHtml(modelInfo, 0)
        self.setModelVersionInfo(modelInfo)
        return modelInfo

    def getUrlByName(self, model_filename=None):
        if self.modelIndex is None:
            # print(Fore.LIGHTYELLOW_EX + f'getUrlByName: Select model first. {model_filename}' + Style.RESET_ALL )
            return
        if self.versionIndex is None:
            # print(Fore.LIGHTYELLOW_EX + f'getUrlByName: Select version first. {model_filename}' + Style.RESET_ALL )
            return
        # print(Fore.LIGHTYELLOW_EX + f'File name . {model_filename}' + Style.RESET_ALL )
        item = self.jsonData['items'][self.modelIndex]
        version = item['modelVersions'][self.versionIndex]
        dl_url = None
        for file in version['files']:
            if file['name'] == model_filename:
                dl_url = file['downloadUrl']
        return dl_url
    def getHashByName(self, model_filename=None):
        if self.modelIndex is None:
            # print(Fore.LIGHTYELLOW_EX + f'getUrlByName: Select model first. {model_filename}' + Style.RESET_ALL )
            return
        if self.versionIndex is None:
            # print(Fore.LIGHTYELLOW_EX + f'getUrlByName: Select version first. {model_filename}' + Style.RESET_ALL )
            return
        # print(Fore.LIGHTYELLOW_EX + f'File name . {model_filename}' + Style.RESET_ALL )
        item = self.jsonData['items'][self.modelIndex]
        version = item['modelVersions'][self.versionIndex]
        sha256 = ""
        for file in version['files']:
            # print_lc(f'{file["hashes"]=}')
            if file['name'] == model_filename and 'SHA256' in file['hashes']:
                sha256 = file['hashes']['SHA256']
        return sha256

    # Pages
    def addFirstPage(self, response:dict, types:list=None, sort:str=None, searchType:str=None,
                     searchTerm:str=None, nsfw:bool=None, period:str=None, basemodels:list=None) -> None:
        self.cardPagination = ModelCardsPagination(response, types, sort, searchType, searchTerm, nsfw, period, basemodels)
        # print_lc(f'{self.cardPagination.getPagination()=}')
    def addNextPage(self, response:dict) -> None:
        self.cardPagination.nextPage(response)
    def backPage(self, response:dict) -> None:
        self.cardPagination.prevPage(response)
    def getJumpUrl(self, page) -> str:
        return self.cardPagination.getJumpUrl(page)
    def pageJump(self, response:dict, page) -> None:
        self.cardPagination.pageJump(response, page)
    def getPagination(self):
        return self.cardPagination.getPagination()

    def getCurrentPage(self) -> str:
        # return f"{self.jsonData['metadata']['currentPage']}"
        return self.cardPagination.currentPage if self.cardPagination is not None else 0
    def getTotalPages(self) -> str:
        # return f"{self.jsonData['metadata']['totalPages']}"
        # return f"{self.jsonData['metadata']['pageSize']}"
        return self.cardPagination.pageSize
    def getPages(self) -> str:
        return f"{self.getCurrentPage()}/{self.getTotalPages()}"
    def nextPage(self) -> str:
        # return self.jsonData['metadata']['nextPage'] if 'nextPage' in self.jsonData['metadata'] else None
        return self.cardPagination.getNextUrl() if self.cardPagination is not None else None
    def prevPage(self) -> str:
        # return self.jsonData['metadata']['prevPage'] if 'prevPage' in self.jsonData['metadata'] else None
        return self.cardPagination.getPrevUrl() if self.cardPagination is not None else None

    # HTML
    # Make model cards html
    def modelCardsHtml(self, models, jsID=0, nsfwLevel=0):
        '''Generate HTML of model cards.'''
        # NG List
        # txtNG = opts.civsfz_ban_creators  # Comma-separated text
        # txtFav = opts.civsfz_favorite_creators  # Comma-separated text
        # ngUsers = [s.strip() for s in txtNG.split(",") if s.strip()]
        # favUsers = [s.strip() for s in txtFav.split(",") if s.strip()]
        cards = []
        for model in models:
            index = model[1]
            item = self.jsonData['items'][model[1]]
            creator = item["creator"]["username"] if "creator" in item else ""
            level = item["nsfwLevel"] | (0 if not creator in BanCreators.getAsList() else self.nsfwLevel["Banned"])
            base_model = ""
            param = {
                "name": item["name"],
                "index": index,
                "jsId": jsID,
                "id": item["id"],
                "isNsfw": False,
                "nsfwLevel": level,
                "matchLevel": self.matchLevel(level, nsfwLevel),
                "type": item["type"],
                "have": "",
                "ea": "",
                "imgType": "",
                "creator": creator,
                "ngUser": creator in BanCreators.getAsList(),
                "favorite": creator in FavoriteCreators.getAsList(),
            }
            if any(item['modelVersions']):
                # if len(item['modelVersions'][0]['images']) > 0:
                # default image
                for i, img in enumerate(item['modelVersions'][0]['images']):
                    if i == 0: # 0 as default
                        param['imgType'] = img['type']
                        param['imgsrc'] = img["url"]
                        if img['nsfwLevel'] > 1 and not self.isShowNsfw():
                            param['isNsfw'] = True
                    if self.matchLevel(img['nsfwLevel'],  nsfwLevel): 
                        # img  = item['modelVersions'][0]['images'][0]
                        param['imgType'] = img['type']
                        param['imgsrc'] = img["url"]
                        if img['nsfwLevel'] > 1 and not self.isShowNsfw():
                            param['isNsfw'] = True
                        break
                base_model = item["modelVersions"][0]['baseModel']
                param['baseModel'] = base_model

                has = self.checkAlreadyHave(index)
                if has[0]:
                    param["have"] = "new"
                elif any(has[1:]) :
                    param["have"] = "old"

                # ea = item["modelVersions"][0]['earlyAccessDeadline'] if "earlyAccessDeadline" in item["modelVersions"][0] else ""
                ea = item["modelVersions"][0]['availability'] == "EarlyAccess"
                if ea:
                    # strEA = item["modelVersions"][0]['earlyAccessDeadline'].replace('Z', '+00:00')  # < Python 3.11
                    # dtEA = datetime.datetime.fromisoformat(strEA)
                    # dtNow = datetime.datetime.now(datetime.timezone.utc)
                    # if dtNow < dtEA:
                    param['ea'] = 'in'
            cards.append(param)

        forTrigger = f'<!-- {datetime.datetime.now()} -->'  # for trigger event
        dictBasemodelColor = dictBasemodelColors(self.getBasemodelOptions())
        template = environment.get_template("cardlist.jinja")
        content = template.render(
            forTrigger=forTrigger,
            cards=cards,
            dictBasemodelColor=dictBasemodelColor,
        )
        return content
    def modelNameTitleHtml(self, name:str, vname:str, base:str, upuser:str="", ea:str=""):
        dictBasemodelColor = dictBasemodelColors(self.getBasemodelOptions())
        template = environment.get_template("modelTitle.jinja")
        content = template.render(
            modelName=name, versionName=vname, baseModel=base, uploadUser=upuser, dictBasemodelColor=dictBasemodelColor, ea=ea,
        )
        return content

    def meta2html(self, meta:dict) -> str:
        # convert key name as infotext
        sortKey = [
            'prompt',
            'negativePrompt',
            'Model',
            'VAE',
            'sampler',
            'Schedule type',
            'cfgScale',
            'steps',
            'seed',
            'clipSkip',
        ]
        infotextDict = { key: meta[key] if key in meta else None for key in sortKey }
        infotextDict.update(meta)
        # print(f"{infotextDict=}")
        # if 'hashes' in infotextDict:
        # print(type(infotextDict['hashes']))

        template = environment.get_template("infotext.jinja")
        content = template.render(infotext=infotextDict)
        return content

    def meta2infotext(self, meta:dict) -> str:
        # convert key name as infotext
        renameKey = {
            'prompt':'Prompt',
            'negativePrompt': 'Negative prompt',
            'sampler': 'Sampler',
            'steps': 'Steps',
            'seed': 'Seed',
            'cfgScale': 'CFG scale',
            'clipSkip': 'Clip skip'
                }
        infotextDict = {renameKey.get(key, key): value for key, value in meta.items()} if meta is not None else None
        # print(f"{infotextDict=}")
        infotext = ""
        if 'Prompt' in infotextDict:
            infotext += infotextDict['Prompt'] + "\n"
        if 'Negative prompt' in infotextDict:
            infotext += "Negative prompt: " + infotextDict['Negative prompt']
        infotext += "\n"
        tmpList:list = []
        for key, value in infotextDict.items():
            if not key in ('Prompt','Negative prompt'):
                tmpList.append("{}:{}".format(key,value))
        infotext += ",".join(tmpList)
        return infotext

    def modelInfoHtml(self, modelInfo:dict, nsfwLevel:int=0) -> str:
        '''Generate HTML of model info'''
        samples = ""
        for pic in modelInfo["modelVersions"][0]["images"]:
            if self.matchLevel(pic['nsfwLevel'], nsfwLevel):
                nsfw = pic['nsfwLevel'] > 1 and not self.showNsfw
                infotext = self.meta2infotext(pic['meta']) if pic['meta'] is not None else ""
                metaHtml = self.meta2html(pic['meta']) if pic['meta'] is not None else ""
                template = environment.get_template("sampleImage.jinja")
                samples += template.render(
                    pic=pic,
                    nsfw=nsfw,
                    infotext=infotext,
                    metaHtml=metaHtml
                    )
        filesize = modelInfo["modelVersions"][0]["files"][0]["sizeKB"]
        # Get primary file size
        fileIndex = 0
        for i, file in enumerate(modelInfo["modelVersions"][0]["files"]):
            if "primary" in file:
                fileIndex = i

        # created = self.getCreatedDatetime().astimezone(
        #    tz.tzlocal()).replace(microsecond=0).isoformat()
        if self.getPublishedDatetime() is not None:
            published = self.getPublishedDatetime().astimezone(
                tz.tzlocal()).replace(microsecond=0).isoformat()
        else:
            published = ""
        # updated = self.getUpdatedDatetime().astimezone(
        #    tz.tzlocal()).replace(microsecond=0).isoformat()
        dictBasemodelColor = dictBasemodelColors(self.getBasemodelOptions())
        template = environment.get_template("modelbasicinfo.jinja")
        basicInfo = template.render(
            modelInfo=modelInfo,
            published=published,
            strNsfw=self.strNsfwLevel(modelInfo["nsfwLevel"]),
            strVNsfw=self.strNsfwLevel(modelInfo["modelVersions"][0]["nsfwLevel"]),
            fileIndex=fileIndex,
            dictBasemodelColor=dictBasemodelColor,
        )

        permissions = self.permissionsHtml(self.allows2permissions())
        # function:copy to clipboard
        js = (
            "<script>"
            "function civsfz_copyInnerText(node, send) {"
            "return navigator.clipboard.writeText(node.nextElementSibling.innerText)"
			".then(function () {"
					"alert('Copied ' + node.nextElementSibling.innerText);"
			"}).catch (function (error) {"
					"alert((error && error.message) || 'Failed to copy infotext');"
			"})}"
            "function civsfz_send2txt2img(text, send = false) {"
                "text = decodeURI(text);"
                "return navigator.clipboard.writeText(text)"
                ".then(function () {"
                    "alert('Copied: ' + text);"
                "}).catch(function (error) {"
                    "alert((error && error.message) || 'Failed to copy infotext');"
                "})"
            "}"
            "</script>"
        )
        template = environment.get_template("modelInfo.jinja")
        content = template.render(
            modelInfo=modelInfo, basicInfo=basicInfo, permissions=permissions,
            samples=samples, js=js)

        return content

    def permissionsHtml(self, premissions:dict, msgType:int=3) -> str:
        template = environment.get_template("permissions.jinja")
        content = template.render(premissions)
        return content

    # REST API
    def makeRequestQuery(self, content_type, sort_type, period, search_type, base_models=None, grChkboxShowNsfw=False, 
            grDrpdwnKeyword="",
            grDrpdwnUserName="",
            grDrpdwnTag="",
            grDrpdwnID="",
            grchkbxfav=""
        ):
        if grDrpdwnID is not None:
            grDrpdwnID = str.strip(grDrpdwnID)
        if "Model ID" in search_type or "Version ID" in search_type:
            if not grDrpdwnID.isdecimal():
                query = ""
                print_ly(f'"{grDrpdwnID}" is not a numerical value')
            else:
                query = str.strip(grDrpdwnID)
        elif "Hash" in search_type:
            try:
                int("0x" + grDrpdwnID, 16)
                isHex = True
            except ValueError:
                isHex = False
            if isHex:
                query = str.strip(grDrpdwnID)
            else:
                query = ""
                print_ly(f'"{grDrpdwnID}" is not a hexadecimal value')
        else:
            query = {'types': content_type, 'sort': sort_type,
                     'limit': opts.civsfz_number_of_cards, 'page': 1, 'nsfw': grChkboxShowNsfw}
            if not period == "AllTime":
                query |= {'period': period}   
            if "User name" in search_type:
                query |= {'username': grDrpdwnUserName }
            if "Tag" in search_type:
                query |= {'tag': grDrpdwnTag }
            if "Keyword" in search_type:
                query |= {"query": grDrpdwnKeyword}
                query.pop("page", None)  # Cannot use page param with query search
            if base_models:
                query |= {'baseModels': base_models }
            if grchkbxfav:
                query |= {"favorites": grchkbxfav}
        return query

    def updateQuery(self, url:str , addQuery:dict) -> str:
        parse = urllib.parse.urlparse(url)
        strQuery = parse.query
        dictQuery = urllib.parse.parse_qs(strQuery)
        query = dictQuery | addQuery
        newURL = parse._replace(query=urllib.parse.urlencode(query,  doseq=True, quote_via=urllib.parse.quote))
        return urllib.parse.urlunparse(newURL)

    def requestApi(self, url=None, query=None, timeout=read_timeout()):
        self.requestError = None
        hasFavorites = "favorites" in query if query else False
        if url is None:
            url = self.getModelsApiUrl()
        if query is not None:
            # Replace Boolean with a lowercase string True->true, False->false
            query = { k: str(v).lower() if isinstance(v, bool) else v
                     for k, v in query.items()}
            # print_lc(f'{query=}')
            query = urllib.parse.urlencode(query, doseq=True, quote_via=urllib.parse.quote)

        # Make a GET request to the API
        # cachePath = Path.joinpath(extensionFolder(), "../api_cache")
        # headers = {'Cache-Control': 'no-cache'} if cache else {}
        try:
            # with CachedSession(cache_name=cachePath.resolve(), expire_after=5*60) as session:
            browse = Browser()
            if hasFavorites:
                api_key=getattr(opts,"civsfz_api_key", None)
                if api_key is None:
                    print_ly(f"No API Key.")
                else:
                    browse.setAPIKey(api_key)
            response = browse.session.get(
                url, params=query, timeout=read_timeout()
            )
            # print_lc(f'{response.url=}')
            # print_lc(f'Page cache: {response.headers["CF-Cache-Status"]}')
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            # print(Fore.LIGHTYELLOW_EX + "Request error: " , e)
            # print(Style.RESET_ALL)
            print_ly(f"Request error: {e}")
            # print(f"{response=}")
            browse.reConnect()
            data = self.jsonData # No update data
            self.requestError = e
        else:
            # print_lc(f'{response.url=}')
            response.encoding  = "utf-8" # response.apparent_encoding
            data = json.loads(response.text)
            data['requestUrl'] = response.url
            data = self.patchResponse(data)
        return data

    def patchResponse(self, data:dict) -> dict:
        # make compatibility
        # if 'metadata' in data:
        # print_lc(f"{data['metadata']=}")
        # parse = urllib.parse.urlparse(data['metadata']['nextPage'])
        # strQuery = parse.query
        # dictQuery = urllib.parse.parse_qs(strQuery)
        # dictQuery.pop('cursor', None)
        # addQuery = { 'page': data['metadata']['currentPage']}
        # query = dictQuery | addQuery
        # currentURL = parse._replace(query=urllib.parse.urlencode(query,  doseq=True, quote_via=urllib.parse.quote))
        # data['metadata']['currentPageUrl'] = urllib.parse.urlunparse(currentURL)
        # if data['metadata']['currentPage'] == data['metadata']['pageSize']:
        #    data['metadata']['nextPage'] = None
        # if data['metadata']['currentPage'] < data['metadata']['pageSize']:
        #    addQuery ={ 'page': data['metadata']['currentPage'] + 1 }
        #    query = dictQuery | addQuery
        #    query.pop('cursor', None)
        #    nextPage = parse._replace(query=urllib.parse.urlencode(query,  doseq=True, quote_via=urllib.parse.quote))
        #    data['metadata']['nextPage'] = urllib.parse.urlunparse(nextPage)
        ##if data['metadata']['currentPage'] > 1:
        #    addQuery ={ 'page': data['metadata']['currentPage'] - 1 }
        #    query = dictQuery | addQuery
        #    query.pop('cursor', None)
        #    prevURL = parse._replace(query=urllib.parse.urlencode(query,  doseq=True, quote_via=urllib.parse.quote))
        #    data['metadata']['prevPage'] = prevURL

        return data

    def requestImagesByVersionId(self, versionId=None, limit=None):
        if versionId == None:
            return None
        params = {"modelVersionId": versionId,
                  "sort": "Oldest",
                  'nsfw': 'X'}
        if limit is not None:
            params |= {"limit": limit}
        return self.requestApi(self.getImagesApiUrl(), params, timeout=read_timeout())
    def requestVersionByVersionID(self, versionID=None):
        if versionID == None:
            return None
        url = self.getVersionsApiUrl(versionID)
        ret = self.requestApi(url, timeout=read_timeout())
        if self.requestError is not None:
            ret = None
        return ret
