import re
import json
import math
import sys

REPORT_NO_REV = (1<<1)
REPORT_NO_EXP = (1<<2)
REPORT_NO_ITEMS = (1<<3)
REPORT_REJECTED_REV = (1<<4)
REPORT_REJECTED_EXP = (1<<5)

#REPORT_DEBUG = REPORT_NO_REV | REPORT_NO_EXP | REPORT_NO_ITEMS
#REPORT_DEBUG = REPORT_NO_ITEMS
#REPORT_DEBUG = REPORT_REJECTED_REV | REPORT_REJECTED_EXP
REPORT_DEBUG = 0

def main(inp, out):
	with open(inp) as f:
		data = f.read()

		deps = {}

		for x in re.finditer("([A-Z ]+)(?:DEPARTMENT:\s*)([0-9]{4})\s*([A-Z ]+)(?:\s*PROGRAM)", data):
			depno = x.group(2)
			depna = x.group(3).strip()

			if depna in deps:
				continue

			deps[depna] = {
					"revenue": 0.0,
					"expenditures": 0.0,
					"fund": x.group(1).strip(),
					"revenue_items": [],
					"expenditure_items": {},
				}

			m = re.search("(?:DEPARTMENT:\s*[0-9]{4}\s*"+depna+"\s*PROGRAM)(.*?)(?:"+depna+"\s*TOTAL\s*REV\s*)([0-9,\.-]+|\s*)(?:.*?TOTAL\s*EXP\s*)([0-9,\.-]+|\s*)", data, flags=re.DOTALL)
			if m:
				#print(depna)

				# General Summary
				revenue = m.group(2).strip().replace(",", "")
				if revenue:
					if revenue.endswith('-'):
						deps[depna]['revenue'] = -float(revenue[:-1])
					else:
						deps[depna]['revenue'] = float(revenue)

				expenditures = m.group(3).strip().replace(",", "")
				if m.group(3).strip():
					if expenditures.endswith('-'):
						deps[depna]["expenditures"] = -float(expenditures[:-1])
					else:
						deps[depna]["expenditures"] = float(expenditures)

				total_items = 0 # Used to find empty deps

				# Revenue items
				revenue_items_s = re.search("(?:REVENUES)(.*?)(?:EXPENDITURE)", m.group(1), flags=re.DOTALL)
				if revenue_items_s:
					revenue_items = re.findall("([ ]{3}[0-9]{5})(.{47})", revenue_items_s.group(1))

					for _, i in revenue_items:
						total_items += 1
						ri = re.match("([a-zA-Z0-9 /\-&\.\(\)':,]+)\s+([0-9,\.]+)([ ]|-)", i)
						if ri:
							deps[depna]["revenue_items"].append((ri.group(1).strip(), float((ri.group(3)+ri.group(2)).replace(",", ""))))
						elif REPORT_DEBUG & REPORT_REJECTED_REV:
							print(depna, "Rejected rev line:", i)

				if not deps[depna]['revenue_items']:
					deps[depna]['revenue'] = 0.0
					if REPORT_DEBUG & REPORT_NO_REV:
						print(depna, "No Revenue items")

				sum = 0
				for i in deps[depna]['revenue_items']:
					sum += i[1]
				if math.fabs(sum - deps[depna]['revenue']) > 1:
					print(depna, "Non-matching revenues!", sum, deps[depna]['revenue'])

				# Expenditure items
				for x in re.finditer("(EXPENDITURE[A-Z\-]+)", m.group(1)):
					exp = x.group(1)
					deps[depna]['expenditure_items'][exp] = []

					exp_items_s = re.search("(?:"+exp+")(.*?)(?:(?:EXPENDITURE)|(?:TOTAL REV))", m.group(1), flags=re.DOTALL)
					exp_items = re.findall("([ ]{3}[0-9]{5})(.{47})", exp_items_s.group(1))

					for _, i in exp_items:
						total_items += 1

						#print(i)
						ei = re.match("([a-zA-Z0-9 /\-&\.\(\)':,]+)\s+([0-9,\.]+)([ ]|-)", i)
						if ei:
							deps[depna]['expenditure_items'][exp].append((ei.group(1).strip(), float((ei.group(3)+ei.group(2)).replace(",", ""))))
						elif REPORT_DEBUG & REPORT_REJECTED_EXP:
							print(depna, "Rejected exp line:", i)

					if not deps[depna]['expenditure_items'][exp]:
						del deps[depna]['expenditure_items'][exp]

				#print(depna, deps[depna]['expenditure_items'])

				if not deps[depna]['expenditure_items']:
					deps[depna]['expenditures'] = 0.0
					if REPORT_DEBUG & REPORT_NO_EXP:
						print(depna, "No expenditure items")

				sum = 0
				for i in deps[depna]['expenditure_items'].values():
					for j in i:
						sum += j[1]
				if math.fabs(sum - deps[depna]['expenditures']) > 1:
					print(depna, "Non-matching expenditures!", sum, deps[depna]['expenditures'])

				if total_items == 0 and REPORT_DEBUG & REPORT_NO_ITEMS:
					print(depna, "No line items")

			else:
				print(depna, "Not found")

			#break

		#print(json.dumps(deps, indent=4))
		with open(out, "w") as wf:
			json.dump(deps, wf)

if __name__ == '__main__':
	if len(sys.argv) != 3:
		print("usage: python", sys.argv[0], "input output")

	main(sys.argv[1], sys.argv[2])