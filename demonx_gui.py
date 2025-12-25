"""
DemonX Nuker - GUI Version
Graphical User Interface for DemonX Nuker
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import asyncio
import threading
import json
import time
import queue
from pathlib import Path
from demonx_complete import DemonXComplete, OperationType
import discord

class DemonXGUI:
    """GUI Application for DemonX Nuker"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("DemonX Nuker - GUI Edition")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1e1e1e')
        
        # Variables
        self.nuker = None
        self.bot_token = tk.StringVar()
        self.guild_id = tk.StringVar()
        self.guild = None
        self.bot_running = False
        self.loop = None
        self.loop_thread = None
        self.loop_ready = threading.Event()  # Signal when loop is ready
        
        # Thread-safe queue for async-to-GUI communication
        self.gui_queue = queue.Queue()
        self._process_gui_queue()
        
        # Style configuration
        self.setup_styles()
        
        # Create UI
        self.create_widgets()
        
        # Load config
        self.load_config()
    
    def setup_styles(self):
        """Setup ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('Dark.TFrame', background='#1e1e1e')
        style.configure('Dark.TLabel', background='#1e1e1e', foreground='#ffffff')
        style.configure('Dark.TButton', background='#2d2d2d', foreground='#ffffff')
        style.map('Dark.TButton',
                  background=[('active', '#3d3d3d')])
        style.configure('Title.TLabel', background='#1e1e1e', foreground='#9d4edd', font=('Arial', 16, 'bold'))
        style.configure('Header.TLabel', background='#1e1e1e', foreground='#4a9eff', font=('Arial', 12, 'bold'))
    
    def create_widgets(self):
        """Create GUI widgets"""
        # Main container
        main_frame = ttk.Frame(self.root, style='Dark.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title = ttk.Label(main_frame, text="DEMONX NUKER", style='Title.TLabel')
        title.pack(pady=(0, 20))
        
        # Connection frame
        conn_frame = ttk.LabelFrame(main_frame, text="Connection", style='Dark.TFrame')
        conn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(conn_frame, text="Bot Token:", style='Dark.TLabel').grid(row=0, column=0, padx=5, pady=5, sticky='w')
        token_entry = ttk.Entry(conn_frame, textvariable=self.bot_token, width=60, show='*')
        token_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        
        ttk.Label(conn_frame, text="Guild ID:", style='Dark.TLabel').grid(row=1, column=0, padx=5, pady=5, sticky='w')
        guild_entry = ttk.Entry(conn_frame, textvariable=self.guild_id, width=60)
        guild_entry.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        
        conn_frame.columnconfigure(1, weight=1)
        
        connect_btn = ttk.Button(conn_frame, text="Connect", command=self.connect_bot)
        connect_btn.grid(row=0, column=2, rowspan=2, padx=5, pady=5)
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="Status", style='Dark.TFrame')
        status_frame.pack(fill=tk.X, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="Not Connected", style='Dark.TLabel', foreground='#ff4444')
        self.status_label.pack(pady=5)
        
        self.bot_info_label = ttk.Label(status_frame, text="", style='Dark.TLabel')
        self.bot_info_label.pack()
        
        # Main content area
        content_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        content_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Left panel - Operations
        left_panel = ttk.LabelFrame(content_frame, text="Operations", style='Dark.TFrame')
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Create scrollable frame for buttons
        canvas = tk.Canvas(left_panel, bg='#1e1e1e', highlightthickness=0)
        scrollbar = ttk.Scrollbar(left_panel, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='Dark.TFrame')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Operation buttons
        self.create_operation_buttons(scrollable_frame)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Right panel - Log/Output
        right_panel = ttk.LabelFrame(content_frame, text="Log Output", style='Dark.TFrame')
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.log_text = scrolledtext.ScrolledText(
            right_panel,
            bg='#2d2d2d',
            fg='#ffffff',
            font=('Consolas', 10),
            wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Statistics frame at bottom
        stats_frame = ttk.LabelFrame(main_frame, text="Statistics", style='Dark.TFrame')
        stats_frame.pack(fill=tk.X, pady=5)
        
        self.stats_label = ttk.Label(stats_frame, text="No operations yet", style='Dark.TLabel')
        self.stats_label.pack(pady=5)
    
    def create_operation_buttons(self, parent):
        """Create operation buttons"""
        operations = [
            ("Member Management", [
                ("Ban All Members", self.ban_all),
                ("Kick All Members", self.kick_all),
                ("Prune Members", self.prune_members),
                ("Mass Nickname", self.mass_nickname),
                ("Grant Admin All", self.grant_admin),
                ("Unban All", self.unban_all),
            ]),
            ("Channel Management", [
                ("Delete Channels", self.delete_channels),
                ("Create Channels", self.create_channels),
                ("Rename Channels", self.rename_channels),
                ("Shuffle Channels", self.shuffle_channels),
                ("Mass Ping", self.mass_ping),
                ("Create Categories", self.create_categories),
                ("Delete Categories", self.delete_categories),
            ]),
            ("Role Management", [
                ("Create Roles", self.create_roles),
                ("Delete Roles", self.delete_roles),
                ("Rename Roles", self.rename_roles),
            ]),
            ("Guild Management", [
                ("Rename Guild", self.rename_guild),
                ("Delete Invites", self.delete_invites),
                ("Create Invites", self.create_invites),
                ("Get Invites", self.get_invites),
            ]),
            ("Advanced", [
                ("Webhook Spam", self.webhook_spam),
                ("Auto React", self.auto_react),
                ("Delete Emojis", self.delete_emojis),
            ]),
            ("Presets & Stats", [
                ("Execute Preset", self.execute_preset),
                ("List Presets", self.list_presets),
                ("Statistics", self.show_statistics),
                ("History", self.show_history),
            ]),
        ]
        
        for category, ops in operations:
            # Category header
            header = ttk.Label(parent, text=category, style='Header.TLabel')
            header.pack(pady=(10, 5), anchor='w')
            
            # Operation buttons
            for op_name, op_func in ops:
                btn = ttk.Button(
                    parent,
                    text=op_name,
                    command=op_func,
                    style='Dark.TButton'
                )
                btn.pack(fill=tk.X, pady=2, padx=5)
    
    def log(self, message, color='#ffffff'):
        """Add message to log"""
        timestamp = time.strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}\n"
        
        # Insert with color tag
        start_pos = self.log_text.index(tk.END)
        self.log_text.insert(tk.END, full_message)
        end_pos = self.log_text.index(tk.END)
        
        # Configure tag for this message
        tag_name = f"color_{color}"
        if tag_name not in self.log_text.tag_names():
            self.log_text.tag_config(tag_name, foreground=color)
        
        self.log_text.tag_add(tag_name, start_pos, end_pos)
        self.log_text.see(tk.END)
        self.root.update()
    
    def load_config(self):
        """Load configuration"""
        self.use_proxy = False
        try:
            if Path('config.json').exists():
                with open('config.json', 'r') as f:
                    config = json.load(f)
                    self.use_proxy = config.get('proxy', False)
                    if self.use_proxy:
                        self.log("Proxy support enabled in config", '#44aaff')
        except Exception as e:
            self.log(f"Error loading config: {e}", '#ff4444')
    
    def connect_bot(self):
        """Connect to Discord bot"""
        token_input = self.bot_token.get().strip()
        guild_id_input = self.guild_id.get().strip()
        
        # Validate token using class method
        try:
            token = DemonXComplete.validate_token(token_input)
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid Bot Token: {str(e)}")
            return
        
        # Validate guild ID using class method
        try:
            guild_id = DemonXComplete.validate_guild_id(guild_id_input)
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid Guild ID: {str(e)}")
            return
        
        # Reset the ready event
        self.loop_ready.clear()
        
        # Start async loop in thread
        self.loop_thread = threading.Thread(target=self.run_bot_async, args=(token, guild_id), daemon=True)
        self.loop_thread.start()
    
    def run_bot_async(self, token, guild_id):
        """Run bot in async thread"""
        try:
            # Create event loop in this thread
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            use_proxy = getattr(self, 'use_proxy', False)
            
            # Create everything inside an async function so the loop is running
            async def setup_and_run_bot():
                # Now the loop is running, so we can create the bot
                self.nuker = DemonXComplete(token, use_proxy, False)
                
                # Log proxy status
                if use_proxy and self.nuker.proxy_manager:
                    proxy_count = len(self.nuker.proxy_manager.proxies) if self.nuker.proxy_manager.proxies else 0
                    if proxy_count > 0:
                        self.root.after(0, lambda: self.log(f"Proxy support: {proxy_count} proxies loaded", '#44aaff'))
                    else:
                        self.root.after(0, lambda: self.log("Proxy enabled but no proxies found in proxies.txt", '#ffaa44'))
                
                @self.nuker.bot.event
                async def on_ready():
                    try:
                        if self.nuker.bot.user:
                            self.root.after(0, lambda: self.update_status("Connected", '#44ff44'))
                            self.root.after(0, lambda: self.log(f"Connected as: {self.nuker.bot.user}", '#44ff44'))
                            self.root.after(0, lambda: self.bot_info_label.config(
                                text=f"Bot: {self.nuker.bot.user} | Guilds: {len(self.nuker.bot.guilds)}"
                            ))
                            
                            guild = self.nuker.bot.get_guild(guild_id)
                            if not guild:
                                self.root.after(0, lambda: messagebox.showerror(
                                    "Error", "Guild not found! Make sure bot is in the guild."
                                ))
                                return
                            
                            self.guild = guild
                            self.root.after(0, lambda: self.log(f"Guild: {guild.name} ({guild.id})", '#44ff44'))
                            self.root.after(0, lambda: self.log(f"Members: {guild.member_count}", '#44ff44'))
                            
                            if not await self.nuker.validate_permissions(guild):
                                self.root.after(0, lambda: messagebox.showerror(
                                    "Error", "Bot needs Administrator permissions!"
                                ))
                                return
                            
                            self.bot_running = True
                            self.root.after(0, lambda: self.log("Ready to execute operations!", '#44ff44'))
                    except Exception as e:
                        self.root.after(0, lambda: self.log(f"Error in on_ready: {e}", '#ff4444'))
                
                # Signal that loop is ready
                self.loop_ready.set()
                
                # Start the bot - this will keep running until bot closes
                try:
                    await self.nuker.bot.start(token)
                except Exception as e:
                    self.root.after(0, lambda: self.log(f"Bot error: {e}", '#ff4444'))
                finally:
                    # Stop the loop when bot closes
                    self.loop.call_soon_threadsafe(self.loop.stop)
            
            # Create task and run loop forever
            # This ensures the loop is running when we create the bot
            task = self.loop.create_task(setup_and_run_bot())
            
            # Run the loop forever - this keeps it running and accessible from other threads
            self.loop.run_forever()
        except discord.LoginFailure:
            error_msg = "Invalid bot token. Please check your token from Discord Developer Portal."
            self.root.after(0, lambda: messagebox.showerror("Authentication Error", error_msg))
            self.root.after(0, lambda: self.log(f"Authentication Error: {error_msg}", '#ff4444'))
        except discord.HTTPException as e:
            if e.status == 401:
                error_msg = "Invalid bot token. Please verify your token."
                self.root.after(0, lambda: messagebox.showerror("Authentication Error", error_msg))
            else:
                error_msg = f"HTTP Error {e.status}: {str(e)[:100]}"
                self.root.after(0, lambda: messagebox.showerror("Connection Error", error_msg))
            self.root.after(0, lambda: self.log(f"Error: {error_msg}", '#ff4444'))
        except ConnectionError:
            error_msg = "Connection error. Check your internet connection and try again."
            self.root.after(0, lambda: messagebox.showerror("Connection Error", error_msg))
            self.root.after(0, lambda: self.log(f"Connection Error: {error_msg}", '#ff4444'))
        except Exception as e:
            import traceback
            error_msg = f"Unexpected error: {str(e)[:100]}"
            error_trace = traceback.format_exc()
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
            self.root.after(0, lambda: self.log(f"Error: {error_msg}", '#ff4444'))
            self.root.after(0, lambda: self.log(f"Traceback: {error_trace}", '#ff4444'))
            print(f"Error in run_bot_async: {e}")
            print(traceback.format_exc())
    
    def update_status(self, status, color='#ffffff'):
        """Update status label"""
        self.status_label.config(text=status, foreground=color)
    
    def check_connected(self):
        """Check if bot is connected"""
        if not self.bot_running or not self.guild:
            messagebox.showwarning("Warning", "Please connect to bot first!")
            return False
        return True
    
    def _process_gui_queue(self):
        """Process GUI update queue (thread-safe)"""
        try:
            while True:
                try:
                    action = self.gui_queue.get_nowait()
                    if action['type'] == 'log':
                        self.log(action['message'], action.get('color', '#ffffff'))
                    elif action['type'] == 'status':
                        self.update_status(action['status'], action.get('color', '#ffffff'))
                    elif action['type'] == 'messagebox_error':
                        messagebox.showerror(action['title'], action['message'])
                    elif action['type'] == 'messagebox_warning':
                        messagebox.showwarning(action['title'], action['message'])
                    elif action['type'] == 'messagebox_info':
                        messagebox.showinfo(action['title'], action['message'])
                    elif action['type'] == 'update_label':
                        action['widget'].config(text=action['text'], **action.get('kwargs', {}))
                except queue.Empty:
                    break
        except Exception as e:
            # Log error but don't crash
            print(f"Error processing GUI queue: {e}")
        finally:
            # Schedule next check
            self.root.after(100, self._process_gui_queue)
    
    def _safe_gui_update(self, action_type: str, **kwargs):
        """Thread-safe GUI update using queue"""
        try:
            self.gui_queue.put({
                'type': action_type,
                **kwargs
            })
        except Exception as e:
            # Fallback to direct update if queue fails
            print(f"Error queuing GUI update: {e}")
            if action_type == 'log':
                self.root.after(0, lambda: self.log(kwargs.get('message', ''), kwargs.get('color', '#ffffff')))
    
    def run_async(self, coro):
        """Run async function with enhanced error handling and thread-safe GUI updates"""
        if not self.loop:
            error_msg = "Event loop not initialized. Please connect to bot first."
            self._safe_gui_update('messagebox_error', title="Error", message=error_msg)
            self._safe_gui_update('log', message=error_msg, color='#ff4444')
            return
        
        # Wait for loop to be ready (with timeout)
        if not self.loop_ready.wait(timeout=5.0):
            error_msg = "Event loop is not ready. Please wait and try again."
            self._safe_gui_update('messagebox_error', title="Error", message=error_msg)
            self._safe_gui_update('log', message=error_msg, color='#ff4444')
            return
        
        # Check if bot is connected
        if not self.bot_running or not self.guild:
            error_msg = "Bot is not connected. Please wait for connection to complete."
            self._safe_gui_update('messagebox_warning', title="Warning", message=error_msg)
            self._safe_gui_update('log', message=error_msg, color='#ffaa44')
            return
        
        def callback(future):
            try:
                result = future.result()
                self._safe_gui_update('log', message="Operation completed!", color='#44ff44')
            except discord.Forbidden as e:
                error_msg = "Permission denied. Bot may lack required permissions."
                self._safe_gui_update('messagebox_error', title="Permission Error", message=error_msg)
                self._safe_gui_update('log', message=f"Permission Error: {error_msg}", color='#ff4444')
            except discord.HTTPException as e:
                if e.status == 429:
                    error_msg = "Rate limited. Please wait and try again."
                    self._safe_gui_update('messagebox_warning', title="Rate Limited", message=error_msg)
                    self._safe_gui_update('log', message=f"Rate Limited: {error_msg}", color='#ffaa44')
                elif e.status == 404:
                    error_msg = "Resource not found. The target may have been deleted."
                    self._safe_gui_update('messagebox_error', title="Not Found", message=error_msg)
                    self._safe_gui_update('log', message=f"Not Found: {error_msg}", color='#ff4444')
                else:
                    error_msg = f"HTTP Error {e.status}: {str(e)[:100]}"
                    self._safe_gui_update('messagebox_error', title="HTTP Error", message=error_msg)
                    self._safe_gui_update('log', message=f"HTTP Error: {error_msg}", color='#ff4444')
            except asyncio.TimeoutError:
                error_msg = "Operation timed out. The server may be slow or unresponsive."
                self._safe_gui_update('messagebox_error', title="Timeout", message=error_msg)
                self._safe_gui_update('log', message=f"Timeout: {error_msg}", color='#ff4444')
            except ConnectionError:
                error_msg = "Connection error. Check your internet connection."
                self._safe_gui_update('messagebox_error', title="Connection Error", message=error_msg)
                self._safe_gui_update('log', message=f"Connection Error: {error_msg}", color='#ff4444')
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)[:100]}"
                self._safe_gui_update('messagebox_error', title="Error", message=error_msg)
                self._safe_gui_update('log', message=f"Error: {error_msg}", color='#ff4444')
        
        # Try to schedule the coroutine
        # run_coroutine_threadsafe works even if loop is not running yet (it will queue it)
        try:
            future = asyncio.run_coroutine_threadsafe(coro, self.loop)
            future.add_done_callback(callback)
        except RuntimeError as e:
            error_msg = f"Failed to schedule operation: {str(e)}"
            if "no running event loop" in str(e).lower() or "no current event loop" in str(e).lower():
                error_msg = "Event loop is not ready. Please wait a moment and try again."
            self._safe_gui_update('messagebox_error', title="Error", message=error_msg)
            self._safe_gui_update('log', message=error_msg, color='#ff4444')
        except Exception as e:
            error_msg = f"Unexpected error scheduling operation: {str(e)[:100]}"
            self._safe_gui_update('messagebox_error', title="Error", message=error_msg)
            self._safe_gui_update('log', message=error_msg, color='#ff4444')
    
    # Operation methods
    def ban_all(self):
        if not self.check_connected():
            return
        self.log("Starting ban all members...", '#ffff44')
        self.run_async(self.nuker.ban_all_members(self.guild))
    
    def kick_all(self):
        if not self.check_connected():
            return
        self.log("Starting kick all members...", '#ffff44')
        self.run_async(self.nuker.kick_all_members(self.guild))
    
    def prune_members(self):
        if not self.check_connected():
            return
        days = simpledialog.askinteger("Prune Members", "Days of inactivity:", initialvalue=7)
        if days:
            self.log(f"Pruning members inactive for {days} days...", '#ffff44')
            self.run_async(self.nuker.prune_members(self.guild, days))
    
    def mass_nickname(self):
        if not self.check_connected():
            return
        nickname = simpledialog.askstring("Mass Nickname", "Enter nickname (leave empty for random):")
        self.log("Changing all nicknames...", '#ffff44')
        self.run_async(self.nuker.mass_nickname(self.guild, nickname if nickname else None))
    
    def grant_admin(self):
        if not self.check_connected():
            return
        self.log("Granting admin to all members...", '#ffff44')
        self.run_async(self.nuker.grant_admin_all(self.guild))
    
    def unban_all(self):
        if not self.check_connected():
            return
        self.log("Unbanning all members...", '#ffff44')
        self.run_async(self.nuker.unban_all_members(self.guild))
    
    def delete_channels(self):
        if not self.check_connected():
            return
        self.log("Deleting all channels...", '#ffff44')
        self.run_async(self.nuker.delete_channels(self.guild))
    
    def create_channels(self):
        if not self.check_connected():
            return
        count = simpledialog.askinteger("Create Channels", "Number of channels:", initialvalue=50)
        if count:
            name = simpledialog.askstring("Create Channels", "Channel name (optional):")
            self.log(f"Creating {count} channels...", '#ffff44')
            self.run_async(self.nuker.create_channels(self.guild, count, name if name else None))
    
    def rename_channels(self):
        if not self.check_connected():
            return
        name = simpledialog.askstring("Rename Channels", "New name (optional):")
        self.log("Renaming all channels...", '#ffff44')
        self.run_async(self.nuker.rename_channels(self.guild, name if name else None))
    
    def shuffle_channels(self):
        if not self.check_connected():
            return
        self.log("Shuffling channels...", '#ffff44')
        self.run_async(self.nuker.shuffle_channels(self.guild))
    
    def mass_ping(self):
        if not self.check_connected():
            return
        message = simpledialog.askstring("Mass Ping", "Message:", initialvalue="@everyone Nuked")
        count = simpledialog.askinteger("Mass Ping", "Count per channel:", initialvalue=5)
        if message and count:
            self.log(f"Mass pinging with message: {message}...", '#ffff44')
            self.run_async(self.nuker.mass_ping(self.guild, message, count))
    
    def create_categories(self):
        if not self.check_connected():
            return
        count = simpledialog.askinteger("Create Categories", "Number of categories:", initialvalue=10)
        if count:
            name = simpledialog.askstring("Create Categories", "Category name (optional):")
            self.log(f"Creating {count} categories...", '#ffff44')
            self.run_async(self.nuker.create_categories(self.guild, count, name if name else None))
    
    def delete_categories(self):
        if not self.check_connected():
            return
        self.log("Deleting all categories...", '#ffff44')
        self.run_async(self.nuker.delete_categories(self.guild))
    
    def create_roles(self):
        if not self.check_connected():
            return
        count = simpledialog.askinteger("Create Roles", "Number of roles:", initialvalue=50)
        if count:
            name = simpledialog.askstring("Create Roles", "Role name (optional):")
            self.log(f"Creating {count} roles...", '#ffff44')
            self.run_async(self.nuker.create_roles(self.guild, count, name if name else None))
    
    def delete_roles(self):
        if not self.check_connected():
            return
        self.log("Deleting all roles...", '#ffff44')
        self.run_async(self.nuker.delete_roles(self.guild))
    
    def rename_roles(self):
        if not self.check_connected():
            return
        name = simpledialog.askstring("Rename Roles", "New name (optional):")
        self.log("Renaming all roles...", '#ffff44')
        self.run_async(self.nuker.rename_roles(self.guild, name if name else None))
    
    def rename_guild(self):
        if not self.check_connected():
            return
        name = simpledialog.askstring("Rename Guild", "New guild name (optional):")
        self.log("Renaming guild...", '#ffff44')
        self.run_async(self.nuker.rename_guild(self.guild, name if name else None))
    
    def delete_invites(self):
        if not self.check_connected():
            return
        self.log("Deleting all invites...", '#ffff44')
        self.run_async(self.nuker.delete_all_invites(self.guild))
    
    def create_invites(self):
        if not self.check_connected():
            return
        count = simpledialog.askinteger("Create Invites", "Number of invites:", initialvalue=10)
        if count:
            self.log(f"Creating {count} invites...", '#ffff44')
            self.run_async(self.nuker.create_invites(self.guild, count))
    
    def get_invites(self):
        if not self.check_connected():
            return
        self.log("Fetching all invites...", '#ffff44')
        
        if not self.loop:
            error_msg = "Event loop not initialized. Please connect to bot first."
            messagebox.showerror("Error", error_msg)
            self.log(error_msg, '#ff4444')
            return
        
        # Wait for loop to be ready
        if not self.loop_ready.wait(timeout=5.0):
            error_msg = "Event loop is not ready. Please wait and try again."
            messagebox.showerror("Error", error_msg)
            self.log(error_msg, '#ff4444')
            return
        
        def callback(future):
            try:
                invites = future.result()
                if invites:
                    self.root.after(0, lambda: self.log(f"Found {len(invites)} invite(s)", '#44ff44'))
                    
                    # Build invite details string
                    invite_details = f"Found {len(invites)} invite(s):\n\n"
                    for i, invite in enumerate(invites, 1):
                        try:
                            invite_details += f"{i}. Code: {invite.code}\n"
                            invite_details += f"   URL: {invite.url}\n"
                            if invite.inviter:
                                invite_details += f"   Created by: {invite.inviter}\n"
                            if invite.channel:
                                invite_details += f"   Channel: #{invite.channel.name}\n"
                            uses = f"{invite.uses}/{invite.max_uses}" if invite.max_uses else f"{invite.uses}/∞"
                            invite_details += f"   Uses: {uses}\n"
                            if invite.expires_at:
                                invite_details += f"   Expires: {invite.expires_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                            invite_details += "\n"
                            
                            # Also log each invite
                            info = f"Invite {i}: {invite.code} | {invite.url}"
                            self.root.after(0, lambda i=info: self.log(i, '#ffffff'))
                        except Exception as e:
                            self.root.after(0, lambda: self.log(f"Error parsing invite: {e}", '#ff4444'))
                    
                    # Show in messagebox
                    self.root.after(0, lambda: messagebox.showinfo("Server Invites", invite_details))
                else:
                    self.root.after(0, lambda: self.log("No invites found", '#ffaa44'))
                    self.root.after(0, lambda: messagebox.showinfo("Server Invites", "No invites found in this server."))
            except Exception as e:
                error_msg = str(e)
                self.root.after(0, lambda: self.log(f"Error: {error_msg}", '#ff4444'))
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to fetch invites:\n{error_msg}"))
        
        try:
            future = asyncio.run_coroutine_threadsafe(self.nuker.get_all_invites(self.guild), self.loop)
            future.add_done_callback(callback)
        except RuntimeError as e:
            error_msg = f"Failed to schedule operation: {str(e)}"
            messagebox.showerror("Error", error_msg)
            self.log(error_msg, '#ff4444')
    
    def webhook_spam(self):
        if not self.check_connected():
            return
        message = simpledialog.askstring("Webhook Spam", "Message:", initialvalue="Nuked")
        count = simpledialog.askinteger("Webhook Spam", "Count per webhook:", initialvalue=10)
        if message and count:
            self.log(f"Webhook spamming: {message}...", '#ffff44')
            self.run_async(self.nuker.webhook_spam(self.guild, message, count))
    
    def auto_react(self):
        if not self.check_connected():
            return
        emoji = simpledialog.askstring("Auto React", "Emoji:", initialvalue="💀")
        limit = simpledialog.askinteger("Auto React", "Messages per channel:", initialvalue=100)
        if emoji and limit:
            self.log(f"Auto reacting with {emoji}...", '#ffff44')
            self.run_async(self.nuker.auto_react_messages(self.guild, emoji, limit))
    
    def delete_emojis(self):
        if not self.check_connected():
            return
        self.log("Deleting all emojis...", '#ffff44')
        self.run_async(self.nuker.delete_emojis(self.guild))
    
    def execute_preset(self):
        if not self.check_connected():
            return
        presets = self.nuker.preset_manager.list_presets()
        if not presets:
            messagebox.showinfo("Info", "No presets found. Create presets in presets.json")
            return
        
        preset_name = simpledialog.askstring("Execute Preset", f"Preset name:\nAvailable: {', '.join(presets)}")
        if preset_name:
            self.log(f"Executing preset: {preset_name}...", '#ffff44')
            self.run_async(self.nuker.execute_preset(self.guild, preset_name))
    
    def list_presets(self):
        presets = self.nuker.preset_manager.list_presets() if self.nuker else []
        if presets:
            message = "Available Presets:\n\n" + "\n".join(f"• {p}" for p in presets)
            messagebox.showinfo("Presets", message)
        else:
            messagebox.showinfo("Presets", "No presets found.")
    
    def show_statistics(self):
        if not self.nuker:
            messagebox.showwarning("Warning", "Not connected!")
            return
        
        stats = self.nuker.stats
        elapsed = time.time() - stats.get('start_time', time.time())
        
        message = f"""Statistics:
        
Banned: {stats.get('banned', 0)}
Kicked: {stats.get('kicked', 0)}
Channels Created: {stats.get('channels_created', 0)}
Channels Deleted: {stats.get('channels_deleted', 0)}
Roles Created: {stats.get('roles_created', 0)}
Roles Deleted: {stats.get('roles_deleted', 0)}
Messages Sent: {stats.get('messages_sent', 0)}
Errors: {stats.get('errors', 0)}
Uptime: {elapsed:.2f} seconds"""
        
        messagebox.showinfo("Statistics", message)
    
    def show_history(self):
        if not self.nuker:
            messagebox.showwarning("Warning", "Not connected!")
            return
        
        stats = self.nuker.operation_history.get_statistics()
        if stats:
            message = "Operation History:\n\n" + "\n".join(f"{k}: {v}" for k, v in sorted(stats.items()))
            messagebox.showinfo("History", message)
        else:
            messagebox.showinfo("History", "No operation history.")

def main():
    """Main function"""
    root = tk.Tk()
    app = DemonXGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()

