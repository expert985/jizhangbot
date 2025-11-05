from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, BigInteger, Text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select
from sqlalchemy import and_, func
import config

Base = declarative_base()

class User(Base):
    """用户表"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    is_admin = Column(Boolean, default=False)
    membership_expires_at = Column(DateTime, nullable=True)  # 会员到期时间
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def is_member_active(self) -> bool:
        """检查会员是否有效"""
        if not self.membership_expires_at:
            return False
        return datetime.now() < self.membership_expires_at

    def get_membership_days_left(self) -> int:
        """获取会员剩余天数"""
        if not self.membership_expires_at:
            return 0
        delta = self.membership_expires_at - datetime.now()
        return max(0, delta.days)


class GroupChat(Base):
    """群组表"""
    __tablename__ = 'group_chats'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    title = Column(String(255))
    is_active = Column(Boolean, default=True)  # 是否激活机器人
    owner_id = Column(Integer, ForeignKey('users.id'))  # 群主
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class GroupOperator(Base):
    """群组操作员表"""
    __tablename__ = 'group_operators'

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('group_chats.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.now)


class GroupSettings(Base):
    """群组设置表"""
    __tablename__ = 'group_settings'

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('group_chats.id'), unique=True, nullable=False)
    currency = Column(String(10), default=config.DEFAULT_CURRENCY)  # 币种
    exchange_rate = Column(Float, default=config.DEFAULT_EXCHANGE_RATE)  # 汇率
    fee_rate = Column(Float, default=config.DEFAULT_FEE_RATE)  # 费率
    merchant_id = Column(String(100))  # 商户号
    calculator_enabled = Column(Boolean, default=True)  # 是否启用计算器
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class BookkeepingRecord(Base):
    """记账记录表"""
    __tablename__ = 'bookkeeping_records'

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('group_chats.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    record_type = Column(String(20), nullable=False)  # income(入款), expense(出款), balance(余额调整)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default='CNY')
    is_usdt = Column(Boolean, default=False)  # 是否为USDT记账
    exchange_rate = Column(Float, nullable=True)  # 单笔交易汇率（可选，为空时使用群组默认汇率）
    description = Column(Text)
    message_id = Column(BigInteger)  # Telegram消息ID
    created_at = Column(DateTime, default=datetime.now, index=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Payment(Base):
    """支付记录表"""
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    order_id = Column(String(100), unique=True, nullable=False)  # OKPAY订单号
    unique_id = Column(String(100), unique=True)  # 我们的唯一订单号
    amount = Column(Float, nullable=False)
    coin = Column(String(10), default='USDT')
    days = Column(Integer, nullable=False)  # 购买天数
    status = Column(String(20), default='pending')  # pending, success, failed
    pay_user_id = Column(BigInteger)  # 支付的用户TG ID
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Database:
    """数据库操作类"""

    def __init__(self):
        self.engine = create_async_engine(config.DATABASE_URL, echo=False)
        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init_db(self):
        """初始化数据库"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_session(self) -> AsyncSession:
        """获取数据库会话"""
        async with self.async_session() as session:
            return session

    # User operations
    async def get_or_create_user(self, telegram_id: int, username: str = None,
                                  first_name: str = None, last_name: str = None) -> User:
        """获取或创建用户"""
        async with self.async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    is_admin=(telegram_id in config.ADMIN_IDS)
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
            else:
                # 更新用户信息
                user.username = username
                user.first_name = first_name
                user.last_name = last_name
                await session.commit()
                await session.refresh(user)

            return user

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """根据Telegram ID获取用户"""
        async with self.async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        username = username.lstrip('@')
        async with self.async_session() as session:
            result = await session.execute(
                select(User).where(User.username == username)
            )
            return result.scalar_one_or_none()

    async def extend_membership(self, user_id: int, days: int):
        """延长用户会员时间"""
        async with self.async_session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if user:
                now = datetime.now()
                if user.membership_expires_at and user.membership_expires_at > now:
                    # 如果会员还未过期，在现有基础上延长
                    user.membership_expires_at += timedelta(days=days)
                else:
                    # 如果已过期或首次开通，从现在开始计算
                    user.membership_expires_at = now + timedelta(days=days)
                await session.commit()

    # Group operations
    async def get_or_create_group(self, telegram_id: int, title: str = None,
                                   owner_id: int = None) -> GroupChat:
        """获取或创建群组"""
        async with self.async_session() as session:
            result = await session.execute(
                select(GroupChat).where(GroupChat.telegram_id == telegram_id)
            )
            group = result.scalar_one_or_none()

            if not group:
                group = GroupChat(
                    telegram_id=telegram_id,
                    title=title,
                    owner_id=owner_id
                )
                session.add(group)
                await session.commit()
                await session.refresh(group)

                # 创建默认设置
                settings = GroupSettings(group_id=group.id)
                session.add(settings)
                await session.commit()
            else:
                # 更新群组信息
                if title:
                    group.title = title
                await session.commit()
                await session.refresh(group)

            return group

    async def get_group_settings(self, group_id: int) -> Optional[GroupSettings]:
        """获取群组设置"""
        async with self.async_session() as session:
            result = await session.execute(
                select(GroupSettings).where(GroupSettings.group_id == group_id)
            )
            return result.scalar_one_or_none()

    async def update_group_settings(self, group_id: int, **kwargs):
        """更新群组设置"""
        async with self.async_session() as session:
            result = await session.execute(
                select(GroupSettings).where(GroupSettings.group_id == group_id)
            )
            settings = result.scalar_one_or_none()

            if settings:
                for key, value in kwargs.items():
                    if hasattr(settings, key):
                        setattr(settings, key, value)
                await session.commit()

    async def is_group_operator(self, group_id: int, user_id: int) -> bool:
        """检查用户是否是群组操作员"""
        async with self.async_session() as session:
            result = await session.execute(
                select(GroupOperator).where(
                    and_(
                        GroupOperator.group_id == group_id,
                        GroupOperator.user_id == user_id
                    )
                )
            )
            return result.scalar_one_or_none() is not None

    async def add_group_operator(self, group_id: int, user_id: int):
        """添加群组操作员"""
        async with self.async_session() as session:
            # 检查是否已存在
            result = await session.execute(
                select(GroupOperator).where(
                    and_(
                        GroupOperator.group_id == group_id,
                        GroupOperator.user_id == user_id
                    )
                )
            )
            if not result.scalar_one_or_none():
                operator = GroupOperator(group_id=group_id, user_id=user_id)
                session.add(operator)
                await session.commit()

    # Bookkeeping operations
    async def add_record(self, group_id: int, user_id: int, record_type: str,
                        amount: float, currency: str = 'CNY', is_usdt: bool = False,
                        exchange_rate: float = None, description: str = None,
                        message_id: int = None) -> BookkeepingRecord:
        """添加记账记录"""
        async with self.async_session() as session:
            record = BookkeepingRecord(
                group_id=group_id,
                user_id=user_id,
                record_type=record_type,
                amount=amount,
                currency=currency,
                is_usdt=is_usdt,
                exchange_rate=exchange_rate,
                description=description,
                message_id=message_id
            )
            session.add(record)
            await session.commit()
            await session.refresh(record)
            return record

    async def get_records_summary(self, group_id: int, start_date: datetime = None,
                                  end_date: datetime = None):
        """获取记账汇总"""
        async with self.async_session() as session:
            query = select(BookkeepingRecord).where(BookkeepingRecord.group_id == group_id)

            if start_date:
                query = query.where(BookkeepingRecord.created_at >= start_date)
            if end_date:
                query = query.where(BookkeepingRecord.created_at <= end_date)

            result = await session.execute(query.order_by(BookkeepingRecord.created_at.desc()))
            records = result.scalars().all()

            # 计算汇总
            income_total = sum(r.amount for r in records if r.record_type == 'income')
            expense_total = sum(r.amount for r in records if r.record_type == 'expense')
            balance_adjustments = sum(r.amount for r in records if r.record_type == 'balance')

            return {
                'records': records,
                'income_total': income_total,
                'expense_total': expense_total,
                'balance_adjustments': balance_adjustments,
                'balance': income_total - expense_total + balance_adjustments
            }

    async def delete_record(self, record_id: int, user_id: int) -> bool:
        """删除记账记录（仅限记录创建者）"""
        async with self.async_session() as session:
            result = await session.execute(
                select(BookkeepingRecord).where(
                    and_(
                        BookkeepingRecord.id == record_id,
                        BookkeepingRecord.user_id == user_id
                    )
                )
            )
            record = result.scalar_one_or_none()
            if record:
                await session.delete(record)
                await session.commit()
                return True
            return False

    # Payment operations
    async def create_payment(self, user_id: int, unique_id: str, amount: float,
                           days: int, coin: str = 'USDT') -> Payment:
        """创建支付记录"""
        async with self.async_session() as session:
            payment = Payment(
                user_id=user_id,
                order_id='',  # 将在获取OKPAY订单号后更新
                unique_id=unique_id,
                amount=amount,
                coin=coin,
                days=days
            )
            session.add(payment)
            await session.commit()
            await session.refresh(payment)
            return payment

    async def update_payment_order_id(self, unique_id: str, order_id: str):
        """更新支付记录的OKPAY订单号"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Payment).where(Payment.unique_id == unique_id)
            )
            payment = result.scalar_one_or_none()
            if payment:
                payment.order_id = order_id
                await session.commit()

    async def get_payment_by_order_id(self, order_id: str) -> Optional[Payment]:
        """根据订单号获取支付记录"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Payment).where(Payment.order_id == order_id)
            )
            return result.scalar_one_or_none()

    async def complete_payment(self, order_id: str, pay_user_id: int):
        """完成支付"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Payment).where(Payment.order_id == order_id)
            )
            payment = result.scalar_one_or_none()
            if payment:
                payment.status = 'success'
                payment.pay_user_id = pay_user_id
                await session.commit()
                await session.refresh(payment)
                return payment
            return None


# 全局数据库实例
db = Database()
