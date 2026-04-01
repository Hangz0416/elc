#!/usr/bin/env python3
"""
创建测试报告数据
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.database import SessionLocal, AuditLog, User
from datetime import datetime, timedelta
import json
import random

def create_test_reports():
    """创建测试报告数据"""
    db = SessionLocal()
    
    try:
        # 获取管理员用户ID
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            print("错误: 找不到管理员用户")
            return
        
        user_id = admin_user.id
        print(f"使用用户: {admin_user.username} (ID: {user_id})")
        
        # 场景列表
        scenes = ["Building", "DailyStuff", "Dimsum", "Ebike", "IronIngot", "LandScape"]
        
        # 创建图像融合报告
        print("\n创建图像融合报告...")
        for i in range(10):
            scene = random.choice(scenes)
            created_at = datetime.now() - timedelta(days=random.randint(0, 30))
            duration = random.randint(30, 300)
            images_count = random.randint(5, 25)
            
            details = {
                "scene": scene,
                "duration": duration,
                "images_count": images_count,
                "metrics": {
                    "avg_ag": f"{random.uniform(5, 15):.2f}",
                    "avg_sd": f"{random.uniform(20, 70):.2f}",
                    "avg_vif": f"{random.uniform(0.5, 1.0):.3f}"
                },
                "output_path": f"/static/{scene}/fusion/"
            }
            
            log = AuditLog(
                user_id=user_id,
                module="fusion",
                action="fusion",
                ip_address="127.0.0.1",
                status="success",
                details=json.dumps(details, ensure_ascii=False),
                created_at=created_at
            )
            db.add(log)
            print(f"  创建融合报告: {scene}, {images_count}张图像")
        
        # 创建三维重建报告
        print("\n创建三维重建报告...")
        methods = ["MSMG", "MFTG", "OMMG"]
        for i in range(8):
            scene = random.choice(scenes)
            method = random.choice(methods)
            created_at = datetime.now() - timedelta(days=random.randint(0, 30))
            duration = random.randint(300, 1800)
            
            details = {
                "scene": scene,
                "duration": duration,
                "method": method,
                "output_path": f"/static/{scene}/reconstruction/"
            }
            
            log = AuditLog(
                user_id=user_id,
                module="reconstruction",
                action="reconstruction",
                ip_address="127.0.0.1",
                status="success",
                details=json.dumps(details, ensure_ascii=False),
                created_at=created_at
            )
            db.add(log)
            print(f"  创建重建报告: {scene}, 方法: {method}")
        
        # 创建场景分割报告
        print("\n创建场景分割报告...")
        for i in range(6):
            scene = random.choice(scenes)
            created_at = datetime.now() - timedelta(days=random.randint(0, 30))
            duration = random.randint(60, 600)
            
            details = {
                "scene": scene,
                "duration": duration,
                "output_path": f"/static/{scene}/segmentation/"
            }
            
            log = AuditLog(
                user_id=user_id,
                module="segmentation",
                action="segmentation",
                ip_address="127.0.0.1",
                status="success",
                details=json.dumps(details, ensure_ascii=False),
                created_at=created_at
            )
            db.add(log)
            print(f"  创建分割报告: {scene}")
        
        # 提交到数据库
        db.commit()
        print("\n✅ 成功创建 24 条测试报告！")
        
        # 统计
        fusion_count = db.query(AuditLog).filter(AuditLog.action == "fusion").count()
        reconstruction_count = db.query(AuditLog).filter(AuditLog.action == "reconstruction").count()
        segmentation_count = db.query(AuditLog).filter(AuditLog.action == "segmentation").count()
        
        print(f"\n当前数据库统计:")
        print(f"  图像融合: {fusion_count} 条")
        print(f"  三维重建: {reconstruction_count} 条")
        print(f"  场景分割: {segmentation_count} 条")
        print(f"  总计: {fusion_count + reconstruction_count + segmentation_count} 条")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 创建失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 50)
    print("创建测试报告数据")
    print("=" * 50)
    create_test_reports()
    print("\n现在可以刷新报告中心页面查看数据！")
