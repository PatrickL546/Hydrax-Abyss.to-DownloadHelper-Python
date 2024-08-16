from base64 import b64decode
from concurrent.futures import ThreadPoolExecutor, wait
from json import loads
from os import makedirs, remove, system
from os.path import abspath, exists, expandvars, join
from re import search
from time import sleep

from requests import RequestException, Timeout, get
from STPyV8 import JSContext
from tqdm import tqdm

version = "v2.1"
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


def log_error(err):
    if enable_error_log:
        with open(error_file, "a", encoding="utf8") as f:
            f.write(f"{err}\n")


def get_turbo_download(vid_ID_text):
    try:
        (
            vid_ID,
            available_resolution,
            values,
            resolution_option,
            extension,
            download_path,
            piece_length,
            quality,
            file_name,
            atob_domain,
            quality_prefix,
            atob_ID,
        ) = get_data(vid_ID_text)

        download_url = f"https://{atob_domain}/{quality_prefix[quality]}{atob_ID}"
        if exists(download_path) and get_size(download_path) == int(
            piece_length[quality]
        ):
            print(f"\n{bcolors.OKGREEN}{file_name} already exists{bcolors.ENDC}\n")
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

            if fragments_to_temp:
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
                                    byte_range,
                                    download_url,
                                    fragment_download_path,
                                    write_method,
                                    fragment_file_name,
                                )
                            )
                        else:
                            downloaded_size = get_size(fragment_download_path)

                            if count + 1 == len(chunk_range):
                                if downloaded_size == last_chunk_size:
                                    print(
                                        f"\n{bcolors.OKGREEN}{fragment_file_name} already exists{bcolors.ENDC}\n"
                                    )
                                    continue
                            else:
                                if downloaded_size == chunk_size:
                                    print(
                                        f"\n{bcolors.OKGREEN}{fragment_file_name} already exists{bcolors.ENDC}\n"
                                    )
                                    continue

                            write_method = "wb"
                            futures.append(
                                pool.submit(
                                    start_download,
                                    vid_ID,
                                    available_resolution,
                                    byte_range,
                                    download_url,
                                    fragment_download_path,
                                    write_method,
                                    fragment_file_name,
                                )
                            )

                wait(futures)

                ok_fragment = 0
                for count, i in enumerate(fragment_list):
                    if count + 1 == len(fragment_list):
                        if get_size(i) == last_chunk_size:
                            ok_fragment += 1
                    else:
                        if get_size(i) == chunk_size:
                            ok_fragment += 1

                if ok_fragment != len(fragment_list):
                    print("\n" * 10)
                    print(
                        f"{bcolors.WARNING}Fragments not verified, retrying: {vid_ID}{bcolors.ENDC}"
                    )
                    print("\n" * 5)
                else:
                    print("\n" * 10)
                    print(f"{bcolors.OKGREEN}Verified, merging: {vid_ID}{bcolors.ENDC}")
                    print("\n" * 5)

                    try:
                        with open(download_path, "wb") as out_file:
                            for i in fragment_list:
                                with open(i, "rb") as in_file:
                                    out_file.write(in_file.read())

                    except Exception as err:
                        print(
                            error := f"""
{bcolors.WARNING}Failed to merge, retrying: {vid_ID} - get_turbo_download
{err}{bcolors.ENDC}
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
{bcolors.FAIL}Failed to delete: {i} - get_turbo_download
{err}{bcolors.ENDC}
"""
                                )
                                log_error(error)

                                with open(i, "wb"):
                                    pass

                                global failed_delete
                                failed_delete = True
                    break

    except Exception as err:
        print(
            error := f"""
{bcolors.FAIL}Error downloading: {vid_ID} - get_turbo_download
{err}{bcolors.ENDC}
"""
        )
        log_error(error)


