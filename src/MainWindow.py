import os
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from typing import Optional

# 导入之前定义的类（假设保存为 progress_tracker.py）
from Task import ProgressTracker, Milestone, Task

# ------------------------------
# 界面类
# ------------------------------
class MainWindow(tk.Tk):
    """主界面：显示所有里程碑"""
    def __init__(self, tracker: ProgressTracker):
        super().__init__()
        self.tracker = tracker
        self.title("学习进度跟踪")
        self.geometry("400x300")
        self._create_widgets()

    def _create_widgets(self):
        # 标题
        label = ttk.Label(self, text="里程碑列表", font=("Arial", 14))
        label.pack(pady=10)

        # 里程碑按钮
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        for milestone in self.tracker.milestones:
            row_frame = ttk.Frame(frame)
            row_frame.pack(fill=tk.X, pady=5)

            btn = ttk.Button(
                row_frame,
                text=f"{milestone.name}\n进度: {milestone.calculate_overall_progress():.1f}%",
                command=lambda ms_id=milestone.id: self._open_milestone(ms_id),
                width=30
            )
            btn.pack(side=tk.LEFT, padx=5)

            # 删除按钮
            btn_del = ttk.Button(
                row_frame,
                text="×",
                style="Danger.TButton",  # 需定义红色样式
                command=lambda ms_id=milestone.id: self._delete_milestone(ms_id)
            )
            btn_del.pack(side=tk.LEFT)
        
        # “添加里程碑”按钮
        btn_add = ttk.Button(self, text="+ 新建里程碑", command=self._open_add_milestone_dialog)
        btn_add.pack(side=tk.BOTTOM, pady=10)

    def _open_milestone(self, milestone_id: str):
        """打开里程碑详情窗口"""
        milestone = self.tracker.find_milestone(milestone_id)
        if milestone:
            self.withdraw()  # 隐藏主窗口
            MilestoneWindow(self, self.tracker, milestone)
        else:
            messagebox.showerror("错误", "未找到该里程碑")

    def _open_add_milestone_dialog(self):
        """新建里程碑对话框"""
        dialog = tk.Toplevel(self)
        dialog.title("新建里程碑")
        
        ttk.Label(dialog, text="名称:").grid(row=0, column=0, padx=5, pady=5)
        entry_name = ttk.Entry(dialog)
        entry_name.grid(row=0, column=1, padx=5, pady=5)
        
        def _save():
            name = entry_name.get()
            if name:
                self.tracker.milestones.append(Milestone(name))
                self.tracker.save_data()
                self._refresh_ui()
                dialog.destroy()
        
        ttk.Button(dialog, text="保存", command=_save).grid(row=1, columnspan=2)

    def _refresh_ui(self):
        """刷新主界面"""
        for widget in self.winfo_children():
            widget.destroy()
        self._create_widgets()

    def _delete_milestone(self, milestone_id: str):
        """删除里程碑确认逻辑"""
        if messagebox.askyesno("确认", "确定删除该里程碑及其所有任务吗？"):
            if self.tracker.remove_milestone(milestone_id):
                self.tracker.save_data()
                self._refresh_ui()  # 刷新界面
            else:
                messagebox.showerror("错误", "删除失败")

