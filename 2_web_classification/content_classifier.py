import csv
from tqdm import tqdm
import time
import types
import pickle
import os
import json
from more_itertools import unique_everseen
import tldextract

import re
from wordfreq import zipf_frequency

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from axe_selenium_python import Axe

chrome_options = Options()  
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920,1080")

cache_file = 'cache.pkl'
max_recursion_stage = 20
zipf_frequency_threshold = 1

main_content_fn_dict = {
    'zh.ch': lambda d,u: d.find_elements(By.XPATH, "//main[@id='main']/div/div/div[.//div[contains(@class, 'mdl-feedback')]][1]/preceding-sibling::div[* and not(descendant::header)] | //main[@id='main']/div/div/div[.//div[contains(@class, 'contact')]][1]/preceding-sibling::div[* and not(descendant::header) and not(contains(@class, 'mdl-feedback'))]") if 'maps.zh.ch' not in u else d.find_elements(By.XPATH, "//div[contains(@class, 'container-fluid')]"),
    'zg.ch': lambda d,u: d.find_elements(By.XPATH, "//article[1]/section[(@id and @id!='kontakt') or contains(@class, 'news-detail')]"),
    'ur.ch': lambda d,u: d.find_elements(By.XPATH, "//section[contains(@class, 'main-content')][1]//div[contains(@class, 'content-inner')]//div[contains(@class, 'content-left') or contains(@class, 'content-right')]"),
    'tg.ch': lambda d,u: d.find_elements(By.XPATH, "//main[@id='content'] | //nav[@id='subnav'] | //nav[@id='mainnav']") if 'map.geo.tg.ch' not in u else d.find_elements(By.XPATH, "//div[contains(@class, 'container')]"),
    'sg.ch': lambda d,u: d.find_elements(By.XPATH, "//div[contains(@class, 'all-paragraph-container') or contains(@class, 'body-text')]"),
    'so.ch': lambda d,u: d.find_elements(By.XPATH, "//div[contains(@class, 'mainContent')] | //div[@id='SubNavigationCol']"),
    'sz.ch': lambda d,u: d.find_elements(By.XPATH, "//main[@id='main']//div[@class='main__content']"),
    'ow.ch': lambda d,u: d.find_elements(By.XPATH, "//div[@id='maincontent']//div[starts-with(@class, 'icms-') and not(ancestor::div[starts-with(@class, 'icms-')])]"),
    'nw.ch': lambda d,u: d.find_elements(By.XPATH, "//div[contains(@class, 'maincontent')]"),
    'lu.ch': lambda d,u: d.find_elements(By.XPATH, "//div[starts-with(@id, 'mymaincontent')] | //div[starts-with(@id, 'mainContent')] | //*[@id='mainNav']"),
    'gr.ch': lambda d,u: d.find_elements(By.XPATH, "//*[@id='MainContent'] | //*[@id='ctl00_panel4'] | //*[@id='PageContent']//div[contains(@class, 'main-content')]"),
    'gl.ch': lambda d,u: d.find_elements(By.XPATH, "(//*[@id='subnav'] | //main[@id='main']//div[@class='mod-wrapper'])"),
    'fr.ch': lambda d,u: d.find_elements(By.XPATH, "//div[contains(@class, 'article__content') or contains(@class, 'content-information-wrapper')]"),
    'be.ch': lambda d,u: d.find_elements(By.XPATH, "//div[@id='main']//*[@data-testid='left-column'] | //div[@id='main']//*[@data-testid='accordion' and not(ancestor::aside)]"),
    'bs.ch': lambda d,u: d.find_elements(By.XPATH, "//div[@id='main' and @role='main'] | //div[@id='nav-box' and @role='navigation'] | //div[@id='wrapper']"),
    # 'baselland.ch': lambda d,u: d.find_elements(By.XPATH, "//div[@id='content-core']"),
    'ai.ch': lambda d,u: d.find_elements(By.XPATH, "//div[@id='content-core']"),
    'ar.ch': lambda d,u: d.find_elements(By.XPATH, "//div[@id='mainColInner'] | //nav[@id='SubNavigation']"),
    'ag.ch': lambda d,u: d.find_elements(By.XPATH, "//div[contains(@class, 'pagesection__inner')]"),
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
            #if row['page_is_software_guide'].startswith("Yes"):
            if row['page_is_software_guide'].startswith("Yes") or row['page_contains_software_guide'].startswith("Yes"):
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

def is_element_or_parent_invisible(element):
    """Check if the given element or any of its parents have invisibility-inducing CSS properties using iteration."""
    # if bool(element.find_elements(By.XPATH, ".//ancestor-or-self::*[contains(@style, 'display: none') or contains(@style, 'visibility: hidden')]")):
    #     return True
    # try:
    #     script = """return !$(arguments[0]).closest(":not(:visible)").length;"""
    #     return not element._parent.execute_script(script, element)
    # except:
    #     pass
    if (element.value_of_css_property("display") == "none" or 
        element.value_of_css_property("visibility") == "hidden"):
        return True
    elements_to_check = element.find_elements(By.XPATH, f'./ancestor::*[position() <= {max_recursion_stage}]')
    for current_element in elements_to_check:
        if (current_element.value_of_css_property("display") == "none" or 
            current_element.value_of_css_property("visibility") == "hidden"):
            return True
    return False

def is_visible_element(element):
    return not is_element_or_parent_invisible(element)

def detect_libraries_for_dynamic_content(driver):
    print('detect_libraries_for_dynamic_content')
    libraries_detected = []
    # Common patterns to detect popular JS libraries/frameworks
    library_patterns = {
        'jQuery': 'jQuery',
        'React': 'React',
        'AngularJS': 'angular',
        'Vue.js': 'Vue',
        'Bootstrap (JavaScript)': 'bootstrap',
        'D3.js': 'd3',
        'Backbone.js': 'Backbone',
        'Ember.js': 'Ember',
        'Alpine.js': 'Alpine',
        'Svelte': 'svelte'
    }
    for lib, pattern in library_patterns.items():
        if driver.execute_script(f"return typeof {pattern}") != 'undefined':
            libraries_detected.append(lib)
    # driver.quit()
    return libraries_detected

def detect_tooltips_popups_hover_effects(main_content_elements):
    print('detect_tooltips_popups_hover_effects')
    # 1. Check for common tooltip and pop-up attributes/classes
    common_selectors = [
        '[data-toggle="tooltip"]',
        '[data-tooltip]',
        '.tooltip',
        '.popover',
        '[role="tooltip"]',
        ':hover'  # Including :hover as per your suggestion
    ]
    for e in main_content_elements:
        for selector in common_selectors:
            elements = e.find_elements(By.CSS_SELECTOR,selector)
            elements = filter(is_visible_element, elements)
            if any(elements):
                return True
    return False

def detect_animations(main_content_elements):
    print('detect_animations')
    animations = []
    for e in main_content_elements:
        # Check for inline styles containing 'animation'
        elements = e.find_elements(By.CSS_SELECTOR,"[style*='animation']")
        elements = filter(is_visible_element, elements)
        animations += elements
    return len(set(animations))

def detect_search_function(driver):
    print('detect_search_function')
    # Check for input of type search # Check for suggestive class or id attributes
    if driver.find_elements("xpath", '//input[@type="search" or contains(@class, "search") or contains(@id, "search")]'):
        return True
    # Check for form elements or buttons with suggestive attributes or values
    if driver.find_elements("xpath", '//form[contains(@class, "search-form") or contains(@id, "search-form")]'):
        return True
    if driver.find_elements("xpath", '//button[contains(text(), "Search") or contains(@value, "Search") or contains(text(), "Suchen") or contains(@value, "Suchen")]'):
        return True
    return False

def detect_hyperlinks(main_content_elements):
    print('detect_hyperlinks')
    # hyperlinks = []
    for e in main_content_elements:
        # Detecting hyperlinks that don't start with #
        elements = e.find_elements("xpath", "//a[@href and not(starts-with(@href, '#'))  and not(starts-with(@href, '/'))]")
        # Filter out non-visible elements
        elements = filter(is_visible_element, elements)
        # hyperlinks.extend(elements)
        if any(elements):
            return True
    # return len(set(hyperlinks))
    return False

def detect_navigation_menu(driver):
    print('detect_navigation_menu')
    # Detecting navigation menus
    common_nav_classes = ['navbar', 'menu', 'navigation', 'nav-bar', 'top-nav']
    nav_class_elements = []
    for nav_class in common_nav_classes:
        if len(driver.find_elements(By.XPATH,f"//*[contains(@class, 'feedback')]//*[@href and not(starts-with(@href, '#'))]")) > 0:
            return True
    elements = driver.find_elements(By.XPATH,"//nav//*[@href and not(starts-with(@href, '#'))]")
    elements = filter(is_visible_element, elements)
    if any(elements):
        return True
    return False

def detect_jargon(main_content_elements):
    print('detect_jargon')
    jargon_words = []
    for e in main_content_elements:
        # Tokenize the document into words
        document_words = map(lambda x:x.strip('*:,.?!;()[]|«»\'"&/\\+-'), e.text.lower().split())

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

def detect_multilingual_support(driver):
    print('detect_multilingual_support')
    for e in driver.find_elements(By.XPATH, "//body"):
        if 'English' in e.text.lower():
            return True
    elements = driver.find_elements(By.XPATH,"//*[contains(@class, 'lang') or contains(@data-testid, 'lang')]")
    elements = filter(is_visible_element, elements)
    if any(elements):
        return True
    return False

def detect_feedback(driver):
    print('detect_feedback')
    elements = driver.find_elements(By.XPATH,"//*[contains(@class, 'feedback')]")
    elements = filter(is_visible_element, elements)
    if any(elements):
        return True
    return False

def count_words_in_page(main_content_elements):
    print('count_words_in_page')
    word_count = 0
    for e in main_content_elements:
        word_count += len(e.text.split())
    return word_count

def detect_sections(main_content_elements):
    print('detect_sections')
    # Initial list of selectors for structured content
    target_tags = [
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'section' 
    ]
    for e in main_content_elements:
        for tag_name in target_tags:
            elements = e.find_elements(By.TAG_NAME, tag_name) # Find all elements with the specified HTML tag
            elements = list(filter(is_visible_element, elements))
            if len(elements) >= 2:
                return True
    return False

def detect_explanatory_images(main_content_elements):
    print('detect_explanatory_images')
    explanatory_images = set()
    for e in main_content_elements:
        for tag in ['img', 'svg', 'canvas', 'picture', 'source']:
            elements = e.find_elements(By.TAG_NAME, tag)
            for element in elements:
                # Size check
                width = element.size['width']
                height = element.size['height']
                if width < 50 and height < 50:  # Adjust as needed
                    continue
                # Alt text and surrounding text check
                alt_text = element.get_attribute('alt')
                if alt_text and "logo" in alt_text.lower():
                    continue
                src = element.get_attribute('src') if tag == 'img' else None
                if src and ("logo" in src.lower() or "brand" in src.lower()):  # Can be expanded based on common patterns for logos
                    continue
                img = element.get_attribute('src')
                if not img:
                    continue
                if not is_visible_element(element):
                    continue
                print('image found:', img)
                explanatory_images.add(img)
    # return explanatory_images
    return len(explanatory_images)

def detect_interactive_elements_within_text(main_content_elements):
    print('detect_interactive_elements_within_text')
    # List of elements to check
    elements = ['button', 'div', 'span', 'nav']
    # Keywords that hint at dynamic behavior
    dynamic_keywords = [
        'accordion', 'toggle', 'collapse', 'dropdown', 'modal',
        'expand', 'slide', 'tab', 'menu', 'popup', 'reveal',
        'hide', 'switch', 'rotate', 'carousel', 'fade', 
        'animate', 'draggable', 'drop', 'overlay', 'trigger', 'lazyload',
        'navbar', 'faqblock'
    ]
    forbidden_dynamic_keywords = ['breadcrumb','cookie']
    # Construct contains clauses for classes and ids based on dynamic_keywords
    contains_clauses = []
    for keyword in dynamic_keywords:
        contains_clauses.extend([
            f"contains(@class, '{keyword}')",
            f"contains(@id, '{keyword}')",
            f"contains(@data-toggle, '{keyword}')",  # added this
            f"contains(@data-trigger, '{keyword}')"   # and this (add more as needed)
        ])
    doesnt_contain_clauses = []
    for forbidden_keyword in forbidden_dynamic_keywords:
        doesnt_contain_clauses.extend([
            f"not(contains(@class, '{forbidden_keyword}'))",
            f"not(contains(@id, '{forbidden_keyword}'))"
        ])

    # Construct the final XPath
    ancestor_clauses = [f"not(ancestor::div[contains(@class, '{keyword}') or contains(@id, '{keyword}')])" for keyword in dynamic_keywords]
    combined_ancestor_clause = " and ".join(ancestor_clauses)

    xpath = ' | '.join(f".//{k}[not(contains(@onclick, 'window.location')) and ({' and '.join(doesnt_contain_clauses)}) and ({' or '.join(contains_clauses)}) and {combined_ancestor_clause}]" for k in elements)
    # xpath = ' | '.join(f".//{k}[not(contains(@onclick, 'window.location')) and ({' or '.join(contains_clauses)})]" for k in elements)

    potential_dynamic_elements = []
    for e in main_content_elements:
        potential_dynamic_elements += filter(is_visible_element, e.find_elements(By.XPATH, xpath))
    # print_iter_of_elements(potential_dynamic_elements,'potential_dynamic_elements:')
    return len(set(potential_dynamic_elements))

def detect_multimedia_elements(main_content_elements):
    print('detect_multimedia_elements')
    # 1. Check for common multimedia tags
    multimedia_tags = ['video', 'audio', 'embed', 'object', 'iframe']
    multimedia_detected = []
    for e in main_content_elements:
        ###
        links = e.find_elements(By.TAG_NAME, 'use')
        for link in links:
            href = link.get_attribute('xlink:href')
            if href and any(platform in href for platform in ['play']):
                if is_visible_element(link):
                    multimedia_detected.append(link)
        ###
        xpath_query = ' | '.join(f".//{tag}" for tag in multimedia_tags)
        elements = e.find_elements(By.XPATH, xpath_query)
        elements = filter(is_visible_element, elements)
        multimedia_detected += elements
        # Check for YouTube links or other popular video platforms
        video_platforms = set(['youtube.com', 'youtu.be', 'vimeo.com', 'dailymotion.com'])
        links = e.find_elements(By.TAG_NAME, 'a')
        for link in links:
            href = link.get_attribute('href')
            if href and any(platform in href for platform in video_platforms):
                if is_visible_element(link):
                    multimedia_detected.append(link)
    return len(set(multimedia_detected))

def test_accessibility(driver):
    print('test_accessibility')
    # Create a new Axe instance
    axe = Axe(driver)
    # Inject the Axe library into the page
    axe.inject()
    
    # Run the accessibility check
    results = axe.run()
    
    # # Print results
    # if results['violations']:
    #     print(f"Found {len(results['violations'])} accessibility issues on {url}:")
    #     for violation in results['violations']:
    #         print(f" - {violation['help']}:")
    #         for node in violation['nodes']:
    #             print(f"   - Element: {node['html']}")
    #             # print(f"     Remediation: {node['any'][0]['message']}")
    # else:
    #     print(f"No accessibility issues found on {url}.")
    return len(list(unique_everseen(results['violations'], key=lambda x: x["id"])))

# Find and return all tables on the page
def find_tables(main_content_elements):
    print('find_tables')
    v = 0
    for e in main_content_elements:
        v += len(list(filter(is_visible_element, e.find_elements(By.TAG_NAME, "table"))))
    return v

# Find and return all lists/enumerations on the page
def find_lists(main_content_elements):
    print('find_lists')
    v = 0
    for e in main_content_elements:
        ul_elements = e.find_elements(By.TAG_NAME, "ul")
        ol_elements = e.find_elements(By.TAG_NAME, "ol")
        for element in ul_elements + ol_elements:
            if not element.get_attribute('class'):  # Check if the element does not have a class attribute
                if is_visible_element(element):
                    v += 1
    return v

# Function to find table of contents/summary (German/Swiss German: Inhaltsverzeichnis/Zusammenfassung)
def find_table_of_contents(main_content_elements):
    print('find_table_of_contents')
    tags = ["Inhaltsverzeichnis", "Zusammenfassung", "Gliederung", "Übersicht", "Inhalt"]
    sub_xpath = ' or '.join(map(lambda x: f'text() = "{x}"', tags))
    for e in main_content_elements:
        if len(list(filter(is_visible_element, e.find_elements(By.XPATH, f'//*[{sub_xpath}]')))) > 0:
            return True
    # common_nav_classes = ['navbar', 'nav-bar', 'anchornav']
    # for e in main_content_elements:
    #     for nav_class in common_nav_classes:
    #         # print(list(map(lambda x: x.get_attribute('outerHTML'), e.find_elements(By.XPATH,f"//*[contains(@class, '{nav_class}')]//*[(starts-with(@href, '#') and string-length(@href) > 1) or @data-href]"))))
    #         if len(e.find_elements(By.XPATH,f"//*[contains(@class, '{nav_class}')]//*[(starts-with(@href, '#') and string-length(@href) > 1) or @data-href]")) > 1:
    #             return True
    return False

# Function to find FAQ sections (German/Swiss German: FAQ)
def find_faq_sections(main_content_elements):
    print('find_faq_sections')
    tags = ["FAQ", "Häufig gestellte Fragen"]
    sub_xpath = ' or '.join(map(lambda x: f'contains(text(), "{x}")', tags))
    for e in main_content_elements:
        if len(list(filter(is_visible_element, e.find_elements(By.XPATH, f'//*[{sub_xpath}]')))) > 0:
            return True
    return False

# Function to find glossaries (German: Glossar)
def find_glossaries(main_content_elements):
    print('find_glossaries')
    tags = ["Glossar"]
    sub_xpath = ' or '.join(map(lambda x: f'text() = "{x}"', tags))
    for e in main_content_elements:
        if len(list(filter(is_visible_element, e.find_elements(By.XPATH, f'//*[{sub_xpath}]')))) > 0:
            return True
    return False

# Function to find an introduction section (German/Swiss German: Einführung)
def find_introduction(main_content_elements):
    print('find_introduction')
    tags = ["Einführung","Einleitung"]
    sub_xpath = ' or '.join(map(lambda x: f'text() = "{x}"', tags))
    for e in main_content_elements:
        if len(list(filter(is_visible_element, e.find_elements(By.XPATH, f'//*[{sub_xpath}]')))) > 0:
            return True
    return False

# Function to find installation/registration instructions (German/Swiss German: Installation/Registrierung)
def find_installation_instructions(main_content_elements):
    print('find_installation_instructions')
    tags = ["Windows", "macOS", "Linux", "Android", "iOS", "Anleitung zur Registrierung", "Installationsanleitung", "Registration", "Installation", "Registrierung"]
    sub_xpath = ' or '.join(map(lambda x: f'contains(text(), "{x}")', tags))
    for e in main_content_elements:
        if len(list(filter(is_visible_element, e.find_elements(By.XPATH, f'//*[{sub_xpath}]')))) > 0:
            return True
    return False

def analyze_webpage(url):
    primary_domain = get_primary_domain(url)
    if primary_domain not in main_content_fn_dict:
        return None
    # Initialize selenium webdriver
    driver = webdriver.Chrome(options=chrome_options)
    # driver.execute_script("window.open('');")
    # driver.switch_to.window(driver.window_handles[-1])
    driver.get(url)
    WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')

    main_content_elements = main_content_fn_dict[primary_domain](driver,url)
    # print_iter_of_elements(main_content_elements,'main_content_elements:')
    # Define the checks
    results = {
        'Main Content Elements': len(main_content_elements),
        # 'Dynamic Content Libs': detect_libraries_for_dynamic_content(driver), # Dynamic Content: Content that changes without the page being reloaded, often seen in modern web apps. This could include live chat features, real-time data updates, etc.
        'Search Function': detect_search_function(driver),
        'Images': detect_explanatory_images(main_content_elements),
        'Feedback Mechanisms': detect_feedback(driver),
        'Multilingual Support': detect_multilingual_support(driver),
        # 'Animations': detect_animations(main_content_elements), # Animations: These can enhance user experience and engagement, though they don't always imply direct user interactivity.
        # 'Interactive Charts/Graphs': driver.find_elements(By.CSS_SELECTOR,"canvas") != [],  # This is a basic check and might not catch all cases. # Some pages might have charts or graphs that users can interact with, such as zooming in or hovering to see data points.
        'Low-frequency Jargon': detect_jargon(main_content_elements),
        'Multimedia Elements': detect_multimedia_elements(main_content_elements),
        'Hyperlinks': detect_hyperlinks(main_content_elements),
        'Navigation Menu': detect_navigation_menu(driver),
        'Interactive Elements': detect_interactive_elements_within_text(main_content_elements), # Interactive Elements on the page, such as buttons, dropdown menus, and input fields.
        'Accessibility Issues': test_accessibility(driver), # do it as last thing
        'Content Length': count_words_in_page(main_content_elements),
        ###############
        'Instructions Divided into Sections': detect_sections(main_content_elements), # Structured Contents: sections with headings, subheadings, and paragraphs; lists; enumerations
        'Tables': find_tables(main_content_elements),
        'Lists/Enumerations': find_lists(main_content_elements),
        'a Table of Contents': find_table_of_contents(main_content_elements),
        'a FAQ Section': find_faq_sections(main_content_elements),
        'a Glossary': find_glossaries(main_content_elements),
        'an Introduction Section': find_introduction(main_content_elements),
        'Installation Instructions': find_installation_instructions(main_content_elements),
    }
    results['an Instructive Example'] = results['Multimedia Elements']>0 or results['Images']>0
    print(url, json.dumps(results, indent=4))
    # Close the driver
    driver.quit()
    return results

def print_iter_of_elements(it,s=''):
    it = map(lambda x: x.get_attribute('outerHTML').strip(), it)
    it = list(unique_everseen(it))
    print(s,len(it), json.dumps(it, indent=4))

def get_link_iter(csv_rows,url_list):
    for row,url in tqdm(zip(csv_rows,url_list),total=len(url_list)):
        link_iter = row['doc_links'].split('\n')
        link_iter = filter(lambda x: get_primary_domain(x)==get_primary_domain(url), link_iter)
        link_iter = filter(lambda x: '.pdf' not in x.lower(), link_iter)
        link_iter = filter(lambda x: '.docx' not in x.lower(), link_iter)
        link_iter = filter(lambda x: '.xls' not in x.lower(), link_iter)
        link_iter = filter(lambda x: '.zip' not in x.lower(), link_iter)
        link_iter = filter(lambda x: '.mp4' not in x.lower(), link_iter)
        # link_iter = map(lambda x: x.split('?')[0], link_iter)
        link_iter = filter(lambda x: x not in url_list, link_iter)
        other_row = row.copy()
        other_row['page_contains_software_guide'] = 'N/A'
        other_row['software_name_explanation'] = 'N/A'
        other_row['page_content'] = 'N/A'
        other_row['guide_format'] = 'Webpage'
        other_row['doc_links'] = ''
        u_list = list(link_iter) if row['page_is_software_guide'] == 'No' else [url]+list(link_iter)
        for u in u_list:
            yield (row if u == url else other_row,u)

# Load URLs from the CSV file
csv_filename = '../1_guide_identification/corrected_guide_identification_analysis.csv'
url_list, csv_rows = load_filtered_urls_from_csv(csv_filename)
# url_list = [
#     'https://kunstmuseum.gr.ch/de/digital/audioguide/Seiten/Start.aspx',
#     'https://www.zh.ch/de/webangebote-entwickeln-und-gestalten/inhalt/inhalte-gestalten/services-anbieten.html',
#     'https://steuerverwaltung.tg.ch/hilfsmittel/efisc-steuererklaerungssoftware/download-efisc2016.html/2959',
#     'https://informatik.tg.ch/download/servicedesk.html/5379',
#     'https://www.sz.ch/finanzdepartement/steuerverwaltung/natuerliche-personen/online-schalter/steuererklaerungs-software.html/10395',
#     'https://www.agi.dij.be.ch/de/start/kataster/oereb-kataster/zugang-zu-oereb-informationen/geoportalkarte-oereb-kataster.html',
#     'https://www.ag.ch/de/smartserviceportal/dienstleistungen?dl=pruefungstermin-mutieren-4217dc60-7afc-4b11-8290-6b0f11c41efd_de',
#     'https://www.ag.ch/de/verwaltung/dvi/gemeindeaufsicht/fachstelle-datenaustausch/aargauischen-grundstueck-und-objektinformationssystem-(agobis)',
#     'https://www.zh.ch/de/planen-bauen/tiefbau.html#-742406552',
#     # 'https://www.hbav.dij.be.ch/de/start/hb-fachthemen/verifikation/standardverifikation-phase-b3.html',
#     # 'https://www.zh.ch/de/migration-integration/integration/integrationsagenda/online-handbuch-iazh/finanzierung-reporting/reporting-iazh--anleitung-und-erlaeuterungen.html',
#     # 'https://www.zh.ch/de/planen-bauen/geoinformation/geodaten/geodatenbezug/kostenlose-geodaten-beziehen.html',
#     # 'https://www.zh.ch/de/steuern-finanzen/steuern/steuern-natuerliche-personen/steuererklaerung-natuerliche-personen.html',
#     # 'https://zg.ch/de/steuern-finanzen/steuern/juristische-personen/steuererklaerung-ausfuellen',
#     # 'https://www.ur.ch/_rte/publikation/8972',
#     # 'https://www.bbz.ch/bibliothek/emedien-ausleihen.html/6637',
#     # 'https://so.ch/verwaltung/volkswirtschaftsdepartement/amt-fuer-wald-jagd-und-fischerei/fischerei/aktuell/aktuell/news/angelpatente-2023-bestellen-via-webshop-efj2/',
#     # 'https://www.sz.ch/verwaltung/bildungsdepartement/amt-fuer-volksschulen-und-sport/unterricht/lern-und-foerdersysteme.html/11898',
#     # 'https://www.ow.ch/_rte/publikation/3949',
#     # 'https://www.nw.ch/_rte/publikation/28441',
#     # 'https://www.lu.ch/verwaltung/staatskanzlei/organisation_aufgaben/telefonzentrale',
#     # 'https://www.gr.ch/DE/Medien/Mitteilungen/MMStaka/2018/Seiten/2018021401.aspx',
#     'https://www.baselland.ch/politik-und-behorden/direktionen/finanz-und-kirchendirektion/steuerverwaltung/e-tax-bl/support',
#     # 'https://www.steuerverwaltung.bs.ch/baltax-help-point.html',
#     # 'https://www.sv.fin.be.ch/de/start/e-services/taxme-online-fuer-privatpersonen.html',
#     # 'https://www.fr.ch/de/steuern/natuerliche-personen/fritax/download-fritax',
#     # 'https://www.gl.ch/verwaltung/sicherheit-und-justiz/justiz/strassenverkehrsamt.html/1678/news/716/newsarchive/1',
#     # 'https://www.ag.ch/de/verwaltung/dvi/kantonspolizei/praevention/cybercrime',
#     # 'https://ar.ch/verwaltung/departement-gesundheit-und-soziales/amt-fuer-gesundheit/abteilung-gesundheitsfoerderung/elektronisches-patientendossier/',
#     # 'https://www.ai.ch/themen/steuern/ai-tax-software/ai-tax-steuererklaerung-software-fuer-natuerliche-personen',
#     # 'https://uwe.lu.ch/themen/abfall/egi',
#     # 'https://www.ow.ch/publikationen/3949',
#     'https://www.sg.ch/news/sgch_standortfoerderung/2020/12/coltene-ermoeglicht-navigation-durch-den-wurzelkanal.html',
#     # 'https://steuerverwaltung.tg.ch/hilfsmittel/formulare.html/10797/product/553',
#     # 'https://zg.ch/de/steuern-finanzen/steuern/natuerliche-personen/steuererklaerung-ausfuellen',
# ]
# csv_rows = [1]*len(url_list)

# Get results
_cache = load_or_create_cache(cache_file, lambda: {})
results = []
for row, url in get_link_iter(csv_rows,url_list):
    try:
        r, was_cached = get_cached_value(url, _cache, analyze_webpage)
        if not r:
            continue
        # else:
        #     primary_domain = get_primary_domain(url)
        #     driver = webdriver.Chrome(options=chrome_options)
        #     driver.get(url)
        #     WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
        #     main_content_elements = main_content_fn_dict[primary_domain](driver)
        #     r['a Table of Contents'] = find_table_of_contents(main_content_elements)
        #     r['a Glossary'] = find_glossaries(main_content_elements)
        #     r['an Introduction Section'] = find_introduction(main_content_elements)
        #     r['Navigation Menu'] = detect_navigation_menu(driver)
        #     # r['Installation Instructions'] = find_installation_instructions(main_content_elements) 
        #     # r['Accessibility Issues'] = test_accessibility(driver) # do it as last thing
        #     _cache[url] = r
        #     print(url, json.dumps(r, indent=4))
        if was_cached and r['Main Content Elements']==0:
            r, was_cached = get_cached_value(url, _cache, analyze_webpage, ignore_cache=True)
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
