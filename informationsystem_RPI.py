import tkinter as tk 
import requests
from bs4 import BeautifulSoup 
import instaloader      
from googleapiclient.discovery import build 
from datetime import datetime, timezone     
import psutil           
import speedtest       
import sys
import os
import imaplib      
import email
from email.header import decode_header

def get_unread_counts_and_last_message(email_address, password):

    def fetch_unread_count(folder_name):
        status, messages = obj.select(folder_name)
        if status == 'OK':
            status, response = obj.search(None, 'UNSEEN')
            if status == 'OK':
                unread_ids = response[0].split()
                unread_count = len(unread_ids)
                return unread_count, unread_ids
        return 0, []

    def fetch_last_unread_message_details():

        unread_count, unread_ids = fetch_unread_count('INBOX')
        if unread_ids:
         
            last_unread_id = unread_ids[-1]
            status, data = obj.fetch(last_unread_id, '(RFC822)')
            if status == 'OK':
                msg = email.message_from_bytes(data[0][1])
                subject, encoding = decode_header(msg['Subject'])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else 'utf-8')
                from_ = msg.get('From')
                return unread_count, subject, from_
        return 0, None, None

    obj = imaplib.IMAP4_SSL('imap.gmail.com', 993)
    obj.login(email_address, password)


    folders = {
        'INBOX': 'INBOX',
        'Kosz': '"[Gmail]/Kosz"',
        'Spam': '"[Gmail]/Spam"'
    }


    subtract_from_inbox = 3789
    result = ""

    for folder_display, folder_name in folders.items():
        try:
            unread_count, _ = fetch_unread_count(folder_name)
            
            if folder_display == 'INBOX':
                unread_count -= subtract_from_inbox

            result += f'Ilość nieprzeczytanych wiadomości w {folder_display}: {unread_count}\n'
        
        except imaplib.IMAP4.error as e:
            result += f'Błąd podczas wybierania folderu {folder_display}: {str(e)}\n'

    try:
        unread_count, subject, from_ = fetch_last_unread_message_details()
        if subject and from_:
            result += f'Ostatnia nieprzeczytana wiadomość w INBOX:\n'
            result += f'Tytuł: {subject}\n'
            result += f'Nadawca: {from_}\n'
        else:
            result += f'Brak nieprzeczytanych wiadomości w INBOX.\n'
    except imaplib.IMAP4.error as e:
        result += f'Błąd podczas sprawdzania wiadomości w INBOX: {str(e)}\n'
    obj.logout()
    return result
result_mail = get_unread_counts_and_last_message('email', 'api_key')


def kalendarz():
    API_KEY_kalendarz = 'calendar_api_key'
    result_kal = ''
    service = build('calendar', 'v3', developerKey=API_KEY_kalendarz)
    now1 = datetime.utcnow().isoformat() + 'Z'

    events_result = service.events().list(
        calendarId='email',
        timeMin=now1,
        maxResults=5,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    if not events:
        result_kal += 'Brak nadchodzących wydarzeń.'
    else:
        result_kal += 'Najbliższe wydarzenia:\n'
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            result_kal += f"{start}, {event['summary']}\n"
    return result_kal

result_string_kal = kalendarz()

def get_covid_summary_poland():
    try:
        response = requests.get('https://disease.sh/v3/covid-19/countries/Poland')
        response.raise_for_status() 
        poland_data = response.json()
        result = "COVID-19 podsumowanie dla Polski:\n"
        result += f"Nowe potwierdzone: {poland_data['todayCases']}\n"
        result += f"Wszystkie potwierdzone: {poland_data['cases']}\n"
        result += f"Nowe śmierci: {poland_data['todayDeaths']}\n"
        result += f"Wszystkie śmierci: {poland_data['deaths']}\n"
        return result

    except requests.exceptions.RequestException as e:
        return f"Wystąpił błąd podczas pobierania danych: {e}"

result_covid = get_covid_summary_poland()

def get_current_temperature(api_key, city_name):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}&units=metric"
    response = requests.get(url)
    data = response.json()
    if data['cod'] == 200:
        temperature = data['main']['temp']
        weather = data['weather'][0]['description']
        pressure = data['main']['pressure']
        humidity = data['main']['humidity']
        return weather, pressure, humidity, temperature
    else:
        return None

def pogoda():
    result = ''
    api_key = 'api_key'
    city_name = 'city'
    weather_data = get_current_temperature(api_key, city_name)
    if weather_data is not None:
        weather, pressure, humidity, temperature = weather_data
        result += f"Aktualna pogoda: {weather}\n"
        result += f"Ciśnienie atmosferyczne: {pressure} hPa\n"
        result += f"Wilgotność: {humidity}%\n"
        result += f"Aktualna temperatura: {temperature}°C\n"
    else:
        result += "Nie udało się pobrać danych o pogodzie."
    return result

