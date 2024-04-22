from base64 import b64decode
from os.path import exists
from requests import get
from json import loads
from re import search
from tqdm import tqdm


def main():
    print("""Enter Vid_ID. ie. "?v=VswFqVUmq" without "?v="
Separate ID with comma ","
""")

    while True:
        vid_ID_list = input("Enter Vid_ID: ")
        if vid_ID_list:
            break

    vid_ID_list = [i.strip() for i in vid_ID_list.split(",")]

    error = []
    for vid_ID in vid_ID_list:
        try:
            abyss_cdn_url = f"https://abysscdn.com/?v={vid_ID}"
            abyss_cdn_text = get(abyss_cdn_url).text
            piece_length_json = loads(
                search(
                    r'({"pieceLength.*?})',
                    abyss_cdn_text,
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

            # "1" = 360p
            # "2" = 480p
            # "3" = 720p
            # "4" = 1080p
            max_quality = "4"  # Set max resolution for automatic selection
            manual = False  # Set "True" to select resolution manually

            quality = max([i for i in resolution_option if i <= max_quality])
            file_name = f"{vid_ID}_{resolution_option[quality]}.mp4"

            if manual:
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
                        break

            if exists(file_name):
                print(f"{file_name} already exists")
            else:
                atob_domain, atob_id = [
                    loads(
                        b64decode(
                            search(
                                r'PLAYER\(atob\("(.*?)"',
                                abyss_cdn_text,
                            ).group(1)
                        )
                    )[i]
                    for i in ["domain", "id"]
                ]

                print(f"Available resolution {available_resolution}")

                url = f"https://{atob_domain}/{quality_prefix[quality]}{atob_id}"
                headers = {"Referer": abyss_cdn_url}
                response = get(url, headers=headers, stream=True)

                with tqdm.wrapattr(
                    open(file_name, "wb"),
                    "write",
                    miniters=1,
                    desc=file_name,
                    total=int(response.headers.get("content-length", 0)),
                ) as f:
                    for chunk in response.iter_content(chunk_size=64 * 1024):
                        f.write(chunk)
        except Exception as err:
            error.append(err)

    for i in error:
        print(f"\nError downloading: {vid_ID}")
        print(i)


if __name__ == "__main__":
    main()
    input("\nPress Enter to exit\n")
