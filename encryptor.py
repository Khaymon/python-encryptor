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
    def __init__(self, key):
        if key is None:
            self._key = None
        elif self.normalize_key(key) is None:
            error("Key error", KEY_ERROR_CODE)
        else:
            self._key = self.normalize_key(key)

    def encrypt(self):
        raise NotImplementedError

    def decrypt(self):
        raise NotImplementedError

    def hack(self, model_file):
        raise NotImplementedError

    def normalize_key(self, key):
        raise NotImplementedError


class CeasarCipher(Cipher):
    def encrypt(self, input_file, output_file):
        for letter in file_iterator(input_file):
            if letter in string.ascii_lowercase:
                position = string.ascii_lowercase.index(letter)
                new_position = (position + self._key) % ALPHABET_SIZE
                output_file.write(string.ascii_lowercase[new_position])
            elif letter in string.ascii_uppercase:
                position = string.ascii_uppercase.index(letter)
                new_position = (position + self._key) % ALPHABET_SIZE
                output_file.write(string.ascii_uppercase[new_position])
            else:
                output_file.write(letter)

    def decrypt(self, input_file, output_file):
        self._key = (ALPHABET_SIZE - self._key) % ALPHABET_SIZE
        self.encrypt(input_file, output_file)

    def train(self, model_file, train_file):
        train_data = get_letters_frequency(train_file)
        json.dump(train_data, model_file)

    def hack(self, input_file, output_file, model_file):

        train_data = defaultdict(int, json.load(model_file))
        base_data = get_letters_frequency(input_file)
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

        self._key = best_shift
        self.encrypt(input_file, output_file)

    def normalize_key(self, key):
        try:
            return int(key)
        except Exception:
            return None


class ViegenereCipher(Cipher):
    def encrypt(self, input_file, output_file):
        key_iterator = 0
        for letter in file_iterator(input_file):
            if letter in string.ascii_lowercase:
                position = string.ascii_lowercase.index(letter)
                shift = string.ascii_uppercase.index(self._key[key_iterator])
                new_position = (position + shift) % ALPHABET_SIZE
                output_file.write(string.ascii_lowercase[new_position])
                key_iterator = (key_iterator + 1) % len(self._key)
            elif letter in string.ascii_uppercase:
                position = string.ascii_uppercase.index(letter)
                shift = string.ascii_uppercase.index(self._key[key_iterator])
                new_position = (position + shift) % ALPHABET_SIZE
                output_file.write(string.ascii_uppercase[new_position])
                key_iterator = (key_iterator + 1) % len(self._key)
            else:
                output_file.write(letter)

    def decrypt(self, input_file, output_file):
        new_key = str()
        for letter in self._key:
            position = string.ascii_uppercase.index(letter)
            new_position = (ALPHABET_SIZE - position) % ALPHABET_SIZE
            new_key += string.ascii_uppercase[new_position]
        self._key = new_key
        self.encrypt(input_file, output_file)

    def normalize_key(self, key):
        try:
            if key.isalpha():
                return key.upper()
            else:
                return None
        except Exception:
            return None


def file_iterator(input_file):
    input_file.seek(0, 0)
    for letter in input_file.read():
        yield letter


def get_distance(first_data, second_data):
    distance = 0

    for letter in string.ascii_lowercase:
        distance += (first_data[letter] - second_data[letter]) ** 2
    return distance


def get_letters_frequency(input_file):
    return Counter((letter.lower() for letter in input_file.read() if
                    letter.lower() in string.ascii_lowercase))


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


def open_file(file_name, mode, verbose):
    if mode == 'read':
        try:
            file = open(file_name, 'r')
        except Exception:
            if verbose:
                error("Error of opening file", FILE_OPEN_ERROR_CODE)
            file = sys.stdin
    elif mode == 'write':
        try:
            file = open(file_name, 'w')
        except Exception:
            if verbose:
                error("Error of opening file", FILE_OPEN_ERROR_CODE)
            file = sys.stdout
    else:
        raise ValueError("Bad argument for open_file")
    return file


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
        cipher = CeasarCipher(key_arg)
    elif cipher_arg == 'viegenere':
        cipher = ViegenereCipher(key_arg)
    else:
        error("Unknown cipher type", ARGUMENT_ERROR_CODE)
    if task == 'encode':
        input_file = open_file(input_file_name_arg, 'read', False)
        output_file = open_file(output_file_name_arg, 'write', False)
        cipher.encrypt(input_file, output_file)
    elif task == 'decode':
        input_file = open_file(input_file_name_arg, 'read', False)
        output_file = open_file(output_file_name_arg, 'write', False)
        cipher.decrypt(input_file, output_file)
        input_file.close()
        output_file.close()
    elif task == 'train':
        train_file = open_file(train_file_name_arg, 'read', True)
        model_file = open_file(model_file_name_arg, 'write', True)
        cipher.train(model_file, train_file)
        train_file.close()
        model_file.close()
    elif task == 'hack':
        input_file = open_file(input_file_name_arg, 'read', False)
        output_file = open_file(output_file_name_arg, 'write', False)
        model_file = open_file(model_file_name_arg, 'read', True)
        cipher.hack(input_file, output_file, model_file)
        input_file.close()
        output_file.close()
        model_file.close()
    else:
        error("Unable to do " + task, TASK_ERROR_CODE)
