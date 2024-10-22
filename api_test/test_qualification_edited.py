import requests


def test_qualification():
    url = 'http://127.0.0.1:8000/qualification/'
    headers = {'pass': '77f6abc7f5cc7c61d7dceed5d9a14b3d'}
    body_insert = {
        "type": "edit",
        "id": 1,
        "title": "GCSE",
        "subject": "math1",
        "countries": "United Kingdom,United States of America",
        "age": 9,
        "study_level": "KeyStage1",
        "var": "Foundation,Higher",
        "org": "Edexcel,AQA,OCR,CCEA,WJEC",
        "grade": "U"
    }
    req = requests.post(url=url, headers=headers, json=body_insert)
    print(req.json())


test_qualification()
