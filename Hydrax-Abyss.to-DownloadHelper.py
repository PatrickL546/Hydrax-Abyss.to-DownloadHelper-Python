from base64 import b64decode
from concurrent.futures import ThreadPoolExecutor, wait
from json import loads
from os import makedirs, remove, system
from os.path import abspath, exists, expandvars, getsize, join
from re import search
from time import sleep

from requests import RequestException, Timeout, get
from tqdm import tqdm

version = "1.5"
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


def log_error(err):
    with open(error_file, "a") as f:
        f.write(f"{err}\n")


def get_turbo_download(vid_ID):
    try:
        vid_ID_url = f"https://abysscdn.com/?v={vid_ID}"

        for i in range(request_retry):
            i += 1
            if i == request_retry:
                raise Exception("\nReached max retry")

            try:
                r = get(vid_ID_url, timeout=request_timeout)

                if r.status_code != 200:
                    print(f"\nRetrying {i}/{request_retry}... {vid_ID_url}")
                    sleep(request_wait)
                else:
                    vid_ID_text = r.text
                    break

            except Timeout as err:
                print(
                    error := f"""
Connection timed out - get_turbo_download - {vid_ID_url} - {vid_ID}
{err}
Retrying {i}/{request_retry}... {vid_ID_url}
"""
                )
                log_error(error)
                sleep(request_wait)
            except RequestException as err:
                print(
                    error := f"""
Request exception - get_turbo_download - {vid_ID_url} - {vid_ID}
{err}
Retrying {i}/{request_retry}... {vid_ID_url}
"""
                )
                log_error(error)
                sleep(request_wait)

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

        piece_length_json = loads(
            search(
                r'({"pieceLength.+?});',
                vid_ID_text,
            ).group(1)
        )

        print(f"\nGetting content length: {vid_ID}")

        resolution_option = {}
        quality_prefix = {}
        piece_length = {}
        if "sd" in piece_length_json.keys():
            resolution_option.update({"1": "360p"})
            quality_prefix.update({"1": ""})
            piece_length.update({"1": get_content_length(atob_domain, "", atob_id)})
        if "mHd" in piece_length_json.keys():
            resolution_option.update({"2": "480p"})
            quality_prefix.update({"2": ""})
            piece_length.update({"2": get_content_length(atob_domain, "", atob_id)})
        if "hd" in piece_length_json.keys():
            resolution_option.update({"3": "720p"})
            quality_prefix.update({"3": "www"})
            piece_length.update({"3": get_content_length(atob_domain, "www", atob_id)})
        if "fullHd" in piece_length_json.keys():
            resolution_option.update({"4": "1080p"})
            quality_prefix.update({"4": "whw"})
            piece_length.update({"4": get_content_length(atob_domain, "whw", atob_id)})

        available_resolution = [i for i in resolution_option.values()]
        quality = max([i for i in resolution_option if i <= str(max_quality)])
        file_name = f"{vid_ID}_{resolution_option[quality]}.mp4"
        download_path = join(abspath(download_directory), file_name)

        if exists(download_path) and getsize(download_path) == int(
            piece_length[quality]
        ):
            print(f"\n{file_name} already exists")
        else:
            if split_by_bytes:
                chunk_range, chunk_size = generate_range_byte(
                    int(piece_length[quality]), turbo_chunk_size_bytes
                )
            else:
                chunk_range, chunk_size = generate_range_split(
                    int(piece_length[quality]), turbo_fragment
                )

            range_min, range_max = chunk_range[-1].split("-")
            last_chunk_size = (int(range_max) - int(range_min)) + 1

            makedirs(expandvars("%TEMP%\\abyss_fragments"), exist_ok=True)
            while True:
                with ThreadPoolExecutor(max_workers=active_download) as pool:
                    fragment_list = []
                    futures = []
                    for count, byte_range in enumerate(chunk_range):
                        fragment_file_name = f"{file_name}.abyss{count+1:04}"

                        if fragments_to_temp:
                            fragment_download_path = join(
                                expandvars("%TEMP%\\abyss_fragments"),
                                fragment_file_name,
                            )
                        else:
                            fragment_download_path = join(
                                download_directory,
                                fragment_file_name,
                            )

                        fragment_list.append(fragment_download_path)

                        if not exists(fragment_download_path):
                            write_method = "wb"
                            futures.append(
                                pool.submit(
                                    start_download,
                                    vid_ID,
                                    available_resolution,
                                    atob_domain,
                                    atob_id,
                                    quality_prefix,
                                    quality,
                                    fragment_download_path,
                                    fragment_file_name,
                                    byte_range,
                                    write_method,
                                )
                            )
                        else:
                            downloaded_size = getsize(fragment_download_path)

                            if count + 1 == len(chunk_range):
                                if downloaded_size == last_chunk_size:
                                    print(f"\n{fragment_file_name} already exists")
                                    continue
                            else:
                                if downloaded_size == chunk_size:
                                    print(f"\n{fragment_file_name} already exists")
                                    continue

                            write_method = "wb"
                            futures.append(
                                pool.submit(
                                    start_download,
                                    vid_ID,
                                    available_resolution,
                                    atob_domain,
                                    atob_id,
                                    quality_prefix,
                                    quality,
                                    fragment_download_path,
                                    fragment_file_name,
                                    byte_range,
                                    write_method,
                                )
                            )

                wait(futures)

                ok_fragment = 0
                for count, i in enumerate(fragment_list):
                    if count + 1 == len(fragment_list):
                        if getsize(i) == last_chunk_size:
                            ok_fragment += 1
                    else:
                        if getsize(i) == chunk_size:
                            ok_fragment += 1

                if ok_fragment != len(fragment_list):
                    print(f"\nFragments not verified, retrying: {vid_ID}")
                else:
                    print(f"\nVerified, merging: {vid_ID}")

                    try:
                        with open(download_path, "wb") as out_file:
                            for i in fragment_list:
                                with open(i, "rb") as in_file:
                                    out_file.write(in_file.read())

                    except Exception as err:
                        print(
                            error := f"""
Failed to merge, retrying: {vid_ID} - get_turbo_download
{err}
"""
                        )
                        log_error(error)

                    if delete_fragment:
                        for i in fragment_list:
                            try:
                                if exists(i):
                                    remove(i)

                            except Exception as err:
                                print(
                                    error := f"""
Failed to delete: {i} - get_turbo_download
{err}
                                    """
                                )
                                log_error(error)
                                with open(i, "wb"):
                                    pass

                    break

    except Exception as err:
        print(
            error := f"""
Error downloading: {vid_ID} - get_turbo_download
{err}
"""
        )
        log_error(error)


