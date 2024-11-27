import pathlib

import requests
import feedparser

ROOT_PATH = pathlib.Path(__file__).parent.parent

def download_mp3(url, save_path):
    """
    Downloads a single MP3 file from a given URL and saves it to the specified path.

    :param url: The URL of the MP3 file to download.
    :param save_path: The Path object where the MP3 file will be saved.
    """
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with save_path.open("wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        print(f"Downloaded {save_path}")
    else:
        print(f"Failed to download {url}")


def download_mp3_list(mp3_urls, save_directory):
    """
    Downloads a list of MP3 files from the provided URLs and saves them to the specified directory.

    :param mp3_urls: A list of URLs pointing to MP3 files.
    :param save_directory: The Path object representing the directory where MP3 files will be saved.
    """
    save_directory.mkdir(exist_ok=True)

    for url in mp3_urls:
        file_name = url.split("/")[-1]
        save_path = save_directory / file_name
        download_mp3(url, save_path)


def parse_rss_feed(rss_url):
    """
    Parses an RSS feed and extracts all MP3 links.

    :param rss_url: The URL of the RSS feed to parse.
    :return: A list of MP3 URLs extracted from the feed.
    """
    feed = feedparser.parse(rss_url)
    mp3_urls = []

    for entry in feed.entries:
        for link in entry.enclosures:
            if link.type == "audio/mpeg":
                mp3_urls.append(link.href)

    return mp3_urls


def main():
    """
    Main function to parse the RSS feed, extract MP3 links, and download the MP3 files.
    """
    rss = "https://lexfridman.com/feed/podcast/"
    mp3_urls = parse_rss_feed(rss)
    podcasts_dir = pathlib.Path("data/podcasts")
    download_mp3_list(mp3_urls, podcasts_dir)


if __name__ == "__main__":
    main()
