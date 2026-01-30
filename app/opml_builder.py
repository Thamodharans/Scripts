import os
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString

OPML_DIR = "opml_groups"
os.makedirs(OPML_DIR, exist_ok=True)

def rebuild_group_opml(group: str, rss_links: list):
    root = Element("opml", {"version": "1.0"})
    body = SubElement(root, "body")

    for link in rss_links:
        outline = SubElement(body, "outline")
        outline.set("type", "rss")
        outline.set("text", os.path.basename(link))
        outline.set("title", os.path.basename(link))
        outline.set("xmlUrl", link)

    pretty = parseString(tostring(root, "utf-8"))
    xml_bytes = pretty.toprettyxml(encoding="utf-8")

    path = os.path.join(OPML_DIR, f"{group}.opml")
    with open(path, "wb") as f:
        f.write(xml_bytes)

    return path
