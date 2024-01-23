import json
import time
import numpy as np
import os
import csv
import re
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium.common.exceptions import TimeoutException
import requests
from bs4 import BeautifulSoup

from selenium.webdriver.chrome.options import Options
chrome_options = Options()  
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920,1080")

data_dir_name = 'scraped_links'

wait_time = 10

keyword_list = [
	"Software",
	#### List of translations of the word “manual” in German: https://www.duden.de/suchen/synonyme/Wegleitung
	'Anleitung',
	'Wegleitung', # common swiss-german synonym for anleitung
	'Unterweisung',
	'Bedienungsvorschrift',
	'Arbeitsanleitung',
	'Instruktion',
	'Anweisung',
	####
	'Bedienungsanleitung',
	'Gebrauchsanleitung',
	'Wegweiser',
	'Benutzerhandbuch',
]

forbidden_format_list = [
	'.pdf',
	'.xls',
	'.zip',
	'.docx',
	'.doc',
	'.ppt'
]

has_forbidden_format = lambda x: any(map(lambda y: y in x, forbidden_format_list))

def baselLandschaft(parola):
	data=set()
	i = 0
	while True:
		#140 should be the level to get
		url = f"https://www.baselland.ch/@@search?facet=true&facet.field:list=portal_type&facet.field:list=review_state&b_start:int={i}&SearchableText={parola}"
		response = requests.get(url)
		soup = BeautifulSoup(response.content, 'html.parser')
		searchResults = soup.find(class_="searchResults")
		if not searchResults:
			break
		
		allFound = searchResults.find_all(class_="contenttype-ftw-simplelayout-contentpage")
		for singleFound in allFound:
			link = singleFound.find(class_="state-")
			link_href = link['href']
			data.add(link_href)
		i+=10
	return data

def baselStadt(parola):
	data=[]
	driver = webdriver.Chrome(options=chrome_options)
	driver.get("https://www.bs.ch/?navopen=search&search="+parola)
	try:
		_ = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.CLASS_NAME, "search-flyout__column")))
		# print("Page is ready!")
	except TimeoutException:
		print("Loading took too much time!")
	time.sleep(1)
	boolean= True
	counter = 0
	while (boolean):
		searchResults= driver.find_element(By.CLASS_NAME, "search-flyout__column")
		startallFound = searchResults.find_elements(By.TAG_NAME, "li")   

		driver.execute_script("window.scrollBy(0,15000)")

		time.sleep(1)
		searchResults= driver.find_element(By.CLASS_NAME, "search-flyout__column")
		endallFound = searchResults.find_elements(By.TAG_NAME, "li")  

		if not endallFound or not startallFound:
			boolean= False
			counter = 0
		elif endallFound[-1] == startallFound[-1]:
			counter += 1
			if counter > 30:
				boolean= False
		else:
			counter = 0

	searchResults= driver.find_element(By.CLASS_NAME, "search-flyout__column")
	allFound = searchResults.find_elements(By.TAG_NAME, "li")
	for singelFound in allFound:
		if not singelFound.find_elements(By.CLASS_NAME, 'fas'):
			continue
		link= singelFound.find_element(By.TAG_NAME, "a")
		link_href = link.get_attribute('href')
		data.insert(-1,link_href)
	driver.quit()
	return data
  
def bern(parola):
	driver = webdriver.Chrome(options=chrome_options)
	driver.get("https://www.be.ch/de/tools/suchresultate.html?q="+parola+"&size=n_20_n&filters%5B0%5D%5Bfield%5D=ktbe_type&filters%5B0%5D%5Bvalues%5D%5B0%5D=cms&filters%5B0%5D%5Btype%5D=all&sort-field=_score&sort-direction=desc")
	try:
		_ = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.CLASS_NAME, 'css-zm9h5m.elh1daz0')))
		# print("Page is ready!")
	except TimeoutException:
		print("Loading took too much time!")
		driver.quit()
		return []
	time.sleep(2)
	driver.find_element(By.CLASS_NAME, 'css-zm9h5m.elh1daz0').click()
	
	buttonscontainer= driver.find_element(By.CLASS_NAME,"css-1hdzekc.e1gotkd71")
	buttons= buttonscontainer.find_elements(By.TAG_NAME,"button")

	data=[]
	for button in buttons:
		time.sleep(4)
		try:
			button.click()
		except:
			continue

		try:
			for i in range(0, 2000 , 1):
				time.sleep(3)
				driver.execute_script("window.scrollBy(0,15000)")

				driver.find_element(By.CLASS_NAME, 'css-1wcrah7.e1gotkd72').click()
		except:
			print ('finished search')

		searchElement =driver.find_element(By.CLASS_NAME, 'css-v5al3.e28tlhh0')
		
		allFound = searchElement.find_elements(By.TAG_NAME, "li")
		for singelFound in allFound:
			link= singelFound.find_element(By.TAG_NAME, "a")
			link_href = link.get_attribute('href')
			data.insert(-1,link_href)
	driver.quit()
	return data
  