def start_download(
    vid_ID,
    available_resolution,
    atob_domain,
    atob_id,
    quality_prefix,
    quality,
    download_path,
    file_name,
    byte_range,
    write_method,
):
    try:
        if automatic and not turbo:
            print(f"Available resolution {vid_ID}: {available_resolution}")

        url = f"https://{atob_domain}/{quality_prefix[quality]}{atob_id}"
        headers = {"Referer": "https://abysscdn.com/", "Range": f"bytes={byte_range}"}
        for i in range(request_retry):
            i += 1
            if i == request_retry:
                raise Exception("\nReached max retry")

            try:
                r = get(url, headers=headers, stream=True, timeout=request_timeout)

                with tqdm.wrapattr(
                    open(download_path, write_method),
                    "write",
                    miniters=1,
                    desc=file_name,
                    total=int(r.headers.get("content-length", 0)),
                    unit_scale=True,
                    unit_divisor=1024,
                ) as f:
                    for chunk in r.iter_content(chunk_size=64 * 1024):
                        f.write(chunk)

                if r.status_code != 200 and r.status_code != 206:
                    print(f"\nRetrying {i}/{request_retry}... {url}")
                    sleep(request_wait)
                else:
                    break

            except Timeout as err:
                print(
                    error := f"""
Connection timed out - start_download - {url} - {vid_ID}
{err}
Retrying {i}/{request_retry}... {url}
"""
                )
                log_error(error)
                sleep(request_wait)
            except RequestException as err:
                print(
                    error := f"""
Request exception - start_download - {url} - {vid_ID}
{err}
Retrying {i}/{request_retry}... {url}
"""
                )
                log_error(error)
                sleep(request_wait)
    except Exception as err:
        print(
            error := f"""
Error downloading: {vid_ID} - start_download
{err}
"""
        )
        log_error(error)


