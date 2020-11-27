#!/usr/bin/env python
import logging
import string
import sys
import json
from collections import defaultdict

CIPHER_ERROR_CODE = 1
KEY_ERROR_CODE = 2
FILE_NAME_ERROR_CODE = 3
FILE_OPEN_ERROR_CODE = 4
TASK_ERROR_CODE = 5

BUFFER_SIZE = 1024

def is_correct_vigenere_key(key):
	for letter in key:
		if letter not in string.ascii_lowercase and letter not in string.ascii_uppercase:
			return False
	return True

def prepare_files(input_file_name, output_file_name):
	if input_file_name is None:
		input_file = sys.stdin
	else:
		try:
			input_file = open(input_file_name, 'r')
		except FileNotFoundError as e:
			error("Unable to open a file: " + e.filename, FILE_OPEN_ERROR_CODE)
	if output_file_name is None:
		output_file = sys.stdout
	else:
		try:
			output_file = open(output_file_name, 'w')
		except FileNotFoundError as e:
			error("Unable to open a file: " + e.filename, FILE_OPEN_ERROR_CODE)
	
	return (input_file, output_file)

def ceasar_encryption(key, input_file_name, output_file_name):
	input_file, output_file = prepare_files(input_file_name, output_file_name)
	alphabet_size = len(string.ascii_lowercase)
	end_of_file = False
	carry_slash = False
	while not end_of_file:
		buffer = input_file.read(BUFFER_SIZE)
		if len(buffer) == 0:
				end_of_file = True
		for i in range(len(buffer)):
			if buffer[i] in string.ascii_lowercase and not carry_slash:
				position = string.ascii_lowercase.index(buffer[i])
				new_position = (position + key) % alphabet_size
				output_file.write(string.ascii_lowercase[new_position])
			elif buffer[i] in string.ascii_uppercase and not carry_slash:
				position = string.ascii_uppercase.index(buffer[i])
				new_position = (position + key) % alphabet_size
				output_file.write(string.ascii_uppercase[new_position])
			else:
				if carry_slash:
					carry_slash = not carry_slash
				elif buffer[i] == '\\':
					carry_slash = True
				output_file.write(buffer[i])
	
	input_file.close()
	output_file.close()

def viegenere_encryption(key, input_file_name, output_file_name):
	if not is_correct_vigenere_key(key):
		error("Invalid key for viegenere cipher", KEY_ERROR_CODE)
	input_file, output_file = prepare_files(input_file_name, output_file_name)
	alphabet_size = len(string.ascii_lowercase)
	
	key_iterator = 0
	end_of_file = False
	carry_slash = False
	while not end_of_file:
		buffer = input_file.read(BUFFER_SIZE)
		if len(buffer) == 0:
				end_of_file = True
		for i in range(len(buffer)):
			if buffer[i] in string.ascii_lowercase and not carry_slash:
				position = string.ascii_lowercase.index(buffer[i])
				shift = string.ascii_uppercase.index(key[key_iterator])
				new_position = (position + shift) % alphabet_size
				output_file.write(string.ascii_lowercase[new_position])
				key_iterator = (key_iterator + 1) % len(key)
			elif buffer[i] in string.ascii_uppercase and not carry_slash:
				position = string.ascii_uppercase.index(buffer[i])
				shift = string.ascii_uppercase.index(key[key_iterator])
				new_position = (position + shift) % alphabet_size
				output_file.write(string.ascii_uppercase[new_position])
				key_iterator = (key_iterator + 1) % len(key)
			else:
				if carry_slash:
					carry_slash = not carry_slash
				elif buffer[i] == '\\':
					carry_slash = True
				output_file.write(buffer[i])
	
	input_file.close()
	output_file.close()

def ceasar_decription(key, input_file_name, output_file_name):
	alphabet_size = len(string.ascii_uppercase)
	key = (alphabet_size - key) % alphabet_size
	ceasar_encryption(key, input_file_name, output_file_name)

def viegenere_decription(key, input_file_name, output_file_name):
	alphabet_size = len(string.ascii_uppercase)
	new_key = str()
	for letter in key:
		position = string.ascii_uppercase.index(letter)
		new_position = (alphabet_size - position) % alphabet_size
		new_key += string.ascii_uppercase[new_position]
	viegenere_encryption(new_key, input_file_name, output_file_name)

def train_model():
	train_file_name = parse_train_file()
	model_file_name = parse_model_file_name()
	train_file, model_file = prepare_files(train_file_name, model_file_name)

	train_data = get_letters_frequency(train_file)
	json.dump(train_data, model_file)

	train_file.close()
	model_file.close()

def hack_cipher():
	input_file_name = parse_input_file_name()
	output_file_name = parse_output_file_name()
	model_file_name = parse_model_file_name()

	hack_caesar(input_file_name, output_file_name, model_file_name)