def glarus(parola):
	data=[]
	driver = webdriver.Chrome(options=chrome_options)
	driver.get("https://www.gl.ch/html/11")
	driver.implicitly_wait(0.5)    

	inputElement = driver.find_element(By.CLASS_NAME, "search-box")
	inputElement.send_keys(parola)
	inputElement.send_keys(Keys.ENTER)

	time.sleep(4)

	try:
		searchElement=driver.find_element(By.CLASS_NAME, "search-result-group.search-result-group--news_news")
		if searchElement:
			allFound = searchElement.find_elements(By.TAG_NAME, "li")
			for singelFound in allFound:
				title= singelFound.find_element(By.TAG_NAME, "h3")
				link= title.find_element(By.TAG_NAME, "a")
				link_href = link.get_attribute('href')
				data.insert(-1,link_href)
	except Exception as e:
		print('no elements found')

	try:
		searchElement=driver.find_element(By.CLASS_NAME, "search-result-group.search-result-group--dam_file")
		if searchElement:
			allFound = searchElement.find_elements(By.TAG_NAME, "li")
			for singelFound in allFound:
				title= singelFound.find_element(By.TAG_NAME, "h3")
				link= title.find_element(By.TAG_NAME, "a")
				link_href = link.get_attribute('href')
				data.insert(-1,link_href)
	except Exception as e:
		print('no elements found')
	
	try:
		searchElement=driver.find_element(By.CLASS_NAME, "search-result-group.search-result-group--cms_page")
		if searchElement:
			allFound = searchElement.find_elements(By.TAG_NAME, "li")
			for singelFound in allFound:
				title= singelFound.find_element(By.TAG_NAME, "h3")
				link= title.find_element(By.TAG_NAME, "a")
				link_href = link.get_attribute('href')
				data.insert(-1,link_href)
	except Exception as e:
		print('no elements found')
	driver.quit()
	return data

def graubunden(parola):
	data=set()
	i=0
	driver = webdriver.Chrome(options=chrome_options)
	while True:
		if i == 0:
			driver.get(f"https://www.gr.ch/DE/Seiten/Suche.aspx?k={parola}#k={parola}#l=2055")
		else:
			driver.get(f"https://www.gr.ch/DE/Seiten/Suche.aspx?k={parola}#k={parola}#s={i+1}#l=2055")
		
		try:
			_ = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.CLASS_NAME, 'ms-srch-item-link')))
			# print("Page is ready!")
		except TimeoutException:
			print("Loading took too much time!")
			break

		try:
			searchResults= driver.find_elements(By.CLASS_NAME, "ms-srch-item-link")
		except:
			break

		for link_item in searchResults:
			try:
				link = link_item.get_attribute('href')
				if not link:
					continue
				# print(link)
				data.add(link)
			except:
				pass
		if len(searchResults) <= 1:
			break
		i+=10
		driver.execute_script("window.open('');")
		driver.switch_to.window(driver.window_handles[-1])
	driver.quit()
	return data

def obwalden(parola):
	data=set()
	i=1
	driver = webdriver.Chrome(options=chrome_options)
	while True:
		driver.get("https://www.ow.ch/suchen?query="+parola+"&filters%5Bsources%5D%5B0%5D=icmsPage&page="+str(i))
		try:
			_ = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.CLASS_NAME, "icms-search-results")))
			# print("Page is ready!")
		except TimeoutException:
			print("Loading took too much time!")
			break

		searchResults= driver.find_element(By.CLASS_NAME, "icms-search-results")
		if not searchResults:
			break

		allFound = searchResults.find_elements(By.CLASS_NAME, "entry-title")
		if not allFound:
			break

		# print(len(allFound))
		for singelFound in allFound:
			link= singelFound.find_element(By.TAG_NAME, "a")

			link_href = link.get_attribute('href')
			data.add(link_href)
		i+=1
		driver.execute_script("window.open('');")
		driver.switch_to.window(driver.window_handles[-1])
	driver.quit()
	return data

# def ticino(parola):
# 	data=set()
# 	driver = webdriver.Chrome(options=chrome_options)
# 	i=1
# 	while True:
# 		driver.get("https://www4.ti.ch/tich/cerca-nel-sito/ricerca?filter=1&start="+str(i)+"&tx_tichgenricerca_ricerca[client]=ti&tx_tichgenricerca_ricerca[q]="+parola+"&tx_tichgenricerca_ricerca[site]=raccolta_completa&tx_tichgenricerca_ricerca[tipoFiltro]=risultatiGsa&cHash=96a4f9505254a6be75a4f9dcabfab5a5")
# 		try:
# 			_ = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.CLASS_NAME, "risultatiTutti")))
# 			# print("Page is ready!")
# 		except TimeoutException:
# 			print("Loading took too much time!")
# 			break

