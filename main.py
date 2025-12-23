from datetime import datetime 
import re
import json
import requests
from bs4 import BeautifulSoup

api_url = 'https://api.loe.lviv.ua/api/menus?page=1&type=photo-grafic'
time_pattern = r"\b([0-1][0-9]|2[0-3]):([0-5][0-9])\b"
time_format = "%H:%M"
selected_group = '4.2'

def main():
    def format_timedelta(td):
        total_seconds = int(td.total_seconds())
        if total_seconds < 0:
            sign = '-'
            total_seconds = abs(total_seconds)
        else:
            sign = ''

        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{sign}{hours:02}:{minutes:02}"
    req = requests.get(api_url)
    res_json = req.json()
    # print(json.dumps(res_json, ensure_ascii=False, indent=2))
    res_html = res_json["hydra:member"][0]["menuItems"][0]["rawHtml"]
    if not res_html:
        print("You will have electricity till rest of the day")
        return
    res_soup = BeautifulSoup(res_html, 'html.parser')
    res_paragraphs = res_soup.find_all('p')
    for i, p in enumerate(res_paragraphs):
        res_paragraphs[i] = p.get_text()
    res_paragraphs = res_paragraphs[2:]
    schedule = {}
    for i in res_paragraphs:
        group = i[6:9]
        body = i[11:-1]
        times = re.findall(time_pattern, body)
        formatted_times = [f"{h}:{m}" for h, m in times]
        for i, time in enumerate(formatted_times):
            formatted_times[i] = datetime.strptime(time, time_format)
        times_grouped = list(zip(formatted_times[::2], formatted_times[1::2]))
        schedule[group] = times_grouped
    now = datetime.now()
    current_hour = now.hour
    current_minute = now.minute
    current_second = now.second
    current_microsecond = now.microsecond
    current_time = datetime(1900, 1, 1, current_hour, current_minute, current_second, current_microsecond)
    has_light = True
    for pair in schedule[selected_group]:
        if pair[0] < current_time and pair[1] > current_time:
            has_light = False
            # return
    if has_light:
        before = True
        for pair in schedule[selected_group]:
            for time in pair:
                if time > current_time:
                    delta = time - current_time
                    delta = format_timedelta(delta)
                    print(f"PWR: OFF IN {delta}")
                    before = False
                    return
        if before:
            print("PWR: ON")
    if not has_light:
        for pair in schedule[selected_group]:
            if pair[0] < current_time and pair[1] > current_time:
                delta = pair[1] - current_time            
                delta = format_timedelta(delta)
                print(f"PWR: IN {delta}")
                return
    if not schedule[selected_group]:
        print("PWR: ON")
if __name__ == "__main__":
    main()
