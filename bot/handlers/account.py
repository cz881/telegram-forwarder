"""
账号管理命令处理器
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from ..middleware import admin_required, error_handler
from ..states import state_manager, UserState


class AccountHandlers:
    """账号管理处理器"""
    
    def __init__(self, settings, database, account_manager, api_pool_manager):
        self.settings = settings
        self.database = database
        self.account_manager = account_manager
        self.api_pool_manager = api_pool_manager
        self.logger = logging.getLogger(__name__)

    @admin_required
    @error_handler
    async def add_listener(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """添加监听账号"""
        args = context.args
        if not args:
            await update.message.reply_text(
                "❌ 请提供手机号\n\n用法: `/add_listener +8613800138000`",
                parse_mode='Markdown'
            )
            return
        
        phone = args[0].strip()
        
        # 验证手机号格式
        if not phone.startswith('+'):
            phone = '+' + phone
        
        try:
            # 开始登录流程
            result = await self.account_manager.start_login(phone)
            
            if result['status'] == 'success':
                # 设置用户状态为等待验证码
                state_manager.set_user_state(
                    update.effective_user.id,
                    UserState.WAITING_CODE,
                    {'phone': phone}
                )
                
                await update.message.reply_text(
                    f"✅ {result['message']}\n\n请直接发送收到的验证码（纯数字）"
                )
            else:
                await update.message.reply_text(f"❌ {result['message']}")
                
        except Exception as e:
            self.logger.error(f"添加监听账号失败: {e}")
            await update.message.reply_text(f"❌ 添加账号失败: {str(e)}")

    @admin_required
    @error_handler
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理用户消息（用于登录流程）"""
        user_id = update.effective_user.id
        user_state = state_manager.get_user_state(user_id)
        user_data = state_manager.get_user_data(user_id)
        message_text = update.message.text.strip()
        
        if user_state == UserState.WAITING_CODE:
            # 处理验证码
            phone = user_data.get('phone')
            if not phone:
                state_manager.clear_user_state(user_id)
                await update.message.reply_text("❌ 会话已过期，请重新开始")
                return
            
            try:
                result = await self.account_manager.submit_code(phone, message_text)
                
                if result['status'] == 'success':
                    state_manager.clear_user_state(user_id)
                    await update.message.reply_text(f"🎉 {result['message']}")
                    
                elif result['status'] == '2fa_required':
                    state_manager.set_user_state(user_id, UserState.WAITING_2FA)
                    await update.message.reply_text(
                        f"🔐 {result['message']}\n\n请发送两步验证密码"
                    )
                else:
                    await update.message.reply_text(f"❌ {result['message']}")
                    
            except Exception as e:
                self.logger.error(f"提交验证码失败: {e}")
                await update.message.reply_text(f"❌ 验证失败: {str(e)}")
        
        elif user_state == UserState.WAITING_2FA:
            # 处理两步验证
            phone = user_data.get('phone')
            if not phone:
                state_manager.clear_user_state(user_id)
                await update.message.reply_text("❌ 会话已过期，请重新开始")
                return
            
            try:
                result = await self.account_manager.submit_2fa_password(phone, message_text)
                
                state_manager.clear_user_state(user_id)
                
                if result['status'] == 'success':
                    await update.message.reply_text(f"🎉 {result['message']}")
                else:
                    await update.message.reply_text(f"❌ {result['message']}")
                    
            except Exception as e:
                self.logger.error(f"两步验证失败: {e}")
                await update.message.reply_text(f"❌ 验证失败: {str(e)}")

    @admin_required
    @error_handler
    async def remove_listener(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """移除监听账号"""
        args = context.args
        if not args:
            await update.message.reply_text(
                "❌ 请提供手机号\n\n用法: `/remove_listener +8613800138000`",
                parse_mode='Markdown'
            )
            return
        
        phone = args[0].strip()
        if not phone.startswith('+'):
            phone = '+' + phone
        
        try:
            success = await self.account_manager.remove_account(phone)
            
            if success:
                await update.message.reply_text(f"✅ 账号 {phone} 已移除")
            else:
                await update.message.reply_text(f"❌ 移除账号失败")
                
        except Exception as e:
            self.logger.error(f"移除账号失败: {e}")
            await update.message.reply_text(f"❌ 移除失败: {str(e)}")

    @admin_required
    @error_handler
    async def account_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """查看账号状态"""
        try:
            stats = await self.account_manager.get_statistics()
            
            status_text = f"""
📊 **账号状态统计**

👥 **总览**
• 总账号数: {stats['total']}
• 活跃账号: {stats['active']} 
• 错误账号: {stats['error']}
• 离线账号: {stats['offline']}
• 使用率: {stats['usage_rate']}%

📱 **账号详情**
"""
            
            for account in stats['accounts'][:10]:  # 显示前10个
                status_emoji = {
                    'active': '🟢',
                    'error': '🔴', 
                    'offline': '⚫'
                }.get(account.get('status'), '⚪')
                
                status_text += f"• {status_emoji} {account['phone']} "
                if account.get('username'):
                    status_text += f"(@{account['username']}) "
                status_text += f"- {account.get('status', 'unknown')}\n"
            
            if len(stats['accounts']) > 10:
                status_text += f"\n... 还有 {len(stats['accounts']) - 10} 个账号"
            
            await update.message.reply_text(status_text, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"获取账号状态失败: {e}")
            await update.message.reply_text(f"❌ 获取状态失败: {str(e)}")

    @admin_required
    @error_handler
    async def account_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """查看账号列表"""
        try:
            accounts = await self.account_manager.get_account_list()
            
            if not accounts:
                await update.message.reply_text("📱 暂无监听账号")
                return
            
            account_text = "📱 **监听账号列表**\n\n"
            
            for i, account in enumerate(accounts, 1):
                status_emoji = {
                    'active': '🟢',
                    'error': '🔴',
                    'offline': '⚫',
                    'unauthorized': '🟡'
                }.get(account.get('status'), '⚪')
                
                account_text += f"{i}. {status_emoji} {account['phone']}\n"
                
                if account.get('username'):
                    account_text += f"   用户名: @{account['username']}\n"
                
                if account.get('api_id'):
                    account_text += f"   API ID: {account['api_id']}\n"
                
                account_text += f"   状态: {account.get('status', 'unknown')}\n"
                account_text += f"   错误次数: {account.get('error_count', 0)}\n\n"
            
            await update.message.reply_text(account_text, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"获取账号列表失败: {e}")
            await update.message.reply_text(f"❌ 获取列表失败: {str(e)}")

    @admin_required
    @error_handler
    async def api_pool_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """查看API池状态"""
        try:
            stats = await self.api_pool_manager.get_statistics()
            
            status_text = f"""
🔑 **API池状态**

📊 **总览**
• 总API数: {stats['total_apis']}
• 总容量: {stats['total_capacity']} 个账号
• 已使用: {stats['total_used']} 个账号
• 可用容量: {stats['available']} 个账号
• 使用率: {stats['usage_rate']}%

🔑 **API详情**
"""
            
            for api in stats['apis']:
                status_text += f"• API {api['app_id']}\n"
                status_text += f"  容量: {api['current_accounts']}/{api['max_accounts']}\n"
                status_text += f"  状态: {api['status']}\n"
                
                if api['assigned_accounts']:
                    accounts_str = ', '.join(api['assigned_accounts'])
                    if len(accounts_str) > 50:
                        accounts_str = accounts_str[:50] + '...'
                    status_text += f"  分配账号: {accounts_str}\n"
                
                status_text += "\n"
            
            await update.message.reply_text(status_text, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"获取API池状态失败: {e}")
            await update.message.reply_text(f"❌ 获取状态失败: {str(e)}")

    @admin_required
    @error_handler
    async def api_pool_add(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """添加API到池中"""
        args = context.args
        if len(args) < 2:
            await update.message.reply_text(
                "❌ 请提供API ID和API Hash\n\n用法: `/api_pool_add 123456 abcdef123456...`",
                parse_mode='Markdown'
            )
            return
        
        app_id = args[0].strip()
        app_hash = args[1].strip()
        max_accounts = int(args[2]) if len(args) > 2 else 1
        
        try:
            success = await self.api_pool_manager.add_api(app_id, app_hash, max_accounts)
            
            if success:
                await update.message.reply_text(
                    f"✅ API ID {app_id} 添加成功\n最大账号数: {max_accounts}"
                )
            else:
                await update.message.reply_text("❌ 添加API失败")
                
        except Exception as e:
            self.logger.error(f"添加API失败: {e}")
            await update.message.reply_text(f"❌ 添加失败: {str(e)}")

    @admin_required
    @error_handler
    async def api_pool_remove(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """从池中移除API"""
        args = context.args
        if not args:
            await update.message.reply_text(
                "❌ 请提供API ID\n\n用法: `/api_pool_remove 123456`",
                parse_mode='Markdown'
            )
            return
        
        app_id = args[0].strip()
        
        try:
            success = await self.api_pool_manager.remove_api(app_id)
            
            if success:
                await update.message.reply_text(f"✅ API ID {app_id} 已移除")
            else:
                await update.message.reply_text("❌ 移除API失败（可能正在被使用）")
                
        except Exception as e:
            self.logger.error(f"移除API失败: {e}")
            await update.message.reply_text(f"❌ 移除失败: {str(e)}")

    @admin_required
    @error_handler
    async def account_api_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """查看账号API分配信息"""
        args = context.args
        
        try:
            if args:
                # 查看指定账号
                phone = args[0].strip()
                if not phone.startswith('+'):
                    phone = '+' + phone
                
                api = await self.api_pool_manager.get_account_api(phone)
                
                if api:
                    await update.message.reply_text(
                        f"📱 账号: {phone}\n"
                        f"🔑 API ID: {api['app_id']}\n"
                        f"📊 使用情况: {api['current_accounts']}/{api['max_accounts']}\n"
                        f"📅 创建时间: {api['created_at']}"
                    )
                else:
                    await update.message.reply_text(f"❌ 账号 {phone} 未分配API或不存在")
            else:
                # 查看所有分配情况
                apis = await self.api_pool_manager.get_pool_status()
                
                info_text = "🔑 **API分配详情**\n\n"
                
                for api in apis:
                    info_text += f"**API {api['app_id']}**\n"
                    info_text += f"使用: {api['current_accounts']}/{api['max_accounts']}\n"
                    
                    if api['assigned_accounts']:
                        info_text += "分配账号:\n"
                        for account in api['assigned_accounts']:
                            info_text += f"  • {account}\n"
                    else:
                        info_text += "暂无分配账号\n"
                    
                    info_text += "\n"
                
                await update.message.reply_text(info_text, parse_mode='Markdown')
                
        except Exception as e:
            self.logger.error(f"获取API分配信息失败: {e}")
            await update.message.reply_text(f"❌ 获取信息失败: {str(e)}")