# 		searchResults= driver.find_element(By.CLASS_NAME, "risultatiTutti")
# 		if not searchResults:
# 			break
# 		allFound = searchResults.find_elements(By.CLASS_NAME, "no-list.hover")
# 		if not allFound:
# 			break
# 		for singelFound in allFound:
# 			link= singelFound.find_element(By.TAG_NAME, "a")

# 			link_href = link.get_attribute('href')
# 			data.insert(-1,link_href)
# 		driver.execute_script("window.open('');")
# 		driver.switch_to.window(driver.window_handles[-1])
# 		i+=1
# 	driver.quit()
# 	print ("ticino: "+ str(len(data)))  
# 	return list(data)

def uri(parola):
	data=[]
	driver = webdriver.Chrome(options=chrome_options)
	driver.get("https://www.ur.ch/suchen?query="+parola+"&selectedTab=website&selectedTabOrder=&selectedTabFilter={}")
	driver.implicitly_wait(0.5)
	searchResults= driver.find_element(By.ID, 'suchformulartab-results')

	searchResults1= searchResults.find_element(By.CLASS_NAME, "nav.nav-tabs")
	allFound = searchResults1.find_elements(By.CLASS_NAME, "nav-item")
	for singelFound in allFound:
		time.sleep(1)
		driver.execute_script("scroll(0, 0);")
		try:
			undercat= singelFound.find_element(By.TAG_NAME, "a")
			# print (undercat.find_element(By.TAG_NAME, "span"))
			undercat.find_element(By.TAG_NAME, "span").click()
			while ( len(driver.find_elements(By.CLASS_NAME, "suchformulartab-paging.icms-btn.icms-btn-primary.icms-btn-block")) > 2):
				driver.find_elements(By.CLASS_NAME, "suchformulartab-paging.icms-btn.icms-btn-primary.icms-btn-block")[0].click()  
		except:
			# print ('a')
			pass
		table= driver.find_element(By.CLASS_NAME, "tabResult")
		rows=table.find_elements(By.CLASS_NAME, "row")
		for row in rows:
			link= row.find_element(By.TAG_NAME, "a")
			link_href = link.get_attribute('href')
			data.insert(-1,link_href)
	driver.quit()
	return data

def zug(parola):
	data=set()
	driver = webdriver.Chrome(options=chrome_options)
	for content_filter in ['content','news']:
		i = 1
		search = True
		while search:
			driver.get(f"https://zg.ch/de/suche?q={parola}&page={i}&filter={content_filter}")
			try:
				_ = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.CLASS_NAME, "search-result-item")))
				# print("Page is ready!")
			except TimeoutException:
				print("Loading took too much time!")
				search = False
				continue
			searchResults= driver.find_elements(By.CLASS_NAME, "search-result-item")
			if not searchResults:
				search = False
				continue
			for singelFound in searchResults:
				link= singelFound.find_element(By.TAG_NAME, "a")
				link_href = link.get_attribute('href')
				data.add(link_href)
			i+=1
			driver.execute_script("window.open('');")
			driver.switch_to.window(driver.window_handles[-1])			
	driver.quit()
	return data

def zurich(parola):
	data=set()
	driver = webdriver.Chrome(options=chrome_options)
	for _type in ['content','service']:
		search = True
		i=1
		while search:
			driver.get(f"https://www.zh.ch/de/suche.html?q={parola}&type={_type}&page={i}")
			try:
				_ = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.CLASS_NAME, "mdl-search_page__list")))
				# print("Page is ready!")
			except TimeoutException:
				print("Loading took too much time!")
				search = False
				continue
			
			searchResults = driver.find_elements(By.CLASS_NAME, "atm-search_result_item__content") + driver.find_elements(By.CLASS_NAME, "mdl-service_list__item")
			if not searchResults:
				search = False
				continue
			for link in searchResults:
				link_href = link.get_attribute('href')
				data.add(link_href)
		
			i+=1
			driver.execute_script("window.open('');")
			driver.switch_to.window(driver.window_handles[-1])
	new_data = set()
	for link in data:
		driver.get(link)
		new_data.add(driver.current_url)
	driver.quit()
	return new_data

