
import json
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import quote


def get_json(url):
    """Fetch JSON from PyPI. Return None for HTTP 404 only."""
    try:
        with urlopen(url, timeout=10) as response:
            return json.load(response)
    except HTTPError as error:
        if error.code == 404:
            return None
        raise


def check_requirements(filename):
    with open(filename, "r", encoding="utf-8") as file:
        lines = [
            line.strip()
            for line in file
            if line.strip() and not line.strip().startswith("#")
        ]

    checked = len(lines)
    missing_packages = 0
    missing_versions = 0
    oldest = None

    for line in lines:
        if "==" not in line:
            continue

        name, version = map(str.strip, line.split("==", 1))

        # Quote package/version to make safe URLs.
        package = quote(name, safe="")
        pinned_version = quote(version, safe="")

        project_url = f"https://pypi.org/pypi/{package}/json"

        try:
            project_data = get_json(project_url)

            if project_data is None:
                missing_packages += 1
                continue

            release_url = (
                f"https://pypi.org/pypi/{package}/{pinned_version}/json"
            )
            release_data = get_json(release_url)

            if release_data is None:
                missing_versions += 1
                continue

            urls = release_data.get("urls", [])
            if not urls:
                continue

            # Use the first file listed under "urls".
            upload_time = urls[0].get("upload_time")
            if not upload_time:
                continue

            year = int(upload_time[:4])
            candidate = (year, name, version)

            if oldest is None or candidate[0] < oldest[0]:
                oldest = candidate

        except (URLError, TimeoutError, json.JSONDecodeError) as error:
            print(f"Could not check {name}=={version}: {error}")

    print(f"dependencies checked: {checked}")
    print(f"packages not on pypi: {missing_packages}")
    print(f"versions not on pypi: {missing_versions}")

    if oldest is not None:
        year, name, version = oldest
        print(f"oldest pinned release: {name}=={version}({year})")
    else:
        print("oldest pinned release: none")


if __name__ == "__main__":
    check_requirements("requirements.txt")