"""
	compare.py
"""

import pickle
from pulp import *

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


def problemDefinition(data, budget, gpu_quantity, power):
	"""
		max Z = GPU1*RETURN1 + GPU2*RETURN2 + ... GPU_N*RETURN_N
		S.A.
			GPU1 + GPU2 + ..., + GPU_N <= n max of gpu to buy
			GPU1*PRICE1 + GPU2*PRICE2 + ... + GPU_N*PRICE_N <= initial investment available
			GPU1, GPU2, ... , GPU_N Binary Integers
	"""
	gpus_list = []
	gpus_winnings = {}
	gpus_prices = {}
	gpus_power = {}

	for element in data:
		model = element.model.replace("-", "_").replace(" ", "_")
		gpus_list.append(model)
		gpus_prices[model] = float(element.price)
		gpus_winnings[model] = float(element.monthly_winning)
		gpus_power[model] = float(element.power_consumption)

	prob = LpProblem("GPU_Optimal_Array_for_mining", LpMaximize)
	gpus_chosen = LpVariable.dicts("Chosen", gpus_list, 0, 1, cat='Integer')

	# Objective function
	prob += lpSum([gpus_chosen[i]*gpus_winnings[i] - gpus_chosen[i]*gpus_power[i]*(24/1000)*power for i in gpus_list])

	# Budget restriction
	prob += lpSum([gpus_chosen[i]*gpus_prices[i] for i in gpus_list]) <= float(budget), "BudgetMaximum"
	# GPU quantity restriction
	prob += lpSum([gpus_chosen[i] for i in gpus_list]) <= int(gpu_quantity), "GpuMaximum"

	print(gpus_power)

	total_power_consumption = 0
	prob.solve()
	print("Status: ", LpStatus[prob.status])
	for v in prob.variables():
		if v.varValue > 0:
			print(v.name, "=", v.varValue)
			model = v.name.replace("Chosen_", "")
			total_power_consumption += gpus_power[model]

	print("Total power consumption:", total_power_consumption)

	return "OK"


def main():
	budget = input("Budget(USD): ")
	gpu_quantity = input("GPU quantity: ")
	power = input("kWh cost: ")
	power = float(power)

	data = loadData()
	data = trimData(data, budget)

	problemDefinition(data, budget, gpu_quantity, power)


if __name__ == "__main__":
	main()