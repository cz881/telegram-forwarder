# 🚀 Telegram Channel Forwarder

一个功能完整的Telegram频道消息搬运工具，采用**搬运组**概念，支持精细化管理不同类型的频道内容。

## ✨ 核心特性

### 🎯 搬运组概念
- **搬运组** = 独立的转发单元，每个组有自己的源频道、目标频道和过滤规则
- **灵活配置** = 不同类型内容可以有不同的处理方式
- **精细管理** = 每个组独立的过滤规则、统计和监控

### 🔧 主要功能
- **定时调度** - 按时间段控制搬运组的启停
- **账号轮换** - 监听账号轮换使用，检测异常状态并自动切换
- **API池管理** - 支持多个API ID，自动分配给账号
- **Bot登录** - 通过Bot验证码登录，sessions保存到服务器
- **自动重连** - 网络断线自动重连，消息发送失败自动重试
- **智能过滤** - 过滤后没有内容自动跳过
- **配置热更新** - 无需重启修改过滤规则、发送频率、动态添加删除频道
- **并行处理** - 不同搬运组独立并行处理
- **历史搬运** - 支持搬运全部历史消息

### 🎮 基础功能
- **多账号监听** - 支持多个Telegram账号同时监听源频道
- **多Bot发送** - 轮换使用多个Bot发送消息，避免频率限制
- **媒体组检测** - 完整转发包含多张图片/视频的消息组
- **全局去重** - 避免重复转发相同消息，重启后仍有效
- **7×24小时运行** - systemd服务自动重启，稳定可靠

## 🎯 使用场景示例

### 场景1：新闻搬运组 (工作时间)
```yaml
组名: 新闻搬运组
源频道: 新华社、人民日报、央视新闻
目标频道: 我的新闻频道
定时调度: 09:00-18:00 (仅工作时间运行)
过滤设置: 开启广告过滤，保留链接，删除@提及
小尾巴: 📰 新闻搬运 | 仅供参考
```

### 场景2：娱乐搬运组 (夜间运行)
```yaml
组名: 娱乐搬运组
源频道: 娱乐八卦频道、明星动态
目标频道: 我的娱乐频道
定时调度: 22:00-08:00 (夜间运行，跨天)
过滤设置: 删除链接，保留表情，开启广告过滤
小尾巴: 🎬 娱乐资讯
```

### 场景3：技术搬运组 (全天运行)
```yaml
组名: 技术搬运组
源频道: GitHub Trending、技术博客
目标频道: 我的技术频道
定时调度: 无 (全天运行)
过滤设置: 保留所有内容，仅开启广告过滤
小尾巴: 💻 技术分享
```

## 📋 快速开始

### 1. 一键安装
```bash
# 从GitHub下载
git clone https://github.com/cz881/telegram-forwarder.git
cd telegram-forwarder
chmod +x scripts/*.sh

# 一键安装
./scripts/install.sh
```

### 2. 配置程序
```bash
# 编辑配置文件
vim .env

# 必须配置项
BOT_TOKEN=your_bot_token_here
ADMIN_USERS=123456789,987654321
ENCRYPTION_KEY=your_32_byte_encryption_key_here
```

### 3. 启动服务
```bash
# 安装系统服务
./scripts/service.sh install

# 启动程序
./scripts/service.sh start

# 查看状态
./scripts/service.sh status
```

### 4. 通过Bot管理
通过Bot私聊发送命令：
```bash
# 添加API池
/api_pool_add 123456 abcdef123456789...

# 添加监听账号
/add_listener +8613800138000

# 创建搬运组
/create_group 新闻组 新闻内容搬运

# 添加频道
/add_source 1 https://t.me/news_channel
/add_target 1 https://t.me/my_news

# 设置定时调度 (工作时间运行)
/set_schedule 1 09:00 18:00

# 开启过滤
/toggle_filter 1 ad_detection

# 同步历史消息
/sync_history 1
```

## 🤖 Bot命令大全

### 基础命令
```bash
/start                     # 查看所有命令
/help                      # 获取帮助信息
/status                    # 查看系统状态
```

### 搬运组管理
```bash
/create_group <组名> [描述]           # 创建搬运组
/list_groups                        # 查看所有组
/group_info <组ID>                  # 查看组详情
/delete_group <组ID>                # 删除组
/add_source <组ID> <频道链接>        # 添加源频道
/add_target <组ID> <频道链接>        # 添加目标频道
/remove_source <组ID> <频道链接>     # 移除源频道
/remove_target <组ID> <频道链接>     # 移除目标频道
```

