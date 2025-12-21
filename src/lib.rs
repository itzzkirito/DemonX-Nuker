pub mod rate_limiter;
pub mod proxy_manager;
pub mod discord_client;

pub use rate_limiter::RateLimiter;
pub use proxy_manager::ProxyManager;
pub use discord_client::DiscordClient;

#[cfg(feature = "python")]
pub mod python;

#[cfg(feature = "python")]
use pyo3::prelude::*;

#[cfg(feature = "python")]
#[pymodule]
fn demonx_rust(_py: Python, m: &PyModule) -> PyResult<()> {
    use python::{PyRateLimiter, PyProxyManager};
    m.add_class::<PyRateLimiter>()?;
    m.add_class::<PyProxyManager>()?;
    Ok(())
}

