import random
import string

def generate_random_string(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def create_go_file(filename, content):
    with open(filename, 'w') as file:
        file.write('package main\n\n')
        file.write('const RandomString = `')
        file.write(content)
        file.write('`\n')

# Generate a 10MB random string
random_string = generate_random_string(10 * 1024 * 1024)

# Create a Go file with the random string as a constant
create_go_file('random_string.go', random_string)

print("Go file 'random_string.go' has been created with a 10MB random string constant.")