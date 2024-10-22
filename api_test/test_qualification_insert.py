import requests


def test_qualification():
    url = 'http://127.0.0.1:8000/qualification_admin/3'
    headers = {'pass': '77f6abc7f5cc7c61d7dceed5d9a14b3d'}
    body_insert = {
        "type": "insert",
        "title": "GCSE",
        "subject": "math12",
        "countries": "United Kingdom,United States of America",
        "age": 15,
        "study_level": "KeyStage1",
        "var": "Foundation,Higher",
        "org": "Edexcel,AQA,OCR,CCEA,WJEC",
        "grade": "U"
    }
    req = requests.get(url=url, headers=headers)
    print(req.json())


test_qualification()

