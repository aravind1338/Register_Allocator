import string
import random
import sys
import gc

class ILOCInstruction():
	"""docstring for ILOCInstruction"""

	"""list of opcodes"""
	opcodes = {"load" : 0, "loadI" : 0, "add" : 0, "sub": 0, "mult": 0, "output": 0, "store": 0, "lshift": 0, "rshift": 0}

	"""list of virtual registers and their frequencies"""
	registers = {}

	"""List of virtual registers in decreasing order of frequency"""
	ordered_register_list = []

	"""List of all the original instructions, represented as lists"""
	original_instruction_list = []

	"""list of final instructions including loadAI and storeAI"""
	final_instruction_list = []

	"""List of virtual registers that are allocated real registers"""
	allocated_real_registers = []

	"""list of real, usable registers"""
	usable_registers = []

	"""feasible registers: virtual registers"""
	register_f2 = ""
	register_f1 = ""
	feasible_registers = {}

	"""Mapping virtual to real, usable registers"""
	map_virtual_to_real_registers = {}

	"""Dictionary of unassigned virtual registers and their offsets"""
	register_to_offset = {}
	offset_counter = -4



	"""of the form ra : [0, 1, 2]"""
	live_ranges = {}
	"""of the form 0 : [ra, rb]"""
	active_reg_for_instruction = {}
	"""tracking what real register is mapped to what virtual register"""
	real_to_virtual = {}
	"""virtual registers that should be spilled"""
	spilled_reg = []
	"""virtual registers that have to be spilled on each line. Of the form 1 : [r1, r2]"""
	to_be_spilled = {}


	"""list of virtual registers that are currently spilled"""
	currently_spilled = []
	instr_index = 0

	def __init__(self, opcode = None, vr1 = None, vr2 = None, imm = None, vr3 = None, offset = None):
		self.opcode = opcode
		self.vr1 = vr1
		self.vr2 = vr2
		self.imm = imm
		self.vr3 = vr3
		self.offset = offset

	"""Method to create an instruction given the components"""
	def write_final_instruction_to_file(self):

		gc.collect()
		
		final_instruction = ""

		for instruction in self.final_instruction_list:

			if instruction[0] == "add" or instruction[0] == "sub" or instruction[0] == "mult" or instruction[0] == "lshift" or instruction[0] == "rshift":
				final_instruction = instruction[0] + " " + instruction[1] + ", " + instruction[2] + " => " + instruction[3]
			elif instruction[0] == "loadI" or instruction[0] == "load" or instruction[0] == "store" or instruction[0] == "loadAI" or instruction[0] == "storeAI":
				final_instruction = instruction[0] + " " + instruction[1] + " => " + instruction[2]
			elif instruction[0] == "output":
		  		final_instruction = instruction[0] + " " + instruction[1]
			else:
				pass

			sys.stdout.write(final_instruction + "\n")

	"""Given the threshold, return a list of spillable registers for that instruction"""
	def spill(self, threshold, active_registers):

		gc.collect()

		spillable_registers = []
		temp_active_registers = {}

		for key, value in self.registers.iteritems():
			if key in active_registers:
				temp_active_registers[key] = value

		"""temp_active_registers contains the live registers of a particular instruction and its frequencies"""

		frequencies = set(val for val in temp_active_registers.values())
		frequencies = sorted(frequencies)
		"""frequencies is a list of all the frequencies of the live registers in increasing order"""

		spill = []

		for item in frequencies:
		  for reg, value in temp_active_registers.iteritems():
		    if value == item and len(spill) < threshold:
		      spill.append(reg)

		return spill

	"""Method to allocate a real register to a given virtual register"""
	def allocate(self, virtual_register, index):
		
		gc.collect()

		for real_register in self.real_to_virtual:
			if self.real_to_virtual[real_register] == None:
				self.real_to_virtual[real_register] = virtual_register
				return real_register

		"""Every real register is allocated, need to free one up"""
		for real_register in self.real_to_virtual:
			reg = self.real_to_virtual[real_register]
			live_range = self.live_ranges[reg]

			if index > live_range[len(live_range) - 1]:
				self.real_to_virtual[real_register] = virtual_register
				return real_register

		return None

	"""The top down allocator discussed in class"""
	def top_down_allocator(self, num_registers):

		ILOCInstruction.create_real_and_feasible_register_list(self, num_registers, "t")

		num_registers = num_registers - 2

		"""Initialize the real_to_virtual mapping"""
		for register in self.usable_registers:
			self.real_to_virtual[register] = None

		"""Give every virtual register a fixed space in memory"""
		for virtual_register in self.ordered_register_list:
			if virtual_register != 'r0':
				self.register_to_offset[virtual_register] = "r0, " + str(self.offset_counter)
				self.offset_counter = self.offset_counter - 4

		"""Implement class top-down algorithm"""

		for instruction, active_registers in self.active_reg_for_instruction.iteritems():

			if len(active_registers) > num_registers:
				threshold = len(active_registers) - num_registers
				"""Maxlive > #physical registers"""
				self.to_be_spilled[instruction] = ILOCInstruction.spill(self, threshold, active_registers)


		for key, value in self.to_be_spilled.iteritems():
			for item in value:
				if item not in self.spilled_reg:
					self.spilled_reg.append(item)


		gc.collect()

		for index, instruction in enumerate(self.original_instruction_list):

			for comp in instruction:
				tempindex = instruction.index(comp)
				temp = comp.replace(',', '')
				instruction[tempindex] = temp

			lhs = []
			rhs = []

			if instruction[0] == "add" or instruction[0] == "sub" or instruction[0] == "mult" or instruction[0] == "lshift" or instruction[0] == "rshift":
				lhs = instruction[:3]
				rhs = instruction[3:]

			elif instruction[0] == "loadI" or instruction[0] == "load" or instruction[0] == "store":
				lhs = instruction[:2]
				rhs = instruction[2:]

			elif instruction[0] == "output":
				lhs = instruction
				rhs = []

			else:
				pass

			self.final_instruction_list.append(instruction)

			previously_used_feasible_register = None

			index_of_instruction = len(self.final_instruction_list) - 1

			for item_index, item in enumerate(lhs):

				if item in self.spilled_reg:

					if self.feasible_registers[self.register_f1] == None:
						previously_used_feasible_register = self.register_f1
						tempReg = self.register_f1
						self.feasible_registers[self.register_f1] = item

					elif self.feasible_registers[self.register_f2] == None:
						previously_used_feasible_register = self.register_f2
						tempReg = self.register_f2
						self.feasible_registers[self.register_f2] = item

					else:
						if previously_used_feasible_register == self.register_f1:
							previously_used_feasible_register = self.register_f2
							tempReg = self.register_f2
						else:
							previously_used_feasible_register = self.register_f1
							tempReg = self.register_f1

						self.feasible_registers[tempReg] = item

					instruction[item_index] = tempReg
					offset = self.register_to_offset[item]
					new_instruction = ["loadAI", offset, tempReg]
					
					self.final_instruction_list.insert(index_of_instruction, new_instruction)
					index_of_instruction += 1

				elif item != 'r0' and item[0] == 'r' and item != 'rshift' and item not in self.real_to_virtual.values():
					reg = ILOCInstruction.allocate(self, item, index)
					instruction[item_index] = reg

				else:
					for real, virtual in self.real_to_virtual.iteritems():
						if virtual == item:
							instruction[item_index] = real
							break

			gc.collect()

			for index_2, item in enumerate(rhs):

				item_index = len(instruction) + index_2 - len(rhs)

				if item in self.spilled_reg:

					if self.feasible_registers[self.register_f1] == None:
						previously_used_feasible_register = self.register_f1
						tempReg = self.register_f1
						self.feasible_registers[self.register_f1] = item

					elif self.feasible_registers[self.register_f2] == None:
						previously_used_feasible_register = self.register_f2
						tempReg = self.register_f2
						self.feasible_registers[self.register_f2] = item
					else:
						if previously_used_feasible_register == self.register_f1:
							previously_used_feasible_register = self.register_f2
							tempReg = self.register_f2
						else:
							previously_used_feasible_register = self.register_f1
							tempReg = self.register_f1

						self.feasible_registers[tempReg] = item


					instruction[item_index] = tempReg
					offset = self.register_to_offset[item]

					if instruction[0] == "store":

						new_instruction_2 = ["loadAI", offset, tempReg]
						self.final_instruction_list.insert(index_of_instruction, new_instruction_2)
						index_of_instruction += 1

					else:

						new_instruction = ["storeAI", tempReg, offset]
						self.final_instruction_list.insert(index_of_instruction + 1, new_instruction)
						self.feasible_registers[tempReg] = None

				elif item != 'r0' and item[0] == 'r' and item != 'rshift' and item not in self.real_to_virtual.values():
					reg = ILOCInstruction.allocate(self, item, index)
					instruction[item_index] = reg

				else:
					for real, virtual in self.real_to_virtual.iteritems():
						if virtual == item:
							instruction[item_index] = real

			self.final_instruction_list[index_of_instruction] = instruction

		gc.collect()

		ILOCInstruction.write_final_instruction_to_file(self)

	"""Method to create lists of real and feasible registers"""
	def create_real_and_feasible_register_list(self, num_registers, allocator):
		x = 1

		if allocator != "b":
			num_registers = num_registers - 2

		while x <= num_registers:
			register = "r" + str(x)
			self.usable_registers.append(register)
			x += 1

		gc.collect()

		self.register_f1 = "r" + str(x)
		self.register_f2 = "r" + str(x+1)
		self.feasible_registers[self.register_f1] = None
		self.feasible_registers[self.register_f2] = None

	"""Modifies and adds appropriate instructions by looking at original_instruction_list"""
	def EAC_top_down_allocator(self, num_registers):
		"""Get rid of commas"""

		temp_num_reg = num_registers - 2

		self.allocated_real_registers = self.ordered_register_list[:temp_num_reg]

		ILOCInstruction.create_real_and_feasible_register_list(self, num_registers, "s")

		"""Map every un-allocated register an offset of the type r0, -x"""
		for virtual_register in self.ordered_register_list:
			if virtual_register not in self.allocated_real_registers and virtual_register != 'r0':
				self.register_to_offset[virtual_register] = "r0, " + str(self.offset_counter)
				self.offset_counter = self.offset_counter - 4

		"""Implement top down EAC algorithm"""

		lhs = []
		rhs = []

		gc.collect()

		for instruction in self.original_instruction_list:

			for comp in instruction:
				tempindex = instruction.index(comp)
				temp = comp.replace(',', '')
				instruction[tempindex] = temp

			self.final_instruction_list.append(instruction)

			index_of_instruction = len(self.final_instruction_list) - 1

			new_instruction = []

			if instruction[0] == "add" or instruction[0] == "sub" or instruction[0] == "mult" or instruction[0] == "lshift" or instruction[0] == "rshift":
				lhs = instruction[:3]
				rhs = instruction[3:]

			elif instruction[0] == "loadI" or instruction[0] == "load" or instruction[0] == "store":
				lhs = instruction[:2]
				rhs = instruction[2:]

			elif instruction[0] == "output":
				lhs = instruction
				rhs = []

			else:
				pass


			previously_used_feasible_register = None

			"""add loadAI's"""
			for index, item in enumerate(lhs):

				item_index = index

				if item in self.register_to_offset:

					if self.feasible_registers[self.register_f1] == None:
						previously_used_feasible_register = self.register_f1
						tempReg = self.register_f1
						self.feasible_registers[self.register_f1] = item

					elif self.feasible_registers[self.register_f2] == None:
						previously_used_feasible_register = self.register_f2
						tempReg = self.register_f2
						self.feasible_registers[self.register_f2] = item

					else:
						if previously_used_feasible_register == self.register_f1:
							previously_used_feasible_register = self.register_f2
							tempReg = self.register_f2
						else:
							previously_used_feasible_register = self.register_f1
							tempReg = self.register_f1

						self.feasible_registers[tempReg] = item

					instruction[item_index] = tempReg
					offset = self.register_to_offset[item]
					new_instruction = ["loadAI", offset, tempReg]
					
					self.final_instruction_list.insert(index_of_instruction, new_instruction)
					index_of_instruction += 1

				elif item not in self.map_virtual_to_real_registers and item[0] == 'r' and item[1] != '0' and item != 'rshift':
					self.map_virtual_to_real_registers[item] = self.usable_registers[0]
					del self.usable_registers[0]

					instruction[item_index] = self.map_virtual_to_real_registers[item]

				elif item in self.map_virtual_to_real_registers:

					instruction[item_index] = self.map_virtual_to_real_registers[item]

				else:
					pass

			gc.collect()

			for index, item in enumerate(rhs):

				item_index = len(instruction) + index - len(rhs)

				if item in self.register_to_offset:

					if self.feasible_registers[self.register_f1] == None:
						previously_used_feasible_register = self.register_f1
						tempReg = self.register_f1
						self.feasible_registers[self.register_f1] = item

					elif self.feasible_registers[self.register_f2] == None:
						previously_used_feasible_register = self.register_f2
						tempReg = self.register_f2
						self.feasible_registers[self.register_f2] = item
					else:
						if previously_used_feasible_register == self.register_f1:
							previously_used_feasible_register = self.register_f2
							tempReg = self.register_f2
						else:
							previously_used_feasible_register = self.register_f1
							tempReg = self.register_f1

						self.feasible_registers[tempReg] = item


					instruction[item_index] = tempReg
					offset = self.register_to_offset[item]

					if instruction[0] == "store":

						new_instruction_2 = ["loadAI", offset, tempReg]
						self.final_instruction_list.insert(index_of_instruction, new_instruction_2)
						index_of_instruction += 1

					else:

						new_instruction = ["storeAI", tempReg, offset]
						self.final_instruction_list.insert(index_of_instruction + 1, new_instruction)
						self.feasible_registers[tempReg] = None

				elif item not in self.map_virtual_to_real_registers and item[0] == 'r' and item[1] != '0' and item != 'rshift':
					self.map_virtual_to_real_registers[item] = self.usable_registers[0]
					del self.usable_registers[0]
					
					instruction[item_index] = self.map_virtual_to_real_registers[item]

				elif item in self.map_virtual_to_real_registers:

					instruction[item_index] = self.map_virtual_to_real_registers[item]

				else:
					pass

			self.final_instruction_list[index_of_instruction] = instruction

		ILOCInstruction.write_final_instruction_to_file(self)

	def bottom_up_allocator(self, num_registers):

		ILOCInstruction.create_real_and_feasible_register_list(self, num_registers, "b")

		for key, value in self.live_ranges.iteritems():
			value.append(1500)

		"""Initialize the real_to_virtual mapping"""
		for register in self.usable_registers:
			self.real_to_virtual[register] = None

		"""Give every virtual register a fixed space in memory"""
		for virtual_register in self.ordered_register_list:
			if virtual_register != 'r0':
				self.register_to_offset[virtual_register] = "r0, " + str(self.offset_counter)
				self.offset_counter = self.offset_counter - 4


		gc.collect()

		for index, instruction in enumerate(self.original_instruction_list):

			for comp in instruction:
				tempindex = instruction.index(comp)
				temp = comp.replace(',', '')
				instruction[tempindex] = temp

			lhs = []
			rhs = []

			if instruction[0] == "add" or instruction[0] == "sub" or instruction[0] == "mult" or instruction[0] == "lshift" or instruction[0] == "rshift":
				lhs = instruction[:3]
				rhs = instruction[3:]

			elif instruction[0] == "loadI" or instruction[0] == "load" or instruction[0] == "store":
				lhs = instruction[:2]
				rhs = instruction[2:]

			elif instruction[0] == "output":
				lhs = instruction
				rhs = []

			else:
				pass

			self.final_instruction_list.append(instruction)

			self.instr_index = len(self.final_instruction_list) - 1

			original_index_of_instruction = index

			for item_index, item in enumerate(lhs):

				if item in self.currently_spilled:

					reg = ILOCInstruction.allocate_reg_bottom_up(self, item, original_index_of_instruction, item_index, instruction, "l")

					self.currently_spilled.remove(item)

					instruction[item_index] = reg
					offset = self.register_to_offset[item]
					new_instruction = ["loadAI", offset, reg]
					
					self.final_instruction_list.insert(self.instr_index, new_instruction)
					self.instr_index += 1

				elif item != 'r0' and item[0] == 'r' and item != 'rshift' and item not in self.real_to_virtual.values():
					reg = ILOCInstruction.allocate_reg_bottom_up(self, item, original_index_of_instruction, item_index, instruction, "l")
					instruction[item_index] = reg

				else:
					for real, virtual in self.real_to_virtual.iteritems():
						if virtual == item:
							instruction[item_index] = real
							break

			gc.collect()

			for index_2, item in enumerate(rhs):

				item_index = len(instruction) + index_2 - len(rhs)

				if item in self.currently_spilled:

					reg = ILOCInstruction.allocate_reg_bottom_up(self, item, original_index_of_instruction, item_index, instruction, "r")

					if instruction[0] == "store":

						offset = self.register_to_offset[item]
						new_instruction_2 = ["loadAI", offset, reg]
						self.final_instruction_list.insert(self.instr_index, new_instruction_2)
						self.instr_index += 1

					self.currently_spilled.remove(item)

					instruction[item_index] = reg

				elif item != 'r0' and item[0] == 'r' and item != 'rshift' and item not in self.real_to_virtual.values():
					reg = ILOCInstruction.allocate_reg_bottom_up(self, item, original_index_of_instruction, item_index, instruction, "r")
					instruction[item_index] = reg

				else:
					for real, virtual in self.real_to_virtual.iteritems():
						if virtual == item:
							instruction[item_index] = real

			self.final_instruction_list[self.instr_index] = instruction

		gc.collect()

		ILOCInstruction.write_final_instruction_to_file(self)

	def allocate_reg_bottom_up(self, virtual_register, original_index_of_instruction, item_index, instruction, side):

		for real_register in self.real_to_virtual:
			if self.real_to_virtual[real_register] == None:
				self.real_to_virtual[real_register] = virtual_register
				return real_register

		"""Every real register is allocated, need to free one up"""

		free_register = ""
		store = False

		"""dictionary of virtual register and its next use"""
		temp_dict = {}

		for real_register, reg in self.real_to_virtual.iteritems():

			live_range = self.live_ranges[reg]
			store = True

			for item in live_range:
				if item > original_index_of_instruction:
					temp_dict[reg] = item
					break

		if side == "r" and instruction[0] == "store":
			not_this_reg = instruction[1]
			for key, value in self.real_to_virtual.iteritems():
				if key == not_this_reg:
					del_this_reg = value

			del temp_dict[del_this_reg]

		if side == "l" and (instruction[0] == "add" or instruction[0] == "sub" or instruction[0] == "mult"):
			if item_index == 2:
				not_this_reg = instruction[1]
				for key, value in self.real_to_virtual.iteritems():
					if key == not_this_reg:
						del_this_reg = value

				del temp_dict[del_this_reg]

		maxValKey = max(temp_dict, key = temp_dict.get)
		max_val = max([i for i in temp_dict.values()])

		for key, value in self.real_to_virtual.iteritems():
			if value == maxValKey:
				free_register = key

		if free_register != "" and store == True:
			if max_val != 1500:
				offset = self.register_to_offset[maxValKey]
				temp_instruction = ["storeAI", free_register, offset]
				self.final_instruction_list.insert(self.instr_index, temp_instruction)
				self.instr_index += 1

			self.real_to_virtual[free_register] = virtual_register
		
		self.currently_spilled.append(maxValKey)

		gc.collect()
		
		return free_register

	"""Method to clean and store the instruction given the components in list form"""
	def store_instruction(self, instruction):

		instruction_list = []

		for item in instruction:
			item = item.strip()
			item = item.translate(string.maketrans("\t", " "))
			item = item.strip(",")
			item = item.split(' ')
		
			instruction_list = instruction_list + item

		gc.collect()

		if instruction_list != ['']:
			self.original_instruction_list.append(instruction_list)

	"""Method to parse a file line by line"""
	def parseFile(self, num_registers, allocator, file):
		"""to get opcodes and register count"""

		instruction_number = -1

		for line in file:

			if line[0] != '/':

				"""Need to create an instruction object"""
				temp = line.split("=>")
				temp[:] = [x for x in temp if x != '']
				
				if temp != ['\n']:
					instruction_number += 1
				
				for item in temp:
					item = item.strip()
					item = item.translate(string.maketrans("\t", " "))
					item = item.strip(',')
					item = item.split(' ')

					for newitems in item:
						newitems = newitems.strip(',')
						if newitems in self.opcodes:
							self.opcodes[newitems] += 1
						else:
							templist = list(newitems)
							if templist != [] and templist[0] == 'r':
								if newitems in self.registers:
									self.registers[newitems] += 1
								else:
									self.registers[newitems] = 1

								if newitems in self.live_ranges:
									self.live_ranges[newitems].append(instruction_number)
								else:
									self.live_ranges[newitems] = []
									self.live_ranges[newitems].append(instruction_number)
								
				self.ordered_register_list = sorted(self.registers, key = self.registers.__getitem__, reverse = True)
				ILOCInstruction.store_instruction(self, temp)


		"""make the live ranges for each register "on exit" for everything but bottom up"""
		if allocator != "b":
			for key, value in self.live_ranges.iteritems():
				value[len(value) - 1] -= 1
		

		"""Create active_reg_for_instruction"""
		while(instruction_number >= 0):
			for key, value in self.live_ranges.iteritems():
				if instruction_number >= value[0] and instruction_number <= value[len(value) - 1]:
					if instruction_number in self.active_reg_for_instruction:
						self.active_reg_for_instruction[instruction_number].append(key)
					else:
						self.active_reg_for_instruction[instruction_number] = []
						self.active_reg_for_instruction[instruction_number].append(key)

			instruction_number -= 1

		if allocator == "b" and num_registers > 0:
			ILOCInstruction.bottom_up_allocator(self, num_registers)
		elif allocator == "s" and num_registers > 0:
			ILOCInstruction.EAC_top_down_allocator(self, num_registers)
		elif allocator == "t" and num_registers > 0:
			ILOCInstruction.top_down_allocator(self, num_registers)
		else:
			sys.stdout.write("Error! Check your allocator inputs")
			return 0

		gc.collect()