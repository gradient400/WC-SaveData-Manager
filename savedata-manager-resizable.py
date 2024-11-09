import os
import shutil
from datetime import datetime
import glob
from pathlib import Path
import re
import time
import sys
import threading
import signal

# ANSI escape codes for colors and formatting
GREEN = '\033[32m'
BRIGHT_GREEN = '\033[92m'
BLACK = '\033[30m'
RESET = '\033[0m'
BOLD = '\033[1m'
CLEAR_SCREEN = '\033[2J\033[H'
CURSOR_UP = '\033[F'
CLEAR_LINE = '\033[K'

class ProgressDisplay:
    def __init__(self, total_steps=50, interval=0.05):
        self.total_steps = total_steps
        self.interval = interval
        self.current_step = 0
        self.message = ""
        self.active = False
        self.last_width = os.get_terminal_size().columns

    def _check_resize(self):
        """Check if terminal has been resized"""
        current_width = os.get_terminal_size().columns
        if current_width != self.last_width:
            self.last_width = current_width
            return True
        return False

    def start(self, ui, message=""):
        """Start the progress display"""
        self.current_step = 0
        self.message = message
        self.active = True
        print(f"{GREEN}> {message}{RESET}")
        self._draw_initial_bar()
    
    def _draw_initial_bar(self):
        """Draw initial progress bar"""
        fixed_chars = 21
        width = os.get_terminal_size().columns - fixed_chars
        print(f"{GREEN}> 0.0% [>{'-' * width}] 0.0 PB/s{RESET}")
    
    def update(self, ui, message=""):
        """Update progress display"""
        self.current_step += 1
        self.message = message
        # Check for resize before drawing
        if self._check_resize():
            # Clear extra characters that might remain from previous wider terminal
            print(CLEAR_LINE, end='\r')
        self._draw_progress(ui)
        time.sleep(self.interval)
    
    def _draw_progress(self, ui):
        """Draw the progress bar"""
        progress = (self.current_step / self.total_steps) * 100
        speed = f"{(self.current_step / self.total_steps) * 9.2:.1f} PB/s"
        self._draw_bar(progress, self.message, speed)
    
    def _draw_bar(self, progress, message, speed):
        """Draw the actual progress bar"""
        # Move cursor up two lines and clear previous progress display
        print(f"\033[2A\r{CLEAR_LINE}", end='')
        print(CLEAR_LINE, end='')
        
        # Calculate width for current terminal size
        fixed_chars = 21
        width = os.get_terminal_size().columns - fixed_chars
        filled = int(width * progress / 100)
        bar = f"{GREEN}>{BRIGHT_GREEN}{'=' * filled}{GREEN}{'-' * (width - filled)}{RESET}"
        percentage = f"{progress:5.1f}%"
        
        # Print the new progress state
        print(f"{GREEN}> {message}{RESET}")
        print(f"{GREEN}> {percentage} [{bar}] {speed}{RESET}", end='\r', flush=True)
    
    def is_complete(self):
        """Check if progress is complete"""
        return self.current_step >= self.total_steps

