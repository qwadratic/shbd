from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import Column, String, DateTime, BigInteger, and_, create_engine, or_, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, timezone

from config import read_config

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    user_id = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=True)
    display_name = Column(String)
    join_date = Column(DateTime, default=datetime.utcnow)
    last_paid = Column(DateTime, nullable=True)
    last_notified = Column(DateTime, nullable=datetime.utcnow)

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'display_name': self.display_name,
            'join_date': self.join_date.strftime('%Y-%m-%d %H:%M:%S'),
            'last_paid': self.last_paid.strftime('%Y-%m-%d %H:%M:%S') if self.last_paid else None,
            'last_notified': self.last_notified.strftime('%Y-%m-%d %H:%M:%S') if self.last_notified else None
        }

def init_db():
    config = read_config()
    engine = create_engine(f'sqlite:///{config['database']['path']}')
    Base.metadata.create_all(engine)

def get_session():
    config = read_config()
    engine = create_engine(f'sqlite:///{config['database']['path']}')
    Session = sessionmaker(bind=engine)
    session = Session()
    return session

async def async_init_db():
    config = read_config()
    engine = create_async_engine(f'sqlite+aiosqlite:///{config["database"]["path"]}')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_async_session() -> AsyncSession:
    config = read_config()
    engine = create_async_engine(f'sqlite+aiosqlite:///{config["database"]["path"]}')
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    return async_session()

async def get_users_without_payment():
    async with await get_async_session() as session:
        return await session.execute(
            select(User).where(
                or_(
                    User.last_paid < datetime.now(timezone.utc) - timedelta(days=30), 
                    User.last_paid == None)))

async def get_users_with_payment():
    q = select(User).where(
            and_(
                User.last_paid != None,
                User.last_paid > datetime.now(timezone.utc) - timedelta(days=30)))
    async with await get_async_session() as session:
        return await session.execute(q)