def hack_caesar(input_file_name, output_file_name, model_file_name):
	alphabet_size = len(string.ascii_lowercase)
	input_file, output_file = prepare_files(input_file_name, output_file_name)
	
	try:
		model_file = open(model_file_name, 'r')
	except FileNotFoundError as e:
		error("Unable to open a file: " + e.filename, FILE_OPEN_ERROR_CODE)

	train_data = defaultdict(int, json.load(model_file))
	base_data = get_letters_frequency(input_file)
	best_data = base_data.copy()
	best_distance = get_distance(train_data, best_data)
	best_shift = 0

	current_data = defaultdict(int)
	for current_shift in range(1, alphabet_size):
		for letter, frequency in base_data.items():
			position = string.ascii_lowercase.index(letter)
			new_position = (position + current_shift) % alphabet_size
			new_letter = string.ascii_lowercase[new_position]
			current_data[new_letter] = frequency
		current_distance = get_distance(current_data, train_data)
		if current_distance < best_distance:
			best_distance = current_distance
			best_data = current_data
			best_shift = current_shift
	
	input_file.close()
	output_file.close()
	model_file.close()
	
	ceasar_encryption(best_shift, input_file_name, output_file_name)

def get_distance(first_data, second_data):
	distance = 0

	for letter in string.ascii_lowercase:
		distance += (first_data[letter] - second_data[letter]) ** 2
	return distance

def get_letters_frequency(input_file):
	data = defaultdict(int)

	end_of_file = False
	carry_slash = False
	while not end_of_file:
		buffer = input_file.read(BUFFER_SIZE)
		if len(buffer) == 0:
				end_of_file = True
		for i in range(len(buffer)):
			letter = buffer[i].lower()
			if letter in string.ascii_lowercase and not carry_slash:
				data[letter] += 1
			else:
				if carry_slash:
					carry_slash = not carry_slash
				elif letter == '\\':
					carry_slash = True
	
	return data

def error(message, exit_code):
	sys.stderr.write(message + "\n")
	sys.exit(exit_code)

def parse_key():
	try:
		key_arg_position = sys.argv.index('--key')
	except ValueError:
		return None
	if key_arg_position + 1 >= len(sys.argv):
		error("Unable to find a key", KEY_ERROR_CODE)
	return sys.argv[key_arg_position + 1]

def parse_cipher():
	try:
		cipher_arg_position = sys.argv.index('--cipher')
	except ValueError:
		return None
	if cipher_arg_position + 1 >= len(sys.argv):
		error("Unable to find cipher method", CIPHER_ERROR_CODE)
	return sys.argv[cipher_arg_position + 1]

def parse_input_file_name():
	try:
		input_file_arg_position = sys.argv.index('--input-file')
	except ValueError:
		return None
	if input_file_arg_position + 1 >= len(sys.argv):
		error("Unable to find an input file name", FILE_NAME_ERROR_CODE)
	return sys.argv[input_file_arg_position + 1]

def parse_output_file_name():
	try:
		output_file_arg_position = sys.argv.index('--output-file')
	except ValueError:
		return None
	if output_file_arg_position + 1 >= len(sys.argv):
		error("Unable to find an output file name", FILE_NAME_ERROR_CODE)
	return sys.argv[output_file_arg_position + 1]

def parse_train_file():
	try:
		output_file_arg_position = sys.argv.index('--text-file')
	except ValueError:
		return None
	if output_file_arg_position + 1 >= len(sys.argv):
		error("Unable to find a train file name", FILE_NAME_ERROR_CODE)
	return sys.argv[output_file_arg_position + 1]

def parse_model_file_name():
	try:
		output_file_arg_position = sys.argv.index('--model-file')
	except ValueError:
		return "model"
	if output_file_arg_position + 1 >= len(sys.argv):
		error("Unable to find a model file name", FILE_NAME_ERROR_CODE)
	return sys.argv[output_file_arg_position + 1]

def encode_text():
	key = parse_key()
	cipher = parse_cipher()
	input_file_name = parse_input_file_name()
	output_file_name = parse_output_file_name()

	if cipher == 'caesar':
		try:
			key = int(key)
		except TypeError:
			error("Caesar key must be an integer", KEY_ERROR_CODE)
		ceasar_encryption(key, input_file_name, output_file_name)
	elif cipher == 'vigenere':
		key = key.upper()
		if not is_correct_vigenere_key(key):
			error("Incorrect viegenere key", KEY_ERROR_CODE)
		viegenere_encryption(key, input_file_name, output_file_name)
	else:
		error("Unknown cipher type: " + cipher, CIPHER_ERROR_CODE)

def decode_text():
	key = parse_key()
	cipher = parse_cipher()
	input_file_name = parse_input_file_name()
	output_file_name = parse_output_file_name()

	if cipher is None:
		error("Error of parsing the cipher", CIPHER_ERROR_CODE)

	if cipher == 'caesar':
		try:
			key = int(key)
		except TypeError:
			error("Caesar key must be an integer", KEY_ERROR_CODE)
		ceasar_decription(key, input_file_name, output_file_name)
	elif cipher == 'vigenere':
		key = key.upper()
		if not is_correct_vigenere_key(key):
			error("Incorrect viegenere key", KEY_ERROR_CODE)
		viegenere_decription(key, input_file_name, output_file_name)
	else:
		error("Unknown cipher type: " + cipher, CIPHER_ERROR_CODE)

if __name__ == "__main__":
	if len(sys.argv) == 1:
		error("No task argument", TASK_ERROR_CODE)
	task = sys.argv[1]
	if task == 'encode':
		encode_text()
	elif task == 'decode':
		decode_text()
	elif task == 'train':
		train_model()
	elif task == 'hack':
		hack_cipher()
	else:
		error("Unable to do " + task, TASK_ERROR_CODE)