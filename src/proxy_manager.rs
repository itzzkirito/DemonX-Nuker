use std::sync::Arc;
use std::time::{Duration, Instant};
use parking_lot::RwLock;
use url::Url;
use serde::{Deserialize, Serialize};

/// Proxy information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProxyInfo {
    pub url: String,
    pub host: String,
    pub port: u16,
    pub username: Option<String>,
    pub password: Option<String>,
    pub success_count: u64,
    pub failure_count: u64,
    pub last_used: Option<Instant>,
    pub last_success: Option<Instant>,
    pub is_active: bool,
}

impl ProxyInfo {
    /// Create a new proxy info
    pub fn new(url: String) -> Result<Self, String> {
        let parsed = Url::parse(&url).map_err(|e| format!("Invalid URL: {}", e))?;
        
        let host = parsed.host_str()
            .ok_or("Missing host")?
            .to_string();
        
        let port = parsed.port()
            .unwrap_or(if parsed.scheme() == "https" { 443 } else { 80 });

        let username = parsed.username().is_empty().then(|| parsed.username().to_string());
        let password = parsed.password().map(|p| p.to_string());

        Ok(Self {
            url,
            host,
            port,
            username,
            password,
            success_count: 0,
            failure_count: 0,
            last_used: None,
            last_success: None,
            is_active: true,
        })
    }

    /// Parse from IP:PORT:USERNAME:PASSWORD format
    pub fn from_string(proxy_str: &str) -> Result<Self, String> {
        let parts: Vec<&str> = proxy_str.split(':').collect();
        
        match parts.len() {
            2 => {
                // IP:PORT
                let ip = parts[0];
                let port = parts[1].parse::<u16>()
                    .map_err(|_| "Invalid port")?;
                Ok(Self::new(format!("http://{}:{}", ip, port))?)
            }
            4 => {
                // IP:PORT:USERNAME:PASSWORD
                let ip = parts[0];
                let port = parts[1].parse::<u16>()
                    .map_err(|_| "Invalid port")?;
                let username = parts[2];
                let password = parts[3];
                Ok(Self::new(format!("http://{}:{}@{}:{}", username, password, ip, port))?)
            }
            _ => Err("Invalid proxy format. Use IP:PORT or IP:PORT:USERNAME:PASSWORD".to_string())
        }
    }

    /// Get success rate
    pub fn success_rate(&self) -> f64 {
        let total = self.success_count + self.failure_count;
        if total == 0 {
            return 1.0;
        }
        self.success_count as f64 / total as f64
    }

    /// Mark as successful
    pub fn mark_success(&mut self) {
        self.success_count += 1;
        self.last_success = Some(Instant::now());
        self.last_used = Some(Instant::now());
    }

    /// Mark as failed
    pub fn mark_failed(&mut self) {
        self.failure_count += 1;
        self.last_used = Some(Instant::now());
        
        // Deactivate if failure rate is too high
        if self.failure_count > 10 && self.success_rate() < 0.1 {
            self.is_active = false;
        }
    }

    /// Get reqwest proxy
    pub fn to_reqwest_proxy(&self) -> Result<reqwest::Proxy, String> {
        if let Some(username) = &self.username {
            if let Some(password) = &self.password {
                reqwest::Proxy::all(&self.url)
                    .map_err(|e| format!("Failed to create proxy: {}", e))?
                    .basic_auth(username, password)
            } else {
                reqwest::Proxy::all(&self.url)
                    .map_err(|e| format!("Failed to create proxy: {}", e))?
            }
        } else {
            reqwest::Proxy::all(&self.url)
                .map_err(|e| format!("Failed to create proxy: {}", e))?
        }
    }
}

/// Proxy manager with rotation and health checking
pub struct ProxyManager {
    proxies: Arc<RwLock<Vec<ProxyInfo>>>,
    current_index: Arc<RwLock<usize>>,
    rotation_strategy: RotationStrategy,
}

#[derive(Debug, Clone, Copy)]
pub enum RotationStrategy {
    RoundRobin,
    Random,
    LeastUsed,
    BestSuccessRate,
}

impl Default for ProxyManager {
    fn default() -> Self {
        Self::new()
    }
}

impl ProxyManager {
    /// Create a new proxy manager
    pub fn new() -> Self {
        Self {
            proxies: Arc::new(RwLock::new(Vec::new())),
            current_index: Arc::new(RwLock::new(0)),
            rotation_strategy: RotationStrategy::RoundRobin,
        }
    }

    /// Create with rotation strategy
    pub fn with_strategy(strategy: RotationStrategy) -> Self {
        Self {
            proxies: Arc::new(RwLock::new(Vec::new())),
            current_index: Arc::new(RwLock::new(0)),
            rotation_strategy: strategy,
        }
    }

