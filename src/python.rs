use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use crate::rate_limiter::RateLimiter;
use crate::proxy_manager::{ProxyManager, RotationStrategy};
use std::sync::Arc;
use parking_lot::RwLock;

/// Python bindings for RateLimiter
#[pyclass]
pub struct PyRateLimiter {
    limiter: Arc<RateLimiter>,
}

#[pymethods]
impl PyRateLimiter {
    #[new]
    fn new() -> Self {
        Self {
            limiter: Arc::new(RateLimiter::new()),
        }
    }

    /// Check if we can make a request
    fn can_request(&self, endpoint: &str) -> bool {
        self.limiter.can_request(endpoint)
    }

    /// Get wait time in seconds
    fn wait_time(&self, endpoint: &str) -> f64 {
        self.limiter.wait_time(endpoint).as_secs_f64()
    }

    /// Handle rate limit
    fn handle_rate_limit(&self, endpoint: &str, retry_after: f64, is_global: bool) {
        use std::time::Duration;
        self.limiter.handle_rate_limit(
            endpoint,
            Duration::from_secs_f64(retry_after),
            is_global,
        );
    }

    /// Decrement remaining count
    fn decrement(&self, endpoint: &str) {
        self.limiter.decrement(endpoint);
    }

    /// Get statistics
    fn get_stats(&self) -> PyObject {
        Python::with_gil(|py| {
            let stats = self.limiter.get_stats();
            let dict = PyDict::new(py);
            dict.set_item("endpoint_count", stats.endpoint_count).unwrap();
            dict.set_item("route_count", stats.route_count).unwrap();
            dict.set_item("total_remaining", stats.total_remaining).unwrap();
            dict.set_item("total_limit", stats.total_limit).unwrap();
            dict.set_item("global_rate_limited", stats.global_rate_limited).unwrap();
            dict.into()
        })
    }
}

/// Python bindings for ProxyManager
#[pyclass]
pub struct PyProxyManager {
    manager: Arc<ProxyManager>,
}

#[pymethods]
impl PyProxyManager {
    #[new]
    fn new() -> Self {
        Self {
            manager: Arc::new(ProxyManager::new()),
        }
    }

    /// Load proxies from a list of strings
    fn load_from_strings(&self, proxy_strings: Vec<String>) -> PyResult<usize> {
        self.manager
            .load_from_strings(proxy_strings)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e))
    }

    /// Load proxies from file
    fn load_from_file(&self, file_path: &str) -> PyResult<usize> {
        Python::with_gil(|py| {
            py.allow_threads(|| {
                tokio::runtime::Runtime::new()
                    .unwrap()
                    .block_on(self.manager.load_from_file(file_path))
            })
        })
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e))
    }

    /// Get next proxy URL
    fn get_next_proxy(&self) -> Option<String> {
        self.manager.get_next_proxy().map(|p| p.url)
    }

    /// Get current proxy URL
    fn get_current_proxy(&self) -> Option<String> {
        self.manager.get_current_proxy().map(|p| p.url)
    }

    /// Mark proxy as successful
    fn mark_success(&self, proxy_url: &str) {
        self.manager.mark_success(proxy_url);
    }

    /// Mark proxy as failed
    fn mark_failed(&self, proxy_url: &str) {
        self.manager.mark_failed(proxy_url);
    }

    /// Get proxy count
    fn count(&self) -> usize {
        self.manager.count()
    }

    /// Get active proxy count
    fn active_count(&self) -> usize {
        self.manager.active_count()
    }

    /// Get statistics
    fn get_stats(&self) -> PyObject {
        Python::with_gil(|py| {
            let stats = self.manager.get_stats();
            let dict = PyDict::new(py);
            dict.set_item("total", stats.total).unwrap();
            dict.set_item("active", stats.active).unwrap();
            dict.set_item("total_success", stats.total_success).unwrap();
            dict.set_item("total_failure", stats.total_failure).unwrap();
            dict.into()
        })
    }
}

// Module is registered in lib.rs

