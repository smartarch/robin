from django.db.models import Q
from typing import Any
from .models import Mapping, ReviewField, PublicationList
from publication.models import Publication

def create_parser(text: str) -> list:
	"""
	This method converts the text of filter to a list of conditions, testing examples:
	test_cases = [
		"(((x=y)))",
		"not (x=y)",
		"( not ( not (xaaa=y) and (y=z)))",
		"(x=y) and (a=b) or (c=z)",
		"(x=y) and ((b=c) or (d=z)) or ((x=y) or ( not (a== w )))",
	]
	:param text: the filter text
	:return: array of conditions, the priority is with the item that appears first
	"""
	index = 0
	stack = [[]]
	while index < len(text):
		c = text[index]

		if c == '(':
			stack.append ([])
			index = index + 1

		elif c == ')':
			if len(stack) < 2:
				raise BufferError

			item = stack.pop()
			if '=' in item:
				item = {''.join(item[:item.index('=')]): ''.join(item[item.index('=')+1:]).replace("=", "")}
			stack[-1].append(item)
			index = index + 1

		elif text[index:index + 5].lower() in [' not ', ' and ']:
			stack[-1].append(text[index+1:index+4])
			index = index + 5

		elif text[index:index + 4].lower() == ' or ':
			stack[-1].append('or')
			index = index + 4

		elif text[index:index + 4].lower() == 'not ':
			stack[-1].append('not')
			index = index + 4

		else:
			stack[-1].append(c)
			index = index + 1

	if len(stack) > 1:
		raise BufferError

	return stack[0]


def create_user_q(mapping: Mapping, publication_list: PublicationList,  key: str, value: Any) -> Q | None:
	try:
		mapping_fields = ReviewField.objects.filter(mapping=mapping)
		key_spliter = key.split('__')

		if len(key_spliter) == 1:
			filtered = ""  # default filter
		else:
			filtered = "__" + key_spliter[1]  # default filter
		field_name = key_spliter[0]

		target_field = mapping_fields.get(name=field_name)
		query = Q(**{f"value{filtered}": value})

		target_objects = target_field.get_value_class().objects.all()
		publications = publication_list.publications.filter(id__in=[t.publication.id for t in target_objects.filter(query)])

		return Q(id__in=[p.id for p in publications])
	except:
		return None

def create_advanced_query(mapping: Mapping, publication_list: PublicationList, text: str) -> Q:
	"""
	Converts the string filter to django.db.Q model
	:param text: filter text
	:return: Q model
	"""

	def creat_q_item(tokens: list) -> Q:
		if len(tokens) == 0:
			return Q()

		def manage_stack(_stack: list, _token: Any) -> list:
			if len(_stack) > 0:
				operator = _stack.pop()

				if operator == "and":
					_stack.append(_stack.pop() & _token)

				elif operator == "or":
					_stack.append(_stack.pop() | _token)

				elif operator == "not":
					_stack.append(~_token)
				else:
					raise BufferError
			else:
				_stack.append(_token)

			return _stack

		stack = []
		for token in tokens:
			if isinstance(token, dict):
				user_q = None
				for key, value in token.items():
					if key in [f.name for f in Publication._meta.fields]:
						break
					user_q = create_user_q(mapping, publication_list, key, value)

				if user_q:
					token = user_q
				else:
					token = Q(**token)

				stack = manage_stack(stack, token)

			elif isinstance(token, list):
				stack = manage_stack(stack, creat_q_item(token))

			else:
				stack.append(token)

		if len(stack) != 1:
			raise BufferError

		return stack[0]

	tokens = create_parser(text)
	return creat_q_item(tokens)
