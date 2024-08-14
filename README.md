# [Info](https://github.com/PatrickL546/How-to-download-hydrax-abyss.to)

# [Userscript downloader](https://github.com/PatrickL546/Hydrax-Abyss.to-DownloadHelper-Userscript)

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

### Mode

- Turbo Mode Squared

![image](https://github.com/user-attachments/assets/f95c05cf-1721-4b48-8a4a-7b41b61d28e7)

- Turbo Mode

![image](https://github.com/user-attachments/assets/ba53d181-42cc-442b-91ba-f1cb122043bc)

- Automatic Mode

![image](https://github.com/user-attachments/assets/20a367b2-4808-4aed-8cc0-c495137144f0)

- Manual Mode

![image](https://github.com/user-attachments/assets/17950047-daa1-4d4d-82d2-2a0fb5a1719c)

## Customize

- Open `Hydrax-Abyss.to-DownloadHelper.py` in a text editor to change settings

```Python
# 1 = 360p
# 2 = 720p
# 3 = 1080p
max_quality = 3                       # Max resolution for automatic selection, or uses minimum available
automatic = True                      # Set "False" to select resolution manually
download_directory = r""              # Set download directory, insert path inside ""
request_timeout = 180                 # Seconds to wait between bytes before timeout
request_retry = 60                    # Retry attempts
request_wait = 6                      # Seconds to wait before retrying
error_file = "Abyss_error.log"        # File name of error log, insert name inside ""
enable_error_log = True               # Set "True" to enable error logging to file

turbo = True                          # Set "True" to multithread download
turbo_squared = False                 # Set "True" to download all Vid_ID at the same time
delete_fragment = True                # Set "True" to delete downloaded fragments
active_download = 10                  # Max active download connections
fragments_to_temp = True              # Set "False" to download fragments in `download_directory` instead of `%TEMP%`

split_by_bytes = True                 # Set "True" to split by bytes with size `turbo_chunk_size_bytes`
                                      # Set "False" to split by fragment files in amount of files `turbo_fragment`
turbo_chunk_size_bytes = 65536 * 128  # Size of each fragment in bytes
# Or
turbo_fragment = 60                   # Number of fragment files the video will get divided into
```
