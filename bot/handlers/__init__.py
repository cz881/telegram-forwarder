"""
Bot命令处理器
"""

from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import BotCommand

from .admin import AdminHandlers
from .group import GroupHandlers
from .account import AccountHandlers
from .config import ConfigHandlers
from .monitor import MonitorHandlers
from ..middleware import admin_required


def setup_handlers(app: Application, settings, database, account_manager, 
                  api_pool_manager, group_processor, task_scheduler):
    """设置所有Bot处理器"""
    
    # 初始化处理器
    admin_handler = AdminHandlers(settings, database)
    group_handler = GroupHandlers(settings, database, group_processor)
    account_handler = AccountHandlers(settings, database, account_manager, api_pool_manager)
    config_handler = ConfigHandlers(settings, database)
    monitor_handler = MonitorHandlers(settings, database, account_manager, group_processor, task_scheduler)
    
    # 添加命令处理器
    
    # 基础命令
    app.add_handler(CommandHandler("start", admin_handler.start_command))
    app.add_handler(CommandHandler("help", admin_handler.help_command))
    app.add_handler(CommandHandler("status", monitor_handler.status_command))
    
    # 搬运组管理
    app.add_handler(CommandHandler("create_group", group_handler.create_group))
    app.add_handler(CommandHandler("list_groups", group_handler.list_groups))
    app.add_handler(CommandHandler("group_info", group_handler.group_info))
    app.add_handler(CommandHandler("delete_group", group_handler.delete_group))
    app.add_handler(CommandHandler("add_source", group_handler.add_source))
    app.add_handler(CommandHandler("add_target", group_handler.add_target))
    app.add_handler(CommandHandler("remove_source", group_handler.remove_source))
    app.add_handler(CommandHandler("remove_target", group_handler.remove_target))
    
    # 账号管理
    app.add_handler(CommandHandler("add_listener", account_handler.add_listener))
    app.add_handler(CommandHandler("remove_listener", account_handler.remove_listener))
    app.add_handler(CommandHandler("account_status", account_handler.account_status))
    app.add_handler(CommandHandler("account_list", account_handler.account_list))
    
    # API池管理
    app.add_handler(CommandHandler("api_pool_status", account_handler.api_pool_status))
    app.add_handler(CommandHandler("api_pool_add", account_handler.api_pool_add))
    app.add_handler(CommandHandler("api_pool_remove", account_handler.api_pool_remove))
    app.add_handler(CommandHandler("account_api_info", account_handler.account_api_info))
    
    # 过滤器管理
    app.add_handler(CommandHandler("set_filter", group_handler.set_filter))
    app.add_handler(CommandHandler("toggle_filter", group_handler.toggle_filter))
    app.add_handler(CommandHandler("filter_test", group_handler.filter_test))
    
    # 调度管理
    app.add_handler(CommandHandler("set_schedule", group_handler.set_schedule))
    app.add_handler(CommandHandler("remove_schedule", group_handler.remove_schedule))
    app.add_handler(CommandHandler("schedule_status", monitor_handler.schedule_status))
    
    # 历史消息
    app.add_handler(CommandHandler("sync_history", group_handler.sync_history))
    app.add_handler(CommandHandler("sync_status", group_handler.sync_status))
    
    # 配置管理
    app.add_handler(CommandHandler("reload_config", config_handler.reload_config))
    app.add_handler(CommandHandler("set_interval", config_handler.set_interval))
    app.add_handler(CommandHandler("set_limit", config_handler.set_limit))
    app.add_handler(CommandHandler("global_status", monitor_handler.global_status))
    
    # 系统管理
    app.add_handler(CommandHandler("system_info", monitor_handler.system_info))
    app.add_handler(CommandHandler("logs", monitor_handler.logs))
    app.add_handler(CommandHandler("backup", admin_handler.backup))
    app.add_handler(CommandHandler("restart", admin_handler.restart))
    
    # 消息处理器（用于登录流程）
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        account_handler.handle_message
    ))
    
    # 设置Bot菜单
    setup_bot_menu(app)


async def setup_bot_menu(app: Application):
    """设置Bot命令菜单"""
    commands = [
        BotCommand("start", "查看所有命令和功能"),
        BotCommand("help", "获取帮助信息"),
        BotCommand("status", "查看系统状态"),
        
        # 搬运组管理
        BotCommand("create_group", "创建搬运组"),
        BotCommand("list_groups", "查看所有搬运组"),
        BotCommand("group_info", "查看组详情"),
        
        # 账号管理
        BotCommand("add_listener", "添加监听账号"),
        BotCommand("account_status", "查看账号状态"),
        BotCommand("api_pool_status", "查看API池状态"),
        
        # 系统管理
        BotCommand("global_status", "全局状态"),
        BotCommand("system_info", "系统信息"),
        BotCommand("logs", "查看日志"),
    ]
    
    try:
        await app.bot.set_my_commands(commands)
    except Exception as e:
        print(f"设置Bot菜单失败: {e}")