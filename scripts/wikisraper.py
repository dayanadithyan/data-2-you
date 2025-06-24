import requests
from bs4 import BeautifulSoup

def extract_subsection_descs():
    """
    Fetches and returns all text contents of divs with class 'subSectionDesc'
    """
    url = "https://steamcommunity.com/sharedfiles/filedetails/?id=123364976"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch page. Status code: {response.status_code}")

    soup = BeautifulSoup(response.text, "html.parser")
    # find all subsection description blocks
    subsections = soup.find_all("div", class_="subSectionDesc")
    if not subsections:
        raise RuntimeError("No elements with class 'subSectionDesc' found.")

    # clean each subsection and extract text
    texts = []
    for div in subsections:
        # remove any nested scripts or styles
        for tag in div(["script", "style"]):
            tag.decompose()
        text = div.get_text(separator="\n", strip=True)
        texts.append(text)

    return texts

if __name__ == "__main__":
    descs = extract_subsection_descs()
    output_file = "subsection_descs.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        for i, text in enumerate(descs, start=1):
            f.write(f"--- Subsection {i} ---\n")
            f.write(text + "\n\n")

    print(f"Extracted {len(descs)} subsection descriptions to '{output_file}'")