def start_download(
    vid_ID,
    available_resolution,
    byte_range,
    download_url,
    download_path,
    write_method,
    file_name,
):
    try:
        if automatic and not turbo:
            print(f"\nAvailable resolution {vid_ID}: {available_resolution}")

        headers = {"Referer": "https://abysscdn.com/", "Range": f"bytes={byte_range}"}
        for i in range(request_retry):
            i += 1
            if i == request_retry:
                raise Exception(f"\n{bcolors.FAIL}Reached max retry{bcolors.ENDC}")

            try:
                r = get(
                    download_url, headers=headers, stream=True, timeout=request_timeout
                )

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
                    print(
                        f"\n{bcolors.WARNING}Retrying {i}/{request_retry}... {download_url}{bcolors.ENDC}\n"
                    )
                    sleep(request_wait)
                else:
                    break

            except Timeout as err:
                print(
                    error := f"""
{bcolors.WARNING}Connection timed out - start_download - {download_url} - {vid_ID}
{err}
Retrying {i}/{request_retry}... {download_url}{bcolors.ENDC}
"""
                )
                log_error(error)
                sleep(request_wait)
            except RequestException as err:
                print(
                    error := f"""
{bcolors.WARNING}Request exception - start_download - {download_url} - {vid_ID}
{err}
Retrying {i}/{request_retry}... {download_url}{bcolors.ENDC}
"""
                )
                log_error(error)
                sleep(request_wait)
    except Exception as err:
        print(
            error := f"""
{bcolors.FAIL}Error downloading: {vid_ID} - start_download
{err}{bcolors.ENDC}
"""
        )
        log_error(error)


def download(vid_ID_text):
    try:
        (
            vid_ID,
            available_resolution,
            values,
            resolution_option,
            extension,
            download_path,
            piece_length,
            quality,
            file_name,
            atob_domain,
            quality_prefix,
            atob_ID,
        ) = get_data(vid_ID_text)

        download_url = f"https://{atob_domain}/{quality_prefix[quality]}{atob_ID}"
        if not automatic:
            print(f"""
Downloading Vid_ID: {vid_ID}
Available resolution {available_resolution}
""")
            if "360p" in values:
                print("[1] 360p")
            if "720p" in values:
                print("[2] 720p")
            if "1080p" in values:
                print("[3] 1080p")

            while True:
                resolution_selected = input("Select option: ")

                if resolution_selected in resolution_option:
                    quality = resolution_selected
                    file_name = (
                        f"{vid_ID}_{resolution_option[quality]}.{extension[quality]}"
                    )
                    download_path = join(abspath(download_directory), file_name)
                    download_url = (
                        f"https://{atob_domain}/{quality_prefix[quality]}{atob_ID}"
                    )
                    break
                else:
                    print(f"{bcolors.WARNING}Select a valid option{bcolors.ENDC}")

        if not exists(download_path):
            byte_range = "0-"
            write_method = "wb"
            start_download(
                vid_ID,
                available_resolution,
                byte_range,
                download_url,
                download_path,
                write_method,
                file_name,
            )
        else:
            downloaded_size = get_size(download_path)
            if downloaded_size == int(piece_length[quality]):
                print(f"\n{bcolors.OKGREEN}{file_name} already exists{bcolors.ENDC}\n")
            else:
                byte_range = f"{downloaded_size}-"
                write_method = "ab"
                start_download(
                    vid_ID,
                    available_resolution,
                    byte_range,
                    download_url,
                    download_path,
                    write_method,
                    file_name,
                )

    except Exception as err:
        print(
            error := f"""
{bcolors.FAIL}Error downloading: {vid_ID} - download
{err}{bcolors.ENDC}
"""
        )
        log_error(error)


