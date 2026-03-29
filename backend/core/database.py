"""
数据库配置和模型定义 - MySQL版本
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# MySQL数据库配置
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "root")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "multimodal_system")

# 构建数据库URL
DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"

# 如果设置了完整的DATABASE_URL环境变量，则使用它
if os.getenv("DATABASE_URL") and not os.getenv("DATABASE_URL").startswith("sqlite"):
    DATABASE_URL = os.getenv("DATABASE_URL")

print(f"数据库连接: mysql+pymysql://{MYSQL_USER}:***@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}")

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # 连接前检查连接是否有效
    pool_recycle=3600,       # 1小时后回收连接
    pool_size=10,            # 连接池大小
    max_overflow=20,         # 最大溢出连接数
    echo=False               # 不打印SQL语句
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()


# 数据库依赖
def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 角色表
class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    permissions = Column(JSON, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    users = relationship("User", back_populates="role")


# 用户表
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    status = Column(String(20), default="active", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # 关系
    role = relationship("Role", back_populates="users")
    audit_logs = relationship("AuditLog", back_populates="user")


# 操作日志表
class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    module = Column(String(50), nullable=False, index=True)
    action = Column(String(50), nullable=False)
    ip_address = Column(String(50))
    status = Column(String(20), nullable=False)
    details = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # 关系
    user = relationship("User", back_populates="audit_logs")


def init_db():
    """初始化数据库，创建所有表"""
    Base.metadata.create_all(bind=engine)
    print("数据库表创建成功")


def init_roles_and_admin():
    """初始化角色和管理员账户"""
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    db = SessionLocal()
    
    try:
        # 检查是否已经初始化
        existing_roles = db.query(Role).count()
        if existing_roles > 0:
            print("角色已存在，跳过初始化")
            return
        
        # 创建角色
        roles_data = [
            {
                "name": "admin",
                "permissions": {"all": True},
                "description": "管理员"
            },
            {
                "name": "algorithm_engineer",
                "permissions": {
                    "fusion": "rw",
                    "reconstruction": "rw",
                    "segmentation": "rw",
                    "reports": "r"
                },
                "description": "算法调试员"
            },
            {
                "name": "inspector",
                "permissions": {
                    "scenes": "rw",
                    "reports": "r"
                },
                "description": "现场巡检员"
            },
            {
                "name": "auditor",
                "permissions": {
                    "reports": "r",
                    "logs": "r"
                },
                "description": "数据审计员"
            }
        ]
        
        for role_data in roles_data:
            role = Role(**role_data)
            db.add(role)
        
        db.commit()
        print("角色初始化成功")
        
        # 创建默认管理员账户
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        admin_user = User(
            username="admin",
            password_hash=pwd_context.hash("admin123"),
            role_id=admin_role.id,
            status="active"
        )
        db.add(admin_user)
        db.commit()
        print("默认管理员账户创建成功 (用户名: admin, 密码: admin123)")
        
    except Exception as e:
        db.rollback()
        print(f"初始化失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("初始化数据库...")
    init_db()
    init_roles_and_admin()
    print("数据库初始化完成")
