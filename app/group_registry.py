from app.state_store import load_state, save_state

_state = load_state()

def register(group, rss_links):
    feeds = _state.setdefault(group, [])
    for link in rss_links:
        if link not in feeds:
            feeds.append(link)
    save_state(_state)

def get_group_links(group):
    return _state.get(group, [])