class TerminalUI:
    def __init__(self):
        self.current_header = ""
        self.last_width = os.get_terminal_size().columns

    def _check_resize(self):
        """Check if terminal has been resized"""
        current_width = os.get_terminal_size().columns
        if current_width != self.last_width:
            self.last_width = current_width
            return True
        return False

    @staticmethod
    def clear_screen():
        """Clear the terminal screen"""
        print(CLEAR_SCREEN, end='')

    def draw_header(self, text):
        """Draw a decorated header with animated bars"""
        self.current_header = text
        self._draw_header_internal()

    def _draw_header_internal(self):
        """Internal method to draw the header"""
        if self._check_resize():
            # Clear any remnants from previous size
            print(CLEAR_LINE, end='\r')
        
        width = os.get_terminal_size().columns
        print(GREEN + "=" * width + RESET)
        
        # Center the text
        padding = (width - len(self.current_header)) // 2
        print(GREEN + " " * padding + BRIGHT_GREEN + self.current_header + RESET)
        print(GREEN + "=" * width + RESET)

    @staticmethod
    def draw_progress_bar(progress, message="", speed=""):
        """Draw a progress bar with message"""
        # Move cursor up two lines and clear previous progress display
        print(f"\033[2A\r{CLEAR_LINE}", end='')
        print(CLEAR_LINE, end='')
        
        width = os.get_terminal_size().columns - 20  # Leave space for percentage
        filled = int(width * progress / 100)
        bar = f"{GREEN}>{BRIGHT_GREEN}{'=' * filled}{GREEN}{'-' * (width - filled)}{RESET}"
        percentage = f"{progress:5.1f}%"
        
        # Print the new progress state without extra newlines
        print(f"{GREEN}> {message}{RESET}")
        print(f"{GREEN}> {percentage} [{bar}] {speed}{RESET}", end='\r', flush=True)


    @staticmethod
    def print_menu():
        """Print the main menu"""
        print(f"\n{GREEN}Game Savedata Manager")
        print(f"{BRIGHT_GREEN}1. Replace savedata with checkpoint")
        print("2. Backup current savedata")
        print("3. Recover savedata from backup")
        print(f"4. Exit{RESET}")

class SaveDataManager:
    def __init__(self, progress_steps=50, progress_interval=0.05):
        self.user_profile = os.path.expandvars('%UserProfile%')
        self.game_save_dir = os.path.join(
            self.user_profile,
            'AppData',
            'LocalLow',
            'GameCreatorNeko',
            'WomanCommunication'
        )
        self.checkpoints_dir = os.path.join(os.path.dirname(__file__), 'checkpoints')
        self.ui = TerminalUI()
        self.progress = ProgressDisplay(progress_steps, progress_interval)

    def copy_with_progress(self, src_dir, dst_dir):
        """Copy directory contents with visual progress display"""
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)

        # Start progress display
        self.progress.start(self.ui, "正在初始化世界...")

        # Start a thread to copy files
        def copy_files():
            shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
        
        copy_thread = threading.Thread(target=copy_files)
        copy_thread.start()

        # Update progress bar until copy is complete
        while copy_thread.is_alive() and not self.progress.is_complete():
            self.progress.update(self.ui, "正在初始化世界...")
        
        # Wait for copy to complete
        copy_thread.join()
        
        # Ensure progress bar reaches 100%
        while not self.progress.is_complete():
            self.progress.update(self.ui, "正在初始化世界...")
        
        # Print final newline
        print()

    def replace_savedata(self, checkpoint_name):
        checkpoint_path = os.path.join(self.checkpoints_dir, checkpoint_name)
        
        if not os.path.exists(checkpoint_path):
            print(f"{GREEN}Checkpoint '{checkpoint_name}' not found!{RESET}")
            return False
        
        try:
            # Silently backup existing data
            self.backup_savedata(silent=True)
            
            if not os.path.exists(self.game_save_dir):
                os.makedirs(self.game_save_dir)
            
            self.copy_with_progress(checkpoint_path, self.game_save_dir)
            print(f"{GREEN}Successfully replaced savedata with checkpoint: {checkpoint_name}{RESET}")
            return True
        except Exception as e:
            print(f"{GREEN}Error replacing savedata: {str(e)}{RESET}")
            return False

    def backup_savedata(self, silent=False):
        """Backup current savedata. If silent=True, don't show any messages."""
        if not os.path.exists(self.game_save_dir):
            if not silent:
                print(f"{GREEN}No savedata found to backup!{RESET}")
            return False
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            backup_dir = f"{self.game_save_dir}-{timestamp}"
            
            if silent:
                # Just copy without progress display
                shutil.copytree(self.game_save_dir, backup_dir)
            else:
                self.copy_with_progress(self.game_save_dir, backup_dir)
                print(f"{GREEN}Successfully backed up savedata to: {backup_dir}{RESET}")
            return True
        except Exception as e:
            if not silent:
                print(f"{GREEN}Error backing up savedata: {str(e)}{RESET}")
            return False

    def list_checkpoints(self):
        checkpoints = []
        if os.path.exists(self.checkpoints_dir):
            checkpoints = [d for d in os.listdir(self.checkpoints_dir) 
                         if os.path.isdir(os.path.join(self.checkpoints_dir, d))]
            checkpoints.sort()
        return checkpoints

    def list_backups(self):
        backup_pattern = os.path.join(
            self.user_profile,
            'AppData',
            'LocalLow',
            'GameCreatorNeko',
            'WomanCommunication-*'
        )
        backups = glob.glob(backup_pattern)
        return sorted([(os.path.basename(b), b) for b in backups], reverse=True)

    def recover_savedata(self, backup_path):
        if not os.path.exists(backup_path):
            print(f"{GREEN}Backup directory not found: {backup_path}{RESET}")
            return False
        
        try:
            # Silently backup existing data
            self.backup_savedata(silent=True)
            
            if not os.path.exists(self.game_save_dir):
                os.makedirs(self.game_save_dir)
            
            self.copy_with_progress(backup_path, self.game_save_dir)
            print(f"{GREEN}Successfully recovered savedata from: {backup_path}{RESET}")
            return True
        except Exception as e:
            print(f"{GREEN}Error recovering savedata: {str(e)}{RESET}")
            return False

