import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import datetime

class HealthDatabase:
    def __init__(self, db_path="health_data.db"):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    age INTEGER,
                    gender TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Records (
                    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    systolic INTEGER,
                    diastolic INTEGER,
                    pulse INTEGER,
                    weight REAL,
                    measure_time TEXT,
                    position TEXT,
                    FOREIGN KEY (user_id) REFERENCES Users (user_id)
                )
            """)
            conn.commit()

    def add_user(self, name, age, gender):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Users (name, age, gender) VALUES (?, ?, ?)", (name, age, gender))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

    def get_users(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, name FROM Users")
            return cursor.fetchall()

    def get_last_weight(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT weight FROM Records WHERE user_id = ? ORDER BY measure_time DESC LIMIT 1", (user_id,))
            result = cursor.fetchone()
            return result[0] if result else None

    def add_record(self, user_id, systolic, diastolic, pulse, weight, measure_time, position):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Records (user_id, systolic, diastolic, pulse, weight, measure_time, position)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, systolic, diastolic, pulse, weight, measure_time, position))
            conn.commit()

    def get_records(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT systolic, diastolic, pulse, weight, measure_time, position 
                FROM Records WHERE user_id = ? ORDER BY measure_time DESC
            """, (user_id,))
            return cursor.fetchall()

class HealthTrackerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("個人健康數據追蹤系統 v2.0")
        self.geometry("500x400")
        
        self.db = HealthDatabase()
        self.current_user = None # Stores (user_id, name)
        
        self.create_widgets()
        self.update_status()

    def create_widgets(self):
        # Status Bar
        self.status_label = tk.Label(self, text="[ 當前使用者: 未登入 ]", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, side=tk.TOP, ipady=5)

        # Main Buttons
        button_frame = tk.Frame(self)
        button_frame.pack(pady=20)

        btn_select_user = tk.Button(button_frame, text="選擇使用者", command=self.select_user)
        btn_select_user.pack(fill=tk.X, pady=5)

        btn_log_record = tk.Button(button_frame, text="登入紀錄", command=self.log_record)
        btn_log_record.pack(fill=tk.X, pady=5)

        btn_view_history = tk.Button(button_frame, text="查看歷史資料", command=self.view_history)
        btn_view_history.pack(fill=tk.X, pady=5)

        btn_exit = tk.Button(button_frame, text="結束程式", command=self.destroy)
        btn_exit.pack(fill=tk.X, pady=5)

    def update_status(self):
        user_display = self.current_user[1] if self.current_user else "未登入"
        self.status_label.config(text=f"[ 當前使用者: {user_display} ]")

    def select_user(self):
        # This will be a new window or a dialog
        SelectUserDialog(self, self.db, self.set_current_user)
    
    def set_current_user(self, user_id, name):
        self.current_user = (user_id, name)
        self.update_status()

    def log_record(self):
        if not self.current_user:
            messagebox.showwarning("錯誤", "請先選擇使用者！")
            return
        RecordDialog(self, self.db, self.current_user)

    def view_history(self):
        if not self.current_user:
            messagebox.showwarning("錯誤", "請先選擇使用者！")
            return
        HistoryDialog(self, self.db, self.current_user)

class SelectUserDialog(tk.Toplevel):
    def __init__(self, parent, db, set_user_callback):
        super().__init__(parent)
        self.title("選擇使用者")
        self.geometry("300x300")
        self.transient(parent)  # Set to be on top of the parent window
        self.grab_set()  # Modal window
        
        self.db = db
        self.set_user_callback = set_user_callback
        self.users = self.db.get_users()
        
        self.create_widgets()

    def create_widgets(self):
        # List existing users
        if not self.users:
            tk.Label(self, text="尚無使用者，請新增。").pack(pady=10)
        else:
            tk.Label(self, text="選擇現有使用者:").pack(pady=5)
            self.user_listbox = tk.Listbox(self, exportselection=0)
            for uid, name in self.users:
                self.user_listbox.insert(tk.END, name)
            self.user_listbox.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
            
            select_btn = tk.Button(self, text="選擇", command=self.on_select_user)
            select_btn.pack(pady=5)
        
        # Add new user
        tk.Button(self, text="新增使用者", command=self.add_new_user).pack(pady=10)
        tk.Button(self, text="取消", command=self.destroy).pack(pady=5)

    def on_select_user(self):
        try:
            selected_index = self.user_listbox.curselection()[0]
            user_id, user_name = self.users[selected_index]
            self.set_user_callback(user_id, user_name)
            messagebox.showinfo("成功", f"已切換至使用者: {user_name}")
            self.destroy()
        except IndexError:
            messagebox.showwarning("警告", "請選擇一個使用者。")

    def add_new_user(self):
        name = simpledialog.askstring("新增使用者", "請輸入姓名:", parent=self)
        if not name:
            return
        
        age_str = simpledialog.askstring("新增使用者", "請輸入年齡:", parent=self)
        try:
            age = int(age_str) if age_str else None
        except ValueError:
            messagebox.showerror("錯誤", "年齡請輸入數字。")
            return
        
        gender = simpledialog.askstring("新增使用者", "請輸入性別 (男/女/其他):")
        
        uid = self.db.add_user(name, age, gender)
        if uid:
            messagebox.showinfo("成功", f"成功新增使用者: {name}")
            self.set_user_callback(uid, name) # Automatically set new user as current
            self.destroy()
        else:
            messagebox.showerror("錯誤", "此姓名已存在。")
            # Refresh user list if we don't destroy
            self.users = self.db.get_users()
            self.create_widgets() # Re-create widgets to update list

