"""Run with: uv run python examples/hello.py"""

from gpyui import Application, Button, Column, Label, TextInput

app = Application(title="gpyui — Hello")
with app:
    with Column():
        Label("Name")
        name = TextInput(placeholder="Enter your name")
        greeting = Label("Enter a name and choose Greet")
        Button("Greet", on_click=lambda: setattr(greeting, "text", f"Hello, {name.value or 'world'}!"))

if __name__ == "__main__":
    app.run()