def main():
    # Enable ANSI escape sequences on Windows
    if os.name == 'nt':
        os.system('color')
    
    manager = SaveDataManager()
    
    while True:
        manager.ui.clear_screen()
        manager.ui.draw_header("世界初始化程序")
        manager.ui.print_menu()
        
        choice = input(f"\n{GREEN}Enter your choice (1-4): {RESET}")
        
        manager.ui.clear_screen()
        manager.ui.draw_header("世界初始化程序")

        if choice == "1":
            checkpoints = manager.list_checkpoints()
            if not checkpoints:
                print(f"{GREEN}No checkpoints found! Please ensure checkpoints are in the './checkpoints' directory.{RESET}")
                continue
            
            print(f"\n{GREEN}Available checkpoints:")
            for i, checkpoint in enumerate(checkpoints):
                print(f"{BRIGHT_GREEN}{i+1}. {checkpoint}{RESET}")
            
            try:
                idx = int(input(f"\n{GREEN}Select checkpoint number: {RESET}")) - 1
                if 0 <= idx < len(checkpoints):
                    manager.ui.clear_screen()
                    manager.ui.draw_header("世界初始化程序")
                    manager.replace_savedata(checkpoints[idx])
                else:
                    print(f"{GREEN}Invalid selection!{RESET}")
            except ValueError:
                print(f"{GREEN}Invalid input! Please enter a number.{RESET}")
        
        elif choice == "2":
            manager.backup_savedata()
        
        elif choice == "3":
            backups = manager.list_backups()
            if not backups:
                print(f"{GREEN}No backups found!{RESET}")
                continue
            
            print(f"\n{GREEN}Available backups:")
            for i, (backup_name, _) in enumerate(backups):
                print(f"{BRIGHT_GREEN}{i+1}. {backup_name}{RESET}")
            
            try:
                idx = int(input(f"\n{GREEN}Select backup number: {RESET}")) - 1
                if 0 <= idx < len(backups):
                    manager.ui.clear_screen()
                    manager.ui.draw_header("世界初始化程序")
                    manager.recover_savedata(backups[idx][1])
                else:
                    print(f"{GREEN}Invalid selection!{RESET}")
            except ValueError:
                print(f"{GREEN}Invalid input! Please enter a number.{RESET}")
        
        elif choice == "4":
            print(f"{GREEN}Thank you for using Game Savedata Manager!{RESET}")
            break
        
        else:
            print(f"{GREEN}Invalid choice! Please enter a number between 1 and 4.{RESET}")
        
        input(f"\n{GREEN}Press Enter to continue...{RESET}")

if __name__ == "__main__":
    # Enable ANSI escape sequences and proper signal handling on Windows
    if os.name == 'nt':
        os.system('color')
        # Windows needs special handling for SIGWINCH
        try:
            import win32api
            win32api.SetConsoleCtrlHandler(None, True)
        except ImportError:
            print("Warning: win32api not found. Resize handling may not work on Windows.")
    main()