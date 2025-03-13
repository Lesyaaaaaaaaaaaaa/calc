
import math

n=10
T=10
r0=0.05
sigma = 0.1
u=math.exp(sigma/math.sqrt(T/n))
d=1/u
p=(math.exp(r0*(T/n))-d)/(u-d)
q=1-p
t=4
k=5
E1=70
E2=80

def build_binomial_tree(r0, u, d, periods, current_period=0, tree=None):
    """
    Рекурсивно строит биномиальное дерево процентных ставок.

    :param r0: Начальная процентная ставка
    :param u: Множитель роста ставки
    :param d: Множитель падения ставки
    :param p: Вероятность роста ставки
    :param periods: Общее количество периодов
    :param current_period: Текущий период рекурсии
    :param tree: Дерево, представленное в виде списка списков
    :return: Биномиальное дерево в виде списка списков
    """
    if tree is None:
        tree = []

    if current_period > periods:
        return tree

    if current_period == 0:
        tree.append([r0])
    else:
        previous_level = tree[current_period - 1]
        current_level = [previous_level[i] * u if i == 0 else previous_level[i - 1] * d for i in range(current_period + 1)]
        tree.append(current_level)

    return build_binomial_tree(r0, u, d, periods, current_period + 1, tree)

def build_zcb_matrix(rate_tree, p, q, T, current_T=None, zcb_tree=None):
    """
    Рекурсивно строит матрицу стоимости бескупонной облигации (ZCB).

    :param rate_tree: Биномиальное дерево процентных ставок.
    :param p: Вероятность повышения ставки.
    :param q: Вероятность понижения ставки.
    :param T: Общее число периодов.
    :param current_T: Текущий период рекурсии.
    :param zcb_tree: Матрица стоимости облигации.
    :return: Биномиальная матрица стоимости облигации.
    """
    if zcb_tree is None:
        zcb_tree = [[] for _ in range(T + 1)]

    if current_T is None:
        current_T = T  # Начинаем с последнего периода

    if current_T == T:
        # В последнем периоде стоимость облигации всегда равна 100%
        zcb_tree[current_T] = [100] * len(rate_tree[current_T])
    else:
        # Двигаемся назад, дисконтируя будущие значения
        next_prices = zcb_tree[current_T + 1]
        current_prices = []

        for i in range(len(rate_tree[current_T])):
            r = rate_tree[current_T][i]
            price = (p * next_prices[i] + q * next_prices[i + 1]) / (1 + r)
            current_prices.append(price)

        zcb_tree[current_T] = current_prices

    if current_T == 0:
        return zcb_tree

    return build_zcb_matrix(rate_tree, p, q, T, current_T - 1, zcb_tree)

def build_futures(example_tree, p, k, q, current_k=None, futures_tree = None):
    if futures_tree is None:
        futures_tree = [[] for _ in range(k + 1)]

    if current_k is None:
        current_k = k

    if current_k == k:
        futures_tree[current_k] = example_tree[k]
    else:
        next_prices = futures_tree[current_k + 1]
        current_prices = []

        for i in range(len(example_tree[current_k])):
            price = (p * next_prices[i] + q * next_prices[i + 1])
            current_prices.append(price)

        futures_tree[current_k] = current_prices

    if current_k == 0:
        return futures_tree

    return build_futures(example_tree, p, k, q, current_k - 1, futures_tree)

def E_solve(E, futures_tree, p, q, k, r, current_k=None, E_tree = None):
    if E_tree is None:
        E_tree = [[] for _ in range(k + 1)]

    if current_k is None:
        current_k = k

    if current_k == k:
        E_tree[current_k] = [i-E if (i-E)>0 else 0 for i in futures_tree[-1]]
    else:
        next_prices = E_tree[current_k + 1]
        current_prices = []

        for i in range(len(futures_tree[current_k])):
            if (futures_tree[current_k][i]-E)>0:
                if (futures_tree[current_k][i]-E)>(p*next_prices[i]+q*next_prices[i+1])/math.exp(r*T/k):
                    price = futures_tree[current_k][i]-E
                else:
                    price = (p*next_prices[i]+q*next_prices[i+1])/math.exp(r*T/k)
            else:
                if 0>(p*next_prices[i]+q*next_prices[i+1])/math.exp(r*T/k):
                    price = 0
                else:
                    price = (p*next_prices[i]+q*next_prices[i+1])/math.exp(r*T/k)
            current_prices.append(price)

        E_tree[current_k] = current_prices

    if current_k == 0:
        return E_tree

    return E_solve(E, futures_tree, p, q, k, r, current_k - 1, E_tree)

def calculate_all(r0, u, d, p, q, T, E, k, t):
    tree = build_binomial_tree(r0, u, d, T)
    zcb_tree = build_zcb_matrix(tree, p, q, T)
    forward_t = build_zcb_matrix(tree, p, q, t)
    example_tree = zcb_tree[:k + 1]
    futures = build_futures(example_tree, p, k, q)
    option_price = E_solve(E, futures, p, q, k, r0)
    forward = zcb_tree[0][0]/forward_t[0][0]
    return [round(option_price[0][0], 3), forward]