### 账号管理
```bash
/add_listener <手机号>              # 添加监听账号
/remove_listener <手机号>           # 移除监听账号
/account_status                     # 查看账号状态
/account_list                       # 查看所有账号
```

### API池管理
```bash
/api_pool_status                    # 查看API池状态
/api_pool_add <app_id> <app_hash>   # 添加API ID
/api_pool_remove <api_id>           # 移除API ID
/account_api_info [账号]            # 查看账号API分配情况
```

### 过滤器管理
```bash
/set_filter <组ID> <类型> <规则>     # 设置过滤规则
/toggle_filter <组ID> <类型>        # 开关过滤功能
/filter_test <组ID> <测试文本>       # 测试过滤效果
```

### 调度管理
```bash
/set_schedule <组ID> <开始时间> <结束时间>  # 设置定时运行
/remove_schedule <组ID>                    # 移除定时调度
/schedule_status [组ID]                    # 查看调度状态
```

### 历史消息管理
```bash
/sync_history <组ID> [数量]         # 同步历史消息
/sync_status <组ID>                 # 查看同步状态
```

### 全局配置管理
```bash
/reload_config                      # 重新加载配置
/set_interval <最小间隔> <最大间隔>  # 调整发送间隔
/set_limit <每小时限制>             # 调整发送限制
/global_status                      # 查看全局状态
```

### 系统管理
```bash
/system_info                        # 查看系统信息
/logs [行数]                        # 查看日志
/backup                             # 手动备份
/restart                            # 重启系统
```

## 🔧 管理工具

### 服务管理
```bash
./scripts/service.sh start          # 启动服务
./scripts/service.sh stop           # 停止服务
./scripts/service.sh restart        # 重启服务
./scripts/service.sh status         # 查看状态
./scripts/service.sh logs           # 查看日志
./scripts/service.sh health         # 健康检查
```

### 监控脚本
```bash
./scripts/monitor.sh                # 系统监控
./scripts/backup.sh                 # 手动备份
```

## ⚙️ 高级配置

### 过滤规则类型
- `remove_links` - 删除所有超链接和包含的文本
- `remove_emojis` - 删除表情符号（除了 # 号保留）
- `remove_special_chars` - 删除特殊符号（除了 # 号保留）
- `ad_detection` - 检测并跳过广告内容
- `smart_filter` - 智能过滤推广、广告类消息
- `custom` - 自定义过滤规则

### 轮换策略
- `message` - 每条消息轮换账号（推荐）
- `time` - 按时间间隔轮换
- `smart` - 智能轮换（结合消息数和时间）

### 调度时间格式
- 工作时间：`09:00 18:00`
- 夜间跨天：`22:00 08:00`
- 全天运行：不设置调度

## 📊 系统要求

### 最低配置
- **系统**: Ubuntu 20.04+ / CentOS 7+ / Debian 10+
- **内存**: 1GB RAM
- **存储**: 10GB 可用空间
- **Python**: 3.8+
- **网络**: 稳定的互联网连接

### 推荐配置
- **系统**: Ubuntu 22.04 LTS
- **内存**: 2GB RAM
- **存储**: 20GB SSD
- **网络**: 境外VPS（推荐）

## 🛡️ 安全建议

1. **保护敏感信息** - 不要将.env文件提交到版本控制
2. **定期备份** - 设置自动备份数据库和配置
3. **监控日志** - 定期检查错误日志
4. **API分配** - 建议3-5个账号共享一个API ID
5. **频率控制** - 根据频道活跃度调整发送间隔

## 🔧 故障排除

### 常见问题
1. **账号登录失败** - 检查手机号格式和API有效性
2. **消息不转发** - 检查组状态、调度时间、过滤规则
3. **频率限制** - 增加发送间隔或添加更多API
4. **权限错误** - 确保Bot有目标频道的发送权限

### 调试命令
```bash
# 查看详细日志
./scripts/service.sh logs 200

# 检查系统状态
/system_info

# 健康检查
./scripts/service.sh health

# 重启服务
./scripts/service.sh restart
```

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## ⚠️ 免责声明

本工具仅供学习和个人使用，请遵守当地法律法规和Telegram服务条款。使用者需对自己的行为负责。

## 📞 技术支持

如有问题请：
1. 查看日志: `./scripts/service.sh logs`
2. 检查状态: `/status` 和 `/system_info`
3. 提交 Issue 或联系维护者

---

**⭐ 如果这个项目对你有帮助，请给一个Star！**
