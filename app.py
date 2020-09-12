from flask import Flask, render_template, redirect, request
from line_pay import LinePay
from models import db, db_url, Transactions
from config import LINE_PAY_URL, LINE_PAY_CHANNEL_ID, LINE_PAY_CHANNEL_SECRET, LINE_PAY_CONFIRM_URL

app = Flask(__name__)
pay = LinePay(channel_id=LINE_PAY_CHANNEL_ID, channel_secret=LINE_PAY_CHANNEL_SECRET,
              line_pay_url=LINE_PAY_URL, confirm_url=LINE_PAY_CONFIRM_URL)


@app.route("/", methods=['GET'])
def index():
    return render_template('index.html')


@app.route("/pay/reserve", methods=['POST'])
def pay_reserve():
    product_name = "チョコレート"
    amount = 1
    currency = "JPY"

    (order_id, response) = pay.request_payments(product_name=product_name, amount=amount, currency=currency)
    print(response["returnCode"])
    print(response["returnMessage"])
    print(response)

    transaction_id = response["info"]["transactionId"]
    print(order_id, transaction_id, product_name, amount, currency)
    obj = Transactions(transaction_id=transaction_id, order_id=order_id,
                       product_name=product_name, amount=amount, currency=currency)
    db.session.add(obj)
    db.session.commit()
    db.session.close()
    redirect_url = response["info"]["paymentUrl"]["web"]
    return redirect(redirect_url)


@app.route("/pay/confirm", methods=['GET'])
def pay_confirm():
    transaction_id = request.args.get('transactionId')
    obj = Transactions.query.filter_by(transaction_id=transaction_id).one_or_none()
    if obj is None:
        raise Exception("Error: transaction_id not found.")

    response = pay.confirm_payments(transaction_id=transaction_id, amount=obj.amount, currency=obj.currency)
    print(response["returnCode"])
    print(response["returnMessage"])

    db.session.query(Transactions).filter(Transactions.transaction_id == transaction_id).delete()
    db.session.commit()
    db.session.close()
    return "Payment successfully finished."


def initialize_app(app: Flask) -> None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    app.config['DEBUG'] = True
    db.init_app(app)
    db.create_all(app=app)


def main() -> None:
    initialize_app(app)
    app.run(host='0.0.0.0', port=5000, threaded=True)


if __name__ == '__main__':
    main()
