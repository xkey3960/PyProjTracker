## 描述
呃，我需要一个简单的跟踪程序来跟踪学习进度以及投入情况。
主界面就是4个里程碑的投入情况和进展。点击每个里程碑，进入详细情况，列出详细的任务，每个任务的投入和完成情况。
点击任务，进入任务的详细页，包括当前进展和下一步计划，还有一些超链接，指向这个任务所需要的文件（任务的目录、设计文档、学习笔记、输出的交付件等等）。
嗯，保存的文件格式，采用json格式。
采用面向对象的设计方法。先抽象为几个层次，再抽象每个层次的类，并设计类的功能、接口。最后根据设计输出代码。
如果输出太长，可以先输出设计文档。我之后，按照每个类的设计文档输入，你再输出详细代码。
另外，尽量使用python内置的lib，减少第三方依赖。

## AI回答
---

### **系统设计文档**

---

#### **1. 系统架构**
采用**三层结构**：
1. **数据层**：使用JSON存储里程碑、任务及关联文件路径。
2. **逻辑层**：面向对象封装里程碑、任务、进度跟踪逻辑。
3. **界面层**：基于`tkinter`的简单GUI，支持点击交互。

---

#### **2. 类设计**
##### **2.1 数据模型类**
###### **`Task` 类**
- **功能**：描述单个任务的详细信息。
- **属性**：
  - `id`：任务唯一标识（UUID）
  - `name`：任务名称
  - `time_planned`：计划投入时间（小时）
  - `time_spent`：已投入时间（小时）
  - `subtasks`：子任务列表（嵌套`Task`对象）
  - `links`：关联文件字典（设计文档、笔记、交付件路径）
  - `progress`：进度百分比（0~100）
  - `next_steps`：下一步计划描述
- **方法**：
  - `add_subtask(subtask: Task)`
  - `update_progress(new_progress: int)`
  - `to_dict()`：转换为JSON可序列化字典

###### **`Milestone` 类**
- **功能**：管理一个里程碑及其关联任务。
- **属性**：
  - `id`：里程碑唯一标识（UUID）
  - `name`：里程碑名称
  - `tasks`：任务列表（`Task`对象）
- **方法**：
  - `add_task(task: Task)`
  - `calculate_total_time()`：计算总投入时间
  - `calculate_overall_progress()`：计算里程碑整体进度
  - `to_dict()`：转换为JSON可序列化字典

---

##### **2.2 持久化类**
###### **`ProgressTracker` 类**
- **功能**：负责数据加载、保存与全局状态管理。
- **属性**：
  - `milestones`：所有里程碑对象列表
  - `data_file`：JSON存储路径（默认`progress.json`）
- **方法**：
  - `load_data()`
  - `save_data()`
  - `find_milestone(milestone_id: str) -> Milestone`
  - `find_task(task_id: str) -> Task`

---

##### **2.3 界面类**
###### **`MainWindow` 类**
- **功能**：主界面显示所有里程碑。
- **属性**：
  - `tracker`：绑定的`ProgressTracker`实例
- **方法**：
  - `_create_milestone_buttons()`：生成里程碑按钮
  - `_on_milestone_click(milestone_id: str)`：处理点击事件

###### **`MilestoneWindow` 类**
- **功能**：展示单个里程碑的详细任务。
- **方法**：
  - `_create_task_list()`：生成任务树形视图

###### **`TaskWindow` 类**
- **功能**：展示任务详细信息。
- **方法**：
  - `_open_link(link_type: str)`：通过`webbrowser`打开关联文件

---

#### **3. JSON数据结构示例**
```json
{
  "milestones": [
    {
      "id": "milestone_1",
      "name": "基础库学习",
      "tasks": [
        {
          "id": "task_1",
          "name": "OpenCV基础",
          "time_planned": 15,
          "time_spent": 5,
          "progress": 30,
          "links": {
            "design_doc": "/docs/opencv.md",
            "notes": "/notes/week1.txt"
          },
          "subtasks": []
        }
      ]
    }
  ]
}
```

---

#### **4. 关键交互逻辑**
1. **主界面**：
   ```python
   # 伪代码示例
   class MainWindow(tk.Tk):
       def __init__(self, tracker):
           super().__init__()
           self.tracker = tracker
           self._create_milestone_buttons()

       def _create_milestone_buttons(self):
           for ms in self.tracker.milestones:
               btn = tk.Button(self, text=ms.name, 
                               command=lambda id=ms.id: self._on_milestone_click(id))
               btn.pack()
   ```

2. **数据持久化**：
   ```python
   class ProgressTracker:
       def save_data(self):
           data = {"milestones": [ms.to_dict() for ms in self.milestones]}
           with open(self.data_file, "w") as f:
               json.dump(data, f, indent=2)
   ```

---

#### **5. 代码输出策略**
1. 先提供`Task`/`Milestone`/`ProgressTracker`的核心实现。
2. 再分步输出`MainWindow`/`MilestoneWindow`/`TaskWindow`的GUI代码。
3. 最后整合为完整可运行程序。

---

是否先输出 `Task`/`Milestone`/`ProgressTracker` 类的详细代码？