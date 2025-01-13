import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from datetime import datetime

# URL target
url = "https://epg.pw/areas/id/epg.html?lang=en&timezone=QXNpYS9KYWthcnRh"

# Mengambil data dari URL
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

# Parsing data dari tabel
programs = []
channels = {}  # Menyimpan informasi channel
table = soup.find("table", class_="table is-bordered is-striped")
if table:
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) > 1:  # Setiap baris memiliki beberapa kolom
            channel_name = cells[0].text.strip()
            channel_id = channel_name.replace(" ", "")  # Channel id tanpa spasi
            for cell in cells[1:]:
                time_tag = cell.find("span", class_="tag is-primary")
                title = cell.get_text(strip=True).replace(time_tag.text.strip(), "") if time_tag else ""
                time = time_tag.text.strip() if time_tag else ""
                
                # Menambahkan tanggal jika waktu hanya berupa jam dan menit
                if time and len(time) == 5:  # Format waktu seperti HH:MM
                    time = f"2025-01-12 {time}"  # Tambahkan tanggal

                programs.append({
                    "channel": channel_name,
                    "channel_id": channel_id,
                    "time": time,
                    "title": title,
                })
                
                # Menyimpan informasi channel jika belum ada
                if channel_id not in channels:
                    channels[channel_id] = {
                        "display_name": channel_name,
                        "icon": ""  # Tambahkan URL ikon jika ada
                    }

# Membuat struktur XMLTV
tv = ET.Element("tv")

# Membuat elemen <channel> untuk setiap channel
for channel_id, channel_info in channels.items():
    channel = ET.SubElement(tv, "channel", id=channel_id)
    display_name = ET.SubElement(channel, "display-name")
    display_name.text = channel_info["display_name"]
    icon = ET.SubElement(channel, "icon", src=channel_info["icon"])
    
# Membuat elemen <programme> untuk setiap program
for i, program in enumerate(programs):
    # Menggunakan format waktu yang telah diperbarui (jika perlu)
    try:
        start_time = datetime.strptime(program["time"], "%Y-%m-%d %H:%M")
        start_str = start_time.strftime("%Y%m%d%H%M%S +0000")
    except ValueError:
        # Jika tidak ada tanggal di waktu
        start_str = f"20250112{program['time'].replace(':', '')}00 +0000"  # Asumsi tanggal default

    # Menentukan waktu stop untuk program berikutnya
    if i < len(programs) - 1:
        next_program = programs[i + 1]
        try:
            next_start_time = datetime.strptime(next_program["time"], "%Y-%m-%d %H:%M")
            stop_str = next_start_time.strftime("%Y%m%d%H%M%S +0000")
        except ValueError:
            stop_str = f"20250112{next_program['time'].replace(':', '')}00 +0000"
    else:
        # Jika ini adalah program terakhir, set waktu stop ke waktu yang sama
        stop_str = start_str

    programme = ET.SubElement(tv, "programme", start=start_str, stop=stop_str, channel=program["channel_id"])
    title = ET.SubElement(programme, "title", lang="en")
    title.text = program["title"]

# Menyimpan ke file XML dengan header XML
with open("epg.xml", "w", encoding="utf-8") as f:
    # Menulis header XML
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    f.write('<tv>\n')
    
    # Menulis elemen channel
    for programme in tv:
        if programme.tag == "channel":
            channel_id = programme.attrib["id"]
            display_name = programme.find("display-name").text
            icon_src = programme.find("icon").attrib.get("src", "")
            f.write(f'  <channel id="{channel_id}">\n')
            f.write(f'    <display-name>{display_name}</display-name>\n')
            f.write(f'    <icon src="{icon_src}"/>\n')
            f.write('  </channel>\n')
        elif programme.tag == "programme":
            # Menulis elemen programme
            start = programme.attrib["start"]
            stop = programme.attrib["stop"]
            channel = programme.attrib["channel"]
            title = programme.find("title").text
            f.write(f'  <programme start="{start}" stop="{stop}" channel="{channel}">\n')
            f.write(f'    <title lang="en">{title}</title>\n')
            f.write('  </programme>\n')

    # Menutup tag <tv>
    f.write('</tv>\n')

print("EPG berhasil disimpan ke epg.xml!")