from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow, QApplication, QLabel, QCheckBox, QFontComboBox,
    QLineEdit, QVBoxLayout, QWidget, QPushButton
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Calc")
        self.setGeometry(300, 100, 500, 600)
        self.central_widget = QWidget(self)
        self.central_widget.setObjectName("central_widget")
        self.layout = QVBoxLayout(self.central_widget)

        self.input_field = QLineEdit(self)
        self.input_field.setObjectName("input_field")
        self.input_field.setPlaceholderText("Enter strike")
        self.input_field.setGeometry(100, 298, 145, 30)

        self.input_field_k = QLineEdit(self)
        self.input_field_k.setObjectName("input_field_k")
        self.input_field_k.setPlaceholderText("Enter k")
        self.input_field_k.setGeometry(255, 298, 145, 30)

        self.input_field_t = QLineEdit(self)
        self.input_field_t.setObjectName("input_field_t")
        self.input_field_t.setPlaceholderText("Enter t")
        self.input_field_t.setGeometry(100, 338, 145, 30)


        # Кнопка
        self.button = QPushButton("Calculate!", self)
        self.button.setObjectName("Calculate")
        self.button.setGeometry(255, 338, 145, 30)
        self.button.clicked.connect(self.calculate)

        # Поле результата
        self.result_label = QLabel("""Option price: 
Forward: """, self)
        self.result_label.setObjectName("result_label")
        self.result_label.setGeometry(100, 378, 301, 50)


        # Окно с текстом
        self.info_text = QLabel(
            """Calculations are performed with the following parameters:
Period T, n = 10 years
Starting bet r0 = 0.05%
Interest rate volatility σ = 0.1
Coefficient growth rate u = exp(σ*Sqrt(T/n))
Coefficient drop rate d = 1/u
Probability of growth p = (exp(r0*T/n)-d)/(u-d)
Probability of drop q = 1-p
            """, self)
        self.info_text.setWordWrap(True)
        self.info_text.setObjectName("info_text")
        self.info_text.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.info_text.setGeometry(89, 117, 320, 172)

        self.setCentralWidget(self.central_widget)

    def calculate(self):
        try:
            global E, k, t, T
            E = float(self.input_field.text())
            k = int(self.input_field_k.text()) if self.input_field_k.text() else k
            t = int(self.input_field_t.text()) if self.input_field_t.text() else t
            result = calculate_all(r0, u, d, p, q, T, E, k, t)
            self.info_text.setGeometry(89, 111, 320, 172)
            self.result_label.setText(f"""Option price: {result[0]}%
Forward: {round(result[1], 3)}""")
            self.info_text.setText(f"""The calculations were performed with the following parameters:
Period (T, n) = {T} years
Starting bet (r0) = 0.05%
Interest rate volatility (σ) = {sigma}
Coefficient growth rate (u) = {round(u, 3)}
Coefficient drop rate (d) = {round(d, 3)}
Probability of growth (p) = {round(p, 3)}
Probability of drop (q) = {round(1 - p, 3)}
Strike (E) = {E}
Point in time (k) = {k}
Point in time (t) = {t}
            """)
        except ValueError:
            self.result_label.setText("Error: enter the number")




if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    w = MainWindow()
    style = """
        QWidget#central_widget{
          background-image: url('calc jp (2).jpg');
          background-repeat: no-repeat; 
          background-position: center;
          background-size: cover;
        }
        QLabel#result_label{
            font-family: "Times New Roman";
            font-size: 15px;
            font-weight: bold;
            color: #8B4513;
            border: 2px solid #8B4513;
            border-radius: 8px;
            padding: 5px;
        }
        QLabel#info_text{
            font-family: "Times New Roman";
            font-size: 15px;
            font-weight: bold;
            color: #8B4513;
            border: 2px solid #8B4513;
            border-radius: 8px;
            padding: 5px;
        }
        QLineEdit{
            border: 2px solid #c9a769;  
            border-radius: 8px;  
            padding: 5px;
            font-size: 16px;
            color: #333;  
            background-color: #f9f9f9; 
        }
        QLineEdit:focus{
            border-color: #E584a6;  
            background-color: #fff;
        }
        QPushButton#Calculate{
            background-color: #FFB5C1;
            color: white;
            border-radius: 8px;
            padding: 5px;
            font-family: "Oswald";
            font-size: 14px;
            font-weight: bold;
        }
        QPushButton#Calculate:hover {
            background-color: #ff8397;
        }
        QPushButton#Calculate:pressed {
            background-color: #d96e7f;
        }
    """
    app.setStyleSheet(style)
    w.show()
    app.exec()

