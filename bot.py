#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram 记账机器人主程序
"""
import logging
import re
import uuid
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler
)
from telegram.constants import ParseMode

import config
from database import db
from okpay import okpay

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class BookkeepingBot:
    """记账机器人类"""

    def __init__(self):
        self.app = Application.builder().token(config.BOT_TOKEN).build()
        self._setup_handlers()

    def _setup_handlers(self):
        """设置命令处理器"""
        # 基础命令
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("menu", self.menu_command))
        self.app.add_handler(CommandHandler("help", self.help_command))

        # 管理员命令
        self.app.add_handler(CommandHandler("admin", self.admin_panel))
        self.app.add_handler(CommandHandler("authorize", self.authorize_command))
        self.app.add_handler(CommandHandler("membership", self.check_membership_command))

        # 会员购买
        self.app.add_handler(CommandHandler("buy", self.buy_membership_command))

        # 群组设置命令
        self.app.add_handler(MessageHandler(
            filters.TEXT & filters.Regex(r'^设置汇率\s*[\d.]+$'),
            self.set_exchange_rate
        ))
        self.app.add_handler(MessageHandler(
            filters.TEXT & filters.Regex(r'^设置费率\s*[\d.]+$'),
            self.set_fee_rate
        ))
        self.app.add_handler(MessageHandler(
            filters.TEXT & filters.Regex(r'^设置币种\s*\w+$'),
            self.set_currency
        ))
        self.app.add_handler(MessageHandler(
            filters.TEXT & filters.Regex(r'^设置商户号\s*.+$'),
            self.set_merchant_id
        ))

        # 记账命令（入款、出款、余额调整）- 支持可选汇率参数
        self.app.add_handler(MessageHandler(
            filters.TEXT & filters.Regex(r'^[+＋][\d.]+[uU]?(\s+[\d.]+)?$'),
            self.add_income
        ))
        self.app.add_handler(MessageHandler(
            filters.TEXT & filters.Regex(r'^(入款|上行)\s*[\d.]+[uU]?(\s+[\d.]+)?$'),
            self.add_income
        ))
        self.app.add_handler(MessageHandler(
            filters.TEXT & filters.Regex(r'^[-－][\d.]+[uU]?(\s+[\d.]+)?$'),
            self.add_expense
        ))
        self.app.add_handler(MessageHandler(
            filters.TEXT & filters.Regex(r'^(出款|下发)\s*[\d.]+[uU]?(\s+[\d.]+)?$'),
            self.add_expense
        ))
        self.app.add_handler(MessageHandler(
            filters.TEXT & filters.Regex(r'^余额[+＋－-][\d.]+[uU]?(\s+[\d.]+)?$'),
            self.adjust_balance
        ))

        # 查询命令
        self.app.add_handler(MessageHandler(
            filters.TEXT & filters.Regex(r'^[查cC]$'),
            self.query_records
        ))

        # 计算器功能
        self.app.add_handler(MessageHandler(
            filters.TEXT & filters.Regex(r'^[\d+\-*/().^\s]+$'),
            self.calculator
        ))
        self.app.add_handler(MessageHandler(
            filters.TEXT & filters.Regex(r'^(开启|关闭)计算器$'),
            self.toggle_calculator
        ))

        # USDT价格查询
        self.app.add_handler(MessageHandler(
            filters.TEXT & filters.Regex(r'^[zwbkteepy]0$'),
            self.query_usdt_price
        ))

        # 申请试用
        self.app.add_handler(MessageHandler(
            filters.TEXT & filters.Regex(r'^申请试用$'),
            self.apply_trial
        ))

        # 中文授权命令
        self.app.add_handler(MessageHandler(
            filters.TEXT & filters.Regex(r'^授权\s+\d+\s+\d+天$'),
            self.authorize_chinese
        ))

        # 中文查询会员命令
        self.app.add_handler(MessageHandler(
            filters.TEXT & filters.Regex(r'^会员到期时间\s+\d+$'),
            self.check_membership_chinese
        ))

        # 回调查询处理
        self.app.add_handler(CallbackQueryHandler(self.button_callback))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /start 命令"""
        user = update.effective_user

        # 创建或获取用户
        db_user = await db.get_or_create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )

        # 检查会员状态
        is_member = db_user.is_member_active() or db_user.is_admin
        days_left = db_user.get_membership_days_left()

        # 构建主菜单按钮
        keyboard = []

        if is_member:
            membership_status = f"✅ 会员有效 (剩余{days_left}天)" if days_left > 0 else "✅ 永久会员"
        else:
            membership_status = "❌ 未开通会员"

        # 第一行：会员相关
        if not is_member:
            # 未开通会员，显示申请试用
            keyboard.append([
                InlineKeyboardButton("🎁 申请试用", callback_data="apply_trial_btn"),
                InlineKeyboardButton("💎 购买会员", callback_data="buy_membership")
            ])
        else:
            # 已开通会员
            keyboard.append([
                InlineKeyboardButton("💎 续费会员", callback_data="buy_membership"),
                InlineKeyboardButton("👤 我的信息", callback_data="my_info")
            ])

        # 第二行：功能按钮
        keyboard.append([
            InlineKeyboardButton("📖 使用教程", callback_data="tutorial"),
            InlineKeyboardButton("📊 查看统计", callback_data="view_stats")
        ])

        # 第三行：Web服务
        keyboard.append([
            InlineKeyboardButton("🌐 Web账单查询", url=f"http://{config.WEBHOOK_HOST}:52000"),
            InlineKeyboardButton("🎛️ 管理后台", url=f"http://{config.WEBHOOK_HOST}:38888")
        ])

        # 如果是管理员，添加管理面板
        if db_user.is_admin:
            keyboard.append([
                InlineKeyboardButton("⚙️ 管理员面板", callback_data="admin_panel")
            ])

        reply_markup = InlineKeyboardMarkup(keyboard)

        welcome_text = f"""
🎉 欢迎使用智能记账机器人！

👤 用户：{user.first_name} (@{user.username or user.id})
💎 会员状态：{membership_status}

📝 快速记账：
• 入款：+100 或 入款100
• 出款：-100 或 出款100
• 余额：余额+100
• USDT：+100u

📊 查看统计：发送"查"或"c"

💡 点击下方按钮探索更多功能
"""
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)

    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """显示主菜单"""
        await self.start_command(update, context)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /help 命令"""
        help_text = """
