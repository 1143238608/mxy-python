import requests
from lxml import etree
import pymysql

# https://wuhan.anjuke.com/
headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
}
cookies = {
    "isp": "true",
    "aQQ_ajkguid": "87C3B0D7-D66C-4787-99C9-15080CE93EF6",
    "sessid": "1735C2F1-2B3B-4F60-99D0-9EA87E240BE8",
    "ajk-appVersion": "",
    "seo_source_type": "1",
    "fzq_h": "7c4073adbd2619ebe44849a9f8cc0338_1763779018076_7806b20a622343db83298a69a7727202_47901743517064072239722485354292405833",
    "obtain_by": "2",
    "twe": "2",
    "xxzlclientid": "f60ec479-2a5c-4bd5-8478-1763779018781",
    "id58": "OWQb0WkhIcpFPyqKCzelAg==",
    "xxzlxxid": "pfmxnIGgEm/D8imWqh/Bro5dsRlIosvhnaZhlyCvE4gwtDDk92cxiODPbgqrlXBREYhl",
    "58tj_uuid": "237867e8-efa4-4411-997a-bba8ff7d33f5",
    "init_refer": "https%253A%252F%252Fwuhan.anjuke.com%252F",
    "new_uv": "1",
    "wmda_uuid": "cab94a89e9f090161256c696a819f702",
    "wmda_new_uuid": "1",
    "wmda_session_id_8788302075828": "1763779029239-74d90afa-9e06-4966-81bf-c34b1b761ca4",
    "wmda_visited_projects": "%3B8788302075828",
    "als": "0",
    "new_session": "0",
    "ctid": "22",
    "wmda_report_times": "7",
    "xxzlbbid": "pfmbM3wxMDMyMnwxLjExLjF8MTc2Mzc3OTQ0MjcyMzIzNTc4NXxGRXpHbkdlbnBzOGpFbk5IdUVHS2FIU3EzUmRwekxINmV4SUhvZ0I4eE8wPXx8"
}
url = "https://wh.fang.anjuke.com/loupan/all/p5/"
response = requests.get(url, headers=headers, cookies=cookies).text

print(response)

tree = etree.HTML(response)

# 连接 MySQL 数据库（请将 database 改成你自己的库名）
connection = pymysql.connect(
    host="47.98.150.68",
    user="root",
    password="r0mxy1q2w3e4r",
    database="fastgpt",
    charset="utf8mb4"
)
cursor = connection.cursor()

insert_sql = """
INSERT INTO housing
    (name, price_amount, price_unit, area, address, household_type, size_range, detail, image_url)
VALUES
    (%s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

for i in range(60):
    if i != -1:
        home_name_xpath = '//*[@id="container"]/div[2]/div[1]/div[3]/div[' + str(i + 1) + ']/div/a[1]/span/text()'
        home_price_xpath = '//*[@id="container"]/div[2]/div[1]/div[3]/div[' + str(i + 1) + ']/a[2]/p/text()'
        home_price2_xpath = '//*[@id="container"]/div[2]/div[1]/div[3]/div[' + str(i + 1) + ']/a[2]/p/span/text()'
        home_address_xpath = '//*[@id="container"]/div[2]/div[1]/div[3]/div[' + str(i + 1) + ']/div/a[2]/span/text()'
        home_hx1_xpath = '//*[@id="container"]/div[2]/div[1]/div[3]/div[' + str(i + 1) + ']/div/a[3]/span[1]/text()'
        home_hx2_xpath = '//*[@id="container"]/div[2]/div[1]/div[3]/div[' + str(i + 1) + ']/div/a[3]/span[2]/text()'
        home_hx3_xpath = '//*[@id="container"]/div[2]/div[1]/div[3]/div[' + str(i + 1) + ']/div/a[3]/span[3]/text()'
        home_hx4_xpath = '//*[@id="container"]/div[2]/div[1]/div[3]/div[' + str(i + 1) + ']/div/a[3]/span[4]/text()'
        home_xq1_xpath = '//*[@id="container"]/div[2]/div[1]/div[3]/div[' + str(i + 1) + ']/div/a[4]/div/i/text()'
        home_xq2_xpath = '//*[@id="container"]/div[2]/div[1]/div[3]/div[' + str(i + 1) + ']/div/a[4]/div/span/text()'
        home_pic_xpath = '//*[@id="container"]/div[2]/div[1]/div[3]/div[' + str(i + 1) + ']/a[1]/img/@src'
        home_name = tree.xpath(home_name_xpath)[0]
        home_price = tree.xpath(home_price_xpath)
        home_price2 = tree.xpath(home_price2_xpath)[0] if tree.xpath(home_price2_xpath) else '售价待定'
        home_unit = home_price[-1]
        home_address = tree.xpath(home_address_xpath)[0]
        home_district = home_address.split(']')[0].strip('[')
        home_address = home_address.split(']')[1].strip('') if ']' in home_address else home_address
        home_hx1 = tree.xpath(home_hx1_xpath)[0]
        home_hx2 = tree.xpath(home_hx2_xpath)[0] if tree.xpath(home_hx2_xpath) else ''
        home_hx3 = tree.xpath(home_hx3_xpath)[0] if tree.xpath(home_hx3_xpath) else ''
        home_hx4 = tree.xpath(home_hx4_xpath)[0] if tree.xpath(home_hx4_xpath) else ''
        if home_hx3 != '':
            home_hx = home_hx1 + '/' + home_hx2 + '/' + home_hx3 + '|' + home_hx4
        else:
            home_hx = home_hx1 + '/' + home_hx2 + ' | ' + home_hx3
        home_xq1 = '|'.join(tree.xpath(home_xq1_xpath))
        home_xq2 = '|'.join(tree.xpath(home_xq2_xpath))
        home_xq = home_xq1 + home_xq2
        home_pic = tree.xpath(home_pic_xpath)[0]
        print(home_name, home_price2, home_unit, home_district, home_address, home_hx, home_xq, home_pic)

        # 处理价格，转换成小数，售价待定则为 None
        price_amount = None
        if home_price2 != '售价待定':
            try:
                price_str = ''.join(ch for ch in home_price2 if ch.isdigit() or ch == '.')
                price_amount = float(price_str) if price_str else None
            except ValueError:
                price_amount = None

        # 插入数据库
        cursor.execute(
            insert_sql,
            (
                home_name,
                price_amount,
                home_unit,
                home_district,
                home_address,
                home_hx,
                None,          # size_range 暂无数据
                home_xq,
                home_pic,
            ),
        )

# 提交事务并关闭连接
connection.commit()
cursor.close()
connection.close()

# //*[@id="container"]/div[2]/div[1]/div[3]/div/div/a[1]/span   名称
# //*[@id="container"]/div[2]/div[1]/div[3]/div[60]/a[2]/p    售价
# //*[@id="container"]/div[2]/div[1]/div[3]/div/div/a[2]/span  地址
# //*[@id="container"]/div[2]/div[1]/div[3]/div/div/a[3]   户型
# //*[@id="container"]/div[2]/div[1]/div[3]/div/div/a[4] 详情
# //*[@id="container"]/div[2]/div[1]/div[3]/div/a[1]/img/@src  图片
