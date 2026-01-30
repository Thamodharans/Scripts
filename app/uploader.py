from app.s3_uploader import upload_file

def upload_artifacts(artifacts: dict):
    links = {}
    for name, path in artifacts.items():
        links[name] = upload_file(path)
    return links
