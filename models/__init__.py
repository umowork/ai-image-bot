from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, event, func, select
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str] = mapped_column(String(128))
    balance: Mapped[float] = mapped_column(default=0.0)
    referral_code: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    referred_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    referrals: Mapped[list[User]] = relationship(
        "User", back_populates="referrer",
        foreign_keys="User.referred_by",
    )
    referrer: Mapped[User | None] = relationship(
        "User", back_populates="referrals",
        foreign_keys="User.referred_by",
        remote_side="User.id",
    )
    generations: Mapped[list[Generation]] = relationship(back_populates="user")
    payments: Mapped[list[Payment]] = relationship(back_populates="user")


class Generation(Base):
    __tablename__ = "generations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    type: Mapped[str] = mapped_column(String(16))  # image | video
    prompt: Mapped[str] = mapped_column(String(4096))
    result_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    cost: Mapped[float] = mapped_column(default=0.0)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped[User] = relationship(back_populates="generations")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    yookassa_payment_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    amount: Mapped[float] = mapped_column()
    currency: Mapped[str] = mapped_column(String(3), default="RUB")
    status: Mapped[str] = mapped_column(String(16), default="pending")
    description: Mapped[str] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped[User] = relationship(back_populates="payments")


class Database:
    def __init__(self, database_url: str):
        self.engine = create_async_engine(database_url, echo=False)
        # SQLite WAL mode for concurrent reads
        @event.listens_for(self.engine, "connect")
        def _set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA busy_timeout=10000")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def create_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_or_create_user(
        self, telegram_id: int, username: str | None, full_name: str,
        referral_code_from: str | None = None,
    ) -> User:
        async with self.session_factory() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            if user is None:
                import secrets
                referral_code = secrets.token_urlsafe(8)[:10]
                referred_by = None
                if referral_code_from:
                    ref = await session.execute(
                        select(User).where(User.referral_code == referral_code_from)
                    )
                    ref_user = ref.scalar_one_or_none()
                    if ref_user:
                        referred_by = ref_user.id
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    full_name=full_name,
                    referral_code=referral_code,
                    referred_by=referred_by,
                    balance=10.0,  # welcome bonus
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
                # Reward referrer
                if user.referred_by:
                    ref_user_obj = await session.get(User, user.referred_by)
                    if ref_user_obj:
                        ref_user_obj.balance += 5.0  # referral bonus
                        await session.commit()
            return user

    async def get_user_by_telegram_id(self, telegram_id: int) -> User | None:
        async with self.session_factory() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            return result.scalar_one_or_none()

    async def add_balance(self, user_id: int, amount: float) -> User:
        async with self.session_factory() as session:
            user = await session.get(User, user_id)
            user.balance += amount
            await session.commit()
            await session.refresh(user)
            return user

    async def deduct_balance(self, user_id: int, amount: float) -> bool:
        async with self.session_factory() as session:
            user = await session.get(User, user_id)
            if user.balance < amount:
                return False
            user.balance -= amount
            await session.commit()
            await session.refresh(user)
            return True

    async def add_generation(
        self, user_id: int, gen_type: str, prompt: str, cost: float
    ) -> Generation:
        async with self.session_factory() as session:
            gen = Generation(
                user_id=user_id, type=gen_type, prompt=prompt, cost=cost
            )
            session.add(gen)
            await session.commit()
            await session.refresh(gen)
            return gen

    async def update_generation(
        self, gen_id: int, result_url: str, status: str = "done"
    ) -> None:
        async with self.session_factory() as session:
            gen = await session.get(Generation, gen_id)
            gen.result_url = result_url
            gen.status = status
            await session.commit()

    async def get_user_generations(
        self, user_id: int, limit: int = 10
    ) -> list[Generation]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Generation)
                .where(Generation.user_id == user_id)
                .order_by(Generation.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())

    async def get_user_payments(self, user_id: int) -> list[Payment]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Payment)
                .where(Payment.user_id == user_id)
                .order_by(Payment.created_at.desc())
            )
            return list(result.scalars().all())

    async def get_all_users(self) -> list[User]:
        async with self.session_factory() as session:
            result = await session.execute(select(User))
            return list(result.scalars().all())

    async def get_payment_by_yookassa_id(self, yookassa_id: str) -> Payment | None:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Payment).where(Payment.yookassa_payment_id == yookassa_id)
            )
            return result.scalar_one_or_none()

    async def update_payment_status(
        self, payment_id: int, status: str, yookassa_id: str | None = None
    ) -> Payment:
        async with self.session_factory() as session:
            pmt = await session.get(Payment, payment_id)
            if yookassa_id:
                pmt.yookassa_payment_id = yookassa_id
            pmt.status = status
            await session.commit()
            await session.refresh(pmt)
            return pmt

    async def create_payment_record(
        self, user_id: int, amount: float, description: str,
        yookassa_id: str | None = None,
    ) -> Payment:
        async with self.session_factory() as session:
            pmt = Payment(
                user_id=user_id,
                amount=amount,
                description=description,
                yookassa_payment_id=yookassa_id,
            )
            session.add(pmt)
            await session.commit()
            await session.refresh(pmt)
            return pmt

    async def get_stats(self) -> dict:
        async with self.session_factory() as session:
            users_count = await session.execute(select(func.count(User.id)))
            generations_count = await session.execute(
                select(func.count(Generation.id))
            )
            payments_sum = await session.execute(
                select(func.sum(Payment.amount)).where(Payment.status == "succeeded")
            )
            return {
                "users": users_count.scalar(),
                "generations": generations_count.scalar(),
                "revenue": payments_sum.scalar() or 0.0,
            }
