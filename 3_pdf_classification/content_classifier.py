import csv
from tqdm import tqdm
import time
import types
import pickle
import os
import json
from more_itertools import unique_everseen
import tldextract
import fitz
import pytesseract
from PIL import Image
import requests
import io
import tabula

import re
from wordfreq import zipf_frequency

zipf_frequency_threshold = 1
cache_file = 'cache.pkl'

main_content_fn_dict = {
    'zh.ch': lambda d: d.find_elements(By.XPATH, "//main[@id='main']/div/div/div[.//div[contains(@class, 'mdl-feedback')]][1]/preceding-sibling::div[* and not(descendant::header)] | //main[@id='main']/div/div/div[.//div[contains(@class, 'contact')]][1]/preceding-sibling::div[* and not(descendant::header) and not(contains(@class, 'mdl-feedback'))]"),
    'zg.ch': lambda d: d.find_elements(By.XPATH, "//article[1]/section[(@id and @id!='kontakt') or contains(@class, 'news-detail')]"),
    'ur.ch': lambda d: d.find_elements(By.XPATH, "//section[contains(@class, 'main-content')][1]//div[contains(@class, 'content-inner')]//div[contains(@class, 'content-left') or contains(@class, 'content-right')]"),
    'tg.ch': lambda d: d.find_elements(By.XPATH, "//main[@id='content'] | //nav[@id='subnav'] | //nav[@id='mainnav']"),
    'sg.ch': lambda d: d.find_elements(By.XPATH, "//div[contains(@class, 'all-paragraph-container') or contains(@class, 'body-text')]"),
    'so.ch': lambda d: d.find_elements(By.XPATH, "//div[contains(@class, 'mainContent')] | //div[@id='SubNavigationCol']"),
    'sz.ch': lambda d: d.find_elements(By.XPATH, "//main[@id='main']//div[@class='main__content']"),
    'ow.ch': lambda d: d.find_elements(By.XPATH, "//div[@id='maincontent']//div[starts-with(@class, 'icms-') and not(ancestor::div[starts-with(@class, 'icms-')])]"),
    'nw.ch': lambda d: d.find_elements(By.XPATH, "//div[contains(@class, 'maincontent')]"),
    'lu.ch': lambda d: d.find_elements(By.XPATH, "//div[starts-with(@id, 'mymaincontent')] | //*[@id='mainNav']"),
    'gr.ch': lambda d: d.find_elements(By.XPATH, "//*[@id='MainContent'] | //*[@id='ctl00_panel4'] | //*[@id='PageContent']//div[contains(@class, 'main-content')]"),
    'gl.ch': lambda d: d.find_elements(By.XPATH, "(//*[@id='subnav'] | //main[@id='main']//div[@class='mod-wrapper'])"),
    'fr.ch': lambda d: d.find_elements(By.XPATH, "//div[contains(@class, 'article__content') or contains(@class, 'content-information-wrapper')]"),
    'be.ch': lambda d: d.find_elements(By.XPATH, "//div[@id='main']//*[@data-testid='left-column'] | //div[@id='main']//*[@data-testid='accordion' and not(ancestor::aside)]"),
    'bs.ch': lambda d: d.find_elements(By.XPATH, "//div[@id='main' and @role='main'] | //div[@id='nav-box' and @role='navigation'] | //div[@id='wrapper']"),
    # 'baselland.ch': lambda d: d.find_elements(By.XPATH, "//div[@id='content-core']"),
    'ai.ch': lambda d: d.find_elements(By.XPATH, "//div[@id='content-core']"),
    'ar.ch': lambda d: d.find_elements(By.XPATH, "//div[@id='mainColInner'] | //nav[@id='SubNavigation']"),
    'ag.ch': lambda d: d.find_elements(By.XPATH, "//div[contains(@class, 'pagesection__inner')]"),
}

def get_primary_domain(url):
    extracted = tldextract.extract(url)
    return f"{extracted.domain}.{extracted.suffix}"

