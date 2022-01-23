"""
	main.py
"""

from bs4 import BeautifulSoup
import requests
import pickle
import re
import time

print("[START]")

class Row():
	def __init__(self, row):
		self.model = row[0]
		self.price = row[1]
		self.ETH = row[2]
		self.ETC = row[3]
		self.EXP = row[4]
		self.UBQ = row[5]
		self.RVN = row[6]
		self.BEAM = row[7]
		self.monthly_winning = row[8]
		self.days = row[10]


def getDocument(url):
	"""
	"""
	request = requests.get(url)
	return request.content


def getParsedRow(row):
	"""
	"""
	row = row.replace("Mh/s","").replace("H/s","").replace("días","")
	row = row.split()

	counter = 0
	for element in row:
		if element.split()[0][0] == "$":
			del row[1:counter]
			break;
		elif counter != 0:
			row[0] = row[0] + " " + element
		counter += 1

	for i in range(len(row)):
		row[i] = row[i].replace("$","")

	print(row)

	return(row)


def scrap(document):
	"""
		Scrap the website and get the table as an array of dicts
	"""

	soup = BeautifulSoup(document, 'html.parser')
	table = soup.find(class_="page-main")
	table = table.find(class_="bg-white pt-3 pb-6 pb-lg-5")
	table = table.find(class_="container pb-6")
	table = table.find_all(class_="row")
	table = table[1].find(class_="col-12")
	table = table.find(class_="table table--mobile-list table--bordered")
	table = table.find("tbody")

	rows = table.find_all("tr")

	new_table = []
	for row in rows:
		parsed_row = getParsedRow(str(row.get_text()))
		row = Row(parsed_row)
		print(row.model, row.monthly_winning)
		new_table.append(row)

	return new_table


def dumpData(table):
	"""
	"""
	filename = "gpu_table.data"
	file = open(filename, "wb")
	pickle.dump(table, file)
	file.close()


def main():
	"""
	"""
	url = "https://www.kryptex.org/es/best-gpus-for-mining"
	document = getDocument(url)
	table = scrap(document)
	dumpData(table)
	print("[END]")

if __name__ == "__main__":
	main()
