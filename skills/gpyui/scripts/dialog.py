"""A prebuilt native confirmation dialog with explicit commands and cancellation."""

from gpyui import Application, Button, Column, Dialog, Label, Row

app = Application(title="Project actions", width=560, height=340, theme="light")


def delete_project() -> None:
    status.text = 'Deleted the local demo project "Roadmap".'
    confirmation.close()


with app, Column().style(padding=24, gap=16):
    Label("Roadmap").style(font_size=22, bold=True)
    status = Label("Local demo project · no remote data")
    with Dialog('Delete "Roadmap"?') as confirmation:
        Label("This removes the local demo project. Choose Cancel to keep it.")
        with Row().style(gap=8):
            Button("Cancel", variant="outline", on_click=lambda: confirmation.close())
            Button("Delete project", variant="danger", on_click=delete_project)
    Button("Delete project…", variant="danger", on_click=lambda: confirmation.open())

if __name__ == "__main__":
    app.run()
