from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import pymysql
from typing import List, Optional

from app.core.settings import settings


router = APIRouter()


class HousingInfo(BaseModel):
    """房屋信息模型"""
    id: Optional[int] = None
    # 根据实际数据库表结构添加字段
    # 示例字段：
    # address: Optional[str] = None
    # price: Optional[float] = None
    # area: Optional[float] = None
    # rooms: Optional[int] = None


def get_db_connection():
    """创建数据库连接"""
    try:
        connection = pymysql.connect(
            host=settings.db_host,
            user=settings.db_user,
            password=settings.db_password,
            database=settings.db_name,
            charset=settings.db_charset,
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except pymysql.Error as e:
        raise HTTPException(status_code=500, detail=f"数据库连接失败: {str(e)}")


@router.get("/", response_model=List[dict])
async def get_housing_info():
    """
    获取房屋信息
    
    Returns:
        List[dict]: 房屋信息列表
    """
    connection = None
    try:
        connection = get_db_connection()
        
        with connection.cursor() as cursor:
            # 查询家口表 - 请根据实际表名修改
            sql = "SELECT * FROM housing"
            cursor.execute(sql)
            result = cursor.fetchall()
            
        return result
        
    except pymysql.Error as e:
        raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")
    finally:
        if connection:
            connection.close()


@router.get("/{housing_id}", response_model=dict)
async def get_housing_by_id(housing_id: int):
    """
    根据ID获取单个房屋信息
    
    Args:
        housing_id: 房屋ID
        
    Returns:
        dict: 房屋信息
    """
    connection = None
    try:
        connection = get_db_connection()
        
        with connection.cursor() as cursor:
            # 根据ID查询 - 请根据实际表结构修改
            sql = "SELECT * FROM housing WHERE id = %s"
            cursor.execute(sql, (housing_id,))
            result = cursor.fetchone()
            
        if not result:
            raise HTTPException(status_code=404, detail="未找到该房屋信息")
            
        return result
        
    except pymysql.Error as e:
        raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")
    finally:
        if connection:
            connection.close()
