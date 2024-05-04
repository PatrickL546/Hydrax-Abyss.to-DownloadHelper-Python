# About The Project

Simple Python program that lets you download Hydrax/Abyss.to videos

## Requirements

- Use my Userscript [Hydrax-Abyss.to-DownloadHelper](https://github.com/PatrickL546/Hydrax-Abyss.to-DownloadHelper) to easily get Vid_ID of the video

- Or read my [guide](https://github.com/PatrickL546/How-to-download-hydrax-abyss.to) on how to get the Vid_ID

- Install additional library listed in requirements.txt

## Usage

- Enter the Vid_ID of the video and that's it!

- Separate the Vid_ID with a comma "," to download multiple videos

![image](https://github.com/PatrickL546/Hydrax-Abyss.to-DownloadHelper-Python/assets/75874561/482e36df-afae-469f-b042-b55e58881279)

- Manual mode

![image](https://github.com/PatrickL546/Hydrax-Abyss.to-DownloadHelper-Python/assets/75874561/51da0d7c-a611-41ab-804c-33272fe55dc4)

## Customize

- You can open the program in a text editor and change these settings

```Python
# "1" = 360p
# "2" = 480p
# "3" = 720p
# "4" = 1080p
max_quality = "4"  # Set max resolution for automatic selection
manual = False  # Set "True" to select resolution manually
download_directory = r""  # Set download directory
```