result_string_pogoda = pogoda()

def get_post_info(username, post_index):
    try:
        loader = instaloader.Instaloader()
        profile = instaloader.Profile.from_username(loader.context, username)
        posts = profile.get_posts()
        
        post = None
        for _ in range(post_index + 1):  
            try:
                post = next(posts)
            except StopIteration:
                return "Nie ma wystarczającej liczby postów.\n"
        
        return {
            'likes': post.likes,
            'comments': post.comments,
            'views': post.video_view_count if post.is_video else None,
            'is_video': post.is_video
        }
    except Exception as e:
        return f"Wystąpił błąd podczas pobierania danych: {str(e)}\n"

def insta():
    result = ""
    konto = "insta_accountname"
    username = konto
    current_post_info = get_post_info(username, 0) 
    previous_post_info = get_post_info(username, 1)  

    if isinstance(current_post_info, dict) and isinstance(previous_post_info, dict):
        result += "Informacje o ostatnim poście:\n"
        result += f"Liczba polubień: {current_post_info['likes']}\n"
        result += f"Liczba komentarzy: {current_post_info['comments']}\n"
        if current_post_info['is_video']:
            result += f"Liczba wyświetleń: {current_post_info['views'] if current_post_info['views'] is not None else 0}\n"
        else:
            result += "Ten post nie jest wideo, więc nie widzimy liczby wyświetleń.\n"

        result += "\nInformacje o przedostatnim poście:\n"
        result += f"Liczba polubień: {previous_post_info['likes']}\n"
        result += f"Liczba komentarzy: {previous_post_info['comments']}\n"
        if previous_post_info['is_video']:
            result += f"Liczba wyświetleń: {previous_post_info['views'] if previous_post_info['views'] is not None else 0}\n"
        else:
            result += "Ten post nie jest wideo, więc nie widzimy liczby wyświetleń.\n"

        likes_difference = current_post_info['likes'] - previous_post_info['likes']
        try:
            likes_change_percentage = (likes_difference / previous_post_info['likes']) * 100
        except ZeroDivisionError: 
            likes_change_percentage = likes_difference * 100
        comments_difference = current_post_info['comments'] - previous_post_info['comments']
        try:
            comments_change_percentage = (comments_difference / previous_post_info['comments']) * 100
        except ZeroDivisionError: 
            comments_change_percentage = comments_difference * 100

        result += "\nPorównanie między postami:\n"
        result += f"Zmiana procentowa polubień: {likes_change_percentage:.1f}%\n"
        result += f"Zmiana procentowa komentarzy: {comments_change_percentage:.1f}%\n"

    else:
        result += "Nie udało się pobrać informacji o postach.\n"
    
    return result
result_string_insta = insta()



def pobierz_kursy_walut():
    url = 'https://api.nbp.pl/api/exchangerates/tables/A?format=json'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data[0]['rates']
    else:
        print(f"Błąd pobierania danych: {response.status_code}")
        return None

def pobierz_kurs_waluty(kursy_walut, waluta):
    for kurs in kursy_walut:
        if kurs['code'] == waluta:
            return kurs
    print(f"Brak danych o kursie waluty {waluta}.")
    return None

def pobierz_kursy_kryptowalut():
    url = 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin%2Cethereum%2Cripple&vs_currencies=pln'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Błąd pobierania danych: {response.status_code}")
        return None

def pobierz_kursy_walut():
    url = 'https://api.nbp.pl/api/exchangerates/tables/A?format=json'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data[0]['rates']
    else:
        return f"Błąd pobierania danych: {response.status_code}"

def pobierz_kurs_waluty(kursy_walut, waluta):
    for kurs in kursy_walut:
        if kurs['code'] == waluta:
            return kurs
    return f"Brak danych o kursie waluty {waluta}."

def pobierz_kursy_kryptowalut(): 
    url = 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin%2Cethereum%2Cripple&vs_currencies=pln'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return f"Błąd pobierania danych: {response.status_code}"