def appenzellInneroden(parola):
	data=set()
	driver = webdriver.Chrome(options=chrome_options)
	i=0
	while True:
		url = "https://www.ai.ch/@@search?facet=true&facet.field=portal_type&facet.field=site_area&b_start="+str(i*10)+"&SearchableText="+parola
		driver.get(url)
		try:
			_ = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.CLASS_NAME, "searchResults")))
			# print("Page is ready!")
		except TimeoutException:
			print("Loading took too much time!")
			break

		try:
			searchResults= driver.find_element(By.CLASS_NAME, "searchResults")
		except Exception as e:
			break
		if not searchResults:
			break

		# allFound = searchResults.find_elements(By.CLASS_NAME, "contenttype-ftw-file-file")
		# found = found or allFound
		# for singelFound in allFound:
		#     link= singelFound.find_element(By.TAG_NAME, "a")
		#     data.add(link.get_attribute('href'))

		# allFound = searchResults.find_elements(By.CLASS_NAME, "contenttype-ftw-news-news")
		# found = found or allFound
		# for singelFound in allFound:
		#     link= singelFound.find_element(By.TAG_NAME, "a")
		#     data.add(link.get_attribute('href'))
			
		# allFound = searchResults.find_elements(By.CLASS_NAME, "contenttype-ftw-events-eventpage")
		# found = found or allFound
		# for singelFound in allFound:
		#     link= singelFound.find_element(By.TAG_NAME, "a")
		#     data.add(link.get_attribute('href'))
			
		allFound = searchResults.find_elements(By.CLASS_NAME, "contenttype-ftw-simplelayout-contentpage")
		for singelFound in allFound:
			link= singelFound.find_element(By.TAG_NAME, "a")
			link_href = link.get_attribute('href')
			data.add(link_href)

		allFound = searchResults.find_elements(By.CLASS_NAME, "contenttype-ftw-simplelayout-textblock")
		for singelFound in allFound:
			link= singelFound.find_element(By.TAG_NAME, "a")
			link_href = link.get_attribute('href')
			data.add(link_href)
		
		allFound = searchResults.find_elements(By.CLASS_NAME, "contenttype-ftw-simplelayout-filelistingblock")
		for singelFound in allFound:
			link= singelFound.find_element(By.TAG_NAME, "a")
			link_href = link.get_attribute('href')
			data.add(link_href)
		
		i+=1
		driver.execute_script("window.open('');")
		driver.switch_to.window(driver.window_handles[-1])
	driver.quit()
	return data

def appenzellAusserroden(parola):
	data=set()
	driver = webdriver.Chrome(options=chrome_options)
	i=1
	while True: 
		driver.get("https://www.ar.ch/search/?tx_solr%5Bq%5D="+parola+"&tx_solr%5Bpage%5D="+str(i))
		try:
			_ = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.CLASS_NAME, "results-list.list-group")))
			# print("Page is ready!")
		except TimeoutException:
			print("Loading took too much time!")
			break

		searchResults= driver.find_element(By.CLASS_NAME, "results-list.list-group")
		if not searchResults:
			break
		allFound = searchResults.find_elements(By.CLASS_NAME, "list-group-item-action.search-result.results-entry")
		if not allFound:
			break
		
		for singelFound in allFound:

			link= singelFound.find_element(By.CLASS_NAME, "results-topic")
			link1= link.find_element(By.TAG_NAME, "a")
			link_href = link1.get_attribute('href')
			data.add(link_href)
		i+=1
		driver.execute_script("window.open('');")
		driver.switch_to.window(driver.window_handles[-1])
	driver.quit()
	return data

def lucerne(parola):
	driver = webdriver.Chrome(options=chrome_options)
	# Open the website
	driver.get(f"https://www.lu.ch/Suchen?q={parola}&sort=&section=")
	try:
		_ = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.ID, "maincontent_0_moreLink")))
		# Continuously click the button until it exists on the page
		while True:
			# Scroll to the bottom of the page
			driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
			# Click button
			WebDriverWait(driver, wait_time).until(EC.element_to_be_clickable((By.ID, "maincontent_0_moreLink"))).click()
	except TimeoutException:
		pass
	# Retrieve all elements with class "searchitem"
	search_items = driver.find_elements(By.CLASS_NAME, value="searchitem")
	# Process the retrieved elements as needed
	linksFromResearch = []
	for item in search_items:
		seconditem= item.find_element(By.TAG_NAME, "a")
		href = seconditem.get_attribute("href")
		linksFromResearch.append(href)
	driver.quit()
	return linksFromResearch

def nidwalden(parola):
	driver = webdriver.Chrome(options=chrome_options)
	# Open the website
	driver.get(f"https://www.nw.ch/aisuche?query={parola}&selectedTab=website&selectedTabOrder=&selectedTabFilter="+"{}")
	try:
		WebDriverWait(driver, wait_time).until(EC.element_to_be_clickable((By.CLASS_NAME, "optin-stats-yesbutton"))).click()
	except TimeoutException:
		pass
	while True:
		# Scroll to the bottom of the page
		driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
		# Locate "show more hits" button
		try:
			section = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.ID, "tabFooter-website")))
			button = WebDriverWait(section, wait_time).until(EC.presence_of_element_located((By.TAG_NAME, "button")))
		except TimeoutException:
			break
		button.click()
		time.sleep(3)
	# Retrieve all elements with class "searchitem"
	try:
		resultListOver = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.ID, "tabResult-website")))
	except TimeoutException:
		driver.quit()
		return []
	search_items = resultListOver.find_elements(By.CLASS_NAME, value="row")
	# Process the retrieved elements as needed
	linksFromResearch = []
	for item in search_items:
		title= item.find_element(By.TAG_NAME, 'h3')
		seconditem= title.find_element(By.TAG_NAME, "a")
		href = seconditem.get_attribute("href")
		linksFromResearch.append(href)
	driver.quit()
	return linksFromResearch

