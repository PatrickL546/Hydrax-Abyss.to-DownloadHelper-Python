from base64 import b64decode
from concurrent.futures import ThreadPoolExecutor
from json import loads
from os import system
from os.path import abspath, exists, join
from re import search
from requests import get
from tqdm import tqdm

version = "1.1"
# "1" = 360p
# "2" = 480p
# "3" = 720p
# "4" = 1080p
max_quality = "4"  # Set max resolution for automatic selection
automatic = True  # Set "False" to select resolution manually
download_directory = r""  # Set download directory


def download(vid_ID):
    try:
        vid_ID_url = f"https://abysscdn.com/?v={vid_ID}"
        vid_ID_text = get(vid_ID_url).text
        piece_length_json = loads(
            search(
                r'({"pieceLength.+?})',
                vid_ID_text,
            ).group(1)
        )

        resolution_option = {}
        quality_prefix = {}
        if "sd" in piece_length_json.keys():
            resolution_option.update({"1": "360p"})
            quality_prefix.update({"1": ""})
        if "mHd" in piece_length_json.keys():
            resolution_option.update({"2": "480p"})
            quality_prefix.update({"2": ""})
        if "hd" in piece_length_json.keys():
            resolution_option.update({"3": "720p"})
            quality_prefix.update({"3": "www"})
        if "fullHd" in piece_length_json.keys():
            resolution_option.update({"4": "1080p"})
            quality_prefix.update({"4": "whw"})

        available_resolution = [i for i in resolution_option.values()]

        quality = max([i for i in resolution_option if i <= max_quality])
        file_name = f"{vid_ID}_{resolution_option[quality]}.mp4"
        download_path = join(abspath(download_directory), file_name)

        if not automatic:
            print(f"""
Downloading Vid_ID: {vid_ID}
Available resolution {available_resolution}

[1] 360p
[2] 480p
[3] 720p
[4] 1080p
""")
            while True:
                resolution_selected = input("Select option: ")
                if resolution_selected in resolution_option:
                    quality = resolution_selected
                    file_name = f"{vid_ID}_{resolution_option[quality]}.mp4"
                    download_path = join(abspath(download_directory), file_name)
                    break

        if exists(download_path):
            print(f"{download_path} already exists")
        else:
            atob_domain, atob_id = [
                loads(
                    b64decode(
                        search(
                            r'PLAYER\(atob\("(.*?)"',
                            vid_ID_text,
                        ).group(1)
                    )
                )[i]
                for i in ["domain", "id"]
            ]

            print(f"Available resolution {vid_ID}: {available_resolution}")

            url = f"https://{atob_domain}/{quality_prefix[quality]}{atob_id}"
            headers = {"Referer": vid_ID_url}
            response = get(url, headers=headers, stream=True)

            with tqdm.wrapattr(
                open(download_path, "wb"),
                "write",
                miniters=1,
                desc=file_name,
                total=int(response.headers.get("content-length", 0)),
                unit_scale=True,
                unit_divisor=1024,
            ) as f:
                for chunk in response.iter_content(chunk_size=64 * 1024):
                    f.write(chunk)
    except Exception as err:
        print(f"\nError downloading: {vid_ID}\n{err}")


def get_input():
    print("""Enter Vid_ID. ie. "?v=VswFqVUmq" without "?v="
Separate ID with space
""")

    while True:
        vid_ID_list = list(filter(None, input("Enter Vid_ID: ").split(" ")))
        if vid_ID_list:
            return vid_ID_list


def automatic_download():
    print("[Automatic Mode]")

    vid_ID_list = get_input()

    with ThreadPoolExecutor() as pool:
        pool.map(download, vid_ID_list)


def manual_download():
    print("[Manual Mode] Simultaneous download not available")

    vid_ID_list = get_input()

    for vid_ID in vid_ID_list:
        download(vid_ID)


def main():
    system(f"title Hydrax-Abyss.to-DownloadHelper {version}")
    if automatic:
        automatic_download()
    else:
        manual_download()


if __name__ == "__main__":
    main()
    input("\nPress Enter to exit\n")
