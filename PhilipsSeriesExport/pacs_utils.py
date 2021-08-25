import requests

def check_frame_number_pacs(series_iuid):
    url = 'http://10.109.20.19:8080/dicom_num?series_iuid={}'.format(series_iuid)
    frameNum = requests.get(url).content.decode().strip()
    return frameNum