def schaffhausen(parola):
	i = 0
	scroll = 0
	page_links = []
	while True:
		driver = webdriver.Chrome(options=chrome_options)
		def get_items():
			try:
				WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.CLASS_NAME, "list_wrapper")))
			except TimeoutException:
				return []
			content = driver.find_elements(By.CLASS_NAME, "list_wrapper")
			return content[0].find_elements("xpath", "//a[@class='list_item_grid' and not(.//p[@class='widget_title file'])]")
		# Open the website
		driver.get(f"https://sh.ch/CMS/Webseite/Kanton-Schaffhausen/Beh-rde/Services/Such-Portal-1212278-DE.html?search={parola}")
		time.sleep(10)
		for _ in range(scroll):
			# Scroll to the bottom of the page
			search_items = get_items()
			driver.execute_script("arguments[0].scrollIntoView();", search_items[-1])
			# driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
			# Wait for a small delay to allow content to load
			time.sleep(10)
		search_items = get_items()
		if i >= len(search_items):
			break
		# Open the link in a new window
		# driver.execute_script("arguments[0].scrollIntoView();", search_items[i])
		driver.execute_script("arguments[0].click();", search_items[i])
		time.sleep(5)
		page_link = driver.current_url
		page_links.append(page_link)
		i += 1
		if i >= len(search_items):
			scroll += 1
		driver.quit()
	driver.quit()
	return page_links

def schwyz(parola):
	driver = webdriver.Chrome(options=chrome_options)
	# Open the website
	driver.get("https://www.sz.ch/")
	try:
		search_button = WebDriverWait(driver, wait_time).until(EC.element_to_be_clickable((By.CLASS_NAME ,"searchform__toggle")))
	except TimeoutException:
		print("Loading took too much time!")
		driver.quit()
		return []
	driver.execute_script("arguments[0].click();", search_button)
	search_input = driver.find_element(By.ID ,"search-input")
	search_input.clear()  # Clear any existing value
	search_input.send_keys(parola)
	# Find the form element and submit it
	form = driver.find_element(By.CLASS_NAME ,"searchform__submit")
	driver.execute_script("arguments[0].click();", form)
	try:
		WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.ID, "news_news")))
	except TimeoutException:
		print("Loading took too much time!")
		driver.quit()
		return []
	results = [
		element.get_attribute("href")
		for element in driver.find_elements("xpath", "//div[@id='news_news' or @id='cms_page' or @id='osm_product']//a[@href]")
	]
	driver.quit()
	return results

def solothurn(parola):
	linksFromResearch = []
	driver = webdriver.Chrome(options=chrome_options)
	i = 1
	while True:
		# Open the website
		driver.get(f"https://so.ch/suche/suche/?tx_solr%5Bpage%5D={i}&tx_solr%5Bq%5D={parola}")
		time.sleep(5)
		differentClasses =["Solr_Results_Item.Solr_Results_Item_Page", "Solr_Results_Item.Solr_Results_Item_File", "Solr_Results_Item.Solr_Results_Item_News"]
		found = False
		for singelClass in differentClasses:
			elements = driver.find_elements(By.CLASS_NAME, singelClass )
			for element in elements:
				seconditem= element.find_element(By.TAG_NAME, "a")
				href = seconditem.get_attribute("href")
				linksFromResearch.append(href)
				found = True
		if not found:
			break
		i += 1
	driver.quit()
	return linksFromResearch

def stGallen(parola):
	linksFromResearch = []
	for t in ['content','news']:
		driver = webdriver.Chrome(options=chrome_options)
		# Open the website
		driver.get(f"https://www.sg.ch/tools/suchen.html#stq={parola}")
		try:
			WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.ID, "st-results-container")))
			# print("Page is ready!")
		except TimeoutException:
			print("Loading took too much time!")
			continue
		try:
			filter_button = driver.find_element("xpath", f"//li[@id='{t}']/a")
		except:
			continue
		filter_button.click()
		time.sleep(5)
		i=1
		while True:
			elements= driver.find_elements("xpath", "//div[@id='st-results-container']//a[@href]")
			if not elements:
				break
			for element in elements:
				href = element.get_attribute("href")
				linksFromResearch.append(href)
			i+=1
			try:
				next_page_button = driver.find_element("xpath", f"//a[@data-page='{i}']")
			except:
				break
			driver.execute_script("arguments[0].click();", next_page_button)
			time.sleep(5)
		driver.quit()
	return linksFromResearch

