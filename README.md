# Sentinel2-3_batch_download
Sentinel卫星数据批量下载
# Sentinel 卫星数据下载脚本使用说明

## 简介

此脚本用于自动化从哥白尼数据空间 (CDS) 下载SENTINEL-2或SENTINEL-3任务的卫星数据。脚本支持根据时间范围、地理坐标和特定的卫星平台来检索并下载数据集。

## 功能特点

- 自动化检索SENTINEL-2和SENTINEL-3卫星数据。
- 通过地理坐标和时间范围定制化搜索。
- 支持指定卫星平台(`S2A`, `S2B`, `S3A`, `S3B`)。
- 使用`wget`进行高效的数据下载。
- 自动处理访问令牌获取。
- 中断信号的优雅处理机制，确保下载的可靠性。

## 环境要求

- Python 3.x
- 安装以下Python库：`requests`, `pandas`
- 网络连接
- 足够的存储空间以保存下载的数据文件
- 系统中需安装`wget`工具

## 安装依赖库

使用pip命令安装所需的Python库：

```bash
pip install requests pandas
```

## 使用前的配置

在运行脚本之前，您需要设置以下参数：

- `output_dir`: 保存下载数据的目录路径。
- `email`: 您的哥白尼数据空间账户的电子邮件地址。
- `password`: 您的哥白尼数据空间账户密码。
- `startDate`: 数据检索的开始日期（格式：`'YYYY-MM-DD'`）。
- `endDate`: 数据检索的结束日期（格式：`'YYYY-MM-DD'`）。
- `coordinates_str`: 数据检索的地理坐标（格式：`"LonMin LatMin, LonMax LatMin, LonMax LatMax, LonMin LatMax, LonMin LatMin"`）。
- `satelliteName`: 需要检索的卫星名称（可选值：`'SENTINEL-2'` 或 `'SENTINEL-3'`）。
- `contains_str`: 文件名中应包含的字符串，用于进一步筛选结果。
- `satelliteplatform`: 指定的卫星平台（对于SENTINEL-2, 可选值：`'S2A'` 或 `'S2B'`；对于SENTINEL-3, 可选值：`'S3A'` 或 `'S3B'`）。
- `timeliness`: 数据的及时性类别（仅SENTINEL-3，可选值：`'NR'` 或 `'NT'`）。

这些参数可以直接在脚本的`__main__`部分进行设置。

## 运行脚本

在配置好所有必要信息后，通过命令行界面运行脚本：

```bash
python sentinel_data_download.py
```

## 输入参数示例

以下是一个示例配置，该配置将会下载`SENTINEL-3`数据，日期为`2023-12-28`，地理坐标为一给定区域：

```python
output_dir = r"E:\SatelliteData\SENTINEL"
email = "your.email@example.com"
password = "your_password"
startDate = '2023-12-28'
endDate = '2023-12-28'
coordinates_str = "-159 23, -155 23, -155 19, -159 19, -159 23"
satelliteName = 'SENTINEL-3'
contains_str = 'OL_1_EFR___'
timeliness = 'NR'
satelliteplatform = 'S3A'
```

请确保将示例中的路径和凭证替换为您自己的信息。

## 中断处理

如果在下载过程中发生中断，例如用户按下`Ctrl+C`，脚本将停止当前的下载任务，并在下次运行时从停止处继续。

## 脚本输出

脚本运行时，所有状态和错误信息将在命令行界面中输出。下载的数据将保存

到`output_dir`指定的目录中。

## 联系信息

如遇到任何问题或需要技术支持，请通过以下方式联系开发者：

- 电子邮箱: your.email@example.com
- Github: https://github.com/yourgithub

## 许可证

在使用此脚本时，请遵守哥白尼数据空间的服务条款。您可以在脚本的许可证部分查看具体的条款内容。

---

请确保替换示例中的所有占位信息（如邮箱、密码、路径）以符合您的实际情况，并严格遵守哥白尼数据空间的使用条款。在使用脚本之前，请确保您有权访问和下载所请求的数据集。
