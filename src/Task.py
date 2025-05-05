import json
import uuid
import os
from typing import Dict, List, Optional

# ------------------------------
# 数据模型类
# ------------------------------
class Task:
    def __init__(
        self,
        name: str,
        time_planned: float = 0,
        time_spent: float = 0,
        progress: int = 0,
        next_steps: str = "",
        links: Optional[Dict[str, str]] = None,
        subtasks: Optional[List["Task"]] = None
    ):
        self.id = str(uuid.uuid4())  # 唯一标识
        self.name = name
        self.time_planned = time_planned
        self.time_spent = time_spent
        self.progress = progress  # 0-100 百分比
        self.next_steps = next_steps
        self.links = links or {"design_doc": "", "notes": "", "deliverables": ""}
        self.subtasks = subtasks or []

    def add_subtask(self, subtask: "Task") -> None:
        """添加子任务"""
        self.subtasks.append(subtask)

    def update_progress(self, new_progress: int) -> None:
        """更新进度（自动限制范围）"""
        self.progress = max(0, min(100, new_progress))

    def to_dict(self) -> dict:
        """转换为可序列化的字典"""
        return {
            "id": self.id,
            "name": self.name,
            "time_planned": self.time_planned,
            "time_spent": self.time_spent,
            "progress": self.progress,
            "next_steps": self.next_steps,
            "links": self.links,
            "subtasks": [t.to_dict() for t in self.subtasks]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """从字典创建 Task 对象（递归处理子任务）"""
        task = cls(
            name=data["name"],
            time_planned=data["time_planned"],
            time_spent=data["time_spent"],
            progress=data["progress"],
            next_steps=data["next_steps"],
            links=data["links"]
        )
        task.id = data["id"]
        task.subtasks = [cls.from_dict(t) for t in data.get("subtasks", [])]
        return task

class Milestone:
    def __init__(self, name: str, tasks: Optional[List[Task]] = None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.tasks = tasks or []

    def add_task(self, task: Task) -> None:
        """添加任务"""
        self.tasks.append(task)

    def calculate_total_time(self) -> float:
        """计算总计划时间（包含子任务）"""
        total = 0.0
        for task in self.tasks:
            total += task.time_planned
            total += sum(sub.time_planned for sub in task.subtasks)
        return total

    def calculate_overall_progress(self) -> float:
        """计算整体进度（加权平均）"""
        if not self.tasks:
            return 0.0
        total_weight = sum(t.time_planned for t in self.tasks)
        if total_weight == 0:
            return 0.0
        return sum(t.progress * t.time_planned for t in self.tasks) / total_weight

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "tasks": [t.to_dict() for t in self.tasks]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Milestone":
        milestone = cls(name=data["name"])
        milestone.id = data["id"]
        milestone.tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
        return milestone

# ------------------------------
# 持久化类
# ------------------------------
class ProgressTracker:
    def __init__(self, data_file: str = "progress.json"):
        self.data_file = data_file
        self.milestones: List[Milestone] = []
        self.load_data()

    def load_data(self) -> None:
        """从 JSON 文件加载数据"""
        if not os.path.exists(self.data_file):
            return

        with open(self.data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.milestones = [Milestone.from_dict(ms) for ms in data.get("milestones", [])]

    def save_data(self) -> None:
        """保存数据到 JSON 文件"""
        data = {
            "milestones": [ms.to_dict() for ms in self.milestones]
        }
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def find_milestone(self, milestone_id: str) -> Optional[Milestone]:
        """通过 ID 查找里程碑"""
        return next((ms for ms in self.milestones if ms.id == milestone_id), None)

    def find_task(self, task_id: str) -> Optional[Task]:
        """递归查找任务（遍历所有里程碑）"""
        for ms in self.milestones:
            for task in ms.tasks:
                if task.id == task_id:
                    return task
                # 递归搜索子任务
                found = self._find_subtask(task, task_id)
                if found:
                    return found
        return None

    def _find_subtask(self, parent_task: Task, target_id: str) -> Optional[Task]:
        """递归查找子任务"""
        for subtask in parent_task.subtasks:
            if subtask.id == target_id:
                return subtask
            found = self._find_subtask(subtask, target_id)
            if found:
                return found
        return None

# ------------------------------
# 测试用例
# ------------------------------
if __name__ == "__main__":
    # 初始化跟踪器
    tracker = ProgressTracker("test_progress.json")

    # 创建示例数据
    milestone = Milestone("基础库学习")
    task1 = Task("OpenCV基础", time_planned=15, progress=30)
    task1.links["design_doc"] = "/docs/opencv.md"
    task1.add_subtask(Task("图像读写", time_planned=5, progress=50))
    
    milestone.add_task(task1)
    tracker.milestones.append(milestone)
    tracker.save_data()

    # 重新加载验证
    new_tracker = ProgressTracker("test_progress.json")
    print("加载后的里程碑:", [ms.name for ms in new_tracker.milestones])