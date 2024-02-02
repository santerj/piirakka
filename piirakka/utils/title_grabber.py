import re

import requests

def plsParser(body: str) -> str:
    # quick and dirty solution - parse File1 with regex
    pattern = r'File1=(https?://\S+)'

    # Search for the pattern in the text
    match = re.search(pattern, body)

    # Check if a match was found
    if match:
        # Extract the link from the match
        link = match.group(1)
        return link
    else:
        return ""

def titleGrabber(url: str) -> str:
    BUFFER = 1024   # should be enough bytes to cover metablock

    r = requests.get(url, headers={"Icy-MetaData": "1"}, stream=True)
    
    if r.headers['Content-Type'] == "audio/x-scpls":
        # follow pls links
        link = plsParser(r.text)
        if link != "":
            return titleGrabber(link)  # warning - recursion
        else:
            return ""

    try:
        interval = int(r.headers['icy-metaint'])  # byte interval for metablock in stream
    except KeyError:
        raise RuntimeError("This is not good")
        return ""

    x = next(r.iter_content(interval + BUFFER), '')[interval:interval + BUFFER]
    r.close()   # don't keep stream open past BUFFER amt of bytes

    meta_length = x[0] * 16  # byte at position marked by icy-metaint contains length of metablock

    if meta_length > BUFFER:
        # metablock is longer than anticipated and not covered by buffer
        raise BufferError(f"Buffer length of { BUFFER } is too small for metablock")

    meta_start = 1  # acual metablock begins
    meta_end = meta_start + meta_length
    metadata = x[meta_start:meta_end].decode()

    # TODO: pattern breaks if song title contains '
    # should terminate at ; instead
    pattern = r"StreamTitle='(.*?)'"
    match = re.search(pattern, metadata)
    if match:
        # Extract the StreamTitle value from the match
        return match.group(1) + "\n"
    else:
        return ""
    