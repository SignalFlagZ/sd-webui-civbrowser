import gradio as gr
import math
import os
import re
import requests
from colorama import Fore, Back, Style
from collections import deque
from datetime import datetime, timedelta, timezone
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from threading import Thread, local
from time import sleep
from tqdm import tqdm
from scripts.civsfz_shared import opts, calculate_sha256, read_timeout, get_proxies
from scripts.civsfz_filemanage import (
    makedirs,
    removeFile,
    extensionFolder,
    open_folder,
    filename_normalization,
)

def print_ly(x): return print(Fore.LIGHTYELLOW_EX +
                              "CivBrowser: " + x + Style.RESET_ALL)
def print_lc(x): return print(Fore.LIGHTCYAN_EX +
                              "CivBrowser: " + x + Style.RESET_ALL)
def print_n(x): return print("CivBrowser: " + x)

class Downloader:
    _dlQ = deque()  # Download
    _threadQ = deque() # Downloading
    _ctrlQ = deque()  # control
    # _msgQ = deque()  # msg from worker
    _thread_local = local()
    _dlResults = deque() # Download results
    _maxThreadNum = 2
    _threadNum = 0

    def __init__(self) -> None:
        Downloader._thread_local.progress = 0

    def get_session(self) -> requests.Session:
        if not hasattr(Downloader._thread_local, 'session'):
            Downloader._thread_local.session = requests.Session()
        return Downloader._thread_local.session

    def add(self, folder, filename,  url, hash, api_key, early_access):
        filename = filename_normalization(filename)
        if Downloader._threadNum == 0:
            # Clear queue because garbage may remain due to errors that cannot be caught
            Downloader._threadQ.clear()
        path = Path(folder, filename)
        Downloader._ctrlQ.clear() # Clear cancel request
        if (not any(item['path'] == path  for item in Downloader._dlQ) 
            and not any(item['path'] == path for item in Downloader._threadQ)):
            Downloader._dlQ.append({"folder": folder,
                                "filename": filename,
                                "path": path,
                                "url": url,
                                "hash": hash,
                                "apiKey": api_key,
                                "EarlyAccess": early_access
                                })
            if Downloader._threadNum < Downloader._maxThreadNum:
                Downloader._threadNum += 1
                worker = Thread(target=self.download)
                worker.start()
        else:
            return "Already in queue"
        return f"Queue {len(Downloader._dlQ)}: Threads {Downloader._threadNum}"

    def sendCancel(self, path:Path):
        '''
            Cancel downloading by file path
        '''
        # path = Path(folder, filename)
        delete = None
        for dl in Downloader._dlQ:
            if path == dl["path"]:
                delete = dl
                break
        if delete is None:
            Downloader._ctrlQ.append({"control": "cancel", "path": path})
        else:
            Downloader._dlQ.remove(dl)
            print_lc(f"Canceled:{path}")
            return f"Canceled:{path}"

    def status(self):
        now = datetime.now(timezone.utc)
        # Discard past results
        expireQ = deque()
        remove = None
        deadline = 15 * 60
        for item in Downloader._dlResults:
            tdDiff = now - item['completedAt']
            secDiff = math.ceil(abs(tdDiff / timedelta(seconds=1)))
            item['expiration'] = secDiff / deadline
            if secDiff < deadline:
                expireQ.append(item)
            else:
                remove = item
        if remove is not None:
            Downloader._dlResults.remove(remove)

        templatesPath = Path.joinpath(
            extensionFolder(), Path("../templates"))
        environment = Environment(
            loader=FileSystemLoader(templatesPath.resolve()),
            extensions=["jinja2.ext.loopcontrols"],
        )
        template = environment.get_template("downloadQueue.jinja")
        content = template.render(
            threadQ=Downloader._threadQ, waitQ=Downloader._dlQ, resultQ=expireQ)
        return content

    def dlHtml(self):
        html = self.status()
        return html
    def uiDlList(self, gr:gr, every:float=None):
        grHtmlDlQueue = gr.HTML(elem_id=f"civsfz_download_queue", value=lambda: self.dlHtml(), every=every)
        return grHtmlDlQueue

    def uiJsEvent(self, gr: gr):
        # Cancel Download item
        grTxtJsEventDl = gr.Textbox(
            label="Event text",
            value=None,
            elem_id="civsfz_eventtext_dl",
            visible=False,
            interactive=True,
            lines=1,
        )
        def eventDl(grTxtJsEventDl):
            command = grTxtJsEventDl.split("??")
            if command[0].startswith("CancelDl"):
                path = Path(command[1])
                self.sendCancel(path)
                gr.Info(f"Cancel")
            elif command[0].startswith("OpenFolder"):
                path = Path(command[1])
                open_folder(path)
                gr.Info(f"Open folder")
            return

        grTxtJsEventDl.change(
            fn=eventDl,
            inputs=[grTxtJsEventDl],
            outputs=[],
        )

    def download(self) -> None:
        session = self.get_session()
        session.proxies, session.auth = get_proxies()
        result = "" # Success or Error
        while len(Downloader._dlQ) > 0:
            q = Downloader._dlQ.popleft()
            q['progress'] = 0 # add progress info
            Downloader._threadQ.append(q)  # for download list
            url = q["url"]
            folder = q["folder"]
            filename = q["filename"]
            hash = q["hash"]
            api_key = q["apiKey"]
            early_access = q["EarlyAccess"]
            #
            makedirs(folder)
            file_name = os.path.join(folder, filename)
            # Maximum number of retries
            max_retries = 3
            # Delay between retries (in seconds)
            retry_delay = 3

            downloaded_size = 0
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0'
            }
            applyAPI = False  # True if API key is added
            mode = "wb"  # Open file mode
            if os.path.exists(file_name):
                print_lc("Overwrite")

            # Split filename from included path
            tokens = re.split(re.escape('\\'), file_name)
            file_name_display = tokens[-1]
            cancel = False
            exitDownloading = False                
            while not exitDownloading:
                # Send a GET request to the URL and save the response to the local file
                try:
                    # Get the total size of the file
                    with session.get(
                        url,
                        headers=headers,
                        stream=True,
                        timeout=read_timeout(),
                    ) as response:
                        response.raise_for_status()
                        # print_lc(f"{response.headers=}")
                        if 'Content-Length' in response.headers:
                            total_size = int(
                                response.headers.get("Content-Length", 0))
                            # Update the total size of the progress bar if the `Content-Length` header is present
                            if total_size == 0:
                                total_size = downloaded_size
                            with tqdm(total=1000000000, unit="B", unit_scale=True, desc=f"Downloading {file_name_display}", initial=downloaded_size, leave=True) as progressConsole:
                                prg = 0  # downloaded_size
                                progressConsole.total = total_size
                                with open(file_name, mode) as file:
                                    for chunk in response.iter_content(chunk_size=1*1024*1024):
                                        if chunk:  # filter out keep-alive new chunks
                                            file.write(chunk)
                                            progressConsole.update(len(chunk))
                                            prg += len(chunk)
                                            # update progress
                                            i = Downloader._threadQ.index(q)
                                            q['progress'] = prg / total_size
                                            Downloader._threadQ[i] = q
                                        # cancel
                                        if len(Downloader._ctrlQ) > 0:
                                            ctrl = Downloader._ctrlQ[0]
                                            if ctrl["control"] == "cancel" and Path(folder, filename) == Path(ctrl["path"]) :
                                                Downloader._ctrlQ.popleft()
                                                exitDownloading = True
                                                cancel = True
                                                result = "Canceled"
                                                print_lc(
                                                    f"Canceled:{file_name_display}:")
                                                break
                            downloaded_size = os.path.getsize(file_name)
                            # Break out of the loop if the download is successful
                            break
                        else:
                            # if early_access and applyAPI:
                            #    print_ly(
                            #        f"{file_name_display}:Download canceled. Early Access!")
                            #    exitDownloading = True
                            #    result = "Early Access"
                            #    break
                            if not applyAPI:
                                print_lc("May need API key")
                                if len(api_key) == 32:
                                    headers.update(
                                        {"Authorization": f"Bearer {api_key}"})
                                    applyAPI = True
                                    print_lc(f"{file_name_display}:Apply API key")
                                else:
                                    exitDownloading = True
                                    result = "No API key"
                                    break
                            else:
                                exitDownloading = True
                                print_lc(
                                    f"{file_name_display}:Invalid API key or Early Access"
                                )
                                result = "Invalid API key or Early Access"
                                break
                except requests.exceptions.ProxyError as e:
                    print_ly("Proxy Error.")
                    result = "Proxy Error"
                except requests.exceptions.Timeout as e:
                    print_ly(f"{file_name_display}:{e}")
                    result = "Timeout"
                except ConnectionError as e:
                    print_ly(f"{file_name_display}:{e}")
                    result = "Connection Error"
                except requests.exceptions.RequestException as e:
                    print_ly(f"{file_name_display}:{e}")
                    result = "Request exception"
                except Exception as e:
                    print_ly(f"{file_name_display}:{e}")
                    result = "Exception"
                    exitDownloading = True
                # Decrement the number of retries
                max_retries -= 1
                # If there are no more retries, raise the exception
                if max_retries == 0:
                    exitDownloading = True
                    result += "(Max retry failure)"
                    break
                # Wait for the specified delay before retrying
                print_lc(f"{file_name_display}:Retry wait {retry_delay}s")
                sleep(retry_delay)

            if exitDownloading:
                if cancel:
                    print_lc(f'Canceled : {file_name_display}')
                    # gr.Warning(f"Canceled: {file_name_display}")
                if os.path.exists(file_name):
                    removeFile(file_name)                
            else:
                if os.path.exists(file_name):
                    # downloaded_size = os.path.getsize(file_name)
                    # Check if the download was successful
                    sha256 = calculate_sha256(file_name).upper()
                    print_lc(f'Downloaded hash : {sha256}')
                    if hash != "":
                        if sha256[:len(hash)] == hash.upper():
                            print_n(f"Save: {file_name_display}")
                            result = "Succeeded"
                            # gr.Info(f"Success: {file_name_display}")
                        else:
                            print_lc(f'Model file hash : {hash}')
                            print_ly(f"Hash mismatch. {file_name_display}")
                            # gr.Warning(f"Hash mismatch: {file_name_display}")
                            if opts.civsfz_discard_different_hash:
                                removeFile(file_name)
                            else:
                                print_ly("Not trashed due to your setting.")
                            result = "Hash mismatch"
                    else:
                        print_n(f"Save: {file_name_display}")
                        print_ly("No hash value provided. Unable to confirm file.")
                        result = "No hash value"
                        # gr.Info(f"No hash: {file_name_display}")
            # Downloader._dlQ.task_done()
            Downloader._threadQ.remove(q)
            q['result'] = result
            q['completedAt'] = datetime.now(timezone.utc)
            Downloader._dlResults.append(q)
        Downloader._threadNum -= 1
