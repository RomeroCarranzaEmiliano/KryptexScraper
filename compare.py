"""
	compare.py
"""

import pickle
from pulp import *
import matplotlib.pyplot as plt

class Row():
	def __init__(self, row):
		self.model = row[0]
		self.price = row[1]
		self.ETH = row[2]
		self.ETC = row[3]
		self.UBQ = row[4]
		self.RVN = row[5]
		self.BEAM = row[6]
		self.monthly_winning = row[7]
		self.days = row[8]


def loadData(filename="gpu_table.data"):
	"""
	"""
	file = open(filename, "rb")
	data = pickle.load(file)
	file.close()

	return data


def trimData(data, budget):
	"""
	"""
	trimed_data = []
	for element in data:
		if float(element.price) < float(budget):
			trimed_data.append(element)
	return trimed_data


def getPowerBill(power_consumption):
	"""
	"""
	power_billing = {
		"[0, 120]": [81.1406, 5,35605, 0],
		"[120, 500]": [112.68, 6.51891, 8.45600],
		"[500, 700]": [163.7425, 7.70296,  9,71500],
		"[700, None]": [163.7425, 8.65052, 10.92850]
	}
	bill = 0
	consumption_range = [0, 0]
	if power_consumption < 700:
		if power_consumption < 500:
			if power_consumption < 120:
				consumption_range = [0, 120]
			else:
				consumption_range = [120, 500]
		else:
			consumption_range = [500, 700]
	else:
		consumption_range = [700, None]

	bill = power_billing[str(consumption_range)][0]
	bill += power_billing[str(consumption_range)][1]*120
	bill += power_billing[str(consumption_range)][2]*(power_consumption-120)

	return bill


def problemDefinition(data, budget, gpu_quantity, power, category):
	"""
		max Z = GPU1*RETURN1 + GPU2*RETURN2 + ... GPU_N*RETURN_N
		S.A.
			GPU1 + GPU2 + ..., + GPU_N <= n max of gpu to buy
			GPU1*PRICE1 + GPU2*PRICE2 + ... + GPU_N*PRICE_N <= initial investment available
			GPU1, GPU2, ... , GPU_N Binary Integers
	"""
	category_list = ["l120", "l500", "l700", "l+"]
	category_top = {
		"l120": 120,
		"l500": 500,
		"l700": 700,
		"l+": 10000000
	}
	category_cost = {
		"l120": [81.1406, 5.35605, 0],
		"l500": [112.68, 6.51891, 8.45600],
		"l700": [163.7425, 7.70296,  9.71500],
		"l+": [163.7425, 8.65052, 10.92850]
	}
	gpus_list = []
	gpus_winnings = {}
	gpus_prices = {}
	gpus_power = {}

	motherboard_cost_per_gpu = 45
	cpu_cost = 35
	memory_cost = 25
	power_supply_cost = 105
	other_cost = 48

	fixed_costs = cpu_cost + memory_cost + power_supply_cost + other_cost
	budget = float(budget) - float(fixed_costs)

	base_power_consumption = 2.5*30

	for element in data:
		model = element.model.replace("-", "_").replace(" ", "_")
		gpus_list.append(model)
		gpus_prices[model] = float(element.price)
		gpus_winnings[model] = float(element.monthly_winning)
		gpus_power[model] = float(element.power_consumption)

	prob = LpProblem("GPU_Optimal_Array_for_mining", LpMaximize)
	gpus_chosen = LpVariable.dicts("Chosen", gpus_list, 0, 1, cat='Integer')
	first_120 = LpVariable("First_120")
	rest_120 = LpVariable("Rest_120")
	rest = LpVariable("Rest")
	total_cost = LpVariable("Total_cost")
	total_earning = LpVariable("Total_earning")
	gpu_budget = LpVariable("Gpu_budget")
	used_budget = LpVariable("Used_budget")
	not_used_budget = LpVariable("Not_used_budget")
	usd = 221

	# Objective function
	prob += total_earning - total_cost

	# First 120 kWh restriction
	prob += first_120 + rest_120 + base_power_consumption == 120, "First120Restriction"
	prob += first_120 >= 0

	# Rest kWh restriction
	prob += rest + rest_120 == rest, "RestRestriction"
	prob += first_120 + rest <= category_top[category_list[category]], "TopRestriction"

	# Lower limit restriction
	prob += lpSum([gpus_chosen[i]*gpus_power[i]*24*30/1000 for i in gpus_list]) == first_120 + rest, "LowerLimitRestriction"

	# Power cost restrictions
	prob += category_cost[category_list[category]] + first_120*category_cost[category_list[category]][1] == total_cost, "PowerCostRestriction"

	# Earnings restriction
	prob += lpSum([gpus_chosen[i]*gpus_winnings[i] for i in gpus_list])*usd*30 == total_earning, "TotalEarnings"

	# Budget restriction
	prob += lpSum([gpus_chosen[i]*gpus_prices[i] for i in gpus_list]) <= used_budget + not_used_budget, "BudgetMaximum"
	prob += used_budget + not_used_budget == gpu_budget

	prob += lpSum([gpus_chosen[i]*motherboard_cost_per_gpu for i in gpus_list]) + gpu_budget == float(budget)
	# GPU quantity restriction
	prob += lpSum([gpus_chosen[i] for i in gpus_list]) <= int(gpu_quantity), "GpuMaximum"

	total_power_consumption = 0
	result = {
		"Category": category_list[category],
		"Total earning": 0,
		"Total cost": 0,
		"Benefits": 0,
		"Total power consumption": 0,
		"Gpu in use": 0,
		"Used budget": 0,
		"ROI": 0,
		"Vars": []
	}
	prob.solve()
	print("Status: ", LpStatus[prob.status])
	print("-"*80)
	for v in prob.variables():
		if v.varValue > 0:
			var = v.name+"="+str(v.varValue)
			result["Vars"].append(var)
			if v.name[0:7] == "Chosen_":
				result["Gpu in use"] += 1
				model = v.name.replace("Chosen_", "")
				total_power_consumption += gpus_power[model]
			if v.name == "Total_cost":
				result["Total cost"] = float(v.varValue)
			if v.name == "Total_earning":
				result["Total earning"] = float(v.varValue)
			if v.name == "Not_used_budget":
				result["Used budget"] = budget - float(v.varValue)

	result["Total power consumption"] = total_power_consumption
	result["Benefits"] = (result["Total earning"] - result["Total cost"])/usd
	result["ROI"] = (result["Used budget"]/result["Benefits"])/12

	return result


