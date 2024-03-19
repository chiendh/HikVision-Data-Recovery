"""
HIKVISION Video Data Recovery
Author: Dane Wullen
Date: 2020
Updated: 2024
Version: 0.2
NO WARRANTY, SOFTWARE IS PROVIDED 'AS IS'

© 2020 Dane Wullen
"""

import os
import shutil
import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from src.hikparser import HikParser
import subprocess


def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_disk_space(required_space, output_dir):
    total, used, free = shutil.disk_usage(output_dir)
    required_space_gb = int(required_space) / pow(1024, 3)
    free_gb = int(free) / pow(1024, 3)

    if required_space_gb >= free_gb:
        logging.error("Insufficient hard disk space! Required: %d GB, Available: %d GB", required_space_gb, free_gb)
        return False
    return True

def create_output_directory(directory):
    if not os.path.isdir(directory):
        os.makedirs(directory)
        logging.info("Output directory created at %s", directory)

def list_physical_drives():
    try:
        # Thực hiện lệnh wmic để lấy thông tin về các ổ đĩa vật lý
        result = subprocess.check_output(['wmic', 'diskdrive', 'get', 'model,name,size'], text=True)
        
        # Tách kết quả thành các dòng và loại bỏ dòng đầu tiên (tiêu đề)
        lines = result.strip().split('\n')[1:]
        
        # Xử lý mỗi dòng để tạo một chuỗi mô tả cho mỗi ổ đĩa
        drives = []
        for line in lines:
            if line.strip():  # Bỏ qua các dòng trống
                drives.append(line.strip())
        return drives
    except subprocess.CalledProcessError as e:
        logging.error("Failed to list physical drives: %s", e)
        return []

def process_files(input_file, output_dir, mode):
    try:
        parser = HikParser(input_file)
        parser.read_master_sector()
        parser.read_hikbtree()
        parser.read_page_list()
        parser.read_page_entries()
        parser.print_hikpagelist(output_dir)
        parser.print_hikpages(output_dir)
        parser.print_master_sector(output_dir)
        parser.print_hikbtree(output_dir)

        if mode == "e":
            required_space = parser.get_total_blocks() * parser.master_sector.data_block_size
            if check_disk_space(required_space, output_dir):
                create_output_directory(output_dir)
                parser.extract_block(output_dir)

    except Exception as e:
        logging.error("Error processing files: %s", e)
        messagebox.showerror("Error", f"Error processing files: {e}")

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        setup_logging()

        self.title("HIKVISION Video Data Recovery")
        self.geometry("500x250")

        self.label_drive = ttk.Label(self, text="Select a Physical Drive:")
        self.label_drive.pack(pady=10)

        self.combobox = ttk.Combobox(self, values=list_physical_drives())
        self.combobox.pack()

        self.label_output_dir = ttk.Label(self, text="Select Output Directory:")
        self.label_output_dir.pack(pady=10)

        self.output_dir_var = tk.StringVar()
        self.entry_output_dir = ttk.Entry(self, textvariable=self.output_dir_var, state="readonly", width=50)
        self.entry_output_dir.pack(pady=5)

        self.select_output_dir_button = ttk.Button(self, text="Browse...", command=self.select_output_directory)
        self.select_output_dir_button.pack(pady=5)

        self.process_button = ttk.Button(self, text="Process", command=self.process_selected_drive)
        self.process_button.pack(pady=20)

    def select_output_directory(self):
        directory = filedialog.askdirectory()
        if directory:  # Khi một thư mục được chọn
            self.output_dir_var.set(directory)

    def process_selected_drive(self):
        selected_drive = self.combobox.get()
        output_dir = self.output_dir_var.get()
        
        if not selected_drive:
            messagebox.showwarning("Warning", "Please select a drive.")
            return
        
        if not output_dir:
            messagebox.showwarning("Warning", "Please select an output directory.")
            return

        # Log the selected drive and output directory for now
        logging.info(f"Selected drive: {selected_drive}")
        logging.info(f"Output directory: {output_dir}")
        
        # Cần thêm logic thực tế để xử lý ổ đĩa vật lý tại đây, ví dụ:
        process_files(selected_drive, output_dir, "e")
        messagebox.showinfo("Info", "Processing started. This may take some time.")

if __name__ == "__main__":
    app = Application()
    app.mainloop()