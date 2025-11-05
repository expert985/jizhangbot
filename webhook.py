#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OKPAY支付回调处理服务器
"""
from flask import Flask, request, jsonify
import asyncio
from database import db
from okpay import okpay
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route('/webhook/okpay', methods=['POST'])
def okpay_callback():
    """处理OKPAY支付回调"""
    try:
        data = request.form.to_dict()
        logger.info(f"收到OKPAY回调: {data}")

        # 验证签名
        if not okpay.check_sign(data):
            logger.error("签名验证失败")
            return jsonify({'status': 'error', 'message': 'Invalid signature'}), 400

        # 检查状态
        if data.get('status') == 'success' and data.get('code') == '10000':
            order_id = data.get('order_id')
            pay_user_id = int(data.get('pay_user_id'))
            amount = float(data.get('amount'))
            coin = data.get('coin')

            # 异步处理支付
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            payment = loop.run_until_complete(db.complete_payment(order_id, pay_user_id))

            if payment:
                # 延长用户会员时间
                loop.run_until_complete(db.extend_membership(payment.user_id, payment.days))
                logger.info(f"支付成功处理完成: 订单号={order_id}, 用户={payment.user_id}, 天数={payment.days}")

                return jsonify({'status': 'success'})
            else:
                logger.error(f"未找到订单: {order_id}")
                return jsonify({'status': 'error', 'message': 'Order not found'}), 404
        else:
            logger.warning(f"支付状态异常: {data}")
            return jsonify({'status': 'error', 'message': 'Invalid payment status'}), 400

    except Exception as e:
        logger.error(f"处理回调失败: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    import config
    app.run(
        host='0.0.0.0',
        port=config.WEBHOOK_PORT,
        debug=False
    )
