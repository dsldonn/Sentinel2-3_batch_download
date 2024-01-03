# Sentinel2&3_batch_download
# Sentinel卫星数据批量下载
#
# Author: DSL
# Email: 757829990@qq.com
# Version: 1.1
# Last Updated: 2024-01-03

import os
import requests
import subprocess
import pandas as pd
import sys
import signal
from datetime import datetime, timedelta

temp_files = []  # 存储临时文件的列表,定义全局变量

class GracefulInterruptHandler(object):
    """用于优雅地处理中断的类"""

    def __init__(self, sig=signal.SIGINT):
        self.sig = sig

    def __enter__(self):
        self.interrupted = False
        self.released = False
        self.original_handler = signal.getsignal(self.sig)

        def handler(signum, frame):
            self.release()
            self.interrupted = True

        signal.signal(self.sig, handler)

        return self

    def __exit__(self, type, value, tb):
        self.release()

    def release(self):
        if self.released:
            return False

        signal.signal(self.sig, self.original_handler)
        self.released = True

        return True

def get_access_token(username, password):
    """
    获取Access Token
    :param username: 哥白尼网站用户名
    :param password: 哥白尼网站密码
    :return:
    """

    data = {
        "client_id": "cdse-public",
        "username": username,
        "password": password,
        "grant_type": "password",
    }
    try:
        response = requests.post("https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
                          data=data)
        response.raise_for_status()
        return response.json()["access_token"]
    except requests.RequestException as e:
        print(f"获取Access Token失败: {e}")
        sys.exit(1)

def format_coordinates(x1, y1, x2, y2):
    """
    :param x1:Lonmin
    :param y1:Latmin
    :param x2:Lonmax
    :param y2:Latmax
    :return:坐标字符串
    """
    # 构建坐标字符串
    coordinates = f"{x1} {y2}, {x2} {y2}, {x2} {y1}, {x1} {y1}, {x1} {y2}"
    return coordinates

def S2_build_search_url(start_date, end_date, satellite, contains_str, coordinates_str, satelliteplatform=None):
    '''
    获取下载URL
    :param start_date:'yyyy-MM-dd'
    :param end_date:'yyyy-MM-dd'
    :param satellite:所需卫星数据，如'SENTINEL-2'
    :param contains_str:检索时文件名需包括的字符串，如'MSIL1C'
    :param coordinates_str:检索区域，如"-159 23, -155 23, -155 19, -159 19, -159 23"
    :param satelliteplatform: 'S2A' or 'S2B', 默认为都检索
    :return:
    '''

    # %% 生成检索链接
    # 基础前缀
    base_prefix = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter="
    # 检索条件
    str_in_name = f"contains(Name,'{contains_str}')"
    collection = f"Collection/Name eq '{satellite}'"
    roi = f"OData.CSC.Intersects(area=geography'SRID=4326;POLYGON(({coordinates_str}))')"
    time_range = f"ContentDate/Start gt {start_date}T00:00:00.000Z and ContentDate/Start lt {end_date}T23:59:59.999Z"
    # 检索属性
    search_lim = "&$top=1000"  # 检索上限 不设置该项的话默认为20个 设置的话最大为1000
    expand_assets = "&$expand=Assets"  # 扩展检索结果的属性 添加后 检索结果中会多一项Assets 里面包含快视图id

    if satelliteplatform == None:
        part3 = ""
    else:
        part3 = f" and contains(Name,'{satelliteplatform}')"

    # 最终检索链接 记得检索条件之间要加 and
    request_url = f"{base_prefix}{str_in_name}{part3} and {collection} and {roi} and {time_range}{search_lim}{expand_assets}"
    return request_url

def S3_build_search_url(start_date, end_date, satellite, contains_str, coordinates_str, timeliness=None, satelliteplatform=None):
    '''
    获取下载URL
    :param start_date:'yyyy-MM-dd'
    :param end_date:'yyyy-MM-dd'
    :param satellite:所需卫星数据，如'SENTINEL-3'
    :param contains_str:检索时文件名需包括的字符串，如'OL_1_EFR___'
    :param coordinates_str:检索区域，如"-159 23, -155 23, -155 19, -159 19, -159 23"
    :param timeliness:'NR'/'NT',默认为都检索
    :param satelliteplatform: 'S3A' or 'S3B', 默认为都检索
    :return:
    '''

    # %% 生成检索链接
    # 基础前缀
    base_prefix = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter="
    # 检索条件
    str_in_name = f"contains(Name,'{contains_str}')"
    collection = f"Collection/Name eq '{satellite}'"
    roi = f"OData.CSC.Intersects(area=geography'SRID=4326;POLYGON(({coordinates_str}))')"
    time_range = f"ContentDate/Start gt {start_date}T00:00:00.000Z and ContentDate/Start lt {end_date}T23:59:59.999Z"
    # 检索属性
    search_lim = "&$top=1000"  # 检索上限 不设置该项的话默认为20个 设置的话最大为1000
    expand_assets = "&$expand=Assets"  # 扩展检索结果的属性 添加后 检索结果中会多一项Assets 里面包含快视图id

    if timeliness == None and satelliteplatform == None:
        part3 = ""
    elif timeliness != None and satelliteplatform == None:
        part3 = f" and contains(Name,'{timeliness}')"
    elif timeliness == None and satelliteplatform != None:
        part3 = f" and contains(Name,'{satelliteplatform}')"
    else:
        part3 = f" and contains(Name,'{satelliteplatform}') and contains(Name,'{timeliness}')"

    # 最终检索链接 记得检索条件之间要加 and
    request_url = f"{base_prefix}{str_in_name}{part3} and {collection} and {roi} and {time_range}{search_lim}{expand_assets}"
    return request_url