def gielda_USD():
    waluty = ['USD']#'USD', 'EUR', 'GBP', 'CHF', 'CZK'

    result = ""
    kursy_walut = pobierz_kursy_walut()
    if isinstance(kursy_walut, list):
        for waluta in waluty:
            kurs_wybranej_waluty = pobierz_kurs_waluty(kursy_walut, waluta)
            if isinstance(kurs_wybranej_waluty, dict):
                result += "------------------------\n"
                result += "Symbol: ($)\n"
                result += f"Skrót: {kurs_wybranej_waluty.get('code', 'Brak danych')}\n"
                result += f"Kurs: {float(kurs_wybranej_waluty.get('mid', 0.0)):.4f}\n"
                result += "------------------------\n"
            else:
                result += f"{kurs_wybranej_waluty}\n"
    else:
        result += f"{kursy_walut}\n"

    return result

def gielda_EUR():
    waluty = ['EUR']#'USD', 'EUR', 'GBP', 'CHF', 'CZK'

    result = ""
    kursy_walut = pobierz_kursy_walut()
    if isinstance(kursy_walut, list):
        for waluta in waluty:
            kurs_wybranej_waluty = pobierz_kurs_waluty(kursy_walut, waluta)
            if isinstance(kurs_wybranej_waluty, dict):
                result += "------------------------\n"
                result += "Symbol: (€)\n"
                result += f"Skrót: {kurs_wybranej_waluty.get('code', 'Brak danych')}\n"
                result += f"Kurs: {float(kurs_wybranej_waluty.get('mid', 0.0)):.4f}\n"
                result += "------------------------\n"
            else:
                result += f"{kurs_wybranej_waluty}\n"
    else:
        result += f"{kursy_walut}\n"

    return result

def gielda_GBP():
    waluty = ['GBP']#'USD', 'EUR', 'GBP', 'CHF', 'CZK'

    result = ""
    kursy_walut = pobierz_kursy_walut()
    if isinstance(kursy_walut, list):
        for waluta in waluty:
            kurs_wybranej_waluty = pobierz_kurs_waluty(kursy_walut, waluta)
            if isinstance(kurs_wybranej_waluty, dict):
                result += "------------------------\n"
                result += "Symbol: (£)\n"
                result += f"Skrót: {kurs_wybranej_waluty.get('code', 'Brak danych')}\n"
                result += f"Kurs: {float(kurs_wybranej_waluty.get('mid', 0.0)):.4f}\n"
                result += "------------------------\n"
            else:
                result += f"{kurs_wybranej_waluty}\n"
    else:
        result += f"{kursy_walut}\n"

    return result

def gielda_CHF():
    waluty = ['CHF']#'USD', 'EUR', 'GBP', 'CHF', 'CZK'

    result = ""
    kursy_walut = pobierz_kursy_walut()
    if isinstance(kursy_walut, list):
        for waluta in waluty:
            kurs_wybranej_waluty = pobierz_kurs_waluty(kursy_walut, waluta)
            if isinstance(kurs_wybranej_waluty, dict):
                result += "------------------------\n"
                result += "Symbol: (₣)\n"
                result += f"Skrót: {kurs_wybranej_waluty.get('code', 'Brak danych')}\n"
                result += f"Kurs: {float(kurs_wybranej_waluty.get('mid', 0.0)):.4f}\n"
                result += "------------------------\n"
            else:
                result += f"{kurs_wybranej_waluty}\n"
    else:
        result += f"{kursy_walut}\n"

    return result

def gielda_CZK():
    waluty = ['CZK']#'USD', 'EUR', 'GBP', 'CHF', 'CZK'

    result = ""
    kursy_walut = pobierz_kursy_walut()
    if isinstance(kursy_walut, list):
        for waluta in waluty:
            kurs_wybranej_waluty = pobierz_kurs_waluty(kursy_walut, waluta)
            if isinstance(kurs_wybranej_waluty, dict):
                result += "------------------------\n"
                result += "Symbol: (Kč)\n"
                result += f"Skrót: {kurs_wybranej_waluty.get('code', 'Brak danych')}\n"
                result += f"Kurs: {float(kurs_wybranej_waluty.get('mid', 0.0)):.4f}\n"
                result += "------------------------\n"
            else:
                result += f"{kurs_wybranej_waluty}\n"
    else:
        result += f"{kursy_walut}\n"

    return result

result_string_gielda_USD = gielda_USD()
result_string_gielda_EUR = gielda_EUR()
result_string_gielda_CZK = gielda_CZK()
result_string_gielda_CHF = gielda_CHF()
result_string_gielda_GBP = gielda_GBP()


def dowcipy():
    page_to_scrape = requests.get("https://piszsuchary.pl/losuj")
    soup = BeautifulSoup(page_to_scrape.text, "html.parser")
    zarty = soup.findAll("figcaption", attrs={"class":"image-description"})
    for zart in zarty:
        return zart.text
    
