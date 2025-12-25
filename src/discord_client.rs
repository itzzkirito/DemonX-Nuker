use crate::rate_limiter::RateLimiter;
use crate::proxy_manager::{ProxyManager, ProxyInfo};
use std::sync::Arc;
use twilight_http::Client as HttpClient;
use twilight_model::id::{Id, marker::{GuildMarker, UserMarker, ChannelMarker}};
use anyhow::Result;
use reqwest::Client as ReqwestClient;

/// Discord client with rate limiting and proxy support
pub struct DiscordClient {
    http_client: HttpClient,
    rate_limiter: Arc<RateLimiter>,
    proxy_manager: Option<Arc<ProxyManager>>,
    reqwest_client: Option<ReqwestClient>,
    token: String,
}

impl DiscordClient {
    /// Create a new Discord client
    pub fn new(token: String) -> Self {
        let http_client = HttpClient::new(token.clone());
        let rate_limiter = Arc::new(RateLimiter::new());

        Self {
            http_client,
            rate_limiter,
            proxy_manager: None,
            reqwest_client: None,
            token,
        }
    }

    /// Create with proxy support
    pub fn with_proxy(token: String, proxy_manager: Arc<ProxyManager>) -> Result<Self> {
        let rate_limiter = Arc::new(RateLimiter::new());
        
        // Get proxy for initial client
        let proxy_info = proxy_manager.get_next_proxy()
            .ok_or_else(|| anyhow::anyhow!("No proxies available"))?;

        // Create reqwest client with proxy
        let mut reqwest_builder = reqwest::Client::builder();
        
        if let Ok(proxy) = proxy_info.to_reqwest_proxy() {
            reqwest_builder = reqwest_builder.proxy(proxy);
        }

        let reqwest_client = reqwest_builder
            .build()
            .map_err(|e| anyhow::anyhow!("Failed to create HTTP client: {}", e))?;

        // Create Twilight HTTP client
        // Note: Twilight doesn't directly support proxies, so we'll need to use reqwest for direct API calls
        let http_client = HttpClient::new(token.clone());

        Ok(Self {
            http_client,
            rate_limiter,
            proxy_manager: Some(proxy_manager),
            reqwest_client: Some(reqwest_client),
            token,
        })
    }

    /// Make a rate-limited request
    pub async fn request_with_rate_limit<F, T>(&self, endpoint: &str, f: F) -> Result<T>
    where
        F: std::future::Future<Output = Result<T>>,
    {
        // Wait for rate limit
        let wait_time = self.rate_limiter.wait_time(endpoint);
        if !wait_time.is_zero() {
            tokio::time::sleep(wait_time).await;
        }

        // Check if we can make the request
        if !self.rate_limiter.can_request(endpoint) {
            let wait_time = self.rate_limiter.wait_time(endpoint);
            tokio::time::sleep(wait_time).await;
        }

        // Execute request
        let result = f.await;

        // Update rate limiter (would need to parse response headers)
        // This is a simplified version - in practice, you'd parse headers from the response

        result
    }

    /// Get HTTP client
    pub fn http(&self) -> &HttpClient {
        &self.http_client
    }

    /// Get rate limiter
    pub fn rate_limiter(&self) -> &Arc<RateLimiter> {
        &self.rate_limiter
    }

    /// Get proxy manager
    pub fn proxy_manager(&self) -> Option<&Arc<ProxyManager>> {
        self.proxy_manager.as_ref()
    }

    /// Rotate to next proxy
    pub async fn rotate_proxy(&mut self) -> Result<()> {
        if let Some(proxy_manager) = &self.proxy_manager {
            if let Some(proxy_info) = proxy_manager.get_next_proxy() {
                let mut reqwest_builder = reqwest::Client::builder();
                
                if let Ok(proxy) = proxy_info.to_reqwest_proxy() {
                    reqwest_builder = reqwest_builder.proxy(proxy);
                }

                self.reqwest_client = Some(
                    reqwest_builder
                        .build()
                        .map_err(|e| anyhow::anyhow!("Failed to create HTTP client: {}", e))?,
                );
            }
        }
        Ok(())
    }
}

// Example usage functions
impl DiscordClient {
    /// Ban a user from a guild
    pub async fn ban_user(&self, guild_id: Id<GuildMarker>, user_id: Id<UserMarker>, reason: Option<&str>) -> Result<()> {
        let endpoint = format!("/guilds/{}/members/{}", guild_id.get(), user_id.get());
        
        self.request_with_rate_limit(&endpoint, async {
            let mut request = self.http().ban_user(guild_id, user_id);
            if let Some(reason) = reason {
                request = request.reason(reason)?;
            }
            request.await?;
            Ok(())
        }).await
    }

    /// Create a channel
    pub async fn create_channel(&self, guild_id: Id<GuildMarker>, name: &str) -> Result<Id<ChannelMarker>> {
        let endpoint = format!("/guilds/{}/channels", guild_id.get());
        
        self.request_with_rate_limit(&endpoint, async {
            use twilight_http::request::guild::create_guild_channel::CreateGuildChannelFields;
            
            let fields = CreateGuildChannelFields::new(name);
            let response = self.http()
                .create_guild_channel(guild_id, &fields)?
                .await?;
            
            let model = response.model().await?;
            Ok(model.id)
        }).await
    }
}