📖 详细使用说明

【记账功能】
入款：+100、入款100、上行100
出款：-100、出款100、下发100
余额调整：余额+100、余额-100
USDT记账：在金额后加u，如+100u
支持小数：+100.5、-88.88

💡 单笔自定义汇率：
+100 7.12 - 入款100，汇率7.12
-200 7.15 - 出款200，汇率7.15
+100u 7.12 - 入款100 USDT，汇率7.12
余额+50 7.2 - 余额增加50，汇率7.2

【查询统计】
发送"查"或"c"：
• 入款总额及明细
• 出款总额及明细
• 余额调整记录
• 当前余额
• 手续费计算

【群组设置】
设置汇率 7.2（设置默认汇率）
设置费率 0.01（1%手续费）
设置币种 JPY
设置商户号 12345

【USDT价格】
z0 - 支付宝收款价
w0 - 微信收款价
b0/k0 - 银行卡收款价
t0 - 泰铢价格
e0 - 欧元价格
p0 - 比索价格
y0 - 英镑价格

【计算器】
直接发送算式：100*7.2+50
支持：+ - * / ^ ( )
开启计算器 / 关闭计算器

【管理员命令】
/authorize @用户名 30 - 授权用户30天
/membership @用户名 - 查询会员到期时间

【购买会员】
/buy - 选择套餐购买会员
通过OKPAY支付USDT
"""
        await update.message.reply_text(help_text)

    async def check_permission(self, update: Update) -> tuple:
        """
        检查用户权限
        返回: (user, group, is_allowed, is_operator, is_admin)
        """
        user_tg = update.effective_user
        chat = update.effective_chat

        # 获取用户
        user = await db.get_user_by_telegram_id(user_tg.id)
        if not user:
            user = await db.get_or_create_user(
                telegram_id=user_tg.id,
                username=user_tg.username,
                first_name=user_tg.first_name,
                last_name=user_tg.last_name
            )

        is_admin = user.is_admin

        # 私聊不需要检查群组权限
        if chat.type == 'private':
            return user, None, True, True, is_admin

        # 获取群组
        group = await db.get_or_create_group(
            telegram_id=chat.id,
            title=chat.title,
            owner_id=user.id
        )

        # 检查会员权限
        is_member = user.is_member_active() or is_admin

        # 检查操作员权限
        is_operator = await db.is_group_operator(group.id, user.id) or is_admin

        return user, group, is_member, is_operator, is_admin

    async def authorize_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """管理员授权用户命令：/authorize @username 30"""
        user, _, _, _, is_admin = await self.check_permission(update)

        if not is_admin:
            await update.message.reply_text("❌ 此命令仅限管理员使用")
            return

        if len(context.args) < 2:
            await update.message.reply_text(
                "❌ 使用方法：/authorize @用户名 天数\n"
                "例如：/authorize @jdccc 30"
            )
            return

        target_identifier = context.args[0]
        try:
            days = int(context.args[1])
        except ValueError:
            await update.message.reply_text("❌ 天数必须是数字")
            return

        # 查找目标用户
        if target_identifier.startswith('@'):
            target_user = await db.get_user_by_username(target_identifier[1:])
        else:
            try:
                target_id = int(target_identifier)
                target_user = await db.get_user_by_telegram_id(target_id)
            except ValueError:
                target_user = await db.get_user_by_username(target_identifier)

        if not target_user:
            await update.message.reply_text("❌ 未找到该用户，用户需要先启动机器人")
            return

        # 延长会员时间
        await db.extend_membership(target_user.id, days)

        # 重新获取用户信息
        target_user = await db.get_user_by_telegram_id(target_user.telegram_id)

        expires_str = target_user.membership_expires_at.strftime('%Y-%m-%d %H:%M:%S')

        await update.message.reply_text(
            f"✅ 已成功授权用户 @{target_user.username or target_user.telegram_id}\n"
            f"📅 会员到期时间：{expires_str}\n"
            f"⏰ 剩余天数：{target_user.get_membership_days_left()}天"
        )

    async def check_membership_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """查询会员到期时间：/membership @username"""
        user, _, _, _, is_admin = await self.check_permission(update)

        if not is_admin:
            await update.message.reply_text("❌ 此命令仅限管理员使用")
            return

        if len(context.args) < 1:
            await update.message.reply_text(
                "❌ 使用方法：/membership @用户名\n"
                "例如：/membership @jdccc"
            )
            return

        target_identifier = context.args[0]

        # 查找目标用户
        if target_identifier.startswith('@'):
            target_user = await db.get_user_by_username(target_identifier[1:])
        else:
            try:
                target_id = int(target_identifier)
                target_user = await db.get_user_by_telegram_id(target_id)
            except ValueError:
                target_user = await db.get_user_by_username(target_identifier)

        if not target_user:
            await update.message.reply_text("❌ 未找到该用户")
            return

        if target_user.membership_expires_at:
            expires_str = target_user.membership_expires_at.strftime('%Y-%m-%d %H:%M:%S')
            days_left = target_user.get_membership_days_left()
            status = "✅ 有效" if target_user.is_member_active() else "❌ 已过期"

            await update.message.reply_text(
                f"👤 用户：@{target_user.username or target_user.telegram_id}\n"
                f"📅 到期时间：{expires_str}\n"
                f"⏰ 剩余天数：{days_left}天\n"
                f"📊 状态：{status}"
            )
        else:
            await update.message.reply_text(
                f"👤 用户：@{target_user.username or target_user.telegram_id}\n"
                f"📊 状态：❌ 未开通会员"
            )

    async def apply_trial(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """申请试用"""
        user = update.effective_user

        # 创建或获取用户
        db_user = await db.get_or_create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )

        # 给用户发送确认消息
        await update.message.reply_text(
            "✅ 您的试用申请已提交\n\n"
            "请耐心等待管理员审核\n"
            "审核通过后将自动通知您"
        )

        # 通知所有管理员
        for admin_id in config.ADMIN_IDS:
            try:
                await self.app.bot.send_message(
                    chat_id=admin_id,
                    text=f"📋 申请试用\n"
                         f"用户ID：{user.id}\n"
                         f"用户名：{user.username or '无'}\n"
                         f"用户名称：{user.first_name or ''}{' ' + user.last_name if user.last_name else ''}\n\n"
                         f"💡 授权命令：\n"
                         f"授权 {user.id} 天数"
                )
            except Exception as e:
                logger.error(f"通知管理员失败: {e}")

    async def authorize_chinese(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """中文授权命令：授权 用户ID 天数"""
        user = update.effective_user
        db_user = await db.get_user_by_telegram_id(user.id)

        if not db_user or not db_user.is_admin:
            await update.message.reply_text("❌ 此命令仅限管理员使用")
            return

        # 解析命令
        text = update.message.text
        match = re.match(r'^授权\s+(\d+)\s+(\d+)天$', text)
        if not match:
            await update.message.reply_text("❌ 命令格式错误\n\n使用格式：授权 用户ID 天数\n例如：授权 123456789 30天")
            return

        target_id = int(match.group(1))
        days = int(match.group(2))

        # 查找目标用户
        target_user = await db.get_user_by_telegram_id(target_id)

        if not target_user:
            await update.message.reply_text("❌ 未找到该用户，用户需要先启动机器人")
            return

        # 延长会员时间
        await db.extend_membership(target_user.id, days)

        # 重新获取用户信息
        target_user = await db.get_user_by_telegram_id(target_user.telegram_id)

        expires_str = target_user.membership_expires_at.strftime('%Y-%m-%d %H:%M:%S')
        days_left = target_user.get_membership_days_left()

        # 给管理员发送确认消息
        await update.message.reply_text(
            f"✅ 已成功授权用户 {target_user.first_name or target_user.username or target_user.telegram_id} ({target_user.telegram_id}) {days}天\n"
            f"到期时间: {expires_str}"
        )

        # 通知被授权用户
        try:
            await self.app.bot.send_message(
                chat_id=target_user.telegram_id,
                text=f"🎉 管理员已为您授权使用 {days}天\n"
                     f"到期时间: {expires_str}\n\n"
                     f"立即发送 /start 开始使用"
            )
        except Exception as e:
            logger.error(f"通知用户失败: {e}")

    async def check_membership_chinese(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """中文查询会员命令：会员到期时间 用户ID"""
        user = update.effective_user
        db_user = await db.get_user_by_telegram_id(user.id)

        if not db_user or not db_user.is_admin:
            await update.message.reply_text("❌ 此命令仅限管理员使用")
            return

        # 解析命令
        text = update.message.text
        match = re.match(r'^会员到期时间\s+(\d+)$', text)
        if not match:
            await update.message.reply_text("❌ 命令格式错误\n\n使用格式：会员到期时间 用户ID\n例如：会员到期时间 123456789")
            return

        target_id = int(match.group(1))

        # 查找目标用户
        target_user = await db.get_user_by_telegram_id(target_id)

        if not target_user:
            await update.message.reply_text("❌ 未找到该用户")
            return

        if target_user.membership_expires_at:
            expires_str = target_user.membership_expires_at.strftime('%Y-%m-%d %H:%M:%S')
            days_left = target_user.get_membership_days_left()
            hours_left = int((target_user.membership_expires_at - datetime.now()).total_seconds() / 3600) % 24

            await update.message.reply_text(
                f"✅ 用户 {target_user.first_name or target_user.username or target_user.telegram_id} ({target_user.telegram_id}) 的授权到期时间: {expires_str}\n"
                f"剩余时间: {days_left}天{hours_left}小时"
            )
        else:
            await update.message.reply_text(
                f"❌ 用户 {target_user.first_name or target_user.username or target_user.telegram_id} ({target_user.telegram_id}) 未开通会员"
            )

    async def buy_membership_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """购买会员命令"""
        user, _, _, _, _ = await self.check_permission(update)

        keyboard = [
            [InlineKeyboardButton(
                f"30天会员 - {config.MEMBERSHIP_PRICE_30_DAYS} USDT",
                callback_data=f"buy_30_{user.telegram_id}"
            )],
            [InlineKeyboardButton(
                f"90天会员 - {config.MEMBERSHIP_PRICE_90_DAYS} USDT",
                callback_data=f"buy_90_{user.telegram_id}"
            )],
            [InlineKeyboardButton(
                f"365天会员 - {config.MEMBERSHIP_PRICE_365_DAYS} USDT",
                callback_data=f"buy_365_{user.telegram_id}"
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "💎 选择会员套餐：\n\n"
            "会员权益：\n"
            "✅ 无限群组使用\n"
            "✅ 完整记账功能\n"
            "✅ 数据统计分析\n"
            "✅ 优先技术支持\n\n"
            "请选择购买时长：",
            reply_markup=reply_markup
        )

    async def admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """管理员面板命令"""
        user = update.effective_user
        db_user = await db.get_user_by_telegram_id(user.id)

        if not db_user or not db_user.is_admin:
            await update.message.reply_text("❌ 此功能仅限管理员使用")
            return

        keyboard = [
            [
                InlineKeyboardButton("👥 用户列表", callback_data="admin_users"),
                InlineKeyboardButton("💎 授权会员", callback_data="admin_authorize")
            ],
            [
                InlineKeyboardButton("🏢 群组列表", callback_data="admin_groups"),
                InlineKeyboardButton("📊 统计数据", callback_data="admin_stats")
            ],
            [
                InlineKeyboardButton("💰 支付记录", callback_data="admin_payments"),
                InlineKeyboardButton("⚙️ 系统设置", callback_data="admin_settings")
            ],
            [InlineKeyboardButton("🔙 返回主菜单", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "⚙️ 管理员控制面板\n\n"
            "请选择要执行的操作：",
            reply_markup=reply_markup
        )

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理按钮回调"""
        query = update.callback_query
        await query.answer()

        data = query.data
        user = query.from_user

        # 主菜单按钮
        if data == "apply_trial_btn":
            await self._handle_apply_trial(query, user)
            return
        elif data == "buy_membership":
            await self._show_buy_membership(query, user)
            return
        elif data == "my_info":
            await self._show_my_info(query, user)
            return
        elif data == "tutorial":
            await self._show_tutorial(query)
            return
        elif data == "view_stats":
            await self._show_my_stats(query, user)
            return
        elif data == "admin_panel":
            await self._show_admin_panel(query, user)
            return
        elif data == "back_to_menu":
            await self._back_to_menu(query, user)
            return

        # 管理员面板按钮
        elif data == "admin_users":
            await self._admin_show_users(query, user)
            return
        elif data == "admin_authorize":
            await self._admin_show_authorize(query)
            return
        elif data == "admin_groups":
            await self._admin_show_groups(query, user)
            return
        elif data == "admin_stats":
            await self._admin_show_stats(query, user)
            return
        elif data == "admin_payments":
            await self._admin_show_payments(query, user)
            return
        elif data == "admin_settings":
            await self._admin_show_settings(query)
            return

        # 购买会员套餐
        elif data.startswith('buy_'):
            parts = data.split('_')
            days = int(parts[1])
            user_id = int(parts[2])

            # 获取价格
            if days == 30:
                amount = config.MEMBERSHIP_PRICE_30_DAYS
            elif days == 90:
                amount = config.MEMBERSHIP_PRICE_90_DAYS
            elif days == 365:
                amount = config.MEMBERSHIP_PRICE_365_DAYS
            else:
                await query.edit_message_text("❌ 无效的套餐")
                return

            # 生成唯一订单号
            unique_id = f"MB_{user_id}_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"

            # 创建支付记录
            user = await db.get_user_by_telegram_id(user_id)
            payment = await db.create_payment(
                user_id=user.id,
                unique_id=unique_id,
                amount=amount,
                days=days,
                coin='USDT'
            )

            # 创建支付链接
            result = await okpay.create_pay_link(
                unique_id=unique_id,
                amount=amount,
                coin='USDT',
                name=f"记账机器人会员 {days}天"
            )

            if result:
                order_id = result.get('order_id')
                pay_url = result.get('pay_url')

                # 更新订单号
                await db.update_payment_order_id(unique_id, order_id)

                keyboard = [[InlineKeyboardButton("💳 立即支付", url=pay_url)]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await query.edit_message_text(
                    f"💎 会员套餐：{days}天\n"
                    f"💰 金额：{amount} USDT\n"
                    f"📝 订单号：{order_id}\n\n"
                    f"请点击下方按钮完成支付：",
                    reply_markup=reply_markup
                )
            else:
                await query.edit_message_text("❌ 创建支付订单失败，请稍后重试")

    async def add_income(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """添加入款记录"""
        user, group, is_member, is_operator, is_admin = await self.check_permission(update)

        if not is_member:
            await update.message.reply_text(
                "❌ 你还不是会员，无法使用记账功能\n\n"
                "使用 /buy 购买会员"
            )
            return

        if not is_operator:
            await update.message.reply_text("❌ 你没有操作权限")
            return

        text = update.message.text

        # 解析金额和可选汇率：+100 或 +100u 或 +100 7.12 或 +100u 7.12
        # 查找所有数字
        numbers = re.findall(r'[\d.]+', text)
        if not numbers:
            return

        amount = float(numbers[0])
        exchange_rate = float(numbers[1]) if len(numbers) > 1 else None

        # 检查是否是USDT（金额后紧跟u/U）
        is_usdt = bool(re.search(r'[\d.]+[uU]', text))

        # 获取群组设置
        settings = await db.get_group_settings(group.id)
        currency = 'USDT' if is_usdt else settings.currency

        # 添加记录
        await db.add_record(
            group_id=group.id,
            user_id=user.id,
            record_type='income',
            amount=amount,
            currency=currency,
            is_usdt=is_usdt,
            exchange_rate=exchange_rate,
            message_id=update.message.message_id
        )

        # 构建确认消息
        confirm_msg = f"✅ 入款记录已添加\n💰 金额：{amount} {currency}"
        if exchange_rate:
            confirm_msg += f"\n💱 汇率：{exchange_rate}"
        elif not is_usdt:
            confirm_msg += f"\n💱 汇率：{settings.exchange_rate} (默认)"

        await update.message.reply_text(confirm_msg)

    async def add_expense(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """添加出款记录"""
        user, group, is_member, is_operator, is_admin = await self.check_permission(update)

        if not is_member:
            await update.message.reply_text(
                "❌ 你还不是会员，无法使用记账功能\n\n"
                "使用 /buy 购买会员"
            )
            return

        if not is_operator:
            await update.message.reply_text("❌ 你没有操作权限")
            return

        text = update.message.text

        # 解析金额和可选汇率：-100 或 -100u 或 -100 7.15 或 -100u 7.15
        numbers = re.findall(r'[\d.]+', text)
        if not numbers:
            return

        amount = float(numbers[0])
        exchange_rate = float(numbers[1]) if len(numbers) > 1 else None

        # 检查是否是USDT（金额后紧跟u/U）
        is_usdt = bool(re.search(r'[\d.]+[uU]', text))

        # 获取群组设置
        settings = await db.get_group_settings(group.id)
        currency = 'USDT' if is_usdt else settings.currency

        # 添加记录
        await db.add_record(
            group_id=group.id,
            user_id=user.id,
            record_type='expense',
            amount=amount,
            currency=currency,
            is_usdt=is_usdt,
            exchange_rate=exchange_rate,
            message_id=update.message.message_id
        )

        # 构建确认消息
        confirm_msg = f"✅ 出款记录已添加\n💰 金额：{amount} {currency}"
        if exchange_rate:
            confirm_msg += f"\n💱 汇率：{exchange_rate}"
        elif not is_usdt:
            confirm_msg += f"\n💱 汇率：{settings.exchange_rate} (默认)"

        await update.message.reply_text(confirm_msg)

    async def adjust_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """调整余额"""
        user, group, is_member, is_operator, is_admin = await self.check_permission(update)

        if not is_member:
            await update.message.reply_text(
                "❌ 你还不是会员，无法使用记账功能\n\n"
                "使用 /buy 购买会员"
            )
            return

        if not is_operator:
            await update.message.reply_text("❌ 你没有操作权限")
            return

        text = update.message.text

        # 解析金额（带正负号）和可选汇率：余额+100 或 余额+100u 或 余额+100 7.2
        match = re.search(r'[+＋－-][\d.]+', text)
        if not match:
            return

        amount_str = match.group()
        # 统一符号
        amount_str = amount_str.replace('＋', '+').replace('－', '-')
        amount = float(amount_str)

        # 检查是否是USDT
        is_usdt = bool(re.search(r'[\d.]+[uU]', text))

        # 查找所有数字，第二个数字（如果存在）是汇率
        numbers = re.findall(r'[\d.]+', text)
        exchange_rate = float(numbers[1]) if len(numbers) > 1 else None

        # 获取群组设置
        settings = await db.get_group_settings(group.id)
        currency = 'USDT' if is_usdt else settings.currency

        # 添加记录
        await db.add_record(
            group_id=group.id,
            user_id=user.id,
            record_type='balance',
            amount=amount,
            currency=currency,
            is_usdt=is_usdt,
            exchange_rate=exchange_rate,
            message_id=update.message.message_id
        )

        action = "增加" if amount > 0 else "减少"
        confirm_msg = f"✅ 余额已{action}\n💰 金额：{amount:+.2f} {currency}"
        if exchange_rate:
            confirm_msg += f"\n💱 汇率：{exchange_rate}"
        elif not is_usdt:
            confirm_msg += f"\n💱 汇率：{settings.exchange_rate} (默认)"

        await update.message.reply_text(confirm_msg)

    async def query_records(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """查询记账统计"""
        user, group, is_member, _, _ = await self.check_permission(update)

        if not is_member:
            await update.message.reply_text(
                "❌ 你还不是会员，无法使用查询功能\n\n"
                "使用 /buy 购买会员"
            )
            return

        if not group:
            await update.message.reply_text("❌ 此功能仅在群组中使用")
            return

        # 获取今日统计
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        summary = await db.get_records_summary(group.id, start_date=today_start)

        settings = await db.get_group_settings(group.id)

        # 计算手续费
        fee = summary['expense_total'] * settings.fee_rate

        # 未下发金额
        undelivered = summary['income_total'] - summary['expense_total']

        response = f"""
📊 今日记账统计

💰 入款总额：{summary['income_total']:.2f} {settings.currency}
💸 出款总额：{summary['expense_total']:.2f} {settings.currency}
🔄 余额调整：{summary['balance_adjustments']:+.2f} {settings.currency}
💵 当前余额：{summary['balance']:.2f} {settings.currency}
🎯 未下发：{undelivered:.2f} {settings.currency}
💳 手续费({settings.fee_rate*100}%)：{fee:.2f} {settings.currency}

⚙️ 当前设置：
• 币种：{settings.currency}
• 默认汇率：{settings.exchange_rate}
• 费率：{settings.fee_rate*100}%
"""

        if settings.merchant_id:
            response += f"• 商户号：{settings.merchant_id}\n"

        response += f"\n💡 单笔交易可使用自定义汇率（如：+100 7.12）"

        await update.message.reply_text(response)

    async def set_exchange_rate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """设置汇率"""
        user, group, is_member, is_operator, _ = await self.check_permission(update)

        if not is_member or not is_operator:
            await update.message.reply_text("❌ 权限不足")
            return

        match = re.search(r'[\d.]+', update.message.text)
        if match:
            rate = float(match.group())
            await db.update_group_settings(group.id, exchange_rate=rate)
            await update.message.reply_text(f"✅ 汇率已设置为：{rate}")

    async def set_fee_rate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """设置费率"""
        user, group, is_member, is_operator, _ = await self.check_permission(update)

        if not is_member or not is_operator:
            await update.message.reply_text("❌ 权限不足")
            return

        match = re.search(r'[\d.]+', update.message.text)
        if match:
            rate = float(match.group())
            await db.update_group_settings(group.id, fee_rate=rate)
            await update.message.reply_text(f"✅ 费率已设置为：{rate*100}%")

    async def set_currency(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """设置币种"""
        user, group, is_member, is_operator, _ = await self.check_permission(update)

        if not is_member or not is_operator:
            await update.message.reply_text("❌ 权限不足")
            return

        match = re.search(r'\w+$', update.message.text)
        if match:
            currency = match.group().upper()
            if currency in config.SUPPORTED_CURRENCIES:
                await db.update_group_settings(group.id, currency=currency)
                await update.message.reply_text(f"✅ 币种已设置为：{currency}")
            else:
                await update.message.reply_text(f"❌ 不支持的币种：{currency}")

    async def set_merchant_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """设置商户号"""
        user, group, is_member, is_operator, _ = await self.check_permission(update)

        if not is_member or not is_operator:
            await update.message.reply_text("❌ 权限不足")
            return

        merchant_id = update.message.text.replace('设置商户号', '').strip()
        await db.update_group_settings(group.id, merchant_id=merchant_id)
        await update.message.reply_text(f"✅ 商户号已设置为：{merchant_id}")

    async def calculator(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """计算器功能"""
        user, group, is_member, _, _ = await self.check_permission(update)

        if group:
            settings = await db.get_group_settings(group.id)
            if not settings.calculator_enabled:
                return

        text = update.message.text.strip()

        # 排除记账命令
        if any(keyword in text for keyword in ['入款', '出款', '上行', '下发', '余额']):
            return

        # 排除查询命令
        if text in ['查', 'c', 'C']:
            return

        try:
            # 替换^为**（Python的幂运算符）
            expression = text.replace('^', '**')
            # 安全计算
            result = eval(expression, {"__builtins__": {}}, {})
            await update.message.reply_text(f"🧮 计算结果：{result}")
        except:
            pass

    async def toggle_calculator(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """开启/关闭计算器"""
        user, group, is_member, is_operator, _ = await self.check_permission(update)

        if not is_member or not is_operator:
            await update.message.reply_text("❌ 权限不足")
            return

        text = update.message.text
        enabled = '开启' in text

        await db.update_group_settings(group.id, calculator_enabled=enabled)
        status = "开启" if enabled else "关闭"
        await update.message.reply_text(f"✅ 计算器已{status}")

    async def query_usdt_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """查询USDT价格"""
        text = update.message.text.lower()

        price_map = {
            'z0': ('支付宝', 7.28),
            'w0': ('微信', 7.25),
            'b0': ('银行卡', 7.30),
            'k0': ('银行卡', 7.30),
            't0': ('泰铢', 35.5),
            'e0': ('欧元', 0.92),
            'p0': ('比索', 57.8),
            'y0': ('英镑', 0.79)
        }

        if text in price_map:
            name, price = price_map[text]
            await update.message.reply_text(
                f"💵 USDT {name}收款价格\n"
                f"💰 当前价格：{price}\n"
                f"⏰ 更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

    # ========== 按钮回调辅助函数 ==========

    async def _handle_apply_trial(self, query, user):
        """处理申请试用按钮"""
        # 创建或获取用户
        db_user = await db.get_or_create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )

        keyboard = [[InlineKeyboardButton("🔙 返回主菜单", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # 给用户发送确认消息
        await query.edit_message_text(
            "✅ 您的试用申请已提交\n\n"
            "请耐心等待管理员审核\n"
            "审核通过后将自动通知您",
            reply_markup=reply_markup
        )

        # 通知所有管理员
        for admin_id in config.ADMIN_IDS:
            try:
                await self.app.bot.send_message(
                    chat_id=admin_id,
                    text=f"📋 申请试用\n"
                         f"用户ID：{user.id}\n"
                         f"用户名：{user.username or '无'}\n"
                         f"用户名称：{user.first_name or ''}{' ' + user.last_name if user.last_name else ''}\n\n"
                         f"💡 授权命令：\n"
                         f"授权 {user.id} 天数"
                )
            except Exception as e:
                logger.error(f"通知管理员失败: {e}")

    async def _show_buy_membership(self, query, user):
        """显示购买会员界面"""
        keyboard = [
            [InlineKeyboardButton(
                f"30天会员 - {config.MEMBERSHIP_PRICE_30_DAYS} USDT",
                callback_data=f"buy_30_{user.id}"
            )],
            [InlineKeyboardButton(
                f"90天会员 - {config.MEMBERSHIP_PRICE_90_DAYS} USDT",
                callback_data=f"buy_90_{user.id}"
            )],
            [InlineKeyboardButton(
                f"365天会员 - {config.MEMBERSHIP_PRICE_365_DAYS} USDT",
                callback_data=f"buy_365_{user.id}"
            )],
            [InlineKeyboardButton("🔙 返回", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "💎 选择会员套餐：\n\n"
            "会员权益：\n"
            "✅ 无限群组使用\n"
            "✅ 完整记账功能\n"
            "✅ 数据统计分析\n"
            "✅ 优先技术支持\n\n"
            "请选择购买时长：",
            reply_markup=reply_markup
        )

    async def _show_my_info(self, query, user):
        """显示我的信息"""
        db_user = await db.get_user_by_telegram_id(user.id)

        if db_user.membership_expires_at:
            expires_str = db_user.membership_expires_at.strftime('%Y-%m-%d %H:%M:%S')
            days_left = db_user.get_membership_days_left()
            status = "✅ 有效" if db_user.is_member_active() else "❌ 已过期"
        else:
            expires_str = "未开通"
            days_left = 0
            status = "❌ 未开通"

        keyboard = [[InlineKeyboardButton("🔙 返回主菜单", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"👤 个人信息\n\n"
            f"🆔 用户ID：{user.id}\n"
            f"📛 用户名：@{user.username or '未设置'}\n"
            f"💎 会员状态：{status}\n"
            f"📅 到期时间：{expires_str}\n"
            f"⏰ 剩余天数：{days_left}天\n"
            f"👑 管理员：{'是' if db_user.is_admin else '否'}",
            reply_markup=reply_markup
        )

    async def _show_tutorial(self, query):
        """显示使用教程"""
        keyboard = [[InlineKeyboardButton("🔙 返回主菜单", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        tutorial_text = """
📖 使用教程

【记账功能】
入款：+100、入款100、上行100
出款：-100、出款100、下发100
余额调整：余额+100、余额-100
USDT记账：在金额后加u，如+100u
支持小数：+100.5、-88.88

💡 单笔自定义汇率：
+100 7.12 - 入款100，汇率7.12
-200 7.15 - 出款200，汇率7.15
+100u 7.12 - USDT入款，汇率7.12

【查询统计】
发送"查"或"c"：
• 入款总额及明细
• 出款总额及明细
• 余额调整记录
• 当前余额
• 手续费计算

【群组设置】
设置汇率 7.2（设置默认汇率）
设置费率 0.01（1%手续费）
设置币种 JPY
设置商户号 12345

【USDT价格】
z0 - 支付宝收款价
w0 - 微信收款价
b0/k0 - 银行卡收款价
t0/e0/p0/y0 - 泰铢/欧元/比索/英镑

【计算器】
直接发送算式：100*7.2+50
支持：+ - * / ^ ( )
开启计算器 / 关闭计算器

💡 更多帮助请访问Web后台
"""
        await query.edit_message_text(tutorial_text, reply_markup=reply_markup)

    async def _show_my_stats(self, query, user):
        """显示我的统计（需要在群组中使用）"""
        keyboard = [[InlineKeyboardButton("🔙 返回主菜单", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "📊 查看统计\n\n"
            "请在群组中发送"查"或"c"查看记账统计\n\n"
            "或访问Web账单系统查看详细数据",
            reply_markup=reply_markup
        )

    async def _show_admin_panel(self, query, user):
        """显示管理员面板"""
        db_user = await db.get_user_by_telegram_id(user.id)

        if not db_user or not db_user.is_admin:
            await query.answer("❌ 权限不足", show_alert=True)
            return

        keyboard = [
            [
                InlineKeyboardButton("👥 用户列表", callback_data="admin_users"),
                InlineKeyboardButton("💎 授权会员", callback_data="admin_authorize")
            ],
            [
                InlineKeyboardButton("🏢 群组列表", callback_data="admin_groups"),
                InlineKeyboardButton("📊 统计数据", callback_data="admin_stats")
            ],
            [
                InlineKeyboardButton("💰 支付记录", callback_data="admin_payments"),
                InlineKeyboardButton("⚙️ 系统设置", callback_data="admin_settings")
            ],
            [InlineKeyboardButton("🔙 返回主菜单", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "⚙️ 管理员控制面板\n\n"
            "请选择要执行的操作：",
            reply_markup=reply_markup
        )

    async def _back_to_menu(self, query, user):
        """返回主菜单"""
        db_user = await db.get_user_by_telegram_id(user.id)

        is_member = db_user.is_member_active() or db_user.is_admin
        days_left = db_user.get_membership_days_left()

        keyboard = []

        if is_member:
            membership_status = f"✅ 会员有效 (剩余{days_left}天)" if days_left > 0 else "✅ 永久会员"
        else:
            membership_status = "❌ 未开通会员"

        # 第一行：会员相关
        if not is_member:
            # 未开通会员，显示申请试用
            keyboard.append([
                InlineKeyboardButton("🎁 申请试用", callback_data="apply_trial_btn"),
                InlineKeyboardButton("💎 购买会员", callback_data="buy_membership")
            ])
        else:
            # 已开通会员
            keyboard.append([
                InlineKeyboardButton("💎 续费会员", callback_data="buy_membership"),
                InlineKeyboardButton("👤 我的信息", callback_data="my_info")
            ])

        # 第二行：功能按钮
        keyboard.append([
            InlineKeyboardButton("📖 使用教程", callback_data="tutorial"),
            InlineKeyboardButton("📊 查看统计", callback_data="view_stats")
        ])

        keyboard.append([
            InlineKeyboardButton("🌐 Web账单查询", url=f"http://{config.WEBHOOK_HOST}:52000"),
            InlineKeyboardButton("🎛️ 管理后台", url=f"http://{config.WEBHOOK_HOST}:38888")
        ])

        if db_user.is_admin:
            keyboard.append([
                InlineKeyboardButton("⚙️ 管理员面板", callback_data="admin_panel")
            ])

        reply_markup = InlineKeyboardMarkup(keyboard)

        welcome_text = f"""
🎉 欢迎使用智能记账机器人！

👤 用户：{user.first_name} (@{user.username or user.id})
💎 会员状态：{membership_status}

📝 快速记账：
• 入款：+100 或 入款100
• 出款：-100 或 出款100
• 余额：余额+100
• USDT：+100u

📊 查看统计：发送"查"或"c"

💡 点击下方按钮探索更多功能
"""
        await query.edit_message_text(welcome_text, reply_markup=reply_markup)

    # ========== 管理员面板辅助函数 ==========

    async def _admin_show_users(self, query, user):
        """显示用户列表（简略版）"""
        db_user = await db.get_user_by_telegram_id(user.id)
        if not db_user or not db_user.is_admin:
            await query.answer("❌ 权限不足", show_alert=True)
            return

        async with db.async_session() as session:
            from sqlalchemy.future import select
            from sqlalchemy import func
            from database import User

            # 统计用户数
            result = await session.execute(select(func.count(User.id)))
            total_users = result.scalar()

            # 统计活跃会员
            now = datetime.now()
            result = await session.execute(
                select(func.count(User.id)).where(User.membership_expires_at > now)
            )
            active_members = result.scalar()

        keyboard = [[InlineKeyboardButton("🔙 返回管理面板", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"👥 用户统计\n\n"
            f"📊 总用户数：{total_users}\n"
            f"💎 活跃会员：{active_members}\n\n"
            f"💡 详细用户列表请访问Web后台：\n"
            f"http://{config.WEBHOOK_HOST}:38888",
            reply_markup=reply_markup
        )

    async def _admin_show_authorize(self, query):
        """显示授权说明"""
        keyboard = [[InlineKeyboardButton("🔙 返回管理面板", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "💎 授权会员\n\n"
            "使用命令格式：\n"
            "/authorize @用户名 天数\n\n"
            "示例：\n"
            "/authorize @jdccc 30\n\n"
            "或通过Web后台进行授权：\n"
            f"http://{config.WEBHOOK_HOST}:38888",
            reply_markup=reply_markup
        )

    async def _admin_show_groups(self, query, user):
        """显示群组统计"""
        db_user = await db.get_user_by_telegram_id(user.id)
        if not db_user or not db_user.is_admin:
            await query.answer("❌ 权限不足", show_alert=True)
            return

        async with db.async_session() as session:
            from sqlalchemy.future import select
            from sqlalchemy import func
            from database import GroupChat, BookkeepingRecord

            result = await session.execute(select(func.count(GroupChat.id)))
            total_groups = result.scalar()

            result = await session.execute(select(func.count(BookkeepingRecord.id)))
            total_records = result.scalar()

        keyboard = [[InlineKeyboardButton("🔙 返回管理面板", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"🏢 群组统计\n\n"
            f"📊 总群组数：{total_groups}\n"
            f"📝 总记账数：{total_records}\n\n"
            f"💡 详细群组列表请访问Web后台",
            reply_markup=reply_markup
        )

    async def _admin_show_stats(self, query, user):
        """显示系统统计"""
        db_user = await db.get_user_by_telegram_id(user.id)
        if not db_user or not db_user.is_admin:
            await query.answer("❌ 权限不足", show_alert=True)
            return

        async with db.async_session() as session:
            from sqlalchemy.future import select
            from sqlalchemy import func
            from database import User, GroupChat, BookkeepingRecord, Payment

            # 总用户数
            result = await session.execute(select(func.count(User.id)))
            total_users = result.scalar()

            # 活跃会员
            now = datetime.now()
            result = await session.execute(
                select(func.count(User.id)).where(User.membership_expires_at > now)
            )
            active_members = result.scalar()

            # 总群组数
            result = await session.execute(select(func.count(GroupChat.id)))
            total_groups = result.scalar()

            # 今日记账数
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            result = await session.execute(
                select(func.count(BookkeepingRecord.id)).where(
                    BookkeepingRecord.created_at >= today_start
                )
            )
            today_records = result.scalar()

            # 总支付订单
            result = await session.execute(select(func.count(Payment.id)))
            total_payments = result.scalar()

        keyboard = [[InlineKeyboardButton("🔙 返回管理面板", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"📊 系统统计\n\n"
            f"👥 总用户数：{total_users}\n"
            f"💎 活跃会员：{active_members}\n"
            f"🏢 总群组数：{total_groups}\n"
            f"📝 今日记账：{today_records} 笔\n"
            f"💰 总订单数：{total_payments}\n\n"
            f"⏰ 统计时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            reply_markup=reply_markup
        )

    async def _admin_show_payments(self, query, user):
        """显示支付记录"""
        db_user = await db.get_user_by_telegram_id(user.id)
        if not db_user or not db_user.is_admin:
            await query.answer("❌ 权限不足", show_alert=True)
            return

        async with db.async_session() as session:
            from sqlalchemy.future import select
            from sqlalchemy import func
            from database import Payment

            result = await session.execute(select(func.count(Payment.id)))
            total = result.scalar()

            result = await session.execute(
                select(func.count(Payment.id)).where(Payment.status == 'success')
            )
            success = result.scalar()

            result = await session.execute(
                select(func.count(Payment.id)).where(Payment.status == 'pending')
            )
            pending = result.scalar()

        keyboard = [[InlineKeyboardButton("🔙 返回管理面板", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"💰 支付记录统计\n\n"
            f"📊 总订单数：{total}\n"
            f"✅ 成功支付：{success}\n"
            f"⏳ 待支付：{pending}\n\n"
            f"💡 详细支付记录请访问Web后台",
            reply_markup=reply_markup
        )

    async def _admin_show_settings(self, query):
        """显示系统设置"""
        keyboard = [[InlineKeyboardButton("🔙 返回管理面板", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"⚙️ 系统设置\n\n"
            f"💎 会员套餐价格：\n"
            f"• 30天：{config.MEMBERSHIP_PRICE_30_DAYS} USDT\n"
            f"• 90天：{config.MEMBERSHIP_PRICE_90_DAYS} USDT\n"
            f"• 365天：{config.MEMBERSHIP_PRICE_365_DAYS} USDT\n\n"
            f"🌐 Web服务：\n"
            f"• 账单查询：端口 {config.WEB_BILL_PORT}\n"
            f"• 管理后台：端口 {config.WEB_ADMIN_PORT}\n\n"
            f"💡 修改价格请编辑 .env 文件",
            reply_markup=reply_markup
        )

    async def run(self):
        """运行机器人"""
        # 初始化数据库
        await db.init_db()

        # 启动机器人
        logger.info("机器人启动中...")
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()

        logger.info("机器人已启动！")


if __name__ == '__main__':
    import asyncio

    bot = BookkeepingBot()
    asyncio.run(bot.run())