class MilestoneWindow(tk.Toplevel):
    """里程碑详情窗口"""
    def __init__(self, parent: tk.Tk, tracker: ProgressTracker, milestone: Milestone):
        super().__init__(parent)
        self.parent = parent
        self.tracker = tracker
        self.milestone = milestone
        self.title(f"里程碑详情 - {milestone.name}")
        self.geometry("600x400")
        self._create_widgets()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self):
        # 返回按钮
        btn_back = ttk.Button(self, text="返回主界面", command=self._on_close)
        btn_back.pack(anchor=tk.NW, padx=10, pady=10)

        # 任务树形列表
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.tree = ttk.Treeview(frame, columns=("name", "progress", "time"), show="headings")
        self.tree.heading("name", text="任务名称")
        self.tree.heading("progress", text="进度 (%)")
        self.tree.heading("time", text="时间 (小时)")
        self.tree.column("name", width=300)
        self.tree.column("progress", width=100)
        self.tree.column("time", width=100)
        
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        # 填充任务数据
        self._populate_tasks(self.milestone.tasks, parent="")

        # 单击展开/折叠
        self.tree.bind("<Button-1>", self._on_tree_click) 
        # 绑定双击事件
        self.tree.bind("<Double-1>", self._on_task_double_click)
        
        # 添加“添加任务”、“添加子任务”按钮
        btn_frame = ttk.Frame(self)
        btn_frame.pack(anchor=tk.NE, padx=10, pady=5)
        
        ttk.Button(btn_frame, text="+ 添加任务", command=self._open_add_task_dialog).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="+ 添加子任务", command=self._open_add_subtask_dialog).pack(side=tk.LEFT, padx=5)
        
        # 树形列表右键菜单
        self.tree.bind("<Button-3>", self._show_context_menu)

    def _populate_tasks(self, tasks: list[Task], parent: str, bSubTask: bool=False):
        """递归填充任务树"""
        for task in tasks:
            taskname = task.name
            if bSubTask is True:
                taskname = "  > "+taskname
            item = self.tree.insert(
                parent, "end", 
                text=task.id,
                values=(f"{taskname}", f"{task.progress}%", f"{task.time_spent}/{task.time_planned}"),
                open=False
            )
            if task.subtasks:
                self._populate_tasks(task.subtasks, parent=item, bSubTask=True)

    def _on_tree_click(self, event):
        """处理单击事件"""
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return

        # 仅当点击项有子项时切换展开状态
        if self.tree.get_children(row_id):
            is_open = self.tree.item(row_id, "open")
            self.tree.item(row_id, open=not is_open)
        
        # 选中当前项（无论是否有子项）
        self.tree.selection_set(row_id)

    def _on_task_double_click(self, event):
        """处理任务双击事件"""
        item = self.tree.selection()[0]
        task_id = self.tree.item(item, "text")
        task = self.tracker.find_task(task_id)
        if task:
            TaskWindow(self, self.tracker, task)
        else:
            messagebox.showerror("错误", "未找到该任务")

    def _on_close(self):
        """关闭时显示父窗口"""
        self.destroy()
        self.parent.deiconify()

    def _refresh_task_list(self):
        """刷新任务树形列表"""
        # 清空现有树节点
        for item in self.tree.get_children():
            self.tree.delete(item)
        # 重新填充数据
        self._populate_tasks(self.milestone.tasks, parent="")
    
    def _open_add_task_dialog(self):
        """新建任务对话框"""
        dialog = tk.Toplevel(self)
        dialog.title("新建任务")
        
        # 输入字段
        fields = [
            ("名称:", "entry_name"),
            ("计划时间（小时）:", "entry_time_planned")
        ]
        for i, (label, _) in enumerate(fields):
            ttk.Label(dialog, text=label).grid(row=i, column=0, padx=5, pady=5)
        
        entry_name = ttk.Entry(dialog)
        entry_time_planned = ttk.Entry(dialog)
        entry_name.grid(row=0, column=1, padx=5, pady=5)
        entry_time_planned.grid(row=1, column=1, padx=5, pady=5)
        
        def _save():
            name = entry_name.get()
            time_planned = float(entry_time_planned.get() or 0)
            if name:
                new_task = Task(name, time_planned=time_planned)
                self.milestone.add_task(new_task)
                self.tracker.save_data()
                self._refresh_task_list()
                dialog.destroy()
        
        ttk.Button(dialog, text="保存", command=_save).grid(row=2, columnspan=2)

    def _show_context_menu(self, event):
        """右键菜单删除选项"""
        item = self.tree.identify_row(event.y)
        if not item:
            return
        
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(
            label="删除任务", 
            command=lambda: self._delete_task(item)
        )
        menu.post(event.x_root, event.y_root)

    def _delete_task(self, tree_item: str):
        """删除任务逻辑"""
        task_id = self.tree.item(tree_item, "text")  # 假设text存储任务ID
        if messagebox.askyesno("确认", "确定删除该任务及其所有子任务吗？"):
            if self.tracker.remove_task(task_id):
                self.tracker.save_data()
                self._refresh_task_list()
            else:
                messagebox.showerror("错误", "删除失败")

    def _open_add_subtask_dialog(self):
        """添加子任务对话框"""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("提示", "请先选择父任务")
            return
        
        parent_task_id = self.tree.item(selected_item[0], "text")  # 假设text存储任务ID
        parent_task = self.tracker.find_task(parent_task_id)
        if not parent_task:
            messagebox.showerror("错误", "未找到父任务")
            return

        # 复用原有任务创建对话框，传入父任务
        self._open_add_task_dialog(parent_task=parent_task)

    def _open_add_task_dialog(self, parent_task: Optional[Task] = None):
        """改进后的任务创建对话框（支持子任务）"""
        dialog = tk.Toplevel(self)
        dialog.title("添加子任务" if parent_task else "添加任务")
        
        # 输入字段（名称、计划时间）
        ttk.Label(dialog, text="名称:").grid(row=0, column=0, padx=5, pady=5)
        entry_name = ttk.Entry(dialog)
        entry_name.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(dialog, text="计划时间（小时）:").grid(row=1, column=0, padx=5, pady=5)
        entry_time_planned = ttk.Entry(dialog)
        entry_time_planned.grid(row=1, column=1, padx=5, pady=5)

        def _save():
            name = entry_name.get()
            time_planned = float(entry_time_planned.get() or 0)
            if not name:
                return
                
            new_task = Task(name, time_planned=time_planned, parent=parent_task)
            if parent_task:
                parent_task.add_subtask(new_task)  # 添加为子任务
            else:
                self.milestone.add_task(new_task)  # 添加为顶层任务
            
            self.tracker._propagate_time_update(new_task)
            self.tracker.save_data()
            self._refresh_task_list()
            dialog.destroy()

        ttk.Button(dialog, text="保存", command=_save).grid(row=2, columnspan=2)

