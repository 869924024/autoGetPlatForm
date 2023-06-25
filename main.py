import os
import re
import tkinter as tk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
import pyperclip
import time
import threading
from pynput import keyboard
import requests


class CodeReceiver:
    def __init__(self):
        self.phone_requests = []
        self.current_index = -1
        self.code_queue = ""

    def add_phone_request(self, phone_number_trimmed, phone_number, request_url):
        self.phone_requests.append((phone_number_trimmed, phone_number, request_url))

    def get_current_phone_number(self):
        if self.current_index >= 0 and self.current_index < len(self.phone_requests):
            return self.phone_requests[self.current_index][0]
        else:
            return None

    def get_current_phone_url(self):
        if self.current_index >= 0 and self.current_index < len(self.phone_requests):
            return self.phone_requests[self.current_index][2]
        else:
            return None

    def get_current_code(self):
        if self.current_index >= 0 and self.current_index < len(self.phone_requests):
            return self.code_queue
        else:
            return None

    def get_next_phone_number(self):
        if self.current_index < len(self.phone_requests) - 1:
            self.current_index += 1
            return self.phone_requests[self.current_index][0]
        else:
            return None

    def extract_code(self, response_content):
        pattern = r"验证码(\d+)"  # 匹配"验证码"后面的数字
        match = re.search(pattern, response_content)
        if match:
            return match.group(1)
        else:
            return None

    def request_code(self, phone_number, request_url):
        # 发送请求到接码平台，获取短信内容
        try:
            response = requests.get(request_url)
            code = self.extract_code(response.text)
            if code:
                self.code_queue = code
            else:
                print(f"No code received for {phone_number} , request_uerl: {request_url}")
        except requests.RequestException as e:
            print(f"Request failed for {phone_number}. Error: {str(e)}")


class AppGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("批量请求")
        self.root.geometry("900x500")

        self.phone_requests = []

        self.list_box = tk.Listbox(self.root)
        self.list_box.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.add_button = tk.Button(self.root, text="添加新的号码和地址", command=self.add_phone_request)
        self.add_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.import_button = tk.Button(self.root, text="导入txt", command=self.import_numbers)
        self.import_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.clear_button = tk.Button(self.root, text="重置", command=self.clear_phone_requests)
        self.clear_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.start_button = tk.Button(self.root, text="开始", command=self.start_processing)
        self.start_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.stop_button = tk.Button(self.root, text="结束", command=self.stop_processing)
        self.stop_button.pack(side=tk.LEFT, padx=10, pady=10)
        self.stop_button.config(state=tk.DISABLED)
        self.current_phone_label = tk.Label(self.root, text="当前手机号:")
        self.current_phone_label.pack(side=tk.TOP, fill=tk.BOTH, padx=10, pady=10)

        self.current_phone_var = tk.StringVar()
        self.current_phone_var.set("")
        self.current_phone_entry = tk.Entry(self.root, textvariable=self.current_phone_var, state="readonly")
        self.current_phone_entry.pack(side=tk.TOP, padx=10, pady=10)

        self.current_code_label = tk.Label(self.root, text="当前验证码:")
        self.current_code_label.pack(side=tk.TOP, padx=10, pady=10)

        self.current_code_var = tk.StringVar()
        self.current_code_var.set("")
        self.current_code_entry = tk.Entry(self.root, textvariable=self.current_code_var, state="readonly")
        self.current_code_entry.pack(side=tk.TOP, padx=10, pady=10)

        self.is_processing = False
        self.is_waiting = False
        self.is_copying = False

        # 创建全局事件监听器
        self.listener = keyboard.GlobalHotKeys({
            '<ctrl>+1': self.copy_current_phone,
            '<ctrl>+2': self.copy_current_code,
            '<ctrl>+3': self.process_next_phone
        })

    def run(self):
        # 启动全局事件监听器
        self.listener.start()
        self.root.mainloop()

    def stop(self):
        # 停止全局事件监听器
        self.listener.stop()

    def add_phone_request(self):
        phone_number_trimmed = tk.simpledialog.askstring("添加手机号", "输入手机号:")
        if phone_number_trimmed:
            request_url = tk.simpledialog.askstring("添加地址", "输入地址:")
            if request_url:
                phone_number_trimmed = phone_number_trimmed.strip()  # 去除号码两端的空白字符
                if "-" in phone_number_trimmed:
                    _, phone_number = phone_number_trimmed.split("-")
                code_receiver.add_phone_request(phone_number_trimmed, phone_number, request_url)
                self.update_list_box()

    def update_list_box(self):
        self.current_phone_var.set("")
        self.current_code_var.set("")
        self.list_box.delete(0, tk.END)
        for i, (phone_number, phone_number_trimmed, request_url) in enumerate(code_receiver.phone_requests):
            item = f"{i + 1}. 手机号: {phone_number}, 地址: {request_url}"
            self.list_box.insert(tk.END, item)
            if i == code_receiver.current_index:
                self.list_box.itemconfig(i, fg="red")  # 将当前号码标识为红色
                #选中当前号码
                self.list_box.select_set(i)
                #移动到当前号码
                self.list_box.see(i)

    def import_numbers(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if file_path:
            with open(file_path, "r") as file:
                lines = file.readlines()

            code_receiver.phone_requests.clear()
            for line in lines:
                line = line.strip()
                if line:
                    phone_number_trimmed, request_url = line.split("\t")
                    if "-" in phone_number_trimmed:
                        _, phone_number = phone_number_trimmed.split("-")
                    code_receiver.add_phone_request(phone_number_trimmed,phone_number, request_url)
            self.update_list_box()  # 更新列表框显示
            self.current_phone_var.set(code_receiver.phone_requests[0][0])
            pyperclip.copy(code_receiver.phone_requests[0][0])

    def clear_phone_requests(self):
        code_receiver.phone_requests.clear()
        code_receiver.current_index = -1
        code_receiver.code_queue = ""
        self.is_processing = False
        self.is_waiting = False
        self.current_phone_var.set("")
        self.current_code_var.set("")
        self.update_list_box()

    def start_processing(self):
        if not self.is_processing:
            self.is_processing = True
            self.is_copying = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.process_next_phone()
            threading.Thread(target=self.wait_for_code).start()
            # self.update_list_box()  # 更新列表框显示

    def stop_processing(self):
        if self.is_processing:
            self.is_processing = False
            self.is_waiting = False
            self.is_copying = False
            self.stop_button.config(state=tk.DISABLED)
            self.start_button.config(state=tk.NORMAL)

    def process_next_phone(self):
        if self.is_processing:
            phone_number = code_receiver.get_next_phone_number()
            if phone_number:
                self.copy_current_phone()
                self.update_list_box()  # 更新列表框显示
                self.current_phone_var.set(phone_number)
                self.current_code_var.set("")
                code_receiver.code_queue = ""
                self.is_waiting = True
                self.is_copying = False
            else:
                self.is_processing = False
                self.is_copying = False
        else:
            self.stop_processing()

    def wait_for_code(self):
        while self.is_waiting:
            self.is_copying = True
            code_receiver.request_code(self.current_phone_var.get(), code_receiver.get_current_phone_url())
            time.sleep(0.5)
            self.check_for_code()

    def check_for_code(self):
        code = code_receiver.get_current_code()
        if code and self.is_copying:
            self.current_code_var.set(code)
            # self.is_waiting = False
            self.copy_current_code()

    def copy_current_phone(self):
        phone_number = code_receiver.get_current_phone_number()
        if phone_number:
            pyperclip.copy(phone_number)

    def copy_current_code(self):
        code = code_receiver.get_current_code()
        if code:
            pyperclip.copy(code)


if __name__ == "__main__":
    code_receiver = CodeReceiver()
    app = AppGUI()
    try:
        app.run()
    finally:
        app.stop()