def thurgau(parola):
	linksFromResearch = []
	siteToSearch=["html_unknown","news","events","course","ausstellung","kuenstler"]
	driver = webdriver.Chrome(options=chrome_options)
	for category in siteToSearch:
		# Open the website
		driver.get(f"https://tgsuche.tg.ch/suche-thurgau.html/1/contenttype/{category}/searchbutton/suchen/searchParams.query/{parola}")
		i = 1
		while True:
			try:
				result = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.CLASS_NAME, "mod-lst.mod-lst-search.reset.search-result-lst.search-result-lst-groupped")))
				# print("Page is ready!")
			except TimeoutException:
				print("Loading took too much time!")
				break
			elements = result.find_elements(By.CLASS_NAME, "mod-entry")
			for element in elements:
				a = element.find_element(By.TAG_NAME,"a")
				href = a.get_attribute("href")
				linksFromResearch.append(href)
			i+=1
			try:
				next_page_button = driver.find_element("xpath", f"//a[@data-page='{i}']")
			except:
				break
			driver.execute_script("arguments[0].click();", next_page_button)
			time.sleep(3)
	driver.quit()
	return linksFromResearch

def aargau (parola):
	linksFromResearch = []
	for t in ['page','medienmitteilung','dienstleistung','event_date']:
		driver = webdriver.Chrome(options=chrome_options)
		driver.get(f"https://www.ag.ch/?search-term={parola}&search-page=100&search-objectType={t}#search")
		try:
			WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.CLASS_NAME, "dyncontent__resultlist")))
			# print("Page is ready!")
		except TimeoutException:
			print("Loading took too much time!")
			continue
		results= driver.find_elements("xpath", "//a[@class='search-result__link' and @href]")
		for linkclass in results:
			href = linkclass.get_attribute("href")
			linksFromResearch.append(href)
		driver.quit()
	return linksFromResearch

def freiburg (parola):
	linksFromResearch = set()
	for t in ['','news','veranstaltungen']:
		i = 1
		running = True
		while running:
			driver = webdriver.Chrome(options=chrome_options)
			driver.get(f"https://www.fr.ch/de/search?q={parola}#gsc.tab=0&gsc.q={parola}{'&gsc.ref=more%3A'+t if t else ''}&gsc.page={i}")
			time.sleep(1)
			try:
				WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.CLASS_NAME, "gsc-webResult.gsc-result")))
				# print("Page is ready!")
			except TimeoutException:
				print("Loading took too much time!")
				break
			results= driver.find_elements("xpath", "//div[@class='gsc-webResult gsc-result' and not(.//div[@class='gs-fileFormat'])]//div[@class='gs-title']/a[@class='gs-title' and @data-ctorig]")
			if not results:
				running = False
			for linkclass in results:
				try:
					href = linkclass.get_attribute("data-ctorig")
					# print(href)
					linksFromResearch.add(href)
				except:
					running = False
			i+=1
			time.sleep(1)
	driver.quit()
	return linksFromResearch

########################################################################################
########################################################################################
# def cityzurich(parola):
#     data=[]
#     typeOfdocument=["webpages","pressrelease","news","publication","publications_statistic", "event","stadtratsbeschluesse","amtliche_mitteilungen","erlass"]
#     for type in typeOfdocument:
#         driver = webdriver.Chrome(options=chrome_options)
#         driver.get("https://www.stadt-zuerich.ch/content/portal/en/index/service/suchen.html?limit=2000&q="+parola+"&id="+type+"&q_type=content&q_area=all#moreItemspressrelease")
#         driver.implicitly_wait(0.5)
#         searchResults= driver.find_element(By.CLASS_NAME, 'ticker')
#         allFound = searchResults.find_elements(By.CLASS_NAME, "row")
#         for singelFound in allFound:
#             link= singelFound.find_element(By.CLASS_NAME, "ticker_link")
#             data.insert(-1,link.get_attribute('href'))	
#     dataset=set(data)
#     data= list(dataset)
#     print ("cityzurich: "+str (len(data)))  
#     return data


# def cityBern(parola):
#     data=[]
#     for i in range(0, 1000, 1):
#         try:
#             driver = webdriver.Chrome(options=chrome_options)
#             driver.get("https://www.bern.ch/en/@@search?facet=true&b_start:int="+str(i*10)+"&facet.field:list=is_service&facet.field:list=object_type&facet.field:list=portal_type&facet.field:list=site_area&SearchableText="+parola)
#             driver.implicitly_wait(0.5)
#             searchResults= driver.find_element(By.CLASS_NAME, 'searchResults')
#             allFound = searchResults.find_elements(By.CLASS_NAME, "contenttype-ftw-simplelayout-contentpage")
#             for singelFound in allFound:
#                 link= singelFound.find_element(By.TAG_NAME, "a")
#                 data.insert(-1,link.get_attribute('href'))
#             allFound = searchResults.find_elements(By.CLASS_NAME, "contenttype-file")
#             for singelFound in allFound:
#                 link= singelFound.find_element(By.TAG_NAME, "a")
#                 data.insert(-1,link.get_attribute('href'))
#             allFound = searchResults.find_elements(By.CLASS_NAME, "contenttype-ftw-simplelayout-textblock is-service")
#             for singelFound in allFound:
#                 link= singelFound.find_element(By.TAG_NAME, "a")
#                 data.insert(-1,link.get_attribute('href'))
#         except:
#             break       
#     dataset=set(data)
#     data= list(dataset)
#     print ("cityBern: "+str (len(data)))  
#     return data