def load_filtered_urls_from_csv(filename):
    with open(filename, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        urls = []
        rows = []
        for row in reader:
            if row['page_contains_software_guide'].startswith("Yes"):
                urls.append(row['page_link'])
                rows.append(row)
        return urls, rows

def create_cache(file_name, create_fn):
    # print(f'Creating cache <{file_name}>..')
    result = create_fn()
    with open(file_name, 'wb') as f:
        pickle.dump(result, f)
    return result

def load_cache(file_name):
    if os.path.isfile(file_name):
        # print(f'Loading cache <{file_name}>..')
        with open(file_name,'rb') as f:
            return pickle.load(f)
    return None

def load_or_create_cache(file_name, create_fn):
    result = load_cache(file_name)
    if result is None:
        result = create_cache(file_name, create_fn)
    return result

def get_cached_value(q, cache, fetch_fn, key_fn=lambda x:x, ignore_cache=False):
    key_q = key_fn(q)
    if not ignore_cache and key_q in cache:
        return cache[key_q], True
    v = fetch_fn(q)
    cache[key_q] = v
    return v, False

def detect_hyperlinks(doc):
    link_count = 0
    for page in doc:
        link_list = page.get_links()
        link_count += len(link_list)
    return link_count > 0  # Returns True if links are found

def detect_navigation_menu(driver):
    print('detect_navigation_menu')
    # Detecting navigation menus
    common_nav_classes = ['navbar', 'menu', 'navigation', 'nav-bar', 'top-nav']
    nav_class_elements = []
    for nav_class in common_nav_classes:
        if len(driver.find_elements(By.CSS_SELECTOR,f".{nav_class}")) > 0:
            return True
    elements = driver.find_elements(By.CSS_SELECTOR,"nav")
    elements = filter(is_visible_element, elements)
    if any(elements):
        return True
    return False

def count_words_in_page(doc):
    text = ""
    for page in doc:
        text += page.get_text()
    return len(text.split())

def detect_explanatory_images(doc):
    image_count = 0
    for page in doc:
        image_list = page.get_images(full=True)
        image_count += len(image_list)
    return image_count  # Returns True if images are found

def contains_ocr_text(page):
    """Use OCR to detect text in image-based PDF pages."""
    pix = page.get_pixmap()
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    text = pytesseract.image_to_string(img)
    return text.strip() != ""

def test_accessibility(doc):
    def non_selectable_text_pages():
        # Check for non-selectable text and images
        for page_num, page in enumerate(doc, start=1):
            # Check for text
            if page.get_text() == "":
                return True
        return False
    def images_with_text():
        for page_num, page in enumerate(doc, start=1):
            for img in page.get_images():
                if not img:
                    continue
                xref = img[0]
                base_image = doc.extract_image(xref)
                image = Image.open(io.BytesIO(base_image["image"]))
                text = pytesseract.image_to_string(image)
                if text.strip():
                    return True
        return False

    issues = 0
    if non_selectable_text_pages():
        issues += 1
    if images_with_text():
        issues += 1

    # Check for basic metadata (like title, author)
    metadata = doc.metadata
    if not metadata.get("title") or not metadata.get("author"):
        issues += 1

    return issues

# Find and return all tables on the page
def find_tables(file_stream):
    tables = tabula.read_pdf(file_stream, pages='all', multiple_tables=True)
    return len(tables)

# Find and return all lists/enumerations on the page
def find_lists(doc):
    print('find_lists')
    list_count = 0
    list_pattern = r'\n\d+\.\s|\n\*\s|\n-\s'  # Modify this pattern as needed
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        list_count += len(list(re.finditer(list_pattern, text)))
    return list_count

def find_text_elements(doc, keywords):
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        for keyword in keywords:
            if keyword in text:
                return True
    return False

def find_table_of_contents(doc):
    print('find_table_of_contents')
    return find_text_elements(doc, ["Inhaltsverzeichnis", "Zusammenfassung", "Gliederung", "Übersicht", "Inhalt"])

def find_faq_sections(doc):
    print('find_faq_sections')
    return find_text_elements(doc, ["FAQ", "Häufig gestellte Fragen"])

def find_glossaries(doc):
    print('find_glossaries')
    return find_text_elements(doc, ["Glossar"])

def find_introduction(doc):
    print('find_introduction')
    return find_text_elements(doc, ["Einführung", "Einleitung"])

def find_installation_instructions(doc):
    print('find_installation_instructions')
    return find_text_elements(doc, ["Windows", "macOS", "Linux", "Android", "iOS", "Anleitung zur Registrierung", "Installationsanleitung", "Registration", "Installation", "Registrierung"])

def detect_multilingual_support(doc):
    print('detect_multilingual_support')
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        if 'English' in text.lower():
            return True
    return False

def detect_jargon(doc):
    print('detect_jargon')
    jargon_words = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        # Tokenize the document into words
        document_words = map(lambda x:x.strip('*:,.?!;()[]|«»\'"&/\\+-'), text.lower().split())
        # Identify jargon words
        jargon_words += [
            word 
            for word in document_words 
            if word 
            and len(word) > 2 
            and zipf_frequency(word, 'de') <= zipf_frequency_threshold
            and not bool(re.search(r'\d', word))
            and not 'http' in word
            and not '.' in word
            and not '@' in word
        ]
    return len(set(jargon_words))

def get_number_of_pages(doc):
    return len(doc)

def detect_sections(doc):
    heading_count = 0
    total_text_size = 0
    text_count = 0

    for page in doc:
        # Extract text blocks and font information
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if b["type"] == 0:  # Text block
                for line in b["lines"]:
                    for span in line["spans"]:
                        # Accumulate text size for average calculation
                        total_text_size += span["size"]
                        text_count += 1

    # Calculate average text size
    if text_count == 0:
        return False  # Avoid division by zero
    average_text_size = total_text_size / text_count

    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if b["type"] == 0:
                for line in b["lines"]:
                    for span in line["spans"]:
                        # Check if the text is larger than average and bold
                        if span["size"] > average_text_size and "bold" in span["font"].lower():
                            heading_count += 1

    return heading_count > 1  # True if more than one heading is found


def analyze_pdf(url):
    primary_domain = get_primary_domain(url)
    if primary_domain not in main_content_fn_dict:
        return None
    
    # Download the PDF from the URL
    response = requests.get(url)
    if response.status_code != 200:
        return None  # Or handle the error as needed

    # Create a file-like object from the downloaded content
    file_stream = io.BytesIO(response.content)

    # Use fitz to open the file-like object
    doc = fitz.open(stream=file_stream, filetype="pdf")

    # Define the checks
    results = {
        'Main Content Elements': 1,
        'Search Function': False,
        'Images': detect_explanatory_images(doc),
        'Feedback Mechanisms': False,
        'Multilingual Support': detect_multilingual_support(doc),
        'Low-frequency Jargon': detect_jargon(doc),
        'number_of_pages': get_number_of_pages(doc),
        'Multimedia Elements': 0,
        'Hyperlinks': detect_hyperlinks(doc),
        'Navigation Menu': False,
        'Interactive Elements': 0,
        'Accessibility Issues': test_accessibility(doc), # do it as last thing
        'Content Length': count_words_in_page(doc),
        ##############
        'Instructions Divided into Sections': detect_sections(doc),
        'Tables': find_tables(file_stream),
        'Lists/Enumerations': find_lists(doc),
        'a Table of Contents': find_table_of_contents(doc),
        'a FAQ Section': find_faq_sections(doc),
        'a Glossary': find_glossaries(doc),
        'an Introduction Section': find_introduction(doc),
        'Installation Instructions': find_installation_instructions(doc),
    }
    results['an Instructive Example'] = results['Multimedia Elements']>0 or results['Images']>0
    print(url, json.dumps(results, indent=4))
    # Close the driver
    doc.close()
    return results

def print_iter_of_elements(it,s=''):
    it = map(lambda x: x.get_attribute('outerHTML').strip(), it)
    it = list(unique_everseen(it))
    print(s,len(it), json.dumps(it, indent=4))

def get_link_iter(csv_rows,url_list):
    for row,url in tqdm(zip(csv_rows,url_list),total=len(url_list)):
        link_iter = row['doc_links'].split('\n')
        link_iter = filter(lambda x: get_primary_domain(x)==get_primary_domain(url), link_iter)
        link_iter = filter(lambda x: '.pdf' in x.lower(), link_iter)
        link_iter = filter(lambda x: x not in url_list, link_iter)
        other_row = row.copy()
        other_row['page_is_software_guide'] = 'Yes'
        other_row['page_contains_software_guide'] = 'N/A'
        other_row['software_name_explanation'] = 'N/A'
        other_row['page_content'] = 'N/A'
        other_row['guide_format'] = 'PDF'
        other_row['doc_links'] = ''
        for u in link_iter:
            yield (other_row,u)

# Load URLs from the CSV file
csv_filename = '../1_guide_identification/corrected_guide_identification_analysis.csv'
url_list, csv_rows = load_filtered_urls_from_csv(csv_filename)

# Get results
_cache = load_or_create_cache(cache_file, lambda: {})
results = []
for row, url in get_link_iter(csv_rows,url_list):
    try:
        r, was_cached = get_cached_value(url, _cache, analyze_pdf)
        if not r:
            continue
        # else:
        #     primary_domain = get_primary_domain(u)
        #     response = requests.get(u)
        #     if response.status_code != 200:
        #         continue
        #     file_stream = io.BytesIO(response.content)
        #     doc = fitz.open(stream=file_stream, filetype="pdf")
        #     r['Instructions Divided into Sections'] = detect_sections(doc)
        #     r['a Table of Contents'] = find_table_of_contents(doc)
        #     r['a FAQ Section'] = find_faq_sections(doc)
        #     r['a Glossary'] = find_glossaries(doc)
        #     r['an Introduction Section'] = find_introduction(doc)
        #     r['Installation Instructions'] = find_installation_instructions(doc)
        #     r['Multilingual Support'] = detect_multilingual_support(doc)
        #     r['Low-frequency Jargon'] = detect_jargon(doc)
        #     r['Multimedia Elements'] = 0
        #     r['Tables'] = find_tables(file_stream)
        #     r['Lists/Enumerations'] = find_lists(doc)
        #     r['an Instructive Example'] = r['Multimedia Elements']>0 or r['Images']>0
        #     r['Feedback Mechanisms'] = False
        #     _cache[u] = r
        #     print(u, json.dumps(r, indent=4))
        if was_cached and r['Main Content Elements']==0:
            r, was_cached = get_cached_value(url, _cache, analyze_pdf, ignore_cache=True)
            if not r:
                continue
        if r['Main Content Elements']!=0:
            results.append((row,r,url))
        create_cache(cache_file, lambda: _cache)
    except Exception as x:
        print(x)
create_cache(cache_file, lambda: _cache)

print('Cantonal links analysed', len(results))

# Write results and original CSV data to a new CSV file
with open('automated_classification_results.csv', 'w', newline='') as file:
    writer = csv.writer(file)

    # Determine headers from the first row of the original CSV and the analysis results
    headers = list(results[0][0].keys()) + list(results[0][1].keys())
    # headers = ['page_link'] + list(results[0][1].keys())
    writer.writerow(headers)

    for original_data, result, url in unique_everseen(results, key=lambda x: x[-1]):
        d = original_data.copy()
        d['page_link'] = url
        row = list(d.values()) + list(result.values())
        # row = [url] + list(result.values())
        writer.writerow(row)
