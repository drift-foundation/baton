def greet(name):
    name = name.strip()
    if not name:
        raise ValueError("name is empty")
    return "Hello, " + name + "!"