def get_vid_ID_text(vid_ID_list):
    print(f"\n{bcolors.BOLD}Getting Vid_ID text{bcolors.ENDC}\n")

    vid_ID_list_text = []
    for vid_ID in vid_ID_list:
        try:
            vid_ID_url = f"https://abysscdn.com/?v={vid_ID}"
            referer = "https://abyss.to/"
            attempted = False

            for i in range(request_retry):
                i += 1
                if i == request_retry:
                    raise Exception(
                        f"\n{bcolors.FAIL}Reached max retry{bcolors.ENDC}\n"
                    )

                try:
                    r = get(
                        vid_ID_url,
                        headers={"Referer": f"{referer}"},
                        timeout=request_timeout,
                    )

                    if r.status_code != 200:
                        print(
                            f"\n{bcolors.WARNING}Retrying {i}/{request_retry}... {vid_ID_url}{bcolors.ENDC}\n"
                        )
                        sleep(request_wait)
                    else:
                        encoded_re = r"(ﾟωﾟﾉ=.+?) \('_'\);"
                        atob_re = r"JSON\.parse\(atob\(\""
                        invalid_re = r"Invalid embedded domain name"

                        if not search(invalid_re, r.text) and search(atob_re, r.text):
                            vid_ID_list_text.append(r.text)
                            break
                        elif not search(invalid_re, r.text) and search(
                            encoded_re, r.text
                        ):
                            encoded = (
                                search(r"(ﾟωﾟﾉ=.+?) \('_'\);", r.text).group(1)
                                + ".toString()"
                            )

                            with JSContext() as ctxt:
                                decoded = ctxt.eval(encoded)

                            vid_ID_list_text.append(decoded)
                            break
                        elif search(invalid_re, r.text):
                            while True:
                                if attempted:
                                    print(
                                        f"{bcolors.WARNING}Failed. Make sure you are using the correct URL{bcolors.ENDC}"
                                    )

                                url = input(
                                    f"""Enter origin URL of "{vid_ID}", or enter "skip": """
                                )

                                if url == "skip":
                                    break

                                try:
                                    referer = search(
                                        r"(https?://[^/]+?)[:/]", url
                                    ).group(1)

                                    attempted = True
                                    break
                                except Exception:
                                    print(
                                        f"{bcolors.WARNING}Enter a valid URL, e.g. https://abyss.to/{bcolors.ENDC}"
                                    )

                                    attempted = False

                            if url == "skip":
                                break

                            print(
                                f"\n{bcolors.WARNING}Retrying {i}/{request_retry}... {vid_ID_url}{bcolors.ENDC}\n"
                            )
                        else:
                            print(
                                f"{bcolors.WARNING}Cannot get Vid_ID text - {vid_ID}{bcolors.ENDC}"
                            )

                except Timeout as err:
                    print(
                        error := f"""
{bcolors.WARNING}Connection timed out - get_vid_ID_text - {vid_ID_url} - {vid_ID}
{err}
Retrying {i}/{request_retry}... {vid_ID_url}{bcolors.ENDC}
"""
                    )
                    log_error(error)
                    sleep(request_wait)
                except RequestException as err:
                    print(
                        error := f"""
{bcolors.WARNING}Request exception - get_vid_ID_text - {vid_ID_url} - {vid_ID}
{err}
Retrying {i}/{request_retry}... {vid_ID_url}{bcolors.ENDC}
"""
                    )
                    log_error(error)
                    sleep(request_wait)

        except Exception as err:
            print(
                error := f"""
{bcolors.FAIL}Failed to get Vid_ID text: {vid_ID} - get_vid_ID_text
{err}{bcolors.ENDC}
"""
            )
            log_error(error)

    return vid_ID_list_text


def get_data(vid_ID_text):
    atob = search(
        r'atob\("(.+?)"\)',
        vid_ID_text,
    ).group(1)
    decoded_atob = b64decode(atob)
    json = loads(decoded_atob)
    values = str(json.values())

    sources = json["sources"]
    vid_ID = json["slug"]
    atob_ID = json["id"]
    atob_domain = json["domain"]

    print(f"\n{bcolors.BOLD}Getting content length: {vid_ID}{bcolors.ENDC}\n")

    resolution_option = {}
    quality_prefix = {}
    piece_length = {}
    extension = {}
    if "360p" in values:
        resolution_option.update({"1": "360p"})
        quality_prefix.update({"1": ""})
        piece_length.update({"1": get_content_length(atob_domain, "", atob_ID)})
        extension.update({"1": search(r"360p.+?type': '(.+?)'", str(sources)).group(1)})
    if "720p" in values:
        resolution_option.update({"2": "720p"})
        quality_prefix.update({"2": "www"})
        piece_length.update({"2": get_content_length(atob_domain, "www", atob_ID)})
        extension.update({"2": search(r"720p.+?type': '(.+?)'", str(sources)).group(1)})
    if "1080p" in values:
        resolution_option.update({"3": "1080p"})
        quality_prefix.update({"3": "whw"})
        piece_length.update({"3": get_content_length(atob_domain, "whw", atob_ID)})
        extension.update(
            {"3": search(r"1080p.+?type': '(.+?)'", str(sources)).group(1)}
        )

    available_resolution = ", ".join([i for i in resolution_option.values()])

    global max_quality
    if str(max_quality) not in ["1", "2", "3"]:
        print(
            f"""{bcolors.WARNING}Invalid max_quality: "{max_quality}", using "3"{bcolors.ENDC}"""
        )
        max_quality = 3

    try:
        quality = max([i for i in resolution_option if i <= str(max_quality)])
    except Exception:
        quality = min(resolution_option.keys())

    file_name = f"{vid_ID}_{resolution_option[quality]}.{extension[quality]}"
    download_path = join(abspath(download_directory), file_name)

    return (
        vid_ID,
        available_resolution,
        values,
        resolution_option,
        extension,
        download_path,
        piece_length,
        quality,
        file_name,
        atob_domain,
        quality_prefix,
        atob_ID,
    )


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


