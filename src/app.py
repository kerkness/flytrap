import sys
from PySide6.QtWidgets import QApplication
from window import MainWindow

app = QApplication(sys.argv)

window = MainWindow()
window.show()

if __name__ == "__main__":
    try:
        app.exec()
    except Exception as e:
        print(e)
    
