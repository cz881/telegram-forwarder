#!/usr/bin/env python3
"""
Telegram Forwarder - 主程序入口
多账号、多API池、搬运组管理的Telegram频道转发工具
"""

import asyncio
import signal
import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import Settings
from config.database import Database
from core.manager import ForwarderManager
from utils.logger import setup_logging


class TelegramForwarder:
    def __init__(self):
        self.settings = Settings()
        self.database = Database()
        self.manager = None
        self.running = False

    async def start(self):
        """启动转发程序"""
        try:
            # 设置日志
            setup_logging(self.settings.log_level, self.settings.log_file)
            logger = logging.getLogger(__name__)
            
            logger.info("🚀 Telegram Forwarder 启动中...")
            
            # 创建必要的目录
            self._create_directories()
            
            # 初始化数据库
            await self.database.init()
            logger.info("✅ 数据库初始化完成")
            
            # 初始化管理器
            self.manager = ForwarderManager(self.settings, self.database)
            await self.manager.start()
            
            self.running = True
            logger.info("🎉 Telegram Forwarder 启动成功!")
            logger.info(f"📊 管理员用户: {self.settings.admin_users}")
            logger.info(f"📁 数据目录: {Path('data').absolute()}")
            
            # 保持运行
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logging.error(f"❌ 启动失败: {e}")
            sys.exit(1)

    async def stop(self):
        """停止转发程序"""
        logger = logging.getLogger(__name__)
        logger.info("🛑 正在停止 Telegram Forwarder...")
        
        self.running = False
        
        if self.manager:
            await self.manager.stop()
            
        await self.database.close()
        logger.info("👋 Telegram Forwarder 已停止")

    def _create_directories(self):
        """创建必要的目录"""
        directories = ['data', 'logs', 'sessions', 'backup']
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)

    def signal_handler(self, signum, frame):
        """信号处理器"""
        print(f"\n收到信号 {signum}, 正在安全退出...")
        asyncio.create_task(self.stop())


async def main():
    """主函数"""
    forwarder = TelegramForwarder()
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, forwarder.signal_handler)
    signal.signal(signal.SIGTERM, forwarder.signal_handler)
    
    try:
        await forwarder.start()
    except KeyboardInterrupt:
        await forwarder.stop()
    except Exception as e:
        logging.error(f"程序异常退出: {e}")
        await forwarder.stop()
        sys.exit(1)


if __name__ == "__main__":
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        sys.exit(1)
    
    # 运行主程序
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 程序已退出")
    except Exception as e:
        print(f"❌ 程序异常: {e}")
        sys.exit(1)