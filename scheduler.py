import yaml
import time
import importlib
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

CONFIG_PATH = 'schedule_config.yaml'

class TaskScheduler:
    def __init__(self, config_path=CONFIG_PATH):
        self.scheduler = BackgroundScheduler()
        self.config_path = config_path
        
    def load_config(self):
        """載入配置檔案"""
        if not os.path.exists(self.config_path):
            print(f"❌ 找不到配置檔案: {self.config_path}")
            return []
            
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config.get('jobs', [])
    
    def get_function(self, func_path):
        """根據路徑字串載入函數"""
        try:
            module_path, func_name = func_path.rsplit(':', 1)
            module = importlib.import_module(module_path)
            return getattr(module, func_name)
        except (ImportError, AttributeError, ValueError) as e:
            print(f"❌ 無法載入函數 {func_path}: {e}")
            return None
    
    def add_job(self, job_config):
        """添加單個任務到排程器"""
        job_id = job_config['id']
        func_path = job_config['func']
        func = self.get_function(func_path)
        
        if not func:
            print(f"⚠️ 跳過任務 {job_id}: 無法找函數")
            return

        trigger_type = job_config['trigger']
        args = job_config.get('args', [])
        
        trigger = None
        if trigger_type == 'interval':
            trigger_params = {
                'weeks': job_config.get('weeks', 0),
                'days': job_config.get('days', 0),
                'hours': job_config.get('hours', 0),
                'minutes': job_config.get('minutes', 0),
                'seconds': job_config.get('seconds', 0),
            }
            trigger_params = {k: v for k, v in trigger_params.items() if v > 0}
            if not trigger_params:
                 # 預設如果沒有參數，設為 1 分鐘以便測試，或報錯
                 # 與其報錯，不如預設 30 分鐘? 不，應該依據 yaml.
                 # 如果 yaml 只寫 trigger: interval 但沒寫時間
                 pass 
            trigger = IntervalTrigger(**trigger_params)
            
        elif trigger_type == 'cron':
            trigger_params = {
                'year': job_config.get('year'),
                'month': job_config.get('month'),
                'day': job_config.get('day'),
                'week': job_config.get('week'),
                'day_of_week': job_config.get('day_of_week'),
                'hour': job_config.get('hour'),
                'minute': job_config.get('minute'),
                'second': job_config.get('second', 0),
            }
            trigger_params = {k: v for k, v in trigger_params.items() if v is not None}
            trigger = CronTrigger(**trigger_params)
        else:
            print(f"⚠️ 跳過任務 {job_id}: 不支援的觸發類型 {trigger_type}")
            return
        
        if trigger:
            self.scheduler.add_job(
                func=func,
                trigger=trigger,
                args=args,
                id=job_id,
                replace_existing=True
            )
            print(f"✅ 已添加任務: {job_id}")
    
    def start(self):
        """啟動排程器"""
        jobs = self.load_config()
        print(f"載入 {len(jobs)} 個任務配置...")
        for job in jobs:
            try:
                self.add_job(job)
            except Exception as e:
                print(f"❌ 添加任務 {job.get('id')} 失敗: {e}")
        
        if self.scheduler.get_jobs():
            self.scheduler.start()
            print("🚀 排程器已啟動")
            self.list_jobs()
        else:
            print("⚠️ 沒有有效任務，排程器未啟動")
    
    def stop(self):
        """停止排程器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            print("🛑 排程器已停止")
    
    def list_jobs(self):
        """列出所有任務"""
        jobs = self.scheduler.get_jobs()
        print("\n📋 目前排程任務:")
        for job in jobs:
            print(f"  - {job.id}: 下次執行於 {job.next_run_time}")
        print("")

if __name__ == '__main__':
    scheduler = TaskScheduler()
    scheduler.start()
    
    try:
        # 保持程式運行
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.stop()
