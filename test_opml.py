from app.group_registry import register, get_group_links
from app.opml_builder import rebuild_group_opml

# fake RSS links
rss1 = "https://example.com/apple-top.rss"
rss2 = "https://example.com/xiaomi-top.rss"

group = "tech"

# register two feeds
register(group, [rss1])
register(group, [rss2])

# rebuild OPML
path = rebuild_group_opml(group, get_group_links(group))

print("OPML created at:", path)