def main():
	budget = input("Budget(USD): ")
	max_gpu_quantity = input("Max GPU quantity: ")
	#power = input("kWh cost: ")
	#power = float(power)
	power = 0

	data = loadData()
	data = trimData(data, budget)

	func = {"l120": [], "l500": [], "l700": [], "l+": []}
	func2 = {"l120": [], "l500": [], "l700": [], "l+": []}
	for k in range(1, int(max_gpu_quantity)+1):
		gpu_quantity = k
		results = []
		for i in range(4):
			category = i
			results.append(problemDefinition(data, budget, gpu_quantity, power, category))

		print("="*80)
		print("Results")
		print("="*80)
		print("Budget: ", budget)
		print("Max GPU quantity: ", gpu_quantity)
		print("_"*80)

		for i in results:
			print("Category: ", i["Category"])
			print("Benefits: ", i["Benefits"])
			print("Total power consumption: ", i["Total power consumption"])
			func[i["Category"]].append(float(i["Benefits"]))
			func2[i["Category"]].append(float(i["ROI"]))
			for j in i["Vars"]:
				print(j)
			print("-"*80)

	fig1 = plt.figure()
	fig2 = plt.figure()
	ax1 = fig1.add_subplot(111)
	ax2 = fig2.add_subplot(111)

	f1, = ax1.plot(func["l120"], label="l120")
	f2, = ax1.plot(func["l500"], label="l500")
	f3, = ax1.plot(func["l700"], label="l700")
	f4, = ax1.plot(func["l+"], label="l+")

	ax1.set_xlabel("n of GPU\'s")
	ax1.set_ylabel("Monthly benefit in USD")

	f21, = ax2.plot(func2["l120"], label="l120")
	f22, = ax2.plot(func2["l500"], label="l500")
	f23, = ax2.plot(func2["l700"], label="l700")
	f24, = ax2.plot(func2["l+"], label="l+")

	ax2.set_xlabel("n of GPU\'s")
	ax2.set_ylabel("ROI(years)")

	plt.xticks(range(1, int(max_gpu_quantity)+1))


	leg = plt.legend(loc="center")
	plt.show()



if __name__ == "__main__":
	main()