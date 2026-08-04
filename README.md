# sd-civitai-browser (CivBrowser)

An extension to help download models from CivitAi without leaving WebUI

## Modifications

<https://github.com/SignalFlagZ/sd-civitai-browser/assets/23202768/56f34586-94ea-40a9-b826-30ff20bf7bb3>

***If you fork, please replace prefix `civsfz` in file names, function names, css class names, etc. with your own prefix to avoid conflicts.***

## Features

- Works with ***A1111***, ***Forge***, ***SD.Next***, ***Forge Neo***(experimental)（above v2.3.5）
  - SD.Next is far away from A1111, so it may stop working eventually
- Search Civitai models in ***multiple tabs***
  - The scroll positions of each individual tab will be restored.
- Download ***queue*** and ***multithreaded*** downloads
- List models as ***card image***
- Safe display in ***sfw*** search
- Highlight models ***you have***
- Highlight models that ***can be updated***
- Searchable by specifying ***Base Models***
- Show ***Base Model*** on a model card
- Display/***save*** model information ***in HTML***
- ***Json data*** of model is also ***saved*** in the same folder as the model file
- If the sample image has meta data, display it with ***infotext compatibility***
- Click on the image to ***send to txt2img***
- Check downloaded model file with ***SHA256***
- ***Automatically*** set save folder, or specify it directly
- Card ***size and colors*** can be changed in Settings
- Support ***API Key***
- ~~Show the ***Early Access*** period of models~~
- Ban creators feature (Hide models by creator names)
- Favorite creators feature (Highlight the model with ⭐️)
- Stores metadata.
  - Create description and activation text from model information.
  - If metadata already exists, it will not be overwritten. Can be changed in settings.
- Proxy support (experimental >=v2.15).
  - Please be advised that your credentials are stored in plain text within the config.json file.
  - The proxy server is specified in `Settings` > `CivBrowser` > `Proxy`. If no value is provided, the `HTTP_PROXY` and `HTTPS_PROXY` environment variables are used instead.

## Installation

1. Launch SD-webUI.
2. Open tab `Extensions` on SD-webUI.
3. Open tab `Available`.
4. Click `Load from:` button.
5. Search `civbrowser`.
6. Click `install` button.
7. Wait for the installation to complete.
8. Open tab `Installed`.
9. Click `Apply and quit` button.
10. Restart SD-webUI.

## Versions

### v2.17

- Handle change in allowCommercialUse data type in API response (now a list).
- Update model permission display to match Civitai.

### v2.16

- Remove 'If the first image is of type "X", treat the model as nsfw' setting.
- Fixed an issue where sample image metadata would not appear.
  - Fetch sample image metadata from version ID API
- Verify query param updates by enums API

### v2.15

- Add HTTP error handling during download (experimental)
- Added proxy support! You can configure it in Settings. It's not fully debugged yet, though, so please let me know how it works for you!
- The proxy server is specified in `Settings` > `CivBrowser` > `Proxy`. If no value is provided, the `HTTP_PROXY` and `HTTPS_PROXY` environment variables are used instead.

### v2.14

- Changed the default URL to `civitai.green`.
  - You can change the URL in Settings.
- Error handling when some model information is missing.

### v2.13

- Add anchor links to navigate within a tab.

### v2.12

- Improved JavaScript for restoring scroll position
- Add “precision” to the display to differentiate identical file names.
  - File selection is done by index number to differentiate files.
  - The filename for saving checkpoints has changed a lot.
  - Display that matches PR #86.

### v2.11

- Add a version ID to the file name so it becomes a unique file name.
  - If a model with a file name lacking a version ID already exists, display “Have with no ID.”
- Added the ability to save and restore the scroll position of the tab, so switching tabs is now more convenient.

~~Current limitation: The script that saves the scroll position does not work unless you switch tabs and scroll once.~~ Resolved in v2.12.5

### v2.10

- Show the download status of the model in a separate tab.

### v2.9

- Add support for Forge Neo (experimental)
  - Video models are treated the same as SD models.
  - The compatibility with ComfyUI, such as unet and diffusion_models folders, is undecided.
  - Separate folders are required for gguf and safetensors, but this cannot be determined due to insufficient model information.

### v2.8

- Stores metadata.
  - Create description and activation text from model information.
  - If metadata already exists, it will not be overwritten. Can be changed in settings.
- You can now search using keywords, usernames, and tags at the same time.
- Searching for Favorites on Civitai.
- Some model information can now be collapsed and hidden. Works in modern browsers.

### v2.7

- Update of option acquisitions due to API response change.

#### v2.7.5

- Support for changing search response by model name. Pageneation is back.

#### v2.7.4

- The maximum number of cards per page when searching model names is now 100. There is no second page because the API response does not include pagination. This is a temporary change.

#### <v2.7.4

- Add timeout setting in Settings
- Set timeout to 30 seconds
- Add "OpenAI" to base models
- Add tooltips

### v2.6

- Fix error that would occur if there was a sample image in video format during ID search.
- Configured video model family in default settings
- Add NoobAI to the SDXL family in default settings
  - To reflect this setting, delete civsfz_color_family* line in the config.json file.
- Replace "__" in the file name with "_" to avoid conflicts when calling with wildcards
  - The presence of some already acquired models cannot be detected
- Displays a prompt to activate the model
  - The second and subsequent trigger words are treated as wildcards
  - Add Send to txt2img and Copy buttons
- Supports Detection type

### v2.5

- Works on reForge (Experimental. Is there demand?)
- Select the display of banned users using Browsing Level
- Indicates the base model of a model version by color
- Indicates the version you have already obtained by color
- Add User Management feature
  - Favorite creators are saved in file `favoriteUsers.txt`
  - Banned creators are saved in file `bannedUsers.txt`
- Add favorite creators in search term
- Add favorite creator feature
  - Display ⭐️ on card by creator name
- Add ban creators feature
  - Hide cards by creator name
- Fix not detected previous models

### v2.4

- Preview family colors in Settings
- The base model color settings have changed
  - You can set the color for each color family
  - You can register the base model to the family
  - Colors within a family will automatically change based on the family color
  - The color changes gradually according to the hls color wheel

### v2.3

- Add setting whether to delete file with different hash value
- Works on SD.Next (Hard to maintain)
- Command line option `--civsfz_api_key` is deprecated. Instead, use Settings.
- Refactoring Settings
- Updated to easily add new model background colors
  - The default color has been changed
- Refactor the base model background color logic
  - Changed variable names in Settings
  - If you have changed the background color, you will need to reconfigure it
- Change the layout of save buttons to reduce mouse movement
- Model name and base model are displayed in large size

### v2.2

- Add background color for Illustrious
- Add background color for SD3 and SD3.5
- Change the position of Back-to-Top button to reduce mouse movement
- Preload next page
- Reduce browser lag on Forge [#59](https://github.com/SignalFlagZ/sd-webui-civbrowser/issues/59)
- Save file name can be changed
- Works on Forge
  - ~~Hash mismatch occurs because calculate_sha256 has changed in Forge~~
- Support Early Access status key that changed to `availability` instead of `earlyAccessDeadline`
- Fix to support arrays of `Trained Tags` and display multiple `Trained Tags`

### v2.1

- Avoid filename length issues on Linux
  - The maximum length of a file/folder name is now 246 bytes (Number of bytes in UTF-8)
  - Previous model files with long names cannot be recognized as existing
  - This is just a display issue, and the models can still be used as before
- FYI
  - Windows
    - [https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation](https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation)
      - Maximum path length: 255 characters (<Windows 10, Version 1607)
    - [https://learn.microsoft.com/en-us/answers/questions/670083/get-childitem-the-specified-path-file-name-or-both](https://learn.microsoft.com/en-us/answers/questions/670083/get-childitem-the-specified-path-file-name-or-both)
      - Directory name length < 248 characters
  - Linux
    - [https://en.wikipedia.org/wiki/Ext4](https://en.wikipedia.org/wiki/Ext4)
      - Max filename length: 256 bytes (NOT CHARACTERS)

### v2.0

- Add background color to model information base model
- The background color of the Pony model can be specified

### v2.0β

- Add cancel download button to cue list
- Add open download folder button to cue list
- Removed the cancel button that was in the model information
- Removed `Save trained tagas` button and included it in `Save model info`

### v1.19β

- Sorted infotext to make it easier to read
- Display download results for a while
- Downloading with queue and multithreading
  - The number of threads is provisionally set to 2.
  - Download can be canceled
  - Show download queue
  - Show download progress

### v1.18

- Support hash value search
- DoRA models are saved in `models\Lora\_DoRA` (default)
- Fix permmissions
- Add DoRA folder
- Add history function for search conditions
  - Store and recall sorting, period, base model and sensitive conditions.
- Fix some models not be displayed
- Use Images API to get meta data
- Fix some settings could not be sent to txt2img
- Improved search term handling
- Suppots Browsing Level (Experimental)
- Temporarily avoid errors due to rating level changes
  - ~~Rating filters will be implemented in the future~~

### v1.17

- Supports API changes

### v1.17α

- Get cards using Session
- Stop using requests_cache
- ~~Use requests_cache for API request~~
- Jumping to previously viewed pages works
  - ~~Jumping to a page that has never been viewed does not work and an error occurs~~
  - Limit jump range
- PREV button works
- NEXT button works
- Temporarily avoid the error because the pagination of Civitai API has been changed
  - Pagination doesn't work
  - ~~ID search is not possible~~
  - Creation and update times are gone
  - Support for changed time notation for publishedAt

### v1.16

- Support for removing `earlyAccessTimeFrame` from Civitai API response and replacing it with `earlyAccessDeadline`.

### v1.15

- Subfolders under the type folder can now be set in Settings \([How to set it up](https://github.com/SignalFlagZ/sd-webui-civbrowser/wiki/How-to-set-up-subfolders-for-model-storage-%5Bv1.15.0-and-above%5D)\)

### v1.14

- Support search term history
  - Term history length is changeable in Settings
  - Term history is saved in `search_history.json` file
- Support search by Version ID
- Fix to use model-versions API to get meta data
- Add color frames to cards that can be updated
- Use jinja template engine

### v1.13

- Fix an issue where API responses changed and permissions could not be displayed correctly. #33
- Fix an issue where the version could not be selected correctly with multiple versions with the same name.
- Change info file format
- Change info file extension to json
- Change design of model information

### v1.12

- Check the match between image and infotext using image ID
- The meta key was missing from the API response, so retrieve it from the images API (Experimental)
  - Hide the infotext because it was displaying infotext different from the image (v1.12.1)

### v1.11

- Add search by model ID
- Change the default setting so that `/` is not treated as a folder separator.
- Get search choices from Civitai after launch and keep them up to date

### v1.10

- Cut file name length to 254 characters
- Show Early Access on card
  - The background color changes during and outside the period
- Show elapsed days on Early Access models
- Add model creation date/time, publication date/time, update date/time in HTML
- Add save folder setting \([How to set it up](https://github.com/SignalFlagZ/sd-webui-civbrowser/wiki/How-to-set-save-folders-by-type-%5Bv1.10.0-and-above%5D)\)
  - Specify path for each model type in JSON string

### v1.9

- Search for multiple model types at the same time
- Show model type on a card
- Changed model card design to display base model
  - Since there were many changes to Settings, it is recommended to delete prefix `civsfz` lines in config.json.
- Add filter for Base Models (experimental)
- ~~Show base model with background color of model name~~
- ~~Display base model in top frame color~~
  - Color can be changed in Settings
- Add an checkbox to the settings to specify whether to treat "/" as a folder separator (default:`True` for backward compatibility)
  - If you change it, some models may not be able to confirm the existence of the file.
- ~~Disable download button for Early Access models~~
  - Early access supporters may be able to download the model. Not tested.
- Rename files to avoid conflicts with other extensions
  - Why do python file conflicts occur? For example, api.py is used by many people and no problems occur.
- Add prefix `civsfz` to javascript function names to make them unique
- If you fork, please replace `civsfz` in file names, function names, css class names, etc. with your own prefix to avoid conflicts.

### v1.8

- Add sort types
- The model download timeout was set to 4 seconds because it was forcibly disconnected after about 5 seconds
- Support API Key
  - Some models require your API key when downloading
  - Models that fail to download may require an API key, but are indistinguishable from those that truly fail
  - API key is not saved for security reasons
  - Apply the API key using the command line option `--civsfz-api-key` or type directly into the text box
  - If there is no Content-Length in the request response, an API Key may be required.

### v1.7

- Add open folder button
- Make tab bar sticky
- Add content types `Upscaler`,`MotionModule`,`Wildcards`,`Workflows`,`Other` (experimental)
  - Save the newly added contenttype files to the `OtherModels` folder. Where should we save the files?
  - Unable to reach stability matrix models folder
- Change default period to `Month`
- Make navigation buttons sticky
- Show save buttons and back-to-top button sticky
- Add back-to-top button
- Rename elements class/id
- Change to unique name
- If the first image is of type `X`, treat the model as nsfw
  - Note that the save folder will change
- Move the file that failed to download to the trash
- Check the hash value of the downloaded file
- Model card size can be set in Settings
- Model card zooming size can be set in Settings
- Some colors of card can now be set in Settings
  - Settings will take effect on the next cards rendering
  - To return to default, search for `civsfz` from config.json and delete that line
- Stop using tkinter. It was causing a crash

### v1.7 beta3

- Fix a mistake when there are models with the same name
- Change model html styles

### v1.7 beta2

- The number of tabs can be changed in Settings
- The number of cards per page can now be changed
- Add Civitai Browser to Settings
- If there is no tkinter module, continue with limited functionality (experimental)
- Clicking on the image sends infotext to txt2img. If local, copy to clipboard
- Separately searchable in multiple tabs

### v1.7 beta

- Two tabs for separate searches (experimental)
  - Probably cannot download at the same time

### v1.6

- Support video type images (Temporarily because the video format is unknown)
- Display image meta data in Infotext-compatible format (can be expanded by pasting into a prompt)
- Click image to copy infotext

### v1.5

- Show download progress
- Add download cancel button
- Show Civitai response error
- File exists, overwrite and continue can be selected.

### v1.4

- Add page slider and jump button
- Rename tab `CivitAi` to `CivitAi Browser`

### v1.3

- Changed to index based model selection
- Add save folder textbox
- Add dropdown list of search period
- Highlighted if you already have the file

### v1.2.0

- NSFW models are saved in `.nsfw`
- Show permmisions in HTML -> [reference](https://github.com/civitai/civitai/blob/main/src/components/PermissionIndicator/PermissionIndicator.tsx#L15)
- Avoid collision when there are same model names
- Deprecate new folder checkbox and its function
- Change version selection from dropdown to radio button

### v1.1.0 and before

- Apply changes made by [thetrebor](https://github.com/thetrebor/sd-civitai-browser)
- Support LoRA
- Set folders from cmd_opts
- Save HTML with images
- Add Trained Tags in html
- Add meta data in html
- Copy first image as thumbnail
- Add thumbnail preview list
- Save model data as ".civitai.info"
- Support LoCon/LyCORIS
- Press the Download Model button again to cancel the download
- Add previous button
- Click on a thumbnail to select a model
- Add zoom effect to thumbnails
- Support ControlNet/Poses
- Support user and tag name search
- Implement page controls
- Support for `--lyco-dir`(To use the existing _LoCon folder, specify with `--lyco-dir`)
- Change the color of the frame of the card that has already been downloaded
- For base models other than SD1, save to a subfolder of the base model name
- Support `--lyco-dir-backcompat` modified in v1.5.1 of SD web UI
- Save to subfolder of base model name (e.g. `_SDXL_1_0` , `_Other`)
