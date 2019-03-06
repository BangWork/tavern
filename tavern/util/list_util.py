# -*- coding: utf-8 -*-
from functools import reduce

def remove_duplicate_elements(check_list):
	func = lambda x,y:x if y in x else x + [y]
	return reduce(func, [[], ] + check_list)