def is_raspberry_pi():
    try:
        with open('/proc/device-tree/model', 'r') as f:
            model_info = f.read().strip()
        return 'Raspberry Pi' in model_info
    except FileNotFoundError:
        return False

def get_system_info():
    if not is_raspberry_pi():
        raise EnvironmentError("This script is designed to run on a Raspberry Pi.")

    def get_hardware_info():

        model_info = os.popen('cat /proc/device-tree/model').read().strip()
        cpu_info = os.popen('cat /proc/cpuinfo').read()
        return model_info, cpu_info


    def get_cpu_usage():
        return psutil.cpu_percent(interval=1)


    def get_ram_usage():
        ram_info = psutil.virtual_memory()
        return ram_info.percent


    def get_cpu_temperature():
        temp = os.popen('vcgencmd measure_temp').read().strip()
        return temp.split('=')[1]  


    def get_power_status():
        status = os.popen('vcgencmd get_throttled').read().strip()
        return status


    def get_network_info():
        try:
            st = speedtest.Speedtest()
            st.get_best_server()
            download_speed = st.download() / 1_000_000  
            upload_speed = st.upload() / 1_000_000  
            network_status = "Polaczono"
            speeds = f"Predkosc pobierania: {download_speed:.2f} Mbps\nPrekosc przesylania: {upload_speed:.2f} Mbps"
        except Exception as e:
            network_status = "Nie ma polaczenia z internetem"
            speeds = str(e)
            
        return network_status, speeds
  
    model_info, cpu_info = get_hardware_info()
    cpu_usage = get_cpu_usage()
    ram_usage = get_ram_usage()
    cpu_temperature = get_cpu_temperature()
    power_status = get_power_status()
    network_status, network_speeds = get_network_info()

    result = f"Model Raspberry Pi: {model_info}\n"
    result += "Informacje o CPU:\n"
    result += f"{cpu_info}\n"
    result += f"Użycie CPU: {cpu_usage}%\n"
    result += f"Użycie RAM: {ram_usage}%\n"
    result += f"Temperatura CPU: {cpu_temperature}\n"
    result += f"Stan zasilania: {power_status}\n"
    result += f"Połączenie sieciowe: {network_status}\n"
    result += f"{network_speeds}\n"

    return result

def wysw_sys():
    try:
        print(get_system_info())
    except EnvironmentError as e:
        return f"Error: {e}"
        


from PIL import Image, ImageTk


