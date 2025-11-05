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
        self.app.add_handler(CommandHandler("help", self.help_command))

        # 管理员命令
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

        # 记账命令（入款、出款、余额调整）
        self.app.add_handler(MessageHandler(
            filters.TEXT & filters.Regex(r'^[+＋][\d.]+[uU]?$'),
            self.add_income
        ))
        self.app.add_handler(MessageHandler(
            filters.TEXT & filters.Regex(r'^(入款|上行)\s*[\d.]+[uU]?$'),
            self.add_income
        ))
        self.app.add_handler(MessageHandler(
            filters.TEXT & filters.Regex(r'^[-－][\d.]+[uU]?$'),
            self.add_expense
        ))
        self.app.add_handler(MessageHandler(
            filters.TEXT & filters.Regex(r'^(出款|下发)\s*[\d.]+[uU]?$'),
            self.add_expense
        ))
        self.app.add_handler(MessageHandler(
            filters.TEXT & filters.Regex(r'^余额[+＋－-][\d.]+[uU]?$'),
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

        # 回调查询处理
        self.app.add_handler(CallbackQueryHandler(self.button_callback))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /start 命令"""
        user = update.effective_user

        # 创建或获取用户
        await db.get_or_create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )

        welcome_text = """
🎉 欢迎使用记账机器人！

📝 基础记账：
• 入款：+100 或 入款100 或 上行100
• 出款：-100 或 出款100 或 下发100
• 余额调整：余额+100 或 余额-100
• USDT记账：金额后加u，如 +100u

💰 USDT价格查询：
• z0 - 支付宝价格
• w0 - 微信价格
• b0/k0 - 银行卡价格

📊 查询统计：
• 发送"查"或"c"查看记账统计

⚙️ 群组设置（需操作员权限）：
• 设置汇率 7.2
• 设置费率 0.01
• 设置币种 CNY
• 设置商户号 12345

🧮 计算器：
• 直接发送算式：100*7.2+50

💎 会员功能：
• /buy - 购买会员
• 授权后可在多个群使用

使用 /help 查看详细帮助
"""
        await update.message.reply_text(welcome_text)

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

【查询统计】
发送"查"或"c"：
• 入款总额及明细
• 出款总额及明细
• 余额调整记录
• 当前余额
• 手续费计算

【群组设置】
设置汇率 7.2
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

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理按钮回调"""
        query = update.callback_query
        await query.answer()

        data = query.data

        if data.startswith('buy_'):
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

        # 解析金额
        match = re.search(r'[\d.]+', text)
        if not match:
            return

        amount = float(match.group())
        is_usdt = text.lower().endswith('u')

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
            message_id=update.message.message_id
        )

        await update.message.reply_text(
            f"✅ 入款记录已添加\n"
            f"💰 金额：{amount} {currency}"
        )

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

        # 解析金额
        match = re.search(r'[\d.]+', text)
        if not match:
            return

        amount = float(match.group())
        is_usdt = text.lower().endswith('u')

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
            message_id=update.message.message_id
        )

        await update.message.reply_text(
            f"✅ 出款记录已添加\n"
            f"💰 金额：{amount} {currency}"
        )

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

        # 解析金额（带正负号）
        match = re.search(r'[+＋－-][\d.]+', text)
        if not match:
            return

        amount_str = match.group()
        # 统一符号
        amount_str = amount_str.replace('＋', '+').replace('－', '-')
        amount = float(amount_str)
        is_usdt = text.lower().endswith('u')

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
            message_id=update.message.message_id
        )

        action = "增加" if amount > 0 else "减少"
        await update.message.reply_text(
            f"✅ 余额已{action}\n"
            f"💰 金额：{amount:+.2f} {currency}"
        )

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
• 汇率：{settings.exchange_rate}
• 费率：{settings.fee_rate*100}%
"""

        if settings.merchant_id:
            response += f"• 商户号：{settings.merchant_id}\n"

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