def get_content_length(atob_domain, quality_prefix, atob_ID):
    url = f"https://{atob_domain}/{quality_prefix}{atob_ID}"
    headers = {"Referer": "https://abysscdn.com/", "Range": "bytes=0-1"}
    for i in range(request_retry):
        i += 1
        if i == request_retry:
            raise Exception(f"\n{bcolors.FAIL}Reached max retry{bcolors.ENDC}")

        try:
            r = get(url, headers=headers, timeout=request_timeout)

            if r.status_code != 200 and r.status_code != 206:
                print(
                    f"\n{bcolors.WARNING}Retrying {i}/{request_retry}... {url}{bcolors.ENDC}\n"
                )
                sleep(request_wait)
            else:
                content_length = str(r.headers["Content-Range"]).split("/")[1]
                break

        except Timeout as err:
            print(
                error := f"""
{bcolors.WARNING}Connection timed out - get_content_length - {url}
{err}
Retrying {i}/{request_retry}... {url}{bcolors.ENDC}
"""
            )
            log_error(error)
            sleep(request_wait)
        except RequestException as err:
            print(
                error := f"""
{bcolors.WARNING}Request exception - get_content_length - {url}
{err}
Retrying {i}/{request_retry}... {url}{bcolors.ENDC}
"""
            )
            log_error(error)
            sleep(request_wait)

    return content_length


def get_size(file):
    with open(file, "rb") as f:
        size = f.read()

    return len(size)


def get_input():
    print(
        f"{bcolors.WARNING}If download slows down, try restarting the program{bcolors.ENDC}\n"
    )
    print("To download multiple videos at once, separate Vid_ID with space\n")

    while True:
        vid_ID_list = list(filter(None, input("Enter Vid_ID: ").split(" ")))
        if vid_ID_list:
            vid_ID_list = list(dict.fromkeys(vid_ID_list))
            return vid_ID_list


def turbo_download():
    if turbo_squared:
        print(f"{bcolors.FAIL}{bcolors.BOLD}[Turbo Mode Squared]{bcolors.ENDC}")
    else:
        print(f"{bcolors.OKGREEN}{bcolors.BOLD}[Turbo Mode]{bcolors.ENDC}")

    vid_ID_list = get_input()
    vid_ID_list_text = get_vid_ID_text(vid_ID_list)

    if not turbo_squared:
        for vid_ID_text in vid_ID_list_text:
            get_turbo_download(vid_ID_text)
    else:
        with ThreadPoolExecutor() as pool:
            pool.map(get_turbo_download, vid_ID_list_text)


def automatic_download():
    print(f"{bcolors.OKGREEN}{bcolors.BOLD}[Automatic Mode]{bcolors.ENDC}")

    vid_ID_list = get_input()
    vid_ID_list_text = get_vid_ID_text(vid_ID_list)

    with ThreadPoolExecutor() as pool:
        pool.map(download, vid_ID_list_text)


def manual_download():
    print(
        f"{bcolors.OKGREEN}{bcolors.BOLD}[Manual Mode]{bcolors.ENDC} {bcolors.WARNING}Simultaneous download not available{bcolors.ENDC}"
    )

    vid_ID_list = get_input()
    vid_ID_list_text = get_vid_ID_text(vid_ID_list)

    for vid_ID_text in vid_ID_list_text:
        download(vid_ID_text)


def version_check():
    try:
        r = get(
            "https://api.github.com/repos/PatrickL546/Hydrax-Abyss.to-DownloadHelper-Python/releases/latest",
            timeout=3,
        )

        online_version = r.json()["name"]
        new_version_link = r.json()["html_url"]

        if online_version > version:
            print(
                f"{bcolors.OKGREEN}New version available: {online_version}{bcolors.ENDC}"
            )
            print(f"{bcolors.UNDERLINE}{new_version_link}{bcolors.ENDC}")

    except Exception:
        print(f"{bcolors.FAIL}Failed to check for update{bcolors.ENDC}")


def main():
    system(f"title Hydrax-Abyss.to-DownloadHelper {version}")
    version_check()

    if turbo:
        turbo_download()
    elif automatic:
        automatic_download()
    else:
        manual_download()


if __name__ == "__main__":

    class bcolors:
        HEADER = "\033[95m"
        OKBLUE = "\033[94m"
        OKGREEN = "\033[92m"
        WARNING = "\033[93m"
        FAIL = "\033[91m"
        BOLD = "\033[1m"
        UNDERLINE = "\033[4m"
        ENDC = "\033[0m"

    failed_delete = False
    main()
    print("\n" * 5)

    if failed_delete and not fragments_to_temp:
        print(f"{bcolors.WARNING}Leftover fragments are safe to delete{bcolors.ENDC}")

    input("Done! press Enter to exit\n")
