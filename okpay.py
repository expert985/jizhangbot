import hashlib
import urllib.parse
import aiohttp
from typing import Dict, Optional
import config


class OKPay:
    """OKPAY支付集成类"""

    def __init__(self):
        self.app_id = config.OKPAY_APP_ID
        self.secret = config.OKPAY_SECRET
        self.api_url = config.OKPAY_API_URL

    def sign(self, data: Dict) -> Dict:
        """数据签名"""
        data['id'] = self.app_id
        # 过滤空值
        data = {k: v for k, v in data.items() if v is not None and v != ''}
        # 排序
        sorted_data = dict(sorted(data.items()))
        # 构建查询字符串
        query_string = urllib.parse.urlencode(sorted_data)
        # 添加token并计算MD5
        sign_string = f"{query_string}&token={self.secret}"
        sign = hashlib.md5(urllib.parse.unquote(sign_string).encode()).hexdigest().upper()
        data['sign'] = sign
        return data

    def check_sign(self, data: Dict) -> bool:
        """校验数据签名"""
        if 'sign' not in data:
            return False

        in_sign = data['sign']
        check_data = data.copy()
        del check_data['sign']

        # 过滤空值
        check_data = {k: v for k, v in check_data.items() if v is not None and v != ''}
        # 排序
        sorted_data = dict(sorted(check_data.items()))
        # 构建查询字符串
        query_string = urllib.parse.urlencode(sorted_data)
        # 添加token并计算MD5
        sign_string = f"{query_string}&token={self.secret}"
        sign = hashlib.md5(urllib.parse.unquote(sign_string).encode()).hexdigest().upper()

        return in_sign == sign

    async def create_pay_link(self, unique_id: str, amount: float, coin: str = 'USDT',
                             name: str = None, return_url: str = None) -> Optional[Dict]:
        """
        创建支付链接

        :param unique_id: 唯一订单号
        :param amount: 金额
        :param coin: 币种 (USDT, TRX)
        :param name: 显示信息
        :param return_url: 返回链接
        :return: {'order_id': 订单号, 'pay_url': 支付链接}
        """
        data = {
            'unique_id': unique_id,
            'amount': amount,
            'coin': coin
        }

        if name:
            data['name'] = name
        if return_url:
            data['return_url'] = return_url

        signed_data = self.sign(data)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}payLink",
                    data=signed_data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    result = await response.json()
                    if result.get('code') == 10000 and result.get('status') == 'success':
                        return result.get('data')
                    return None
        except Exception as e:
            print(f"创建支付链接失败: {e}")
            return None

    async def transfer(self, to_user_id: int, amount: float, coin: str = 'USDT',
                      unique_id: str = None, name: str = None) -> Optional[Dict]:
        """
        转账给用户

        :param to_user_id: 用户TG ID
        :param amount: 金额
        :param coin: 币种 (USDT, TRX)
        :param unique_id: 唯一订单号
        :param name: 显示信息
        :return: {'order_id': 订单号}
        """
        data = {
            'to_user_id': to_user_id,
            'amount': amount,
            'coin': coin
        }

        if unique_id:
            data['unique_id'] = unique_id
        if name:
            data['name'] = name

        signed_data = self.sign(data)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}transfer",
                    data=signed_data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    result = await response.json()
                    if result.get('code') == 10000 and result.get('status') == 'success':
                        return result.get('data')
                    return None
        except Exception as e:
            print(f"转账失败: {e}")
            return None

    async def check_user_exists(self, telegram_id: int) -> bool:
        """
        检查用户是否存在（是否启动过OKPAY钱包）

        :param telegram_id: Telegram用户ID
        :return: True/False
        """
        data = {'telegramID': telegram_id}
        signed_data = self.sign(data)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}censorUserByTG",
                    data=signed_data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    result = await response.json()
                    if result.get('code') == 10000 and result.get('status') == 'success':
                        data = result.get('data', {})
                        return data.get('exist', False)
                    return False
        except Exception as e:
            print(f"检查用户失败: {e}")
            return False

    async def check_transfer_by_txid(self, txid: str) -> Optional[Dict]:
        """
        检查订单是否完成

        :param txid: 订单号
        :return: 订单信息
        """
        data = {'txid': txid}
        signed_data = self.sign(data)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}checkTransferByTxid",
                    data=signed_data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    result = await response.json()
                    if result.get('code') == 10000 and result.get('status') == 'success':
                        return result.get('data')
                    return None
        except Exception as e:
            print(f"检查订单失败: {e}")
            return None


# 全局OKPAY实例
okpay = OKPay()
