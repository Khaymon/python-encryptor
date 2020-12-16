#!/usr/bin/env python
import logging
import string
import sys
import json
from collections import Counter
from collections import defaultdict

CIPHER_ERROR_CODE = 1
KEY_ERROR_CODE = 2
ARGUMENT_ERROR_CODE = 3
FILE_OPEN_ERROR_CODE = 4
TASK_ERROR_CODE = 5
ALPHABET_SIZE = 26


class Cipher:
    def __init__(self, input_file=None, output_file=None):
        if input_file is None:
            self._input_file = sys.stdin
        else:
            try:
                self._input_file = open(input_file, 'r')
            except Exception as input_file_exception:
                error(input_file_exception, FILE_OPEN_ERROR_CODE)
        if output_file is None:
            self._output_file = sys.stdout
        else:
            try:
                self._output_file = open(output_file, 'w')
            except Exception as output_file_exception:
                error(output_file_exception, FILE_OPEN_ERROR_CODE)

    def __del__(self):
        self._input_file.close()
        self._output_file.close()

    def encrypt(self):
        raise NotImplementedError

    def decrypt(self):
        raise NotImplementedError

    def hack(self, model_file):
        raise NotImplementedError


class CeasarCipher(Cipher):
    def encrypt(self, key: str):
        if not key.isdecimal():
            error("Invalid key", ARGUMENT_ERROR_CODE)
        key = int(key)

        for letter in file_iterator(self._input_file):
            if letter in string.ascii_lowercase:
                position = string.ascii_lowercase.index(letter)
                new_position = (position + key) % ALPHABET_SIZE
                self._output_file.write(string.ascii_lowercase[new_position])
            elif letter in string.ascii_uppercase:
                position = string.ascii_uppercase.index(letter)
                new_position = (position + key) % ALPHABET_SIZE
                self._output_file.write(string.ascii_uppercase[new_position])
            else:
                self._output_file.write(letter)

    def decrypt(self, key: str):
        if not key.isdecimal():
            error("Invalid key", ARGUMENT_ERROR_CODE)

        key = (ALPHABET_SIZE - int(key)) % ALPHABET_SIZE
        self.encrypt(str(key))

    def train(self, model_file_name, train_file_name):
        try:
            model_file = open(model_file_name, 'w')
        except Exception as model_file_exception:
            error(model_file_exception, FILE_OPEN_ERROR_CODE)
        try:
            train_file = open(train_file_name, 'r')
        except Exception as train_file_exception:
            error(train_file_exception, FILE_OPEN_ERROR_CODE)

        train_data = get_letters_frequency(train_file)
        json.dump(train_data, model_file)

        model_file.close()
        train_file.close()

    def hack(self, model_file_name):
        try:
            model_file = open(model_file_name, 'r')
        except Exception as model_file_exception:
            error(model_file_exception, FILE_OPEN_ERROR_CODE)

        train_data = defaultdict(int, json.load(model_file))
        base_data = get_letters_frequency(self._input_file)
        best_data = base_data.copy()
        best_distance = get_distance(train_data, best_data)
        best_shift = 0

        current_data = defaultdict(int)
        for current_shift in range(1, ALPHABET_SIZE):
            for letter, frequency in base_data.items():
                position = string.ascii_lowercase.index(letter)
                new_position = (position + current_shift) % ALPHABET_SIZE
                new_letter = string.ascii_lowercase[new_position]
                current_data[new_letter] = frequency
            current_distance = get_distance(current_data, train_data)
            if current_distance < best_distance:
                best_distance = current_distance
                best_data = current_data
                best_shift = current_shift

        model_file.close()
        self.encrypt(str(best_shift))


class ViegenereCipher(Cipher):
    def encrypt(self, key: str):
        if not key.isalpha():
            error("Invalid key for viegenere cipher", KEY_ERROR_CODE)
        key = key.upper()

        key_iterator = 0
        for letter in file_iterator(self._input_file):
            if letter in string.ascii_lowercase:
                position = string.ascii_lowercase.index(letter)
                shift = string.ascii_uppercase.index(key[key_iterator])
                new_position = (position + shift) % ALPHABET_SIZE
                self._output_file.write(string.ascii_lowercase[new_position])
                key_iterator = (key_iterator + 1) % len(key)
            elif letter in string.ascii_uppercase:
                position = string.ascii_uppercase.index(letter)
                shift = string.ascii_uppercase.index(key[key_iterator])
                new_position = (position + shift) % ALPHABET_SIZE
                self._output_file.write(string.ascii_uppercase[new_position])
                key_iterator = (key_iterator + 1) % len(key)
            else:
                self._output_file.write(letter)

    def decrypt(self, key: str):
        if not key.isalpha():
            error("Invalid key for viegenere cipher", KEY_ERROR_CODE)
        key = key.upper()

        new_key = str()
        for letter in key:
            position = string.ascii_uppercase.index(letter)
            new_position = (ALPHABET_SIZE - position) % ALPHABET_SIZE
            new_key += string.ascii_uppercase[new_position]
        self.encrypt(new_key)


def file_iterator(input_file):
    input_file.seek(0, 0)
    end_of_file = False
    carry_slash = False
    while not end_of_file:
        buffer = input_file.read()
        if len(buffer) == 0:
            end_of_file = True
        for letter in buffer:
            if carry_slash:
                carry_slash = not carry_slash
                yield '\\' + letter
            elif letter == '\\':
                carry_slash = True
            else:
                yield letter


def get_distance(first_data, second_data):
    distance = 0

    for letter in string.ascii_lowercase:
        distance += (first_data[letter] - second_data[letter]) ** 2
    return distance


def get_letters_frequency(input_file):
    data = Counter()
    for letter in file_iterator(input_file):
        if letter.lower() in string.ascii_lowercase:
            data[letter.lower()] += 1
    return data


def error(message, exit_code):
    sys.stderr.write(message + "\n")
    sys.exit(exit_code)


def parse(argument):
    try:
        key_arg_position = sys.argv.index(argument)
    except ValueError:
        return None
    if key_arg_position + 1 >= len(sys.argv):
        error("Unable to find a " + argument, ARGUMENT_ERROR_CODE)
    return sys.argv[key_arg_position + 1]


if __name__ == "__main__":
    if len(sys.argv) == 1:
        error("No task argument", TASK_ERROR_CODE)
    task = sys.argv[1]
    input_file_name_arg = parse('--input-file')
    output_file_name_arg = parse('--output-file')
    train_file_name_arg = parse('--text-file')
    model_file_name_arg = parse('--model-file')
    key_arg = parse('--key')
    cipher_arg = parse('--cipher')
    if cipher_arg == 'caesar':
        cipher = CeasarCipher(input_file_name_arg, output_file_name_arg)
    elif cipher_arg == 'viegenere':
        cipher = ViegenereCipher(input_file_name_arg, output_file_name_arg)
    else:
        error("Unknown cipher type", ARGUMENT_ERROR_CODE)
    if task == 'encode':
        cipher.encrypt(key_arg)
    elif task == 'decode':
        cipher.decrypt(key_arg)
    elif task == 'train':
        cipher.train(model_file_name_arg, train_file_name_arg)
    elif task == 'hack':
        cipher.hack(model_file_name_arg)
    else:
        error("Unable to do " + task, TASK_ERROR_CODE)
