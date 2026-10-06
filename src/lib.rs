mod bridge;
mod commands;
mod images;
mod kit;
mod protocol;
mod theme;
mod view;

use pyo3::prelude::*;

#[pymodule]
fn _core(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_class::<bridge::Bridge>()?;
    module.add(
        "GPUI_KIT_REVISION",
        "3a142844d3661159964dce9e5512ca9a40286160",
    )?;
    module.add("GPUI_VERSION", "0.3.7")?;
    Ok(())
}
