mod bridge;
mod commands;
mod images;
mod kit;
mod protocol;
mod theme;
mod view;
mod windows;

use pyo3::prelude::*;

#[pymodule]
fn _core(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_class::<bridge::Bridge>()?;
    module.add(
        "GPUI_KIT_REVISION",
        "c1bda59e67f46266991a230ae94f749af496af2a",
    )?;
    module.add("GPUI_VERSION", "0.3.8")?;
    Ok(())
}
