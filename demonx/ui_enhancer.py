"""
DemonX UI Enhancement Module
Provides enhanced visual elements while maintaining async architecture
"""

from typing import Optional, List, Tuple
import os
import time
import shutil

# Try to import Rich and PyFiglet, fallback to colorama if not available
try:
    from rich.console import Console
    from rich.text import Text
    from rich.align import Align
    from rich.panel import Panel
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None

try:
    import pyfiglet
    PYFIGLET_AVAILABLE = True
except ImportError:
    PYFIGLET_AVAILABLE = False

# Fallback to colorama
from colorama import Fore, Style, init
init(autoreset=True)


class UIEnhancer:
    """
    Enhanced UI renderer with DemonX-style visual elements
    Maintains compatibility with existing DemonX architecture
    """
    
    def __init__(self, use_rich: bool = True, use_figlet: bool = True):
        """
        Initialize UI Enhancer
        
        Args:
            use_rich: Use Rich library if available
            use_figlet: Use PyFiglet for banners if available
        """
        self.use_rich = use_rich and RICH_AVAILABLE
        self.use_figlet = use_figlet and PYFIGLET_AVAILABLE
        
        if self.use_rich:
            self.console = Console()
            # Get terminal width from Rich console
            self.terminal_width = self.console.width
        else:
            self.console = None
            # Get terminal width manually
            try:
                self.terminal_width = shutil.get_terminal_size().columns
            except:
                self.terminal_width = 80  # Fallback width
    
    def clear_screen(self) -> None:
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
        if self.use_rich and self.console:
            self.console.clear()
    
    def print_banner_enhanced(self, title: str = "DEMONX") -> None:
        """
        Print banner in DemonX style using Rich + PyFiglet
        
        Args:
            title: Title text for banner
        """
        if self.use_rich and self.use_figlet and self.console:
            try:
                # Generate ASCII art with PyFiglet
                figlet = pyfiglet.Figlet(font="big")
                ascii_title = figlet.renderText(title)
                
                # Create styled text with Rich - Main text/logo color: #00CFFF
                banner_text = Text()
                for line in ascii_title.splitlines():
                    if line.strip():  # Skip empty lines
                        banner_text.append(line + "\n", style="#00CFFF bold")
                
                # Center and print
                self.console.print(Align.center(banner_text))
                
                # Add warning message - Glow/accent color: #3AF2FF
                warning = Text("THEY CALL IT CHAOS. I CALL IT A BUSINESS MODEL.", 
                             style="#3AF2FF")
                self.console.print(Align.center(warning))
                self.console.print()  # Blank line
                return
            except Exception as e:
                # Fallback to classic if figlet fails
                pass
        
        # Fallback to classic banner
        self._print_banner_classic()
    
    def _print_banner_classic(self) -> None:
        """Classic DemonX banner (fallback) - centered using terminal width"""
        # Use CYAN as closest match to #00CFFF for colorama
        banner_lines = [
            "",
            f"{Fore.CYAN}{Style.BRIGHT}",
            " ██████████                                                █████ █████",
            "░░███░░░░███                                              ░░███ ░░███ ",
            " ░███   ░░███  ██████  █████████████    ██████  ████████   ░░███ ███  ",
            " ░███    ░███ ███░░███░░███░░███░░███  ███░░███░░███░░███   ░░█████   ",
            " ░███    ░███░███████  ░███ ░███ ░███ ░███ ░███ ░███ ░███    ███░███  ",
            " ░███    ███ ░███░░░   ░███ ░███ ░███ ░███ ░███ ░███ ░███   ███ ░░███ ",
            " ██████████  ░░██████  █████░███ █████░░██████  ████ █████ █████ █████",
            "░░░░░░░░░░    ░░░░░░  ░░░░░ ░░░ ░░░░░  ░░░░░░  ░░░░ ░░░░░ ░░░░░ ░░░░░ ",
            f"{Fore.CYAN}{Style.RESET_ALL}",
            ""
        ]
        
        # Helper function to strip ANSI codes
        def strip_ansi(text):
            for code in [Fore.CYAN, Fore.BLUE, Style.BRIGHT, Style.RESET_ALL]:
                text = text.replace(code, '')
            return text
        
        # Center each line using actual terminal width
        for line in banner_lines:
            if line.strip():
                line_len = len(strip_ansi(line))
                padding = max(0, (self.terminal_width - line_len) // 2)
                print(" " * padding + line)
            else:
                print(line)
        
        # Center warning message - Glow/accent color (bright cyan)
        warning = f"{Fore.CYAN}{Style.BRIGHT}THEY CALL IT CHAOS. I CALL IT A BUSINESS MODEL.{Style.RESET_ALL}"
        warning_len = len(strip_ansi(warning))
        padding = max(0, (self.terminal_width - warning_len) // 2)
        print(" " * padding + warning + "\n")
    
    def display_menu_enhanced(self, menu_data: List[List[Tuple[str, str]]]) -> None:
        """
        Display menu with enhanced DemonX-style formatting (centered with aligned columns)
        
        Args:
            menu_data: List of rows, each containing tuples of (number, text)
        """
        if self.use_rich and self.console:
            # Calculate max width for each column to align them properly
            max_cols = max(len(row) for row in menu_data) if menu_data else 5
            col_widths = [0] * max_cols
            
            # First pass: calculate column widths
            for row in menu_data:
                for col_idx, (num, text) in enumerate(row):
                    if num and text:
                        formatted = f"{num} {text}"
                        col_widths[col_idx] = max(col_widths[col_idx], len(formatted))
            
            # Add spacing between columns
            column_spacing = 3
            
            # Print blank line before menu
            self.console.print()
            
            # Second pass: build and center each line
            for row in menu_data:
                line_parts = []
                for col_idx, (num, text) in enumerate(row):
                    if num and text:
                        formatted = f"{num} {text}"
                        # Pad to column width
                        padded = f"{formatted:<{col_widths[col_idx]}}"
                        line_parts.append(padded)
                
                if line_parts:
                    # Join columns with spacing
                    line = (" " * column_spacing).join(line_parts)
                    # Secondary text color: #0F6FBF
                    line_text = Text(line, style="#0F6FBF")
                    # Center the entire line
                    self.console.print(Align.center(line_text))
            
            # Print blank line after menu
            self.console.print()
            
            # Warning message centered - Glow/accent color: #3AF2FF
            warning = Text("THEY CALL IT CHAOS. I CALL IT A BUSINESS MODEL.", style="#3AF2FF")
            self.console.print(Align.center(warning))
            self.console.print()
        else:
            # Classic menu display
            self._display_menu_classic(menu_data)
    
    def _display_menu_classic(self, menu_data: List[List[Tuple[str, str]]]) -> None:
        """Classic menu display (fallback) - centered with aligned columns"""
        # Helper function to strip ANSI codes
        def strip_ansi(text):
            for code in [Fore.CYAN, Fore.BLUE, Style.BRIGHT, Style.RESET_ALL]:
                text = text.replace(code, '')
            return text
        
        # Calculate max width for each column to align them properly
        max_cols = max(len(row) for row in menu_data) if menu_data else 5
        col_widths = [0] * max_cols
        
        # First pass: calculate column widths (without ANSI codes)
        for row in menu_data:
            for col_idx, (num, text) in enumerate(row):
                if num and text:
                    formatted = f"{num} {text}"
                    col_widths[col_idx] = max(col_widths[col_idx], len(formatted))
        
        # Column spacing
        column_spacing = 3
        
        print()  # Blank line before menu
        
        # Second pass: build and center each line
        for row in menu_data:
            line_items = []
            for col_idx, (num, text) in enumerate(row):
                if num and text:
                    # Main text color for numbers: #00CFFF, Secondary for text: #0F6FBF
                    formatted = f"{Fore.CYAN}{num}{Fore.BLUE} {text}{Style.RESET_ALL}"
                    # Pad to column width (using plain text length)
                    plain_text = f"{num} {text}"
                    padded_plain = f"{plain_text:<{col_widths[col_idx]}}"
                    # Apply same padding to styled text
                    padding_needed = col_widths[col_idx] - len(plain_text)
                    if padding_needed > 0:
                        formatted = formatted + " " * padding_needed
                    line_items.append(formatted)
            
            if line_items:
                # Join columns with spacing
                formatted_line = (" " * column_spacing).join(line_items)
                # Center the line using actual terminal width
                line_len = len(strip_ansi(formatted_line))
                padding = max(0, (self.terminal_width - line_len) // 2)
                print(" " * padding + formatted_line)
        
        print()  # Blank line after menu
        
        # Center warning message - Glow/accent color (bright cyan)
        warning = f"{Fore.CYAN}{Style.BRIGHT}THEY CALL IT CHAOS. I CALL IT A BUSINESS MODEL.{Style.RESET_ALL}"
        warning_len = len(strip_ansi(warning))
        padding = max(0, (self.terminal_width - warning_len) // 2)
        print(" " * padding + warning + "\n")
    
    def print_prompt_enhanced(self) -> str:
        """
        Enhanced prompt in DemonX style (centered)
        
        Returns:
            User input string
        """
        current_time = time.strftime("%H:%M:%S")
        
        if self.use_rich and self.console:
            self.console.print()
            # Center timestamp
            time_text = Text(current_time, style="white")
            self.console.print(Align.center(time_text))
            # Center prompt label
            prompt_label = Text("INP", style="red") + Text(" • ", style="white") + Text("OPTION", style="red")
            self.console.print(Align.center(prompt_label))
            # Center the input prompt
            # Note: Python's input() always starts at column 0, so we'll just center the visual prompt
            # The actual input will appear left-aligned, which is standard terminal behavior
            prompt_symbol = Text("> ", style="white")
            self.console.print(Align.center(prompt_symbol))
            # Get input - it will be on next line left-aligned (this is standard terminal behavior)
            choice = input()
        else:
            # Classic prompt - centered using terminal width
            def strip_ansi(text):
                for code in [Fore.RED, Fore.WHITE, Style.RESET_ALL]:
                    text = text.replace(code, '')
                return text
            
            print()
            # Center timestamp
            time_len = len(current_time)
            padding = max(0, (self.terminal_width - time_len) // 2)
            print(" " * padding + f"{Fore.WHITE}{current_time}{Style.RESET_ALL}")
            # Center prompt label
            prompt_text = f"{Fore.RED}INP{Style.RESET_ALL} {Fore.WHITE}•{Style.RESET_ALL} {Fore.RED}OPTION{Style.RESET_ALL}"
            prompt_len = len(strip_ansi(prompt_text))
            padding = max(0, (self.terminal_width - prompt_len) // 2)
            print(" " * padding + prompt_text)
            # Center prompt symbol
            prompt_symbol = f"{Fore.WHITE}>{Style.RESET_ALL} "
            symbol_len = len(strip_ansi(prompt_symbol))
            padding = max(0, (self.terminal_width - symbol_len) // 2)
            print(" " * padding, end="")
            choice = input()
        
        return choice.strip()
    
    def print_info_panel(self, title: str, content: str, style: str = "cyan") -> None:
        """
        Print information in a styled panel (Rich only)
        
        Args:
            title: Panel title
            content: Panel content
            style: Color style
        """
        if self.use_rich and self.console:
            panel = Panel(
                content,
                title=title,
                border_style=style,
                title_align="left"
            )
            self.console.print(panel)
        else:
            # Classic display
            print(f"\n{Fore.CYAN}{'═'*70}")
            print(f"{Fore.CYAN}║{Fore.WHITE}{Style.BRIGHT}  {title}{Fore.CYAN}{' ' * (68 - len(title))}║")
            print(f"{Fore.CYAN}{'═'*70}")
            print(content)
            print(f"{Fore.CYAN}{'═'*70}{Style.RESET_ALL}\n")
    
    def print_success(self, message: str) -> None:
        """Print success message"""
        if self.use_rich and self.console:
            self.console.print(f"[bold green]✓[/bold green] {message}")
        else:
            print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")
    
    def print_error(self, message: str) -> None:
        """Print error message"""
        if self.use_rich and self.console:
            self.console.print(f"[bold red]✗[/bold red] {message}")
        else:
            print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")
    
    def print_warning(self, message: str) -> None:
        """Print warning message"""
        if self.use_rich and self.console:
            self.console.print(f"[bold yellow]⚠[/bold yellow] {message}")
        else:
            print(f"{Fore.YELLOW}⚠ {message}{Style.RESET_ALL}")


# Convenience function for easy integration
def create_ui_enhancer(use_rich: bool = True, use_figlet: bool = True) -> UIEnhancer:
    """
    Create a UI enhancer instance with automatic fallback
    
    Args:
        use_rich: Try to use Rich library
        use_figlet: Try to use PyFiglet
        
    Returns:
        UIEnhancer instance
    """
    return UIEnhancer(use_rich=use_rich, use_figlet=use_figlet)


# Example usage
if __name__ == "__main__":
    # Test the UI enhancer
    ui = create_ui_enhancer()
    
    # Clear screen
    ui.clear_screen()
    
    # Print banner
    ui.print_banner_enhanced("DEMONX")
    
    # Example menu data
    menu_data = [
        [("[01]", "BAN MEMBERS"), ("[02]", "DELETE CHANNELS"), ("[03]", "KICK MEMBERS")],
        [("[04]", "PRUNE"), ("[05]", "CREATE CHANNELS"), ("[06]", "MASS PING")],
    ]
    
    # Display menu
    ui.display_menu_enhanced(menu_data)
    
    # Print info panel
    ui.print_info_panel("Bot Information", "Bot is ready!")
    
    # Test prompts
    ui.print_success("Operation completed")
    ui.print_error("Operation failed")
    ui.print_warning("Rate limit approaching")
    
    # Get user input
    choice = ui.print_prompt_enhanced()
    print(f"You selected: {choice}")