# def cityWinterthur(parola):
#     data=[]
#     for i in range(0, 30, 1):
#         try:
#             driver = webdriver.Chrome(options=chrome_options)
#             driver.get("https://stadt.winterthur.ch/@@search?facet=true&facet.field:list=portal_type&facet.field:list=site_area&b_start:int="+str(i*10)+"&SearchableText="+parola)
#             driver.implicitly_wait(0.5)
#             searchResults= driver.find_element(By.CLASS_NAME, 'searchResults')
#             allFound = searchResults.find_elements(By.CLASS_NAME, "contenttype-ftw-events-eventpage")
#             for singelFound in allFound:
#                 link= singelFound.find_element(By.TAG_NAME, "a")
#                 data.insert(-1,link.get_attribute('href'))
#             allFound = searchResults.find_elements(By.CLASS_NAME, "contenttype-ftw-simplelayout-contentpage")
#             for singelFound in allFound:
#                 link= singelFound.find_element(By.TAG_NAME, "a")
#                 data.insert(-1,link.get_attribute('href'))
#             allFound = searchResults.find_elements(By.CLASS_NAME, "contenttype-ftw-news-news")
#             for singelFound in allFound:
#                 link= singelFound.find_element(By.TAG_NAME, "a")
#                 data.insert(-1,link.get_attribute('href'))
#             allFound = searchResults.find_elements(By.CLASS_NAME, "contenttype-ftw-file-file")
#             for singelFound in allFound:
#                 link= singelFound.find_element(By.TAG_NAME, "a")
#                 data.insert(-1,link.get_attribute('href'))
#             print ("cityWinterthur: "+str (len(data))) 
#         except:
#             break       
#     dataset=set(data)
#     data= list(dataset)
#     print ("cityWinterthur: "+str (len(data)))  
#     return data


# def cityLucern(parola):
#     data=[]
#     driver = webdriver.Chrome(options=chrome_options)
#     driver.get("https://www.stadtluzern.ch/suche?query="+parola+"&selectedTab=website&selectedTabOrder=&selectedTabFilter={}")
#     driver.implicitly_wait(0.5)
#     menunavi= driver.find_element(By.CLASS_NAME,"nav.nav-tabs")
#     singelnavilist= menunavi.find_elements(By.CLASS_NAME,"nav-item")
#     for singelnavi in singelnavilist:
#         driver.execute_script("arguments[0].scrollIntoView();", singelnavi)
#         driver.execute_script("window.scrollBy(0,-200)")
#         singelnavi.click()
#         time.sleep(2)
#         while ( len(driver.find_elements(By.CLASS_NAME, "suchformulartab-paging.icms-btn.icms-btn-primary.icms-btn-block")) > 0):
#             try:
#                 button= driver.find_elements(By.CLASS_NAME, "suchformulartab-paging.icms-btn.icms-btn-primary.icms-btn-block")[0]
#                 driver.execute_script("arguments[0].scrollIntoView();", button)
#                 driver.execute_script("window.scrollBy(0,-200)")
#                 button.click()
#                 time.sleep(1)
#             except:
#                 try:
#                     button= driver.find_elements(By.CLASS_NAME, "suchformulartab-paging.icms-btn.icms-btn-primary.icms-btn-block")[0]
#                     driver.execute_script("arguments[0].scrollIntoView();", button)
#                     driver.execute_script("window.scrollBy(0,-200)")
#                     button.click()
#                     time.sleep(1)
#                 except:
#                     try:
#                         button= driver.find_elements(By.CLASS_NAME, "suchformulartab-paging.icms-btn.icms-btn-primary.icms-btn-block")[1]
#                         driver.execute_script("arguments[0].scrollIntoView();", button)
#                         driver.execute_script("window.scrollBy(0,-200)")
#                         button.click()
#                         time.sleep(1)
#                     except:
#                         try:
#                             button= driver.find_elements(By.CLASS_NAME, "suchformulartab-paging.icms-btn.icms-btn-primary.icms-btn-block")[1]
#                             driver.execute_script("arguments[0].scrollIntoView();", button)
#                             driver.execute_script("window.scrollBy(0,-200)")
#                             button.click()
#                             time.sleep(1)
#                         except:
#                             break
#         time.sleep(10)                      
#         searchResults= driver.find_elements(By.CLASS_NAME, 'tabResult')
#         for searchResult in searchResults:
#             allFound = searchResult.find_elements(By.CLASS_NAME, "row")
#             for singelFound in allFound:
#                 link= singelFound.find_element(By.CLASS_NAME, "entry-title")
#                 link1= link.find_element(By.TAG_NAME, "a")
#                 data.insert(-1,link1.get_attribute('href'))            	
#     dataset=set(data)
#     data= list(dataset)
#     print ("cityLucern: "+str (len(data)))
#     return data


