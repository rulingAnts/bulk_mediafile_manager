#!/usr/bin/env python3.11
import tkinter as tk
from tkinter import filedialog, ttk
import os
import shutil
import pathlib
import subprocess
from pydub import AudioSegment
import time
import sys

# --- Configuration and Constants ---
# NOTE: The 'ffmpeg' executable must be installed and accessible in your system's PATH
# for the conversion features (both pydub and the subprocess video calls) to work.

class BulkFileProcessor(tk.Tk):
    """
    A Tkinter GUI application for selecting multiple files, choosing a target
    directory, applying bulk renaming, and optionally converting audio/video
    formats using pydub and ffmpeg (via subprocess).
    """
    def __init__(self):
        super().__init__()
        self.title("Bulk File Processor & Converter")
        self.geometry("800x650")
        
        # Apply a modern style
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        
        # State variables
        self.source_files = []
        self.target_dir = tk.StringVar()
        self.target_dir.set("No target directory selected")
        
        self.rename_prefix = tk.StringVar(value="")
        self.rename_suffix = tk.StringVar(value="")
        
        self.convert_enabled = tk.BooleanVar(value=False)
        self.target_extension = tk.StringVar(value="")
        self.conversion_params = tk.StringVar(value="-b:a 192k") # Default audio bitrate
        
        # New: Conflict Policy State
        self.conflict_policy = tk.StringVar(value="auto_rename") # 'skip', 'overwrite', 'auto_rename'

        self.create_widgets()

    def create_widgets(self):
        """Sets up the main application UI components."""
        
        # --- File Selection Frame ---
        file_frame = ttk.LabelFrame(self, text="1. Select Files and Target", padding="10")
        file_frame.pack(fill='x', padx=10, pady=5)

        # Source Files Button & Display
        ttk.Button(file_frame, text="Select Source Files (Shift/Ctrl Click Supported)", command=self.select_source_files).pack(fill='x', pady=5)
        
        self.file_list_label = ttk.Label(file_frame, text="0 files selected.", wraplength=750, justify=tk.LEFT)
        self.file_list_label.pack(fill='x', pady=5)
        
        # Target Directory Button & Display
        ttk.Button(file_frame, text="Select Target Directory", command=self.select_target_directory).pack(fill='x', pady=5)
        ttk.Label(file_frame, textvariable=self.target_dir, foreground="#0066CC").pack(fill='x', pady=5)
        
        # Conflict Policy Options
        ttk.Label(file_frame, text="Conflict Policy (If file exists in Target):", font=('Arial', 10, 'bold')).pack(fill='x', pady=(10, 2))
        policy_frame = ttk.Frame(file_frame)
        policy_frame.pack(fill='x', pady=5)
        ttk.Radiobutton(policy_frame, text="Auto-Rename (file (1).ext)", variable=self.conflict_policy, value="auto_rename").pack(side='left', padx=5)
        ttk.Radiobutton(policy_frame, text="Skip File", variable=self.conflict_policy, value="skip").pack(side='left', padx=5)
        ttk.Radiobutton(policy_frame, text="Overwrite Existing", variable=self.conflict_policy, value="overwrite").pack(side='left', padx=5)


        # --- Rename Options Frame ---
        rename_frame = ttk.LabelFrame(self, text="2. Rename Options", padding="10")
        rename_frame.pack(fill='x', padx=10, pady=5)

        # Prefix
        ttk.Label(rename_frame, text="Filename Prefix (e.g., '2a_'):").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(rename_frame, textvariable=self.rename_prefix).grid(row=0, column=1, sticky='ew', padx=5, pady=2)

        # Suffix
        ttk.Label(rename_frame, text="Filename Suffix (e.g., '-phon'):").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(rename_frame, textvariable=self.rename_suffix).grid(row=1, column=1, sticky='ew', padx=5, pady=2)
        rename_frame.grid_columnconfigure(1, weight=1)

        # --- Conversion Options Frame ---
        conversion_frame = ttk.LabelFrame(self, text="3. Conversion Options (Requires FFmpeg)", padding="10")
        conversion_frame.pack(fill='x', padx=10, pady=5)

        # Enable Checkbox
        ttk.Checkbutton(conversion_frame, text="Enable Audio/Video Conversion", variable=self.convert_enabled).grid(row=0, column=0, columnspan=2, sticky='w', padx=5, pady=5)

        # Target Extension
        ttk.Label(conversion_frame, text="Target Extension (e.g., '.mp4', '.m4a'):").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(conversion_frame, textvariable=self.target_extension).grid(row=1, column=1, sticky='ew', padx=5, pady=2)
        
        # Conversion Parameters
        ttk.Label(conversion_frame, text="FFmpeg Params (e.g., '-b:a 192k' or '-vcodec libx264'):").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(conversion_frame, textvariable=self.conversion_params).grid(row=2, column=1, sticky='ew', padx=5, pady=2)
        conversion_frame.grid_columnconfigure(1, weight=1)

        # --- Process Button ---
        ttk.Button(self, text="4. START PROCESS (Copy/Convert/Rename)", command=self.process_files, style='Accent.TButton').pack(fill='x', padx=10, pady=10)

        # Custom Style for the Process Button (using standard Tkinter methods for simplicity)
        self.style.configure('Accent.TButton', font=('Arial', 12, 'bold'), foreground='white', background='#28a745')
        self.style.map('Accent.TButton', background=[('active', '#218838')])


        # --- Logging Area ---
        log_frame = ttk.LabelFrame(self, text="Process Log", padding="10")
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.log_text = tk.Text(log_frame, height=10, state='disabled', wrap='word', bg='#f8f9fa', fg='#333333', font=('Courier', 10))
        self.log_text.pack(fill='both', expand=True)

    def log_message(self, message, is_error=False):
        """Adds a message to the log text area."""
        self.log_text.config(state='normal')
        tag = 'error' if is_error else 'info'
        
        if is_error:
             self.log_text.tag_config('error', foreground='red', font=('Courier', 10, 'bold'))
        else:
             self.log_text.tag_config('info', foreground='black')

        self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n", tag)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.update() # Force GUI update

    def select_source_files(self):
        """Opens a dialog to select multiple source files."""
        file_paths = filedialog.askopenfilenames(
            title="Select Source Files",
            filetypes=[
                ("All files", "*.*"),
                ("Audio files", "*.mp3 *.wav *.flac *.m4a *.aac"),
                ("Video files", "*.mp4 *.mov *.avi *.mkv")
            ]
        )
        if file_paths:
            self.source_files = [pathlib.Path(p) for p in file_paths]
            self.file_list_label.config(text=f"{len(self.source_files)} files selected.")
            self.log_message(f"Selected {len(self.source_files)} files.")

    def select_target_directory(self):
        """Opens a dialog to select the target destination directory."""
        dir_path = filedialog.askdirectory(title="Select Target Directory")
        if dir_path:
            self.target_dir.set(dir_path)
            self.log_message(f"Target directory set to: {dir_path}")

    def get_output_path(self, source_path):
        """Calculates the final destination path, applying renaming and conversion extension."""
        if not self.target_dir.get() or self.target_dir.get() == "No target directory selected":
            return None
        
        original_name = source_path.stem
        original_ext = source_path.suffix.lower()
        
        # 1. Apply renaming (prefix and suffix)
        new_name = self.rename_prefix.get() + original_name + self.rename_suffix.get()
        
        # 2. Determine final extension
        if self.convert_enabled.get() and self.target_extension.get():
            # Use the user-specified conversion extension
            target_ext = self.target_extension.get()
            if not target_ext.startswith('.'):
                target_ext = '.' + target_ext
        else:
            # Use the original extension
            target_ext = original_ext
            
        final_path = pathlib.Path(self.target_dir.get()) / (new_name + target_ext)
        return final_path

    def get_unique_output_path(self, target_path):
        """If target_path exists, finds a unique name by appending (1), (2), etc."""
        if not target_path.exists():
            return target_path
        
        base_stem = target_path.stem
        ext = target_path.suffix
        counter = 1
        new_path = target_path
        
        while new_path.exists():
            new_name = f"{base_stem} ({counter}){ext}"
            # Handle case where original stem might already have (N) pattern, though unlikely with original stem logic
            new_path = target_path.with_name(new_name) 
            counter += 1
            
        return new_path

    def run_ffmpeg_conversion(self, input_path, output_path, params):
        """
        Executes an FFmpeg subprocess command for video or general media conversion.
        This handles all video formats and any complex audio conversion.
        """
        # Base command structure: ffmpeg -i <input> <params> <output>
        # Note: If policy is 'overwrite', -y is essential to prevent blocking
        command = [
            'ffmpeg', 
            '-i', str(input_path), 
            *params.split(), # Split parameters string into a list
            str(output_path),
            '-y' # Overwrite output files without asking
        ]
        
        self.log_message(f"  -> FFmpeg Command: {' '.join(command)}")

        try:
            # Run the command, capturing output for logging
            process = subprocess.run(
                command, 
                check=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                encoding='utf-8'
            )
            self.log_message(f"  -> Conversion Success (FFmpeg). Output: {output_path.name}")
            return True
        except subprocess.CalledProcessError as e:
            self.log_message(f"  -> ERROR during FFmpeg conversion for {input_path.name}:", is_error=True)
            self.log_message(f"     Return Code: {e.returncode}. Stderr: {e.stderr.strip()}", is_error=True)
            return False
        except FileNotFoundError:
            self.log_message("  -> ERROR: 'ffmpeg' executable not found. Please ensure it is installed and in your PATH.", is_error=True)
            return False
        except Exception as e:
            self.log_message(f"  -> An unexpected error occurred during conversion: {e}", is_error=True)
            return False

    def process_files(self):
        """Main function to orchestrate the copy, rename, and conversion process."""
        self.log_message("--- Starting Bulk Processing ---", is_error=False)
        
        if not self.source_files:
            self.log_message("Error: No source files selected.", is_error=True)
            return
        
        if not self.target_dir.get() or self.target_dir.get() == "No target directory selected":
            self.log_message("Error: No target directory selected.", is_error=True)
            return

        total_files = len(self.source_files)
        success_count = 0
        
        for i, source_path in enumerate(self.source_files):
            self.log_message(f"Processing file {i+1}/{total_files}: {source_path.name}")
            
            # 1. Determine the initial desired output path (incorporating prefix/suffix/conversion ext)
            output_path = self.get_output_path(source_path)
            if output_path is None:
                 self.log_message("Skipping: Could not determine output path.", is_error=True)
                 continue
                 
            # 2. Check for conflict and apply policy
            if output_path.exists():
                policy = self.conflict_policy.get()
                
                if policy == "skip":
                    self.log_message(f"  -> Conflict: {output_path.name} exists. Skipping based on policy.", is_error=True)
                    continue
                
                elif policy == "auto_rename":
                    original_output_path = output_path
                    output_path = self.get_unique_output_path(output_path)
                    self.log_message(f"  -> Conflict: {original_output_path.name} exists. Auto-renaming to: {output_path.name}")
                
                elif policy == "overwrite":
                    self.log_message(f"  -> Conflict: {output_path.name} exists. Overwriting based on policy.")
                    # Continue execution, the file operation will handle the overwrite
            
            # 3. Final check to prevent input and output being the exact same file
            if source_path.resolve() == output_path.resolve():
                self.log_message(f"Skipping {source_path.name}: Input and output paths are identical.", is_error=True)
                continue

            # 4. Perform Copy/Conversion
            try:
                if self.convert_enabled.get() and self.target_extension.get():
                    # --- Conversion Required ---
                    
                    self.log_message(f"  -> Converting to {output_path.suffix} with parameters: '{self.conversion_params.get()}'")
                    
                    if self.run_ffmpeg_conversion(source_path, output_path, self.conversion_params.get()):
                        success_count += 1

                else:
                    # --- Simple Copy/Rename Required ---
                    self.log_message(f"  -> Copying (No conversion) to: {output_path.name}")
                    shutil.copy2(source_path, output_path)
                    self.log_message(f"  -> Copy Success. Output: {output_path.name}")
                    success_count += 1
                    
            except FileNotFoundError:
                self.log_message(f"Error: Source file not found: {source_path.name}", is_error=True)
            except PermissionError:
                self.log_message(f"Error: Permission denied for file: {output_path.name}", is_error=True)
            except Exception as e:
                self.log_message(f"An unknown error occurred processing {source_path.name}: {e}", is_error=True)
                
        self.log_message(f"--- Processing Complete: {success_count}/{total_files} files successfully handled ---", is_error=(success_count != total_files))


if __name__ == "__main__":
    app = BulkFileProcessor()
    app.mainloop()
