import requests
import json
import pandas as pd
import asyncio
import aiohttp
from datetime import datetime
from tqdm import tqdm
import time

API_KEY = ""
SECRET_KEY = ""  

def get_access_token():
    """
    使用 AK，SK 生成鉴权签名（Access Token）
    :return: access_token，或是None(如果错误)
    """
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {"grant_type": "client_credentials", "client_id": API_KEY, "client_secret": SECRET_KEY}
    return str(requests.post(url, params=params).json().get("access_token"))

def data_type(text):
    data = {
        "messages": [
            {"role": "user", "content": text}
        ]
    }
    return data

if __name__ == '__main__':
    url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/ernie_speed?access_token=" + get_access_token()
    headers = {
        'Content-Type': 'application/json'
    }
    notes = []
    prompt0 = '你是中国电信的投诉处理人员，请使用最简洁的语言，对如下文本内容归纳出最最核心的意思，要求在20字以内:\n'
    chunks = []
    df = pd.read_csv('语料.csv',nrows=350)
    m = 0
    for m in tqdm(range(int(len(df)/300)+1)):
        t0 = datetime.now()
        for n in range(30):
            data_list = []
            chunk = df[m*300+n*10:m*300+n*10+10]
            for x in chunk['业务内容']:
                data_list.append(data_type(prompt0+x))

            async def fetch(session, url, headers, data):
                async with session.post(url, headers=headers, json=data) as response:
                    return await response.json()

            # 创建一个 aiohttp 会话
            async def re_post():
                async with aiohttp.ClientSession() as session:
                    # 创建一个任务列表
                    tasks = [fetch(session, url, headers, data) for data in data_list]
                    # print(tasks)
                    # 等待所有任务完成
                    results = await asyncio.gather(*tasks)
                    return results
            loop = asyncio.get_event_loop()
            results=loop.run_until_complete(re_post())

            for result in results:
                # print(result)
                result_text = result.get('result', '') if isinstance(result, dict) else ''
                notes.append(result_text)

            if 300*m+10*n+10<len(df):
                print(f'已完成{300*m+10*n+10}条记录')
        if m*300+300 < len(df):
            t1 = datetime.now()
            t = t1-t0
            if 60-int(t.seconds) >0:
                print('1分钟内已调用300次,请稍候')
                time.sleep(60-int(t.seconds))
    # print(notes)
    df['note'] = notes
    df.to_csv('data/1.csv',index=0)