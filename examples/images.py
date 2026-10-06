"""A light image viewer: native decoding, fit modes, failure and retry."""

import argparse

import gpyui as ui

LANDSCAPE = b"""<svg xmlns="http://www.w3.org/2000/svg" width="960" height="480" viewBox="0 0 960 480">
<defs><linearGradient id="sky" x2="0" y2="1"><stop stop-color="#dbeafe"/><stop offset="1" stop-color="#f0fdfa"/></linearGradient>
<linearGradient id="lake" x2="0" y2="1"><stop stop-color="#67e8f9"/><stop offset="1" stop-color="#0e7490"/></linearGradient></defs>
<rect width="960" height="480" fill="url(#sky)"/><circle cx="760" cy="102" r="46" fill="#fbbf24"/>
<path d="M0 350L230 80L440 350L620 150L960 350Z" fill="#0f766e"/>
<path d="M168 151L230 80L285 150L245 140L226 160L209 140Z" fill="#f0fdfa"/>
<path d="M535 240L620 150L695 240L650 220L620 250L590 224Z" fill="#ccfbf1"/>
<path d="M0 340Q210 315 480 350T960 340V480H0Z" fill="url(#lake)"/>
<path d="M80 397H285M620 424H855M365 450H570" stroke="#cffafe" stroke-width="4" stroke-linecap="round"/>
</svg>"""


def build_app(source=None):
    status = ui.Label("Loading preview…").style(color="muted_foreground")

    def loaded(event):
        info = event.value
        status.text = f"{info['width']} × {info['height']} px"
        if info["frames"] > 1:
            status.text += f" · {info['frames']} animated frames"

    def failed(event):
        status.text = "Could not load this image. Check the location and retry."

    image = ui.Image(source or LANDSCAPE, on_load=loaded, on_error=failed).style(
        full_width=True, height=360, radius=12, background="muted"
    )
    location = ui.TextInput("", placeholder="Local file path or https:// image URL").style(flex=1)
    fit = ui.Select(
        ["contain", "cover", "fill", "scale_down", "none"],
        value="contain",
        on_change=lambda e: setattr(image, "fit", e.value),
    )
    grayscale = ui.Switch("Grayscale", on_change=lambda e: setattr(image, "grayscale", e.value))

    def open_image():
        if location.value.strip():
            image.source = location.value.strip()

    content = ui.Column(
        [
            ui.Label("Image preview").style(font_size=24, bold=True),
            ui.Label("Preview a file or URL, adjust its fit, or explore the sample.").style(
                color="muted_foreground"
            ),
            ui.Row([location, ui.Button("Open image", variant="outline", on_click=open_image)]).style(
                full_width=True
            ),
            image,
            ui.Row([ui.Label("Fit"), fit, grayscale]).style(gap=16),
            status,
            ui.Row(
                [
                    ui.Button("Retry", on_click=image.reload),
                    ui.Button("Sample illustration", on_click=lambda: setattr(image, "source", LANDSCAPE)),
                    ui.Button("Clear", on_click=lambda: setattr(image, "source", None)),
                ]
            ),
        ]
    ).style(full_width=True, gap=14)
    return ui.Application(content, title="gpyui image viewer", width=840, height=650, theme="light")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", help="Local file path or HTTP(S) image URL")
    build_app(parser.parse_args().source).run()