def download(vid_ID):
    try:
        vid_ID_url = f"https://abysscdn.com/?v={vid_ID}"

        for i in range(request_retry):
            i += 1
            if i == request_retry:
                raise Exception("\nReached max retry")

            try:
                r = get(vid_ID_url, timeout=request_timeout)

                if r.status_code != 200:
                    print(f"\nRetrying {i}/{request_retry}... {vid_ID_url}")
                    sleep(request_wait)
                else:
                    vid_ID_text = r.text
                    break

            except Timeout as err:
                print(
                    error := f"""
Connection timed out - download - {vid_ID_url} - {vid_ID}
{err}
Retrying {i}/{request_retry}... {vid_ID_url}
"""
                )
                log_error(error)
                sleep(request_wait)
            except RequestException as err:
                print(
                    error := f"""
Request exception - download - {vid_ID_url} - {vid_ID}
{err}
Retrying {i}/{request_retry}... {vid_ID_url}
"""
                )
                log_error(error)
                sleep(request_wait)

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

        piece_length_json = loads(
            search(
                r'({"pieceLength.+?});',
                vid_ID_text,
            ).group(1)
        )

        print(f"\nGetting content length: {vid_ID}")

        resolution_option = {}
        quality_prefix = {}
        piece_length = {}
        if "sd" in piece_length_json.keys():
            resolution_option.update({"1": "360p"})
            quality_prefix.update({"1": ""})
            piece_length.update({"1": get_content_length(atob_domain, "", atob_id)})
        if "mHd" in piece_length_json.keys():
            resolution_option.update({"2": "480p"})
            quality_prefix.update({"2": ""})
            piece_length.update({"2": get_content_length(atob_domain, "", atob_id)})
        if "hd" in piece_length_json.keys():
            resolution_option.update({"3": "720p"})
            quality_prefix.update({"3": "www"})
            piece_length.update({"3": get_content_length(atob_domain, "www", atob_id)})
        if "fullHd" in piece_length_json.keys():
            resolution_option.update({"4": "1080p"})
            quality_prefix.update({"4": "whw"})
            piece_length.update({"4": get_content_length(atob_domain, "whw", atob_id)})

        available_resolution = [i for i in resolution_option.values()]
        quality = max([i for i in resolution_option if i <= str(max_quality)])
        file_name = f"{vid_ID}_{resolution_option[quality]}.mp4"
        download_path = join(abspath(download_directory), file_name)

        if not automatic:
            print(f"""
Downloading Vid_ID: {vid_ID}
Available resolution {available_resolution}
""")
            if "sd" in piece_length_json.keys():
                print("[1] 360p")
            if "mHd" in piece_length_json.keys():
                print("[2] 480p")
            if "hd" in piece_length_json.keys():
                print("[3] 720p")
            if "fullHd" in piece_length_json.keys():
                print("[4] 1080p")

            while True:
                resolution_selected = input("Select option: ")

                if resolution_selected in resolution_option:
                    quality = resolution_selected
                    file_name = f"{vid_ID}_{resolution_option[quality]}.mp4"
                    download_path = join(abspath(download_directory), file_name)
                    break
                else:
                    print("Select a valid option")

        if not exists(download_path):
            byte_range = "0-"
            write_method = "wb"
            start_download(
                vid_ID,
                available_resolution,
                atob_domain,
                atob_id,
                quality_prefix,
                quality,
                download_path,
                file_name,
                byte_range,
                write_method,
            )
        else:
            downloaded_size = getsize(download_path)
            if downloaded_size == int(piece_length[quality]):
                print(f"\n{file_name} already exists")
            else:
                byte_range = f"{downloaded_size}-"
                write_method = "ab"
                start_download(
                    vid_ID,
                    available_resolution,
                    atob_domain,
                    atob_id,
                    quality_prefix,
                    quality,
                    download_path,
                    file_name,
                    byte_range,
                    write_method,
                )

    except Exception as err:
        print(
            error := f"""
Error downloading: {vid_ID} - download
{err}
"""
        )
        log_error(error)


def generate_range_split(file_size, split):
    result_size = 0
    chunk_range = []
    chunk_size = file_size // split
    for i in range(split):
        min_val = i * chunk_size
        max_val = min_val + chunk_size - 1
        if i == split - 1:
            max_val = file_size - 1

        result_size += max_val - min_val + 1
        chunk_range.append(f"{min_val}-{max_val}")

    return chunk_range, chunk_size


def generate_range_byte(file_size, chunk_size):
    chunk_range = []
    for i in range(0, file_size, chunk_size):
        min_val = i
        max_val = min(i + chunk_size - 1, file_size - 1)
        chunk_range.append(f"{min_val}-{max_val}")

    return chunk_range, chunk_size


def get_content_length(atob_domain, quality_prefix, atob_id):
    url = f"https://{atob_domain}/{quality_prefix}{atob_id}"
    headers = {"Referer": "https://abysscdn.com/", "Range": "bytes=0-1"}
    for i in range(request_retry):
        i += 1
        if i == request_retry:
            raise Exception("\nReached max retry")

        try:
            r = get(url, headers=headers, timeout=request_timeout)

            if r.status_code != 200 and r.status_code != 206:
                print(f"\nRetrying {i}/{request_retry}... {url}")
                sleep(request_wait)
            else:
                content_length = str(r.headers["Content-Range"]).split("/")[1]
                break

        except Timeout as err:
            print(
                error := f"""
Connection timed out - get_content_length - {url}
{err}
Retrying {i}/{request_retry}... {url}
"""
            )
            log_error(error)
            sleep(request_wait)
        except RequestException as err:
            print(
                error := f"""
Request exception - get_content_length - {url}
{err}
Retrying {i}/{request_retry}... {url}
"""
            )
            log_error(error)
            sleep(request_wait)

    return content_length


def get_input():
    print("To download multiple videos at once, separate Vid_ID with space\n")

    while True:
        vid_ID_list = list(filter(None, input("Enter Vid_ID: ").split(" ")))
        if vid_ID_list:
            return vid_ID_list


def turbo_download():
    print("""[Turbo Mode] Multithreaded download
Abyss fragments by default are stored in "%TEMP%\\abyss_fragments"
If fragments failed to get deleted, its data is wiped to save space
Set `turbo_squared = False` if you are having problems
""")

    vid_ID_list = get_input()

    if not turbo_squared:
        for vid_ID in vid_ID_list:
            get_turbo_download(vid_ID)
    else:
        with ThreadPoolExecutor() as pool:
            pool.map(get_turbo_download, vid_ID_list)


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

    if turbo:
        turbo_download()
    else:
        if automatic:
            automatic_download()
        else:
            manual_download()


if __name__ == "__main__":
    main()
    print("\n" * 15)
    input("Press Enter to exit\n")