# def cityStGallen(parola):
#     data=[]
#     driver = webdriver.Chrome(options=chrome_options)
#     for i in range(1, 20, 1):
#         try:
#             driver.get("https://www.stadt.sg.ch/tools/suchen.html#stq="+parola+"&stp="+str(i))
#             time.sleep(2)
#             driver.implicitly_wait(0.5)
#             searchResults= driver.find_element(By.CLASS_NAME, "tilebox.tilebox-search")
#             allFound = searchResults.find_elements(By.TAG_NAME, "a")
#             for singelFound in allFound:
#                 data.insert(-1,singelFound.get_attribute('href'))
#         except:
#             break
#     dataset=set(data)
#     data= list(dataset)
#     print ("cityStGallen: "+ str(len(data)))  
#     return data


# def cityLugano(parola):
#     data=[]
#     driver = webdriver.Chrome(options=chrome_options)
#     for i in range(1, 100, 1):
#         driver.get("https://www.lugano.ch/tools/search-results/top/0.html?ajax=true&category=&currentPage="+str(i)+"&typology=&q="+parola+"&order=relevant")
#         time.sleep(2)
#         driver.implicitly_wait(0.5)
#         searchResults= driver.find_element(By.CLASS_NAME, "component")
#         allFound = searchResults.find_elements(By.CLASS_NAME, "search-result.border-top1.mb-3.mb-md-0")
#         for singelFound in allFound:
#             link= singelFound.find_element(By.CLASS_NAME,"color-grey-6")
#             data.insert(-1,link.get_attribute('href'))
#     dataset=set(data)
#     data= list(dataset)
#     print ("cityLugano: "+ str(len(data)))  
#     return data


# def cityBienne(parola):
#     data=[]
#     driver = webdriver.Chrome(options=chrome_options)
#     driver.get("https://www.biel-bienne.ch/en/your-search-results.html/3")
#     searchbox= driver.find_element(By.ID, "search-input")
#     searchbox.send_keys(parola)
#     searchbox.send_keys(Keys.ENTER)
#     time.sleep(2)
#     driver.implicitly_wait(0.5)
#     searchResults= driver.find_element(By.ID, "cms_page")
#     allFound = searchResults.find_elements(By.CLASS_NAME, "mod-entry")
#     for singelFound in allFound:
#         link= singelFound.find_element(By.CSS_SELECTOR,"a")
#         data.insert(-1,link.get_attribute('href'))
#     searchResults= driver.find_element(By.ID, "dam_file")
#     allFound = searchResults.find_elements(By.CLASS_NAME, "mod-entry.mod-entry--file")
#     for singelFound in allFound:
#         link= singelFound.find_element(By.CSS_SELECTOR,"a")
#         data.insert(-1,link.get_attribute('href'))
#     dataset=set(data)
#     data= list(dataset)
#     print ("cityBienne: "+ str(len(data)))  
#     return data
########################################################################################
########################################################################################


german_canton_generator_dict = {
	###
	'freiburg': freiburg,
	'schwyz': schwyz,
	'solothurn': solothurn,
	'stGallen': stGallen,
	'nidwalden': nidwalden,
	'lucerne': lucerne,
	'thurgau': thurgau,
	'aargau': aargau,
	'schaffhausen': schaffhausen,
	###
	'graubunden': graubunden,
	'obwalden': obwalden,
	'glarus': glarus,
	'zurich': zurich,
	'bern': bern,
	'zug': zug,
	'baselStadt': baselStadt,
	'uri': uri,
	'appenzellInneroden': appenzellInneroden,
	'appenzellAusserroden': appenzellAusserroden,
	'baselLandschaft': baselLandschaft,
}

os.makedirs(data_dir_name, exist_ok=True)

allCantonsData = []
for canton,link_gen in german_canton_generator_dict.items():
	canton_links = set()
	for k in keyword_list:
		links_for_k = link_gen(k)
		links_for_k = map(lambda x: re.sub(r'\?searchterm=.+','',x), links_for_k)
		links_for_k = filter(lambda x: not has_forbidden_format(x.lower()), links_for_k)
		links_for_k = set(links_for_k)
		print (f"{canton} | {k}: {len(links_for_k)}")
		canton_links.update(links_for_k)
	canton_links = list(canton_links)
	print (f"{canton}: {len(canton_links)}")
	allCantonsData += map(lambda x: (canton,x), canton_links)
	with open(os.path.join(data_dir_name, f"{canton}.json"), "w") as f:
	    f.write(json.dumps(canton_links, indent=4))

with open(os.path.join(data_dir_name, "all_data.csv"), "w") as f:
	f.write('\n'.join(map(';'.join, [('canton','link')]+allCantonsData)))