class TaskWindow(tk.Toplevel):
    """任务详情窗口"""
    def __init__(self, parent: tk.Toplevel, tracker: ProgressTracker, task: Task):
        super().__init__(parent)
        self.parent = parent
        self.tracker = tracker
        self.task = task
        self.title(f"任务详情 - {task.name}")
        self.geometry("500x400")
        self._create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _create_widgets(self):
        # 基础信息
        ttk.Label(self, text=f"任务名称: {self.task.name}").pack(anchor=tk.W, padx=10, pady=5)
        
        # 进度管理
        frame_progress = ttk.Frame(self)
        frame_progress.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(frame_progress, text="进度 (%):").grid(row=0, column=0)
        self.progress_var = tk.StringVar(value=str(int(self.task.calculate_progress())))
        self.entry_progress = ttk.Entry(frame_progress, textvariable=self.progress_var, width=5)
        
        # 有子任务时禁用输入
        if self.task.has_children:
            self.entry_progress.config(state="disabled")
            ttk.Label(frame_progress, text="(自动计算)").grid(row=0, column=2)
        else:
            self.entry_progress.config(validate="key", 
                validatecommand=(self.register(self._validate_progress), "%P"))
        
        self.entry_progress.grid(row=0, column=1)

        # 时间管理
        frame_time = ttk.Frame(self)
        frame_time.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(frame_time, text="已投入/计划时间:").grid(row=0, column=0)
        self.time_spent_var = tk.DoubleVar(value=self.task.time_spent)
        ttk.Entry(frame_time, textvariable=self.time_spent_var, width=8).grid(row=0, column=1)
        ttk.Label(frame_time, text="/").grid(row=0, column=2)
        self.time_planned_var = tk.DoubleVar(value=self.task.time_planned)
        ttk.Entry(frame_time, textvariable=self.time_planned_var, width=8).grid(row=0, column=3)

        # 下一步计划
        ttk.Label(self, text="下一步计划:").pack(anchor=tk.W, padx=10, pady=5)
        self.next_steps_text = tk.Text(self, height=5)
        self.next_steps_text.insert("1.0", self.task.next_steps)
        self.next_steps_text.pack(fill=tk.X, padx=10, pady=5)

        # 超链接
        self._create_links_section()

        # 保存按钮
        btn_save = ttk.Button(self, text="保存修改", command=self._save_changes)
        btn_save.pack(pady=10)

        # 新增状态选择下拉框
        frame_status = ttk.Frame(self)
        frame_status.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(frame_status, text="状态:").pack(side=tk.LEFT)
        self.status_var = tk.StringVar(value=self.task.status)
        status_combobox = ttk.Combobox(
            frame_status, 
            textvariable=self.status_var,
            values=["TODO", "DOING", "DONE"],
            state="readonly"
        )
        status_combobox.pack(side=tk.LEFT, padx=5)
        status_combobox.bind("<<ComboboxSelected>>", self._update_status)

        # 显示耗时（如果已完成）
        if self.task.status == "DONE" and self.task.time_spent > 0:
            ttk.Label(self, text=f"实际耗时: {self.task.time_spent:.1f} 小时").pack(anchor=tk.W, padx=10)
    
    def _validate_progress(self, value: str) -> bool:
        """验证进度输入（0-100整数）"""
        if value == "":
            return True
        try:
            num = int(value)
            return 0 <= num <= 100
        except ValueError:
            return False

    def _create_links_section(self):
        """创建超链接区域"""
        frame = ttk.LabelFrame(self, text="关联文件")
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        link_types = {
            "design_doc": "设计文档",
            "notes": "学习笔记",
            "deliverables": "交付件"
        }
        
        for link_key, link_text in link_types.items():
            row_frame = ttk.Frame(frame)
            row_frame.pack(anchor=tk.W, pady=2)
            
            ttk.Label(row_frame, text=f"{link_text}:").pack(side=tk.LEFT)
            path = self.task.links.get(link_key, "")
            label = ttk.Label(row_frame, text=path, foreground="blue", cursor="hand2")
            label.pack(side=tk.LEFT, padx=5)
            label.bind("<Button-1>", lambda e, p=path: self._open_link(p))

    def _open_link(self, path: str):
        """打开关联文件"""
        if path and os.path.exists(path):
            webbrowser.open(path)
        else:
            messagebox.showwarning("警告", f"文件不存在: {path}")

    def _update_progress(self, value: int):
        """实时更新进度显示"""
        self.progress_var.set(value)
        for widget in self.winfo_children():
            if isinstance(widget, ttk.Label) and widget["text"].startswith("进度:"):
                widget.config(text=f"进度: {value}%")

    def _save_changes(self):
        """保存时处理进度更新"""
        if not self.task.has_children:
            try:
                self.task.update_progress(int(self.progress_var.get()))
            except ValueError as e:
                messagebox.showerror("错误", str(e))
                return
        """保存修改到数据模型"""
        self.task.progress = self.progress_var.get()
        self.task.time_spent = self.time_spent_var.get()
        self.task.time_planned = self.time_planned_var.get()
        self.task.next_steps = self.next_steps_text.get("1.0", tk.END).strip()
        self.tracker.save_data()
        messagebox.showinfo("提示", "保存成功！")

        # 触发时间更新
        self.tracker._propagate_time_update(self.task)
        self.tracker.save_data()
        self.parent._refresh_task_list()  # 刷新父窗口

    def _update_status(self, event):
        """处理状态变更"""
        new_status = self.status_var.get()
        self.task.update_status(new_status)
        self.tracker.save_data()

# ------------------------------
# 启动程序
# ------------------------------
if __name__ == "__main__":

    # 初始化数据跟踪器
    tracker = ProgressTracker()
    
    # 如果无数据，创建示例数据
    if not tracker.milestones:
        ms1 = Milestone("基础库学习")
        task1 = Task("OpenCV基础", time_planned=15, progress=30)
        task1.links["design_doc"] = "/docs/opencv.md"
        task1.add_subtask(Task("图像读写", time_planned=5, progress=50))
        ms1.add_task(task1)
        tracker.milestones.append(ms1)
        tracker.save_data()
    
    # 启动主界面
    app = MainWindow(tracker)
    app.mainloop()