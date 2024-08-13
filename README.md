# [Info](https://github.com/PatrickL546/How-to-download-hydrax-abyss.to)

# [Userscript downloader](https://github.com/PatrickL546/Hydrax-Abyss.to-DownloadHelper-Userscript)

> [!WARNING]  
> Outdated and broken due to new update

## Requirements

- Vid_ID of the video. Use my [Userscript](https://github.com/PatrickL546/Hydrax-Abyss.to-DownloadHelper-Userscript) or read [my guide](https://github.com/PatrickL546/How-to-download-hydrax-abyss.to) to get it

![image](https://github.com/user-attachments/assets/c4499f2f-6593-45af-8a1d-cf257347fc89)

- Windows 10 with latest updates

- Install additional library listed in `requirements.txt`

## Installation

- Download [Python](https://www.python.org/)

- Get the latest release [here](https://github.com/PatrickL546/Hydrax-Abyss.to-DownloadHelper-Python/releases/latest). Download `Source code` zip or tar.gz

- Extract the archive

- Install the requirements. [How to install requirements](https://packaging.python.org/en/latest/tutorials/installing-packages/#requirements-files)

- Run `Hydrax-Abyss.to-DownloadHelper.py`

## Usage

- Just enter the Vid_ID to download them all at once

- If the download was not completed. It will continue where it left off

- Turbo mode. Takes priority if enabled

![image](https://github.com/user-attachments/assets/4671400b-caaf-4264-8923-18ef3e643ffe)

- Automatic mode

![image](https://github.com/user-attachments/assets/b4eb4462-42ba-43da-8a5b-626c63c44bac)

- Manual mode

![image](https://github.com/user-attachments/assets/c5c73aba-3689-4178-82b0-5263f770c431)

## Customize

- Open `Hydrax-Abyss.to-DownloadHelper.py` in a text editor to change settings

```Python
# 1 = 360p
# 2 = 480p
# 3 = 720p
# 4 = 1080p
max_quality = 4                       # Max resolution for automatic selection
automatic = True                      # Set "False" to select resolution manually
download_directory = r""              # Set download directory, insert path inside ""
request_timeout = 180                 # Seconds to wait between bytes before timeout
request_retry = 60                    # Retry attempts
request_wait = 6                      # Seconds to wait before retrying
error_file = "Abyss_error.log"        # File name of error log
enable_error_log = True               # Enable error logging to file

turbo = False                         # Set "True" to multithread download, uses `max_quality` option
turbo_squared = False                 # Set "True" to download all Vid_ID at the same time
delete_fragment = True                # Set "False" to not delete downloaded fragments
active_download = 10                  # Max active download connections
fragments_to_temp = True              # Set "False" to download fragments in `download_directory`

split_by_bytes = True                 # Set "False" to split by fragment amount
                                      # If `split_by_bytes` is "True", fragment will be split by `turbo_chunk_size_bytes`
                                      # It will generate an arbitrary number of fragment files with file size `turbo_chunk_size_bytes`
                                      # Otherwise it will generate fixed number of fragment files `turbo_fragment`
                                      # Each fragment will have an arbitrary file size
turbo_chunk_size_bytes = 65536 * 128  # Size of each fragment in bytes
# Or
turbo_fragment = 60                   # Number of fragment files the video will get divided into
```
