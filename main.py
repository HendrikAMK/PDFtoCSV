import csv
import os
import re
from PyPDF2 import PdfReader


def skip_certain_lines(text, lines_to_skip):
    for line in lines_to_skip:
        text = text.replace(line, '')
    return text


def extract_name_and_address(text):
    lines = text.split('\n')
    an_line_index = next((i for i, line in enumerate(lines) if line.strip() == 'An'), None)
    if an_line_index is not None and len(lines) > an_line_index + 3:
        name = lines[an_line_index + 1].strip()
        address = lines[an_line_index + 2].strip()
        city = lines[an_line_index + 3].strip()
    else:
        name = ''
        address = ''
        city = ''
    return name, address, city


def extract_name_and_address_investbank(text):
    lines = text.split('\n')
    depot_line_index = next((i for i, line in enumerate(lines) if 'Depot' in line), None)
    if depot_line_index is not None and depot_line_index > 2:
        if 'Investbank' in lines[depot_line_index - 3]:
            name = lines[depot_line_index - 2].strip()
        else:
            name = lines[depot_line_index - 3].strip()
        address = lines[depot_line_index - 2].strip()
        city = lines[depot_line_index - 1].strip()
    else:
        name = ''
        address = ''
        city = ''
    return name, address, city


def extract_date(text):
    match = re.search(r'Datum:\s*(\d{2}\.\d{2}\.\d{4})', text)
    return match.group(1) if match else None


def extract_depot(text):
    match = re.search(r'Depot:\s*(\d+)', text)
    return match.group(1) if match else None


def extract_purchase_info(text):
    match = re.search(r'Kauf um (\d{2}:\d{2} Uhr), am (\d{2}\.\d{2}\.\d{4}) auf (\w+).', text)
    return match.groups() if match else (None, None, None)

def remove_text_after_word(directory, word):
    for filename in os.listdir(directory):
        if filename.endswith('.txt'):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r') as file:
                text = file.read()
            # Split the text at the word and keep only the part before the word
            text = text.split(word)[0]
            with open(filepath, 'w') as file:
                file.write(text)


def filter_purchases(text):
    pattern = r'(.+?)\s+(\d+)\s+([\d,.]+)\s+([\d,.]+)'
    matches = re.findall(pattern, text)
    extracted_data = []

    for match in matches:
        name, quantity, value, price = match
        value = float(re.sub(r'(\d)\.(\d)', r'\1\2', value).replace(',', '.'))
        if price != '':
            price = float(re.sub(r'(\d)\.(\d)', r'\1\2', price).replace(',', '.'))
        else:
            price = value * int(quantity)
        extracted_data.append((name.strip(), int(quantity), value, price))

    return extracted_data


def write_to_file(output_filepath, data, headers=None):
    with open(output_filepath, 'w', newline='') as output_file:
        writer = csv.writer(output_file)
        if headers:
            writer.writerow(headers)
            print(','.join(headers))  # print the headers
        for row in data:
            row[-2] = str(row[-2]) + '0 EURO'
            row[-1] = str(row[-1]) + '0 EURO'
            writer.writerow(row)
            print(','.join(map(str, row)))  # print the row


def read_from_file(input_filepath):
    with open(input_filepath, 'r') as input_file:
        return input_file.read()


def remove_text_from_files(directory, texts_to_remove):
    for filename in os.listdir(directory):
        if filename.endswith('.txt'):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r') as file:
                filedata = file.read()

            for text_to_remove in texts_to_remove:
                filedata = filedata.replace(text_to_remove, '')

            with open(filepath, 'w') as file:
                file.write(filedata)


def filter_street_name_investbank(street_name):
    street_name = street_name.partition("Datum:")[0].strip()
    return street_name


def extract_city_and_zip(text):
    lines = text.split('\n')
    city = ''
    zip_code = ''

    for line in lines:
        line = re.sub(r'Depot:\s*\d+\s*', '', line)
        match = re.search(r'(\d{5})\s+(.+)$', line)
        if match:
            zip_code = match.group(1).strip()
            city = match.group(2).strip()
            break

    return city, zip_code


def process_file(input_filepath, output_filepath):
    text = read_from_file(input_filepath)
    purchase_date, time, platform = extract_purchase_info(text)
    depot = extract_depot(text)
    skip_certain_lines(text, "Investbank AG")

    if 'Investbank' in input_filepath:
        name, address, city = extract_name_and_address_investbank(text)
        purchases = filter_purchases(text)
        address = filter_street_name_investbank(city)
        city, zip_code = extract_city_and_zip(text)
        city = zip_code + ' ' + city
        purchases = [[purchase_date, time, platform, depot, name, address, city] + list(purchase) for purchase in
                     purchases]
        headers = ["Zeit", "Datum", "Platform", "Depot-Nr.", "Käufer", "Anschrift-Käufer", "Stadt", "Wertpapier Name", "Anzahl", "Wert", "Preis"]
        write_to_file(output_filepath, purchases, headers)
    else:
        name, address, city = extract_name_and_address(text)
        purchases = filter_purchases(text)
        purchases = [[purchase_date, time, platform, depot, name, address, city] + list(purchase) for purchase in
                     purchases]
        headers = ["Zeit", "Datum", "Platform", "Depot-Nr.", "Käufer", "Anschrift-Käufer", "Stadt", "Wertpapier Name", "Anzahl", "Wert", "Preis"]
        write_to_file(output_filepath, purchases, headers)


ordner_pfad_in = 'txt-dump/in'
ordner_pfad_out = 'csv_dump'
pdf_ordner = 'pdfs'

for filename in os.listdir(pdf_ordner):
    if filename.endswith('.pdf'):
        pdf_dateipfad = os.path.join(pdf_ordner, filename)
        reader = PdfReader(pdf_dateipfad)
        if reader is not None and len(reader.pages) > 0:
            page = reader.pages[0]
            pdf_text = page.extract_text()

            input_dateipfad = os.path.join(ordner_pfad_in, f"{filename}.txt")
            with open(input_dateipfad, "w") as text_file:
                text_file.write(pdf_text)

        input_dateipfad = f'txt-dump/in/{filename}.txt'
        output_dateipfad = f'csv_dump/{filename}.csv'
        remove_text_from_files('txt-dump/in', texts_to_remove=[
            " | Investallee 33 | 32938 Investopedia",
            "Finance Free Capital",
            "Goldweg 13 Seite: 1 von 1",
            "45612 Frankfurt",
            "Tel.: 03571 - 96520",
            "Fax: 0351 - 965299",
            "info@ff-capital.com",
            "www.ff-capital.com",
            "Handelsrepublik GmbH & Co. KG",
            "Silberstraße 99",
            "45612 Frankfurt",
            "Tel.: 03151 - 89320",
            "Fax: 03151 - 893299",
            "info@handelsrepublik.de",
            "www.handelsrepublik.de",
            "Seite: 1 von 1"
        ])
        remove_text_after_word('txt-dump/in', 'Abrechnung')
        process_file(input_dateipfad, output_dateipfad)
