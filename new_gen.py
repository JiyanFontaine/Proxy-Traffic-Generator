import os
import requests
import concurrent.futures
import time
import re
from fake_headers import Headers
from queue import Queue


class RotatingProxyPool(Queue):
    def __init__(self, proxies):
        super().__init__()
        self.proxies = proxies
        self._fill_pool()

    def _fill_pool(self):
        for proxy in self.proxies:
            self.put(proxy)

    def get(self, *args, **kwargs):
        value = super().get(*args, **kwargs)
        self.put(value)
        return value


def grab_proxies():
    proxies = []
    websites = ["https://www.sslproxies.org/",
                "https://free-proxy-list.net/", "https://www.us-proxy.org/"]

    for url in websites:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                content = response.text
                pattern = re.compile(r'\d+\.\d+\.\d+\.\d+:\d+')
                matches = pattern.findall(content)
                for match in matches:
                    proxies.append(match)
            else:
                print(f"Error: Failed to retrieve proxies from {url}")
        except:
            print(f"Error: Failed to connect to {url}")

    return proxies


def test_proxy(proxy):
    try:
        response = requests.get(
            'https://httpbin.org/ip', proxies={"http": proxy, "https": proxy}, timeout=5)
        if response.status_code == 200:
            return proxy
        else:
            return None
    except:
        return None


def get_valid_proxies(proxies):
    valid_proxies = []

    if os.path.exists("proxies.txt"):
        with open("proxies.txt", "r") as f:
            valid_proxies = f.read().splitlines()
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = [executor.submit(test_proxy, proxy) for proxy in proxies]
            for future in concurrent.futures.as_completed(results):
                proxy = future.result()
                if proxy is not None:
                    valid_proxies.append(proxy)

            valid_proxies = [p for p in valid_proxies if requests.get(
                'https://httpbin.org/ip', proxies={"http": p, "https": p}, timeout=5).elapsed.total_seconds() * 1000 < 200]

            with open("proxies.txt", "w") as f:
                f.write("\n".join(valid_proxies))

    return valid_proxies


def get_urls_with_proxies(session, urls, num_processes, proxies):
    valid_proxies = get_valid_proxies(proxies)

    print(f"Using {len(valid_proxies)} valid proxies out of {len(proxies)}")

    with concurrent.futures.ProcessPoolExecutor(max_workers=num_processes) as executor:
        for proxy in valid_proxies:
            executor.submit(make_requests, session, urls, proxy)

        start_time = time.time()

        executor.shutdown(wait=True)

        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Finished {len(urls)} requests in {elapsed_time:.2f} seconds")


def make_requests(session, urls, proxy):
    session.proxies = {"http": proxy, "https": proxy}

    for url in urls:
        try:
            response = session.get(url, timeout=10)
            response.raise_for_status()
            print(f"Request to {url} using proxy {proxy} successful")
        except (requests.exceptions.RequestException):
            print(f"Request to {url} using proxy {proxy} failed")


def load_proxies_from_file(filename):
    if not os.path.exists(filename):
        return []
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip()]


def main():
    proxies = load_proxies_from_file("valid_proxies.txt")
    if not proxies:
        proxies = get_valid_proxies(load_proxies_from_file("proxies.txt"))

    urls = ["https://httpbin.org/ip"]

    with requests.Session() as session:
        for proxy in proxies:
            make_requests(session, urls, proxy)


if __name__ == '__main__':
    main()