def download_data(data_id, data_name, access_token, output_dir, current, total):
    """
    数据下载
    :param data_id:数据ID
    :param data_name:文件名
    :param access_token:Access Token
    :param output_dir:保存目录
    :param current:已下载文件数
    :param total:全部文件数
    :return:
    """
    # 下载数据
    global temp_files
    file_path = os.path.join(output_dir, f"{data_name}.zip")
    if os.path.exists(file_path):
        print(f"文件 {file_path} 已存在，跳过下载")
        return

    temp_files.append(file_path)  # 将文件添加到临时列表中

    command = [
        "wget",
        "--header", f"Authorization: Bearer {access_token}",
        f"http://catalogue.dataspace.copernicus.eu/odata/v1/Products({data_id})/$value",
        "-O", file_path,
        "--show-progress"
    ]

    try:
        print(f"开始下载: {data_name} ({current}/{total})")
        subprocess.run(command, check=True)
        temp_files.remove(file_path)  # 下载完成后从临时列表移除
        print(f"下载成功: {data_name} ({current}/{total})")
    except subprocess.CalledProcessError as e:
        print(f"下载失败: {data_name}, 错误: {e} ({current}/{total})")
        # if file_path in temp_files:
        #     temp_files.remove(file_path)  # 如果发生错误，从临时列表中移除

def batch_download_data(output_dir, email, password, startDate, endDate, coordinates_str, satelliteName, contains_str, satelliteplatform=None, timeliness=None):
    """
    批量下载数据
    :param output_dir: 保存路径
    :param email: 哥白尼账户
    :param password: 哥白尼密码
    :param startDate: 开始日期
    :param endDate: 截止日期
    :param coordinates_str:检索区域坐标
    :param satelliteName: 检索卫星
    :param contains_str: 检索字符串，可以用来检索包含该字符串的数据，此处用来检索传感器
    :param timeliness: 检索timeliness
    :param satelliteplatform:检索对应卫星
    :return:
    """
    interrupted = False
    try:
        with GracefulInterruptHandler() as h:

            # request_url = build_search_url(startDate, endDate, satellite, contains_str, coordinates_str)
            if satelliteName =='SENTINEL-3':
                request_url = S3_build_search_url(startDate, endDate, satelliteName, contains_str, coordinates_str,
                                                  timeliness=timeliness, satelliteplatform=satelliteplatform)
            elif satelliteName =='SENTINEL-2':
                request_url = S3_build_search_url(startDate, endDate, satelliteName, contains_str, coordinates_str,
                                                  satelliteplatform=satelliteplatform)
            else:
                print("您输入的卫星名称有误，请输入'SENTINEL-2'或'SENTINEL-3'。")

            print(request_url)
            response = requests.get(request_url)
            df = pd.DataFrame.from_dict(response.json()['value'])

            if len(df) == 0:
                print('未查询到数据')
                data_name_list = []
                sys.exit()

            columns_to_print = ['Id', 'Name', 'S3Path', 'GeoFootprint']
            df[columns_to_print].head(3)

            data_id_list = df.Id
            data_name_list = df.Name
            total_files = len(data_id_list)
            print(f"总共需要下载 {total_files} 个文件。")
            for index, data_id in enumerate(data_id_list):
                access_token = get_access_token(email, password)
                download_data(data_id, data_name_list[index], access_token, output_dir, index+1, total_files)
                if h.interrupted:
                    print("检测到中断，正在清理未完成的下载...")
                    interrupted = True
                    break

    finally:
        # 清理未完成的下载
        for file_path in temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"已删除未完成的文件: {file_path}")
            except Exception as e:
                print(f"清理未完成文件时出错: {e}")

        if interrupted:
            print("下载任务因中断而停止")
        else:
            print("所有下载任务完成")


if __name__ == "__main__":
    """
    :param output_dir: 保存路径
    :param email: 哥白尼账户
    :param password: 哥白尼密码
    :param startDate: 开始日期
    :param endDate: 截止日期
    :param coordinates_str:检索区域坐标
    :param satelliteName: 检索卫星，'SENTINEL-2' or 'SENTINEL-3'
    :param contains_str: 检索字符串，可以用来检索包含该字符串的数据，此处用来检索传感器，如'OL_1_EFR___'
    :param timeliness: 检索timeliness，如'NR',SENTINEL-2没有此参数
    :param satelliteplatform:检索对应卫星，如'S2A'，'S3A'
    """
    # 基础设置
    startDate = '2023-12-28'
    endDate = '2023-12-28'
    satelliteShortName = 'SENTINEL-3'
    contains_str = 'OL_1_EFR___'
    coordinates_str = "-159 23, -155 23, -155 19, -159 19, -159 23"
    timeliness = 'NR'
    satelliteplatform = 'S3A'
    output_dir = r"更换为您的保存路径"
    email = "更换为您的账号"
    password = "更换为您的密码"

    batch_download_data(output_dir, email, password, startDate, endDate, coordinates_str, satelliteShortName, contains_str, timeliness=timeliness, satelliteplatform=satelliteplatform)