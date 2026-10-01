"""Native editing and explicit state binding with an asyncio callback."""

import asyncio

from gpyui import Application, Button, Column, Label, State, TextInput

name = State("")
message = State("Enter a name and choose Greet")
app = Application(title="gpyui — Async binding")


async def greet():
    button.disabled = True
    message.value = "Preparing greeting…"
    await asyncio.sleep(0.25)
    message.value = f"Hello, {name.value or 'world'}!"
    button.disabled = False


app.add(
    Column(
        [
            Label("Name"),
            TextInput(placeholder="Enter your name").bind_value(name),
            Label().bind_text(message),
            button := Button("Greet", on_click=greet),
        ]
    )
)

if __name__ == "__main__":
    app.run()
