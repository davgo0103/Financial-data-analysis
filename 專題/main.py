import plotly.express as px
import pandas as pd
import plotly.io as pio
import requests
import datetime
from bs4 import BeautifulSoup
from discord_webhook import DiscordWebhook
import schedule
import time
import sys
import os

################################## Config ##################################
line_token = '42CbyNEG6cR7rCAIVnZao0TxTNNsp1Ad54PWAmVBReO' #TOKEN   
dc_url = 'https://discord.com/api/webhooks/782196400003219456/l-sbfRV08zxjFpOAjC_WwfHxfc_-dNgsXGOwmsPBwWaU_EKVZOLcUfyiMPmv-Pp4R1VD' #Discord WebHook URL
SEND_TYPE = 'LINE' #訊息傳遞種類，可填 LINE、Discord、ALL 注意大小寫
DATE = "" #留空使用預設日期 格式:yyyymmdd
############################################################################

def leave():
    os.system("pause")
    sys.exit()


def main():

    url = "https://www.twse.com.tw/zh/exchangeReport/MI_INDEX"
    par = {
        "response": "html",
        "date": datetime_format,
        "type": "ALLBUT0999"
    }
    try:
        HTML_respinse = requests.post(url, par)
        if(HTML_respinse.status_code != 200):
            print("資料查詢失敗!")
            leave()
    except:
        print("資料查詢失敗!")
        leave()
    HTML = BeautifulSoup(HTML_respinse.text,features="html.parser")
    if(HTML.find("div").text == '\n    \n        很抱歉，沒有符合條件的資料!\n    \n'):
        print("沒有符合條件的資料!")
        leave()
    #price_HTML = HTML.find("table")

    for num in range(0,3):
        thead_list = []
        tbody_list = []
        price_HTML = HTML.find_all("table")[num]
        title = price_HTML.find("th").text
        thead_HTML = price_HTML.find("thead")
        tbody_HTML = price_HTML.find("tbody")

        tr = thead_HTML.find_all("tr")[1]
        for td in tr.find_all("td"):
            thead_list.append(td.text)

        tbody_all_row = tbody_HTML.find_all("tr")

        for i in tbody_all_row:
            row_list = []
            for td in i.find_all("td"):
                if(td.text != "--"):  #檢查資料是否為數值，不然無法產生圖片
                    row_list.append(td.text)
            tbody_list.append(row_list)
        
        shareprice_df = pd.DataFrame(data = tbody_list,columns=thead_list)
        for i in shareprice_df:
            shareprice_df['特殊處理註記'] = title

        shareprice_df.to_excel(f"{num}.xlsx")

    df0 = pd.read_excel('0.xlsx')
    df1 = pd.read_excel('1.xlsx')
    df2 = pd.read_excel('2.xlsx')
    #df3 = pd.read_excel('3.xlsx')
    #df4 = pd.read_excel('4.xlsx')
    #df5 = pd.read_excel('5.xlsx')

    df = pd.concat([df0,df1,df2], ignore_index=False)
    df.to_excel('merge.xlsx')

    df = pd.read_excel("./merge.xlsx")

    #開始繪圖
    fig = px.treemap(df,path=['指數'], 
                        values='漲跌百分比(%)',
                        color_continuous_scale='Geyser',
                        color='漲跌百分比(%)',
                        height = 4500,
                        width = 4500,)

    fig.update_traces(textposition='middle center',
                            textfont_size=68,
                            textinfo='label+text+value+percent parent'
                            )
    fig.data[0].texttemplate = "%{label}<br>%{value}%"

    pio.write_image(fig, 'img.png') #產生圖片
    message = new_dt.strftime("%Y-%m-%d") + " 指數漲跌" #訊息    

    
    if(SEND_TYPE == 'LINE' or SEND_TYPE == 'ALL'):
        #透過 LINE 發送圖片
        headers = { "Authorization": "Bearer " + line_token } 
        data = { 'message': message }

        image = open('img.png', 'rb')
        files = { 'imageFile': image }

        requests.post("https://notify-api.line.me/api/notify",headers = headers, data = data, files = files)
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " 已向 LINE 送出資料")

    if(SEND_TYPE == 'Discord' or SEND_TYPE == 'ALL'):
        #透過 Discord 發送圖片
        webhook = DiscordWebhook(url = dc_url , username = "下午茶配指數",content = message)
        with open("img.png", "rb") as f:
            webhook.add_file(file=f.read(), filename='img.png')

        response = webhook.execute()
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " 已向 Discord 送出資料")



def init():
    global datetime_format
    global DATE
    global new_dt
    if(DATE == "" and int(datetime.datetime.now().strftime("%H")) > 13):
        new_dt = datetime.date.today()
        datetime_format = new_dt.strftime("%Y%m%d")
    else:
        if(DATE == ""):
            time_del = datetime.timedelta(days=1)  #此部分不影響指定日期的code
            new_dt = datetime.date.today() - time_del
            datetime_format = new_dt.strftime("%Y%m%d")
        else:
            try:
                new_dt = datetime.datetime.strptime(DATE, "%Y%m%d")
                datetime_format = new_dt.strftime("%Y%m%d")
                print("檢測到指定的日期: " + new_dt.strftime("%Y-%m-%d"))
            except:
                print("日期格式錯誤")
                leave()


    if(int(new_dt.strftime("%w")) !=6 and int(new_dt.strftime("%w")) != 0):
        main()
    else:
        print('假日無資料')
        if(DATE != ""):
            leave()



# START
if(SEND_TYPE != 'Discord' and SEND_TYPE != 'LINE'):
    print("訊息傳遞種類錯誤")
    leave()
else:
    init()

schedule.every().day.at("14:00").do(init) #每日定時重複執行

while True:
    schedule.run_pending()
    time.sleep(1)