class InteractiveMenu:
    def __init__(self, root):
        icon_image = Image.open("C:/Users/test/Pictures/watlogo.jpg")  
        icon_photo = ImageTk.PhotoImage(icon_image)
        root.iconphoto(True, icon_photo)
        self.root = root
        self.root.title("Mikroprocesorowy system informacyjny")
        self.root.geometry("400x300") 
        self.root.configure(bg="#FFD1D1")  
        root.grid_rowconfigure(0, weight=0)  
        root.grid_rowconfigure(1, weight=1)  
        root.grid_rowconfigure(2, weight=0)


       
        self.main_menu()

    def main_menu(self):
        self.clear_window()

        label = tk.Label(self.root, text="Główne Menu", bg="#FFD1D1")
        label.grid(row=0, column=0, columnspan=3, pady=20)  

        btn1 = tk.Button(self.root, text="Czujnik", command=self.sub_menu1, bg="#FF9494", fg="#FFE3E1", width=11, height=2)
        btn1.grid(row=1, column=0, padx=24, pady=15)

        btn2 = tk.Button(self.root, text="Gielda", command=self.show_gielda_menu, bg="#FF9494", fg="#FFE3E1", width=11, height=2)
        btn2.grid(row=1, column=1, padx=24, pady=15)

        btn3 = tk.Button(self.root, text="Poczta", command=self.sub_menu3, bg="#FF9494", fg="#FFE3E1", width=11, height=2)
        btn3.grid(row=1, column=2, padx=24, pady=15)

        btn4 = tk.Button(self.root, text="Kalendarz", command=self.sub_menu4, bg="#FF9494", fg="#FFE3E1", width=11, height=2)
        btn4.grid(row=2, column=0, padx=24, pady=15)

        btn5 = tk.Button(self.root, text="Pogoda", command=self.sub_menu5, bg="#FF9494", fg="#FFE3E1", width=11, height=2)
        btn5.grid(row=2, column=1, padx=24, pady=15)

        btn6 = tk.Button(self.root, text="Instagram", command=self.sub_menu6, bg="#FF9494", fg="#FFE3E1", width=11, height=2)
        btn6.grid(row=2, column=2, padx=24, pady=15)

        btn7 = tk.Button(self.root, text="Dowcip", command=self.sub_menu7, bg="#FF9494", fg="#FFE3E1", width=11, height=2)
        btn7.grid(row=3, column=1, padx=24, pady=15)

        btn8 = tk.Button(self.root, text="System", command=self.sub_menu2, bg="#FF9494", fg="#FFE3E1", width=11, height=2)
        btn8.grid(row=3, column=0, padx=24, pady=15)

        btn9 = tk.Button(self.root, text="Covid-19", command=self.sub_menu8, bg="#FF9494", fg="#FFE3E1", width=11, height=2)
        btn9.grid(row=3, column=2, padx=24, pady=15)

    def sub_menu1(self):
        self.show_sub_menu("Czujnik otoczenia", "")

    def sub_menu2(self):
        self.show_sub_menu("Informacje systemowe", wysw_sys())

    def sub_menu3(self):
        self.show_sub_menu("Skrzynka Pocztowa", result_mail)

    def sub_menu4(self):
        self.show_sub_menu("Kalendarz", result_string_kal)

    def sub_menu5(self):
        self.show_sub_menu("Informacje o pogodzie", result_string_pogoda)

    def sub_menu6(self):
        self.show_sub_menu("Statystyki konta instagramowego", result_string_insta)

    def sub_menu7(self):
        self.show_sub_menu("Dowcip", dowcipy())

    def sub_menu8(self):
        self.show_sub_menu("Covid-19 Statystyki", result_covid)

    def show_sub_menu(self, menu_title, info_text):
        self.clear_window()

        label = tk.Label(self.root, text=menu_title, bg="#FFD1D1")
        label.grid(row=0, column=2, pady=0, sticky="nsew")

        info = tk.Label(self.root, text=info_text, bg="#FFD1D1")
        info.grid(row=1, column=2, columnspan=4, pady=0, sticky="nsew")
        info.place(relx=0.5, rely=0.5, anchor="center")

        back_btn = tk.Button(self.root, text="Wróć", command=self.main_menu, bg="#FF9494", fg="#FFE3E1", width=9, height=2)
        back_btn.grid(sticky="ew")
        back_btn.place(relx=0.5, rely=0.9, anchor="center")



    def usd(self):
        self.info.config(text=result_string_gielda_USD)

    def chf(self):
        self.info.config(text=result_string_gielda_CHF)

    def czk(self):
        self.info.config(text=result_string_gielda_CZK)

    def gbp(self):
        self.info.config(text=result_string_gielda_GBP)

    def eur(self):
        self.info.config(text=result_string_gielda_EUR)

    def show_gielda_menu(self):
        

        self.clear_window()
        label = tk.Label(self.root, text="Giełda", bg="#FFD1D1")
        label.grid(row=0, column=2, pady=0, sticky="nsew")
        self.info = tk.Label(self.root, text="", bg="#FFD1D1")
        self.info.grid(row=1, column=2, pady=5)
        self.info.config(width=10)
        root.grid_rowconfigure(1, weight=1) 
        root.grid_columnconfigure(2, minsize=10)  
        

        USD_btn = tk.Button(self.root, text="Kurs USD", command=self.usd, bg="#FF9494", fg="#FFE3E1", width=9, height=2)
        USD_btn.grid(row=2, column=0, padx=5, pady=5, sticky="ew")


        EUR_btn = tk.Button(self.root, text="Kurs EUR", command=self.eur, bg="#FF9494", fg="#FFE3E1", width=9, height=2)
        EUR_btn.grid(row=2, column=1, padx=5, pady=5, sticky="ew")


        CHF_btn = tk.Button(self.root, text="Kurs CHF", command=self.chf, bg="#FF9494", fg="#FFE3E1", width=9, height=2)
        CHF_btn.grid(row=2, column=2, padx=5, pady=5)


        czk_btn = tk.Button(self.root, text="Kurs CZK", command=self.czk, bg="#FF9494", fg="#FFE3E1", width=9, height=2)
        czk_btn.grid(row=2, column=3, padx=5, pady=5, sticky="ew")


        GBP_btn = tk.Button(self.root, text="Kurs GBP", command=self.gbp, bg="#FF9494", fg="#FFE3E1", width=9, height=2)
        GBP_btn.grid(row=2, column=4, padx=5, pady=5, sticky="ew")

        back_btn = tk.Button(self.root, text="Wróć", command=self.main_menu, bg="#FF9494", fg="#FFE3E1", width=9, height=2)
        back_btn.grid(row=3, column=2, padx=5, pady=5)



    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = InteractiveMenu(root)
    root.mainloop()