    /// Load proxies from a vector of strings
    pub fn load_from_strings(&self, proxy_strings: Vec<String>) -> Result<usize, String> {
        let mut proxies = self.proxies.write();
        proxies.clear();

        let mut loaded = 0;
        for proxy_str in proxy_strings {
            match ProxyInfo::from_string(&proxy_str) {
                Ok(proxy) => {
                    proxies.push(proxy);
                    loaded += 1;
                }
                Err(e) => {
                    eprintln!("Failed to parse proxy '{}': {}", proxy_str, e);
                }
            }
        }

        Ok(loaded)
    }

    /// Load proxies from file
    pub async fn load_from_file(&self, file_path: &str) -> Result<usize, String> {
        let content = tokio::fs::read_to_string(file_path)
            .await
            .map_err(|e| format!("Failed to read file: {}", e))?;

        let proxy_strings: Vec<String> = content
            .lines()
            .map(|s| s.trim().to_string())
            .filter(|s| !s.is_empty())
            .collect();

        self.load_from_strings(proxy_strings)
    }

    /// Get next proxy based on rotation strategy
    pub fn get_next_proxy(&self) -> Option<ProxyInfo> {
        let proxies = self.proxies.read();
        if proxies.is_empty() {
            return None;
        }

        let active_proxies: Vec<&ProxyInfo> = proxies.iter()
            .filter(|p| p.is_active)
            .collect();

        if active_proxies.is_empty() {
            // No active proxies, return any proxy
            return proxies.first().cloned();
        }

        let proxy = match self.rotation_strategy {
            RotationStrategy::RoundRobin => {
                let mut index = self.current_index.write();
                let proxy = active_proxies[*index % active_proxies.len()].clone();
                *index = (*index + 1) % active_proxies.len();
                proxy
            }
            RotationStrategy::Random => {
                use rand::Rng;
                let mut rng = rand::thread_rng();
                if active_proxies.is_empty() {
                    return None;
                }
                active_proxies[rng.gen_range(0..active_proxies.len())].clone()
            }
            RotationStrategy::LeastUsed => {
                active_proxies.iter()
                    .min_by_key(|p| p.success_count + p.failure_count)
                    .unwrap()
                    .clone()
            }
            RotationStrategy::BestSuccessRate => {
                active_proxies.iter()
                    .max_by(|a, b| a.success_rate().partial_cmp(&b.success_rate()).unwrap())
                    .unwrap()
                    .clone()
            }
        };

        Some(proxy)
    }

    /// Get current proxy
    pub fn get_current_proxy(&self) -> Option<ProxyInfo> {
        let proxies = self.proxies.read();
        let index = *self.current_index.read();
        proxies.get(index).cloned()
    }

    /// Mark proxy as successful
    pub fn mark_success(&self, proxy_url: &str) {
        let mut proxies = self.proxies.write();
        if let Some(proxy) = proxies.iter_mut().find(|p| p.url == proxy_url) {
            proxy.mark_success();
        }
    }

    /// Mark proxy as failed
    pub fn mark_failed(&self, proxy_url: &str) {
        let mut proxies = self.proxies.write();
        if let Some(proxy) = proxies.iter_mut().find(|p| p.url == proxy_url) {
            proxy.mark_failed();
        }
    }

    /// Get proxy count
    pub fn count(&self) -> usize {
        self.proxies.read().len()
    }

    /// Get active proxy count
    pub fn active_count(&self) -> usize {
        self.proxies.read().iter()
            .filter(|p| p.is_active)
            .count()
    }

    /// Get statistics
    pub fn get_stats(&self) -> ProxyStats {
        let proxies = self.proxies.read();
        let total = proxies.len();
        let active = proxies.iter().filter(|p| p.is_active).count();
        let total_success: u64 = proxies.iter().map(|p| p.success_count).sum();
        let total_failure: u64 = proxies.iter().map(|p| p.failure_count).sum();

        ProxyStats {
            total,
            active,
            total_success,
            total_failure,
        }
    }
}

#[derive(Debug, Clone)]
pub struct ProxyStats {
    pub total: usize,
    pub active: usize,
    pub total_success: u64,
    pub total_failure: u64,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_proxy_parsing() {
        let proxy = ProxyInfo::from_string("127.0.0.1:8080").unwrap();
        assert_eq!(proxy.host, "127.0.0.1");
        assert_eq!(proxy.port, 8080);
    }

    #[test]
    fn test_proxy_with_auth() {
        let proxy = ProxyInfo::from_string("127.0.0.1:8080:user:pass").unwrap();
        assert_eq!(proxy.username, Some("user".to_string()));
        assert_eq!(proxy.password, Some("pass".to_string()));
    }
}

