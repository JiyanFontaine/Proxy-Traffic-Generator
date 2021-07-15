import os

try:
    import requests
    from fake_headers import Headers
except ImportError:
    try:
        if os.name == 'nt':
            os.system("pip install requests")
            os.system("pip install fake-headers")
        else:
            os.system("python3 -m pip install requests")
            os.system("python3 -m pip install fake-headers")
    except ImportError:
        print("Couldn't Import Modules")

urls = ["https://httpbin.org/ip", "https://nordvpn.com"]

headers = Headers(os="win", headers=True).generate()

with open("proxies.txt", "r") as proxies:
    for proxy in proxies:
        try:
            for url in urls:
                try:
                    r = requests.get(
                        url,
                        headers=headers,
                        proxies={"http://": proxy, "https://": proxy},
                        timeout=5,
                    )
                    print(f"trying proxy: {proxy} url: {url}")
                    print(r.status_code)
                except ConnectionError:
                    print("Connection Error")
                except Exception:
                    print("Error")
        except Exception:
            print("Error")
