use dashmap::DashMap;
use parking_lot::RwLock;
use std::sync::Arc;
use std::time::{Duration, Instant};
use chrono::Utc;

/// Rate limit information for an endpoint
#[derive(Debug, Clone)]
pub struct RateLimitInfo {
    pub remaining: u32,
    pub limit: u32,
    pub reset_at: Instant,
    pub reset_after: Duration,
}

/// Advanced rate limiter for Discord API
pub struct RateLimiter {
    /// Per-endpoint rate limits
    endpoint_limits: Arc<DashMap<String, RateLimitInfo>>,
    /// Global rate limit
    global_limit: Arc<RwLock<Option<Instant>>>,
    /// Per-route rate limits (e.g., /channels/{id}/messages)
    route_limits: Arc<DashMap<String, RateLimitInfo>>,
    /// Bucket-based rate limits (Discord uses buckets)
    bucket_limits: Arc<DashMap<String, RateLimitInfo>>,
}

impl Default for RateLimiter {
    fn default() -> Self {
        Self::new()
    }
}

impl RateLimiter {
    /// Create a new rate limiter
    pub fn new() -> Self {
        Self {
            endpoint_limits: Arc::new(DashMap::new()),
            global_limit: Arc::new(RwLock::new(None)),
            route_limits: Arc::new(DashMap::new()),
            bucket_limits: Arc::new(DashMap::new()),
        }
    }

    /// Check if we can make a request to an endpoint
    pub fn can_request(&self, endpoint: &str) -> bool {
        // Check global rate limit
        if let Some(global_limit) = *self.global_limit.read() {
            if global_limit > Instant::now() {
                return false;
            }
        }

        // Check endpoint-specific limit
        if let Some(limit_info) = self.endpoint_limits.get(endpoint) {
            if limit_info.reset_at > Instant::now() && limit_info.remaining == 0 {
                return false;
            }
        }

        // Check route limit
        let route = self.extract_route(endpoint);
        if let Some(limit_info) = self.route_limits.get(&route) {
            if limit_info.reset_at > Instant::now() && limit_info.remaining == 0 {
                return false;
            }
        }

        true
    }

    /// Get the wait time before making a request
    pub fn wait_time(&self, endpoint: &str) -> Duration {
        let mut max_wait = Duration::ZERO;

        // Check global rate limit
        if let Some(global_limit) = *self.global_limit.read() {
            let now = Instant::now();
            if global_limit > now {
                let wait = global_limit.duration_since(now);
                if wait > max_wait {
                    max_wait = wait;
                }
            }
        }

        // Check endpoint-specific limit
        if let Some(limit_info) = self.endpoint_limits.get(endpoint) {
            let now = Instant::now();
            if limit_info.reset_at > now && limit_info.remaining == 0 {
                let wait = limit_info.reset_at.duration_since(now);
                if wait > max_wait {
                    max_wait = wait;
                }
            }
        }

        // Check route limit
        let route = self.extract_route(endpoint);
        if let Some(limit_info) = self.route_limits.get(&route) {
            let now = Instant::now();
            if limit_info.reset_at > now && limit_info.remaining == 0 {
                let wait = limit_info.reset_at.duration_since(now);
                if wait > max_wait {
                    max_wait = wait;
                }
            }
        }

        max_wait
    }

