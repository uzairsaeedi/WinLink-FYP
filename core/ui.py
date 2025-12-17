from PyQt5 import QtWidgets


def show_info(parent, title: str, text: str, details: str = None, copy_text: str = None):
    dlg = QtWidgets.QMessageBox(parent)
    dlg.setIcon(QtWidgets.QMessageBox.Information)
    dlg.setWindowTitle(title)
    dlg.setText(text)
    if details:
        dlg.setDetailedText(details)
    try:
        copy_btn = dlg.addButton("Copy Details", QtWidgets.QMessageBox.ActionRole)
    except Exception:
        copy_btn = None
    dlg.addButton(QtWidgets.QMessageBox.Ok)
    dlg.exec_()
    if copy_btn and dlg.clickedButton() == copy_btn:
        data_to_copy = copy_text if copy_text is not None else (details or text)
        try:
            QtWidgets.QApplication.clipboard().setText(data_to_copy)
        except Exception:
            pass


def show_warning(parent, title: str, text: str, details: str = None, copy_text: str = None):
    dlg = QtWidgets.QMessageBox(parent)
    dlg.setIcon(QtWidgets.QMessageBox.Warning)
    dlg.setWindowTitle(title)
    dlg.setText(text)
    if details:
        dlg.setDetailedText(details)
    try:
        copy_btn = dlg.addButton("Copy Details", QtWidgets.QMessageBox.ActionRole)
    except Exception:
        copy_btn = None
    dlg.addButton(QtWidgets.QMessageBox.Ok)
    dlg.exec_()
    if copy_btn and dlg.clickedButton() == copy_btn:
        data_to_copy = copy_text if copy_text is not None else (details or text)
        try:
            QtWidgets.QApplication.clipboard().setText(data_to_copy)
        except Exception:
            pass


def show_error(parent, title: str, text: str, details: str = None, copy_text: str = None):
    dlg = QtWidgets.QMessageBox(parent)
    dlg.setIcon(QtWidgets.QMessageBox.Critical)
    dlg.setWindowTitle(title)
    dlg.setText(text)
    if details:
        dlg.setDetailedText(details)
    try:
        copy_btn = dlg.addButton("Copy Details", QtWidgets.QMessageBox.ActionRole)
    except Exception:
        copy_btn = None
    dlg.addButton(QtWidgets.QMessageBox.Ok)
    dlg.exec_()
    if copy_btn and dlg.clickedButton() == copy_btn:
        data_to_copy = copy_text if copy_text is not None else (details or text)
        try:
            QtWidgets.QApplication.clipboard().setText(data_to_copy)
        except Exception:
            pass


def ask_confirmation(parent, title: str, text: str, details: str = None, yes_text: str = "Yes", no_text: str = "No") -> bool:
    dlg = QtWidgets.QMessageBox(parent)
    dlg.setIcon(QtWidgets.QMessageBox.Question)
    dlg.setWindowTitle(title)
    dlg.setText(text)
    if details:
        dlg.setDetailedText(details)
    yes = dlg.addButton(yes_text, QtWidgets.QMessageBox.YesRole)
    no = dlg.addButton(no_text, QtWidgets.QMessageBox.NoRole)
    dlg.exec_()
    return dlg.clickedButton() == yes