class RecordDialog(tk.Toplevel):
    def __init__(self, parent, db, current_user):
        super().__init__(parent)
        self.title("登錄健康紀錄")
        self.geometry("400x450")
        self.transient(parent)
        self.grab_set()

        self.db = db
        self.current_user = current_user

        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text=f"為 {self.current_user[1]} 登錄紀錄", font=("Arial", 14)).pack(pady=10)

        form_frame = tk.Frame(self)
        form_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        labels = ["收縮壓 (mmHg):", "舒張壓 (mmHg):", "脈搏 (次/分):", "體重 (kg):", "測量時間:", "測量部位:"]
        self.entries = {}
        
        last_weight = self.db.get_last_weight(self.current_user[0])
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for i, label_text in enumerate(labels):
            tk.Label(form_frame, text=label_text).grid(row=i, column=0, sticky=tk.W, pady=5)
            entry = tk.Entry(form_frame)
            entry.grid(row=i, column=1, sticky=tk.EW, pady=5, padx=5)
            self.entries[label_text] = entry
            
            if label_text == "測量時間:":
                entry.insert(0, now)
            elif label_text == "體重 (kg):" and last_weight:
                entry.insert(0, str(last_weight))
        
        form_frame.grid_columnconfigure(1, weight=1)

        save_btn = tk.Button(self, text="儲存紀錄", command=self.save_record)
        save_btn.pack(pady=10)
        cancel_btn = tk.Button(self, text="取消", command=self.destroy)
        cancel_btn.pack(pady=5)

    def save_record(self):
        try:
            systolic = int(self.entries["收縮壓 (mmHg):"].get())
            diastolic = int(self.entries["舒張壓 (mmHg):"].get())
            pulse = int(self.entries["脈搏 (次/分):"].get())
            weight_str = self.entries["體重 (kg):"].get()
            weight = float(weight_str) if weight_str else None
            measure_time = self.entries["測量時間:"].get()
            position = self.entries["測量部位:"].get()

            if weight is None:
                messagebox.showwarning("警告", "首次登入請輸入體重。")
                return

            self.db.add_record(self.current_user[0], systolic, diastolic, pulse, weight, measure_time, position)
            messagebox.showinfo("成功", "紀錄儲存成功！")
            self.destroy()
        except ValueError:
            messagebox.showerror("錯誤", "輸入錯誤，請確保數值為數字。")
        except Exception as e:
            messagebox.showerror("錯誤", f"儲存失敗: {e}")

class HistoryDialog(tk.Toplevel):
    def __init__(self, parent, db, current_user):
        super().__init__(parent)
        self.title(f"{current_user[1]} 的歷史紀錄")
        self.geometry("700x400")
        self.transient(parent)
        self.grab_set()

        self.db = db
        self.current_user = current_user

        self.create_widgets()
        self.load_records()

    def create_widgets(self):
        columns = ("時間", "收縮壓", "舒張壓", "脈搏", "體重", "部位")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=tk.CENTER)
            
        self.tree.column("時間", width=150)
        self.tree.column("收縮壓", width=70)
        self.tree.column("舒張壓", width=70)
        self.tree.column("脈搏", width=50)
        self.tree.column("體重", width=60)
        self.tree.column("部位", width=100)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        tk.Button(self, text="關閉", command=self.destroy).pack(pady=10)

    def load_records(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        records = self.db.get_records(self.current_user[0])
        if records:
            for sys_p, dia_p, pulse, weight, m_time, pos in records:
                self.tree.insert("", tk.END, values=(m_time, sys_p, dia_p, pulse, weight, pos))
        else:
            self.tree.insert("", tk.END, values=("尚無紀錄", "", "", "", "", ""))

if __name__ == "__main__":
    app = HealthTrackerGUI()
    app.mainloop()