    /// Update rate limit information from response headers
    pub fn update_from_headers(&self, endpoint: &str, headers: &reqwest::header::HeaderMap) {
        // Parse rate limit headers
        let remaining = headers
            .get("x-ratelimit-remaining")
            .and_then(|v| v.to_str().ok())
            .and_then(|s| s.parse::<u32>().ok())
            .unwrap_or(50);

        let limit = headers
            .get("x-ratelimit-limit")
            .and_then(|v| v.to_str().ok())
            .and_then(|s| s.parse::<u32>().ok())
            .unwrap_or(50);

        let reset_after = headers
            .get("x-ratelimit-reset-after")
            .and_then(|v| v.to_str().ok())
            .and_then(|s| s.parse::<f64>().ok())
            .map(|s| Duration::from_secs_f64(s))
            .unwrap_or(Duration::from_secs(1));

        let reset_at = Instant::now() + reset_after;

        // Update endpoint limit
        self.endpoint_limits.insert(
            endpoint.to_string(),
            RateLimitInfo {
                remaining,
                limit,
                reset_at,
                reset_after,
            },
        );

        // Update route limit
        let route = self.extract_route(endpoint);
        self.route_limits.insert(
            route,
            RateLimitInfo {
                remaining,
                limit,
                reset_at,
                reset_after,
            },
        );

        // Check for global rate limit
        if headers
            .get("x-ratelimit-global")
            .and_then(|v| v.to_str().ok())
            .map(|s| s == "true")
            .unwrap_or(false)
        {
            let retry_after = headers
                .get("retry-after")
                .and_then(|v| v.to_str().ok())
                .and_then(|s| s.parse::<f64>().ok())
                .map(|s| Duration::from_secs_f64(s))
                .unwrap_or(Duration::from_secs(1));

            *self.global_limit.write() = Some(Instant::now() + retry_after);
        }
    }

    /// Handle a 429 rate limit response
    pub fn handle_rate_limit(&self, endpoint: &str, retry_after: Duration, is_global: bool) {
        if is_global {
            *self.global_limit.write() = Some(Instant::now() + retry_after);
        } else {
            let reset_at = Instant::now() + retry_after;
            if let Some(mut limit_info) = self.endpoint_limits.get_mut(endpoint) {
                limit_info.reset_at = reset_at;
                limit_info.remaining = 0;
            } else {
                self.endpoint_limits.insert(
                    endpoint.to_string(),
                    RateLimitInfo {
                        remaining: 0,
                        limit: 50,
                        reset_at,
                        reset_after,
                    },
                );
            }
        }
    }

    /// Decrement remaining count for an endpoint
    pub fn decrement(&self, endpoint: &str) {
        if let Some(mut limit_info) = self.endpoint_limits.get_mut(endpoint) {
            if limit_info.remaining > 0 {
                limit_info.remaining -= 1;
            }
        }

        let route = self.extract_route(endpoint);
        if let Some(mut limit_info) = self.route_limits.get_mut(&route) {
            if limit_info.remaining > 0 {
                limit_info.remaining -= 1;
            }
        }
    }

    /// Extract route from endpoint (e.g., /guilds/{id}/members -> /guilds/{id}/members)
    fn extract_route(&self, endpoint: &str) -> String {
        // Remove query parameters
        let route = endpoint.split('?').next().unwrap_or(endpoint);
        
        // Normalize route (remove IDs for bucket matching)
        // Discord uses bucket-based rate limiting
        route.to_string()
    }

    /// Get statistics about rate limits
    pub fn get_stats(&self) -> RateLimitStats {
        let mut endpoint_count = 0;
        let mut route_count = 0;
        let mut total_remaining = 0;
        let mut total_limit = 0;

        for limit_info in self.endpoint_limits.iter() {
            endpoint_count += 1;
            total_remaining += limit_info.remaining as u64;
            total_limit += limit_info.limit as u64;
        }

        for limit_info in self.route_limits.iter() {
            route_count += 1;
        }

        RateLimitStats {
            endpoint_count,
            route_count,
            total_remaining,
            total_limit,
            global_rate_limited: self.global_limit.read().is_some(),
        }
    }
}

/// Rate limit statistics
#[derive(Debug, Clone)]
pub struct RateLimitStats {
    pub endpoint_count: usize,
    pub route_count: usize,
    pub total_remaining: u64,
    pub total_limit: u64,
    pub global_rate_limited: bool,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_rate_limiter() {
        let limiter = RateLimiter::new();
        assert!(limiter.can_request("/api/guilds/123"));
    }

    #[test]
    fn test_wait_time() {
        let limiter = RateLimiter::new();
        let wait = limiter.wait_time("/api/guilds/123");
        assert_eq!(wait, Duration::ZERO);
    }
}

