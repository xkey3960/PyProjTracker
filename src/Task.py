import time
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
        subtasks: Optional[List["Task"]] = None,
        parent: Optional["Task"] = None
    ):
        self.id = str(uuid.uuid4())  # 唯一标识
        self.name = name
        self.time_planned = time_planned
        self.time_spent = time_spent
        self.progress = progress  # 0-100 百分比
        self.next_steps = next_steps
        self.links = links or {"design_doc": "", "notes": "", "deliverables": ""}
        self.subtasks = subtasks or []
        self.status = "TODO"  # 新增状态（TODO/DOING/DONE）
        self.start_time: Optional[float] = None  # 开始时间戳（DOING时记录）
        self.end_time: Optional[float] = None    # 结束时间戳（DONE时记录）
        self.parent = parent  # 新增父任务引用

    def add_subtask(self, subtask: "Task") -> None:
        """添加子任务"""
        subtask.parent = self # 设置子任务的父引用
        self.subtasks.append(subtask)

    @property
    def has_children(self) -> bool:
        """是否有子任务"""
        return len(self.subtasks) > 0

    def update_progress(self, new_progress: int) -> None:
        """更新进度（仅叶子任务可手动修改）"""
        if self.has_children:
            raise ValueError("有子任务的任务不能手动修改进度")
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
            "subtasks": [t.to_dict() for t in self.subtasks],
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time
        }

    @classmethod
    def from_dict(cls, data: dict, parent: Optional["Task"] = None) -> "Task":
        """从字典创建 Task 对象（递归处理子任务）"""
        task = cls(
            name=data["name"],
            time_planned=data["time_planned"],
            time_spent=data["time_spent"],
            progress=data["progress"],
            next_steps=data["next_steps"],
            links=data["links"],
            parent=parent
        )
        task.id = data["id"]
        subtasks_data = data.get("subtasks", [])
        task.subtasks = [
            cls.from_dict(subtask_data, parent=task)  # 关键修复：传递parent=task
            for subtask_data in subtasks_data
        ]
        task.status = data.get("status", "TODO")
        task.start_time = data.get("start_time")
        task.end_time = data.get("end_time")
        return task

    def update_status(self, new_status: str):
        """更新状态并记录时间"""
        if self.status != new_status:
            if new_status == "DOING":
                self.start_time = time.time()
            elif new_status == "DONE":
                self.end_time = time.time()
                # 自动计算耗时（秒转小时）
                if self.start_time:
                    self.time_spent += (self.end_time - self.start_time) / 3600
            self.status = new_status

    def calculate_progress(self) -> float:
        """计算进度（如果是父任务则根据子任务加权平均）"""
        if not self.has_children:
            return float(self.progress)
        total_weight = sum(t.time_planned for t in self.subtasks)
        if total_weight == 0:
            return 0.0
        return sum(t.calculate_progress() * t.time_planned for t in self.subtasks) / total_weight

    def calculate_total_time_planned(self) -> float:
        """计算总计划时间（递归子任务）"""
        return self.time_planned + sum(t.calculate_total_time_planned() for t in self.subtasks)

    def calculate_total_time_spent(self) -> float:
        """计算总投入时间（递归子任务）"""
        return self.time_spent + sum(t.calculate_total_time_spent() for t in self.subtasks)

class Milestone:
    def __init__(self, name: str, tasks: Optional[List[Task]] = None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.tasks = tasks or []

    def add_task(self, task: Task) -> None:
        """添加任务"""
        self.tasks.append(task)
    
    def remove_task(self, task_id: str) -> bool:
        """删除指定ID的任务（递归查找子任务）"""
        for i, task in enumerate(self.tasks):
            if task.id == task_id:
                del self.tasks[i]
                return True
            # 递归删除子任务
            if self._remove_subtask(task, task_id):
                return True
        return False

    def _remove_subtask(self, parent_task: Task, target_id: str) -> bool:
        for i, subtask in enumerate(parent_task.subtasks):
            if subtask.id == target_id:
                del parent_task.subtasks[i]
                return True
            if self._remove_subtask(subtask, target_id):
                return True
        return False

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
        milestone.tasks = [Task.from_dict(t, parent=None) for t in data.get("tasks", [])]
        return milestone

    def calculate_total_time_planned(self) -> float:
        """里程碑总计划时间（所有任务递归）"""
        return sum(t.calculate_total_time_planned() for t in self.tasks)

    def calculate_total_time_spent(self) -> float:
        """里程碑总投入时间（所有任务递归）"""
        return sum(t.calculate_total_time_spent() for t in self.tasks)

    def calculate_overall_progress(self) -> float:
        """里程碑整体进度（加权平均）"""
        total_weight = self.calculate_total_time_planned()
        if total_weight == 0:
            return 0.0
        return sum(t.calculate_progress() * t.calculate_total_time_planned() for t in self.tasks) / total_weight

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

    def remove_milestone(self, milestone_id: str) -> bool:
        """删除里程碑"""
        for i, ms in enumerate(self.milestones):
            if ms.id == milestone_id:
                del self.milestones[i]
                return True
        return False
    
    def _update_info4subtasks(self, task: Task):
        if task.has_children:
            task.time_planned = sum(t.calculate_total_time_planned() for t in task.subtasks)
            task.time_spent = sum(t.calculate_total_time_spent() for t in task.subtasks)
            task.progress = task.calculate_progress()

    def remove_task(self, task_id: str) -> bool:
        """全局删除任务（跨里程碑）"""
        for milestone in self.milestones:
            deleted_task = self.find_task(task_id)
            if deleted_task:
                parent = deleted_task.parent
            if milestone.remove_task(task_id):
                # 查找被删除任务的父任务（通过任务引用）
                deleted_task = self.find_task(task_id)  # 假设任务未完全从内存清除
                if parent:
                    self._update_info4subtasks(parent)
                self.save_data()
                return True
        return False

    def _propagate_time_update(self, task: Task):
        """递归向上更新父任务时间"""
        # 实现逻辑需根据数据结构补充父任务引用
        # 此处假设每个任务存储了parent引用
        current = task
        while current.parent is not None:
            self._update_info4subtasks(current)
            current = current.parent

    def add_task(self, parent_task: Optional[Task], new_task: Task):
        """添加任务时维护父子关系"""
        new_task.parent = parent_task
        if parent_task:
            parent_task.subtasks.append(new_task)
        else:
            self.milestones[-1].tasks.append(new_task)
        self._propagate_time_update(new_task)
        self.save_data()

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