import requests


def test_qualification():
    url = 'http://127.0.0.1:8000/qualification/'
    headers = {'pass': '77f6abc7f5cc7c61d7dceed5d9a14b3d'}
    body_insert = {
        "type": "delete",
        "id": 1
    }
    req = requests.post(url=url, headers=headers, json=body_insert)
    print(req.json())


test_qualification()
