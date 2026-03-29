#!/usr/bin/env python3
"""
数据库初始化脚本
运行此脚本来创建数据库表和初始数据
"""
from backend.core.database import init_db, init_roles_and_admin

if __name__ == "__main__":
    print("=" * 50)
    print("开始初始化数据库...")
    print("=" * 50)
    
    try:
        # 创建所有表
        init_db()
        
        # 初始化角色和管理员账户
        init_roles_and_admin()
        
        print("\n" + "=" * 50)
        print("数据库初始化完成！")
        print("=" * 50)
        print("\n默认管理员账户:")
        print("  用户名: admin")
        print("  密码: admin123")
        print("\n请在生产环境中修改默认密码！")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n初始化失败: {e}")
        import traceback
        traceback.print_exc()
